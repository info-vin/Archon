# Phase 5.14: 新版 Lead 評分（LLM 結構化分類 A/B/C/X）與 G1 / G3 / G4 可觀測性硬化 (PRP)

## 1. 背景與目標 (Background & Objectives)

依據 2026-11-18 與 2026-11-19 定案之評分決策（已整併至 [GEMINI.md](file:///Users/vincenta/GoogleKwok022/Archon/GEMINI.md)）：
* **問題根因**：現行 [job_board_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/job_board_service.py#L139-L196) 第一層 HyDE 向量相似度在 46 筆樣本上 AUC 僅 `0.50`（置換檢定 `p ≈ 0.98`，與亂猜無異），且第二層 `llm_judge` 只回傳 `YES / NO`，無拒絕理由、無分類標籤，被刷掉的職缺也未結構化留存，無法做人工校準。
* **本階段目標（合併 G1 / G3 / G4 與新版第二層評分為單一可審核 PR，合併前需經 Vincent 核准）**：
  1. **G1**：將被刷掉的職缺以結構化 JSON 寫入 `archon_logs`（**不在 `leads` 表新增 `discarded` 狀態**，遵守不破壞現有 7 處未過濾 status 查詢之決議）。
  2. **G3**：將 `leads_patrol.py` 各排程任務的「開始 (`start`)」與「例外 (`error`)」統一結構化寫入 `archon_logs`。
  3. **G4 + 第二層 LLM 結構化分類 (`A / B / C / X`)**：將 `llm_judge` 升級為回傳結構化 JSON `{category, confidence, reason}`，依 2026-11-18 ICP 規則分類並記錄拒絕理由。
  4. **A:B = 60:40 配額制**：在批次寫入 `qualified` 潛客時依 A:B 60:40 採配額制篩選（不直接乘進評分權重）。

---

## 2. Pre-Action Risk Assessment & Comprehensive Impact Analysis

### 2.1 受影響檔案清單
| 檔案 | 修改性質 | 風險與防禦 |
| :--- | :--- | :--- |
| [sales_prompts.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/prompts/sales_prompts.py) | 升級 `ALICE_LEAD_JUDGE_DEFAULT` 為 A/B/C/X 結構化 JSON 規則 | 若 DB `archon_prompts` 內已有舊版 `ALICE_LEAD_JUDGE`，需同步提供 SQL migration 更新或先檢查線上 prompt，避免「改了預設值但線上仍跑舊 DB prompt」。 |
| [lead_evaluator.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/crawling/lead_evaluator.py) | 新增 `LeadJudgeResult` DTO 與 `evaluate_lead_structured(job)`，保留 `llm_judge(job) -> bool` 相容包裝 | LLM 若偶發回傳非純 JSON（含 markdown code fence），需先做 JSON 提取與 Pydantic 驗證；解析失敗一律 fail-safe 為 `X` 並記錄原文於 `reason`。 |
| [job_board_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/job_board_service.py) | 接入 `evaluate_lead_structured`、實作 G1 結構化寫入 `archon_logs`、G4 記錄拒絕理由、實作 A:B 60:40 配額 | 遵守 `CONTRIBUTING_tw.md` 原則 18：G1 淘汰紀錄在迴圈外一次性 Bulk Insert 至 `archon_logs`，禁止迴圈內逐筆寫入。 |
| [leads_patrol.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/scheduler/jobs/leads_patrol.py) | 實作 G3：排程開始 (`start`) 與例外 (`error`) 結構化寫入 `archon_logs` | 記錄 `job_name`, `phase` (`start`/`completed`/`error`), `error_type`, `error_message`，不改變原本排程回傳值與冷卻機制。 |
| 測試檔案 | 補齊單元測試並檢查所有依賴 `llm_judge` / `JobBoardService` 的既有測試 Mock | 嚴守 `GEMINI.md` Rule 13（防範虛假測試與回傳型別斷層），先 `git grep llm_judge` 盤查所有呼叫點與測試。 |

### 2.2 明確不做（Out of Scope，避免改 A 壞 B）
* **不修改 `leads` 資料表新增 `discarded` 狀態**（維持 2026-11-18 決議，人工標記過渡兩週走試算表）。
* **不改動 `model_ssot.py` 升級至 Gemini 4**（維持現有 `DEFAULT_TEXT`，避免混入模型變因干擾評分校準）。
* **不更動現有 104 WAF 延遲與 `curl_cffi` 指紋邏輯**。

---

## 3. 詳細實作設計 (Implementation Details)

### 3.1 ICP 分類定義（A / B / C / X）
寫入 `ALICE_LEAD_JUDGE_DEFAULT`（並同步檢查 Supabase `archon_prompts`）：
* **`A`（核心目標客群）**：30–300 人之傳統／非軟體企業、研究機構或醫院，職缺顯示缺乏內部 AI 團隊、有數位轉型／流程自動化／系統整合外包痛點。
* **`B`（小型潛客／轉介）**：規模較小（約 30 人以下）但有明確 AI 導入或自動化需求之企業，列為轉介候選。
* **`C`（明確排除）**：同業 AI/LLM 軟體公司、SI 系統整合商、人力派遣、獵頭顧問、自動化設備商。
* **`X`（無關職缺）**：與 AI／自動化／系統整合無關之一般職缺或資訊不足無法判斷。

**強制 JSON 輸出格式**：
```json
{
  "category": "A",
  "confidence": 0.85,
  "reason": "傳統製造業徵求流程自動化窗口，非同業且具備系統整合痛點"
}
```

### 3.2 G1：被刷職缺結構化寫入 (`archon_logs`)
* 在 `JobBoardService.identify_leads_and_save` 中，對第一層（向量相似度未過）與第二層（LLM 判定為 `C` 或 `X`）被刷掉的職缺，收集至 `rejected_logs: list[dict]`，於批次結束後一次性 Bulk Insert 至 `archon_logs`：
  * `source`: `"job_board_service_triage"`
  * `level`: `"INFO"`
  * `message`: `f"Lead rejected [{stage}]: {job.company} - {job.title}"`
  * `details`: `{"stage": "layer1_similarity" | "layer2_llm_judge", "company": ..., "job_title": ..., "url": ..., "keyword": ..., "similarity": ..., "category": ..., "confidence": ..., "reason": ...}`

### 3.3 G3：排程開始與例外寫入 (`leads_patrol.py` / `scheduler/utils.py`)
* 在 `run_auto_fetch_leads`、`run_prune_stale_leads`、`run_market_report` 的入口與 `except Exception` 區塊，透過共用 helper `log_patrol_event(job_name, phase, message, details)` 寫入 `archon_logs`（`phase` 為 `"start"` / `"completed"` / `"error"`）。

### 3.4 G4 與 A:B = 60:40 配額制
* `evaluate_lead_structured(job)` 永遠回傳 `LeadJudgeResult(category, confidence, reason)`，拒絕理由 (`reason`) 隨 G1 一起落盤。
* 通過篩選的 `A`、`B` 類候選名單，在寫入 `leads` 前依 **60:40 配額制** 分配 `qualified` 名額（例如單批上限為 `N` 時，A 類優先佔 60%、B 類佔 40%，若其中一類不足則保留實際數量，不直接把 0.6/0.4 乘進 `enrichment_score`）。
* `enrichment_score` 改由結構化信心分數與分類映射（例如 `int(round(confidence * 100))`），並在 `identified_need` 前綴標註 `[A類]` / `[B類]` 與判斷理由，方便人工試算表複核。

---

## 4. 驗收標準與驗證閘門 (Acceptance Criteria & Gates)
- [x] **靜態與架構門禁**：`ruff check`、`mypy src/`（397 檔 0 錯誤）、`scripts/phase_audit.py` 全門禁通過。
- [x] **單元測試**：
  - `evaluate_lead_structured` 覆蓋 A / B / C / X 正常 JSON、Markdown 包裹 JSON、非法 JSON fail-safe 測試。
  - G1 驗證被刷職缺以單次 Bulk Insert 寫入 `archon_logs` 且含 `category / confidence / reason`。
  - G3 驗證 `leads_patrol` 開始與例外皆寫入 `archon_logs`。
  - 配額測試驗證 A:B = 60:40 配額邏輯，且未在 `leads` 產生 `discarded` 狀態。
- [x] **人工校準門檻（合併前 / 上線校準）**：
  - 2026-11-26 完成 39 筆實測樣本人工標記比對（`A:6, B:3, C:30`）：初版精確準確率 **82.1%（32/39）**、二元合格準確率 **84.6%（33/39）**；將 2 筆誤放行（`新立資訊`、`暉睿智能`）歸檔為 `archived` 並微調 `ALICE_LEAD_ICP_CRITERIA`（同步 `archon_prompts`）後，7 筆差異樣本重測 **6/7 完全命中**，且補跑 3 個中文關鍵字 via `gemini-decision-1` 正常寫入 6 筆新潛客。
- [x] **另案提醒**：`migration/20261118_revoke_truncate_and_test_rpcs.sql` 已由 Vincent 於雲端 Supabase 執行完成。
