# Phase 5.16: Manager Nexus HUD 去重與真實數據對齊

**日期**: 2026-11-28  
**狀態**: 🟢 Completed（`bd59d3d7`, `5383535d` 已部署並完成線上 Playwright 實測）  
**關聯文件**: `GEMINI.md`, `PRPs/ai_docs/UI_STANDARDS.md`, `PRPs/Phase_5.5.7_Nexus_Consolidation_Self_Healing.md`

---

## 1. 背景與實測斷層（AS-IS）

對雲端 Supabase / `StatsService` 實測數值與線上 `/#/nexus`（`charlie@archon.com`）畫面比對後，確認以下斷層：

| 指標卡片 | 雲端 DB / Service 真實值 | Nexus 畫面顯示值 | 問題分類 |
| :--- | :--- | :--- | :--- |
| **Integrity** | `100.0%`（`21/21` sources indexed） | `85%` | `consolidated_service.py` 硬編碼 `85` |
| **Resources** | `$0.0046`（24h 成本） | `$0.00`（`Monthly Cap`） | 未映射 `system_telemetry.cost_24h` 且副標誤標 `Monthly Cap` |
| **Op Load** | `4` 筆待審 `blog_posts` | `0 Items` | 與側邊欄 `Approvals` 重複，且未查 DB |
| **Act Force** | `10` 位 `status='active'` | `0 Online` | 與側邊欄 `Team Management` 重複 |
| **Sent Risks / Ethics / Prompts** | `errors_24h: 0` | `0 Alerts` / `Secure` / `System` | 告警與審核同質重疊，`Prompts` 為靜態寫死字樣 |
| **Graph (Knowledge ROI)** | `0.0%` / `21 Total Nodes` | `0%` / `21 Total Nodes` | 「21 Total Nodes」與 `Integrity` 重疊 |
| **Collab / Reliability** | `+328.0%` / `100.0%` | `+328%` / `100%` | 與 DB 一致 |

---

## 2. 目標架構（TO-BE：10 張 → 6 張無重複核心指標）

1. **後端真實數據對齊與 `stats/` 硬編碼清理**
   - `python/src/server/services/stats/consolidated_service.py:72`：移除硬編碼 `health_score: 85 / 65` 與錯誤鍵名 `ov.get("error_count", 0)`，改讀 `ov.get("integrity_score", ...)` 與真實 `ov.get("errors_24h", 0)`。
   - `consolidated_service.py`：`system_telemetry` 回傳完整 `ov`（含真實 `cost_24h` 與 `errors_24h`），並以 `execute_query_async` / `asyncio.to_thread` 實查待審 `blog_posts`（`draft` / `changes_requested` / `pending`）與 24h `archon_logs` `ERROR`/`WARNING`，寫入 `pending_approvals` 與 `active_alerts`。
   - `python/src/server/services/stats/domains/system_metrics.py:85,91,95`：移除硬編碼 `"budget_limit": 100.0`、固定 `100000` token 上限與 `request_count * 1000` 估算，改讀 `BudgetConfig` / `SettingsService` SSOT（並優先對齊真實 token 用量來源）；同時檢視 `system_metrics.py:46,67` 無任務時預設 `100.0%` SLA 的標示語義。
   - `python/src/server/services/stats/performance.py:334-345`：將 `_get_agent_level` 的門檻數字（`880, 870, 850, 800, 700, 500`）抽離為具名常數/查表（SSOT）。
2. **前端 HUD 去重精簡（`enduser-ui-fe`）**
   - `NexusHUD.tsx`、`ManagerNexus.tsx`、`useManagerNexusStats.ts` 收斂為 6 張卡片：
     - `Integrity`（RAG 與系統健康度）
     - `Resources`（真實 `24H Token Cost`，移除錯誤的 `Monthly Cap` 標籤）
     - `Risk & Ethics`（合併 `Sent Risks` + `Ethics`）
     - `Collab`（跨部門協作動能）
     - `Graph`（Knowledge ROI 轉換率）
     - `Reliability`（SLA 達標率）
   - 移除重複或靜態卡片：`Op Load`（側邊欄已有 `Approvals`）、`Act Force`（側邊欄已有 `Team Management`）、`Prompts`（已於 `AdminPage` 管理）。
   - 遵守 `UI_STANDARDS.md`：靜態 Tailwind 格線類別（`grid-cols-2 md:grid-cols-3 lg:grid-cols-6`）、無動態插值字串、保留無障礙屬性。
3. **測試對齊（`NexusHUD.test.tsx`）**
   - 補齊精簡後 6 張卡片的真實渲染與 `Risk & Ethics` 合併行為斷言。

---

## 3. 驗收標準（無虛假驗證）

- [x] `make lint` 全數通過（`enduser-ui-fe`、`archon-ui-main`、`ruff`、`mypy`、`.single()`、`lean_proofs`）。
- [x] `python3 scripts/phase_audit.py` 顯示 `Found 0 monoliths (>400 lines)` 且 Step 7–11 全過。
- [x] `pytest tests/server/test_nexus_oracle.py -v` 與 `stats/` 相關單元測試全過，且 `enduser-ui-fe` `npx tsc --noEmit`、`npm run build`、`vitest run` 全過。
- [x] 部署後以無頭 Playwright 登入 `charlie@archon.com` 實測 `/#/nexus` 截圖，確認僅顯示 6 張去重卡片、`Integrity` 與 `Resources` 為真實 DB 數值、0 個 `4xx/5xx`。
