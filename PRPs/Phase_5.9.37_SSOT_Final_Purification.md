# Phase 5.9.37: SSOT Final Purification (The Last 38 Violations)

## Goal
徹底消除系統中最後殘存的 38 項 SSOT 違規（Hardcoded String Set Literal），涵蓋 `rbac_service.py`、`agent_registry.py` 以及其餘服務中的硬編碼字串陣列。這將完成整個系統的「SSOT（單一事實來源）淨化」最後一哩路。

## User Review Required
> [!IMPORTANT]
> 此階段將修改系統的核心 RBAC 邏輯模組 (`rbac_service.py`)，將其中大量的硬編碼角色 (如 `"admin", "manager", "employee"`) 替換為統一的 `RoleEnum`。請確認此架構調整符合您的期望。

## 開發歷程比對 (Development History Context)
根據 `git log` 的歷史追溯，這些硬編碼陣列的形成有以下兩種不同脈絡：

1. **架構債 (需重構為 Enum)**: 
   - `rbac_service.py` 中的角色權限矩陣是在 2026 年 1 月 (Phase 4.4.3 & 5.1) 由開發者 (tek Atrust) 建立。當時為了直接對應資料庫欄位，手動寫死了 `"admin", "system_admin", "manager"` 等字串，並隨著時間推移從小寫變大寫再變回小寫。這正是 SSOT 缺失的典型技術債，必須使用 `RoleEnum` 來統一。
2. **合法靜態宣告 (需加入 `# 合法` 註解)**:
   - `extraction_service.py` (Phase 4.6.23) 中的 `["name", "domain_pattern", "schema_definition"]` 是為了防禦惡意 Payload 注入，所設立的明確 JSON Schema Key 過濾器。
   - `agent_registry.py` (Phase 4.6.24) 中的 `"tools": ["search_job_market", "generate_sales_email"]` 是 Agent 靜態配置檔 (Config) 的一部分，用來對應 MCP Tool Names。
   - 這些陣列在物理意義上屬於「特定邏輯的靜態邊界」，強行抽出為 Enum 反而會造成「過度工程化 (Over-engineering)」並破壞原檔案的內聚性。因此，對於這些陣列，符合我們在 `GEMINI.md` 中的「# 合法」標註規範。

## Proposed Changes

### 1. 角色與權限核心 (RBAC & Auth)
我們將全面使用 `shared_constants.py` 中的 `RoleEnum` 取代散落各處的字串。
- **[MODIFY]** `python/src/server/services/rbac_service.py`
  - 替換所有角色關聯矩陣 (Role Mapping) 與權限檢查陣列 (如 `["admin", "system_admin"]`)，改用 `RoleEnum`。
- **[MODIFY]** `python/src/server/services/agent_service.py`
  - 第 65 行：替換 `["admin", "system_admin", "manager"]` 為 `RoleEnum` 陣列。
- **[MODIFY]** `python/src/server/services/crawler_service.py`
  - 第 39 行：替換權限檢查為 `RoleEnum`。

### 2. 背景任務與系統日誌 (Tasks & Logs)
- **[MODIFY]** `python/src/server/services/background_task_manager.py`
  - 第 191 行：狀態檢查 `["complete", "error", "cancelled"]` 替換為 `TaskStatusEnum` / 常數。
- **[MODIFY]** `python/src/server/services/marketing_service.py` & `report_service.py`
  - 處理寫死的日誌等級查詢 (`"ALERT"`, `"ERROR"`) 等，加入 `# 合法` 或對應常數。

### 3. 白名單合法陣列 (Whitelist Static Mappings)
超過半數的違規屬於「合法且合理的靜態陣列」（如 Beautifulsoup 標籤、LLM 解析關鍵字、Librarian 歸檔 Tags、指令參數等）。為了避免過度工程化 (Over-engineering)，我們將以自動化腳本為這些特定行尾標註 `# 合法`。
- **[MODIFY]** `extraction_service.py` (Line 154) - Schema keys
- **[MODIFY]** `agent_registry.py` (Lines 72, 90, 96) - Agent Tools 陣列
- **[MODIFY]** `crawler_service.py` (Line 70) - `soup(["script", "style", "nav", "footer"])`
- **[MODIFY]** `librarian/business_archiver.py` (Lines 34, 135, 223) - 啟發式標籤 (Tags)
- **[MODIFY]** `librarian/web_archiver.py` (Line 92) - 啟發式標籤 (Tags)
- **[MODIFY]** `librarian/file_archiver.py` (Line 39) - 啟發式標籤 (Tags)
- **[MODIFY]** `lean/compiler_service.py` (Line 36) - CLI args `["lake", "build"]`
- **[MODIFY]** `llm/parsing.py` (Line 85) - Parser Keys
- **[MODIFY]** `llm/models.py`, `llm/utils.py`, `llm/clients.py` - Providers 清單檢查
- **[MODIFY]** `llm/hybrid_router.py` (Line 46) - `keywords` 陣列

### 4. `job_board_service.py` 進階 SSOT 與 DRY 淨化 (擴充目標)
根據最新的深度 Code Review，在完成 LLM 呼叫的 DRY 重構後，我們發現在資料存取層與配置解析上仍存在架構債：
- **DRY 違規 (配置讀取重複)**：`auto_fetch_daily_leads` 與 `_process_single_job` 中各自撰寫了 `SettingsService` 並透過 `try-except` 解析 `CrawlerJobConfig` 的邏輯。應抽離為統一的 `_get_crawler_config(self)`。
- **DRY 違規 (系統日誌重複)**：程式碼中三處散落 `self.supabase.table("archon_logs").insert(...).execute()`，缺乏共用的日誌方法。
- **SSOT 違規 (繞過 Repository)**：大量依賴 `self.supabase.table("leads")....execute()`。根據 Phase 5.9.32 的規範，所有資料庫寫入應收斂至 `BaseRepository.execute_query`，不該在 Service 中手刻 Supabase 查詢。
- **嚴重脆性硬編碼 (Brittle Hardcoding)**：
  - `_get_core_text` 依賴脆弱的字串切割 (例如 `content.find("### Knowledge Base Tools")`) 來讀取 `AGENTS.md`，極易因文件微調而靜默崩潰。
  - `initial_delay=2.0` 在 `@retry_with_backoff` 中被硬編碼。
  - 數十行的繁體中文預設提示詞 (`default_prompt`) 直接寫死在代碼中，而非由資料庫或配置檔集中管控。

## Verification Plan
### Automated Tests
- `make lint-be`：確保替換 `RoleEnum` 時不會再次發生型別錯誤。
- `make test-be`：確保 616+ 項後端單元測試與 E2E 測試皆通過。
- `make phase-audit`：確保所有 `Hardcoded String Set Literal` 警告數量歸零 (0 violations)。
