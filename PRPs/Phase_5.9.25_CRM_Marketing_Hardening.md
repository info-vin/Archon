# Phase 5.9.25: CRM 與行銷業務核心 (3.5) 型別與 SSOT 硬化計畫

## 1. 核心目標與原則
1. **絕不硬編碼 (No Hardcoding)**：型別補齊時，絕不能硬寫 `dict` 或是魔法字串。
2. **符合 SSOT (Adhere to SSOT)**：使用者身分與權限的傳遞，必須全面採用 `UserProfileDTO` 作為單一真實來源 (Single Source of Truth)，拋棄舊有的 `user_dict` 或 `user_role` 字串傳遞。
3. **不要改 A 壞 B (Zero Regressions)**：所有的型別修改，必須同步考量對依賴方的影響。修改後必須完整通過 `make test-be` (612 項測試) 以及 `uv run ruff check`，確保公證無誤才進行提交。

## 2. 待修復的 57 個未標註函式列表 (The 57 Untyped Functions List)
透過 AST 腳本對 3.5 模組 (32 個檔案) 的物理探勘，精準抓出以下 57 個缺乏回傳型別 (`-> Any` / `-> None` 等) 或是參數型別的邊緣函式。我們將採取「精準打擊」逐一補齊：

### 核心與行銷模組 (Core & Marketing)
- `marketing_service.py`: `__init__`
- `report_service.py`: `__init__`
- `propose_change_service.py`: `__init__`
- `visit_log_service.py`: `__init__`, `_query` (x3)
- `blog_service.py`: `__init__`, `_query` (x5)
- `marketing/lead_handler.py`: `_query` (x2), `_insert`, `_check_existing`
- `marketing/sales_pitch.py`: `_call_gemini`
- `marketing/blog_generator.py`: `_call_gemini` (x2)

### 專案與工單模組 (Projects & Tasks)
- `projects/project_service.py`: `__init__`, `_query` (x6)
- `projects/document_service.py`: `__init__`, `_query` (x5)
- `projects/project_creation_service.py`: `__init__`, `_query`, `agent_progress_callback`
- `projects/task_service.py`: `__init__`
- `projects/versioning_service.py`: `__init__`, `_get_latest`, `_insert`, `_query` (x5), `_update_project`
- `projects/tasks/query_logic.py`: `_query`
- `projects/tasks/create_logic.py`: `_create_query`, `_get_first_project`
- `projects/tasks/maintenance.py`: `_archive_query`
- `projects/tasks/ai_operations.py`: `_call_gemini`
- `projects/tasks/update_logic.py`: `_update_query`

### 統計模組 (Stats)
- `stats/metrics.py`: `__init__`
- `stats/__init__.py`: `__init__`
- `stats/performance.py`: `__init__`
- `stats/domains/marketing_metrics.py`: `__init__`
- `stats/domains/agent_metrics.py`: `__init__`

## 3. 實作步驟 (Execution Plan)

### Step 1: 閉包與建構子基礎修補 (Closures & Constructors)
- **行動**：遍歷所有 Service 檔案。
- **作法**：
  - 將所有的 `def __init__(self, ...):` 補齊 `-> None`，並確保 `supabase_client` 標註為 `Any | None`。
  - 將所有的巢狀查詢閉包 (如 `def _query():`, `def _insert():`) 補齊 `-> Any`。

### Step 2: 業務邏輯的 SSOT 對齊 (Business Logic SSOT Alignment)
- **行動**：深度掃描 CRM 與行銷核心 (`marketing_service.py`, `project_service.py` 等)。
- **作法**：將原本傳遞 `user: dict` 或 `user_role: str` 的方法，重構為接收 `user: UserProfileDTO`。確保我們使用的是 Auth 層定義好的 SSOT 模型，不自己幻想或硬編碼權限邏輯。

### Step 3: 全面測試與公證 (Full Testing & Notarization)
- **行動**：在修改後，強制執行防禦網。
- **作法**：
  1. 執行 `uv run mypy src/server/services` 確保型別邏輯一致。
  2. 執行 `uv run ruff check` 確認無語法或匯入錯誤。
  3. 執行 `make test-be`，確保所有原本 Mock 的地方不會因為我們把 `dict` 換成 `UserProfileDTO` 而導致測試崩潰 (防止改 A 壞 B)。
  4. 執行 `python scripts/backend_type_health.py` 確認 3.5 模組的指標達到完美的 **100.0%**。
