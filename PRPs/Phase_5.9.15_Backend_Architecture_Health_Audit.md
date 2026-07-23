# Phase 5.9.15: 後端四大架構動態健康度掃描與 3.3 巡檢戰線型別重構計畫

> **階段編號**: Phase 5.9.15  
> **當前狀態**: 進行中 / 階段一已完成 (Phase 1 Completed & Verified) 🟢  
> **目標子系統**: `scripts/` (健康度掃描器), `python/src/server/services/` (3.3 排程巡檢戰線)  
> **核心目標**: 建立 100% 動態、全覆蓋、數值守恆與零硬編碼的四大架構與戰略子要塞健康度掃描器，整合至 `make phase-audit`，並針對探測出之 3.3 巡檢戰線型別技術債進行 P2 補齊修復。

---

## 🛡️ 4 大執行鐵律規範 (Ironclad Constraints)

1. **消滅硬編碼 (No Hardcoding)**：嚴禁硬編碼任何閾值、Cron 時區或 Prompt，統一由 `SettingsService` / `PromptService` SSOT 動態讀取。
2. **防範副作用 (Don't break A while fixing B)**：僅補充強型別宣告 (`: str`, `-> Dict[str, Any]`, `-> None`)，嚴禁更動運行期相容邏輯，修復前後執行全套測試防止改 A 壞 B。
3. **巨型檔案門禁防線 (No Monolith Files > 400 lines)**：`scheduler_service.py` 目前為 369 行，重構後**嚴禁超過 400 行**門禁上限；若接近上限必須抽離微型輔助函式至子模組。
4. **物理穿透驗證 (No Fake Verification)**：修復後必須實體執行 `make lint-be`、`make test-be-fast` 與 `make phase-audit`，以真實數據證實 3.3 型別覆蓋率升至 85%+、健康度升至 90%+ 🟢！

---

## 1. 執行摘要與痛點診斷

### 當前系統現況與診斷
1. **四大架構動態健康度掃描器 (已完成 🟢)**：
   - 建立 `scripts/backend_type_health.py`，實作型別覆蓋率 ($50\%$)、無巨型檔案率 ($30\%$) 與穩定基礎 ($20\%$) 之綜合評級公式。
   - 實現全覆蓋 (Exhaustive Categorization) 與數值守恆，確保 17 個 Sub-domains 子項目之檔案與代碼行數加總 100% 等於 4 大主模組。
   - 徹底消滅 `PRESET_DESCS` 與 `EVOLUTION_DESCS` 文字硬編碼，改為 AST 動態特徵探測與 `health_baseline.json` 歷史基線對比。
   - 整合至 `scripts/phase_audit.py` 作為 Step 6 自動化品質門禁。

2. **3.3 背景與排程巡檢戰線型別技術債 (待執行階段二)**：
   - **實體痛點**：經動態掃描探測，`3.3 背景與排程巡檢戰線` 的型別覆蓋率僅為 **39.3%**（最新健康度 69.7% 🟡），為全後端 17 個分區中唯一低於 70% 的弱勢戰線。
   - **核心病灶**：`scheduler/jobs/` 目錄下的 7 個巡檢腳本（`leads_patrol.py`, `tech_debt_patrol.py`, `cleanup_patrol.py` 等）以及 `scheduler_service.py` 中有 28 個 helper 函式完全缺少 Return / Parameter Type Hints。
   - **效益與目標**：由 P2 (Jules 代理型別守護者) 補齊 Type Hints，預期將 3.3 型別覆蓋率拉升至 **85%+**，健康度跨越至 **90%+ 🟢**。

---

## 2. 實作架構與戰略子分區 (Sub-domains) 規劃

### 後端四大架構全覆蓋對照
* **1. MCP 協議擴充 (`mcp_server` - 28 檔 / 3,211 行)**
  * `├─ 1.1 核心服務與 Server 路由` (8 檔 / 1,122 行)
  * `├─ 1.2 知識與 RAG 工具鏈` (6 檔 / 796 行)
  * `├─ 1.3 專案與工單工具鏈` (5 檔 / 703 行)
  * `└─ 1.4 行銷、開發與設計工具鏈` (9 檔 / 590 行)

* **2. 自主 Agent 引擎 (`agents` - 30 檔 / 3,576 行)**
  * `├─ 2.1 核心執行與推演引擎` (5 檔 / 1,064 行)
  * `├─ 2.2 DB 狀態斷點與快照 (Checkpoint)` (1 檔 / 99 行)
  * `├─ 2.3 HITL 人工審核防線 (Approval)` (1 檔 / 117 行)
  * `└─ 2.4 多 Agent 工作流與專屬 Agent` (23 檔 / 2,296 行)

* **3. 核心業務服務 (`services` - 205 檔 / 26,353 行)**
  * `├─ 3.1 RAG 與向量檢索核心` (70 檔 / 8,467 行)
  * `├─ 3.2 Model SSOT 與 Prompt 治理` (37 檔 / 3,825 行)
  * `🚨 3.3 背景與排程巡檢戰線` (12 檔 / 2,288 行 - **重點重構標的**)
  * `├─ 3.4 Auth 與細粒度 RBAC` (4 檔 / 537 行)
  * `├─ 3.5 CRM 與行銷業務核心` (32 檔 / 4,983 行)
  * `└─ 3.6 Agent 核心與基礎設施` (50 檔 / 6,253 行)

* **4. API 門戶與路由 (`api_routes` - 49 檔 / 5,443 行)**
  * `├─ 4.1 系統治理、Auth 與 HITL 端點` (11 檔 / 1,455 行)
  * `├─ 4.2 商業行銷與內容端點` (12 檔 / 1,648 行)
  * `├─ 4.3 知識庫、AI 與模型端點` (19 檔 / 1,709 行)
  * `└─ 4.4 資源、設定與檔案端點` (7 檔 / 631 行)

---

## 3. 驗證與公證計畫 (Verification Plan)

### 自動化測試與門禁
1. **動態掃描器驗證**：
   - 執行 `python scripts/backend_type_health.py`，確認 4 大模組與 17 個 Sub-domains 檔案數與行數相加 100% 數值守恆。
2. **Phase Audit 門禁公證**：
   - 執行 `make phase-audit`，確認 Step 6 能穩定輸出包含「基準健康度」、「最新健康度」、「實體檔案數/行數 (含 ↑/↓ 箭頭)」、「型別覆蓋率」與「最新演進說明」之完整 Markdown 表格。
3. **P2 巡檢戰線重構驗證 (Phase 2)**：
   - Jules 代理完成型別補齊後，執行 `make lint-be` 與 `make phase-audit`，確認 3.3 健康度升至 90%+ 🟢，無巨型檔案報錯，且所有單元測試綠燈通過。
