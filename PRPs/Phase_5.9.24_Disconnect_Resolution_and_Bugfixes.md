# Phase 5.9.24 - Disconnect Resolution and Bugfixes (架構斷層修復)

## 📌 Phase Objective (階段目標)
本階段旨在修復系統在執行「背景排程作業 (Stateful Jobs / Scheduler)」與「資料處理管線」時所暴露出的三大架構與文件斷層 (Disconnects)。這些問題不僅影響週日排程，更會隨機阻斷任何觸發上述路徑的日常作業。斷層包含：幻覺與未對齊 SSOT 的資料表參照、遺漏更名的殘留代碼、以及全域多處違反架構鐵律的高風險 `.single()` 資料庫存取寫法。

## 🛠️ Action Items (執行項目)

### 1. 根除全域 `.single()` 崩潰與 HTTP 500 (落實 GEMINI.md 鐵律 12)
- **歷史脈絡與改 A 壞 B 風險評估**:
  - **歷史探勘**: 透過 `git blame` 追溯，`settings_service.py` 的 `.single()` 寫法是在 `fix(auth): root-cause navigation and permission instability` (2026/02/05) 時被引入。雖然外層包了 `try-except Exception:`，但在 Supabase Python Client 的底層，當查詢為 0 筆時 `.single()` 依然會噴出 `APIError (PGRST116)`。這會導致背景服務 (如 `execute_query` 裝飾器) 攔截並印出巨量的 Error Traceback，進發錯誤警報甚至中斷 Transaction。
  - **退化現象**: 在 `document_service.py` 中，過去 100 多行的安全查詢邏輯，在近期的重構中被粗暴地縮減為 `res = ...single().execute()`，完全忽略了「找不到專案」的合法邊界情況 (Edge Case)。
  - **防破壞替換策略 (Safe Refactoring)**:
    - 絕不直接把 `.single()` 刪掉就收工。
    - 必須改為 `.execute()`，並**嚴格檢查回傳陣列長度 (`if not res.data:`)**。
    - **型別對齊**: 如果原本 `.single().execute().data` 是回傳 `dict`，修改後必須回傳 `res.data[0]` 以維持 Caller 端的型別不變，避免改 A (修復 SQL Error) 壞 B (造成 Caller 端 `TypeError: list indices must be integers`)。
- **盤點清單**: 以下 10 個檔案共 13 處將依照上述策略安全替換：
  1. `python/src/server/services/settings_service.py` (Line 78) 
  2. `python/src/server/api_routes/pages_api.py` (Line 155, 187)
  3. `python/src/server/services/blog_service.py` (Line 34)
  4. `python/src/server/services/enrichment_service.py` (Line 26)
  5. `python/src/server/services/knowledge/knowledge_item_service.py` (Line 52)
  6. `python/src/server/services/marketing/approval_manager.py` (Line 58)
  7. `python/src/server/services/marketing/blog_generator.py` (Line 204)
  8. `python/src/server/services/projects/document_service.py` (Line 71, 97, 111)
  9. `python/src/server/services/projects/project_service.py` (Line 107)
  10. `python/src/server/services/projects/versioning_service.py` (Line 124)

### 2. 修復幽靈資料表 `projects` 參照 (Phase 5.9.19 遺漏)
- **問題點**: 雖然資料庫已在 Phase 5.9.19 將 `projects` 遷移為 `archon_projects`，但 `report_service.py` 與 `tests/test_supabase_stateful_mock.py` 仍殘留對舊表名的查詢，引發 `PGRST205` 錯誤。
- **修復方案**: 
  - 替換 `supabase_client.table("projects")` 為 `supabase_client.table("archon_projects")`，與 Schema SSOT 對齊。
  - 同步更新測試檔中的 mock 實體。

### 3. 校正 `archon_approvals` 幻覺，對齊 SSOT 表格
- **問題點**: `NexusOracleAgent` (在 `nexus_oracle_agent.py`) 硬編碼依賴了 `archon_approvals` 進行健康度審查，但系統的 Single Source of Truth (SSOT) 簽核資料表實為 `agent_pending_approvals`。此幻覺硬編碼導致 Agent 查詢不存在的表並超時鎖死 180 秒。
- **修復方案**: 
  - **不新增多餘的 SQL 資料表**。
  - 將 `nexus_oracle_agent.py` 中硬編碼的 `supabase.table("archon_approvals")` 更改為正確的 SSOT 實體：`supabase.table("agent_pending_approvals")`，從根本解決架構斷層。

## 🛡️ Architecture Hardening (架構防禦升級與自動化驗證)

為杜絕未來再次發生類似斷層，我們將導入以下**自動化驗證與防禦機制**：

1. **實作 `.single()` 靜態掃描門禁 (CI/CD Linter)**
   - **作法**: 在 `Makefile` 的 `lint-be` 指令或 Git Pre-commit Hook 中，加入簡單的 Regex 掃描器 (`grep -r "\.single()" python/src/ | grep -v "tests/"`)。
   - **效果**: 若未來有工程師或 Agent 再次試圖寫入 `.single()`，CI/CD 將直接中斷 (Exit Code 1) 並拒絕 Commit，強制其改用 `.execute()` 陣列。
2. **擴充現有 `phase_audit.py` 進行實體「三向連動」查核 (Physical Schema Audit)**
   - **作法**: 絕不盲目新增腳本。我們將直接擴充現有的 `scripts/phase_audit.py` (此腳本專職於查核斷層)，加入掃描 `migration/` 資料夾下 `.sql` 表名的邏輯，並與 `python/src/` 的代碼進行實體交叉比對。
   - **效果**: 透過原生的 `make phase-audit` 門禁，在 CI/CD 階段就能將「資料庫有、但代碼沒寫」或「代碼有、但資料庫沒建」的斷層攔截，避免幽靈呼叫 (如 `projects`) 再次發生。
3. **SSOT 唯一信任源**
   - 開發 Agent 操作資料庫時，必須先查閱其他 Manager 或 Schema 文件，嚴禁靠直覺硬編碼與幻覺捏造資料表。
