# Phase 5.10.3: Test Pollution and Shadow DB Migration Fix

## 1. 目標 (Objective)
解決在執行 `make audit-qa` 時，測試套件卡死以及影子資料庫遷移 (Shadow DB Migration) 失敗的嚴重問題。確保 CI/CD 門禁與自動化驗證流程 100% 綠燈，維持物理與架構一致性。

## 2. 問題與根本原因 (Problems & Root Causes)

### 2.1 測試套件卡死 (Test Suite Teardown Hangs)
* **現象：** `make test-be` 與 `make audit-qa` 在執行到特定端點測試（如 `test_marketing_api_list_leads.py`、`test_settings_api.py`）後，Pytest 會卡在 teardown 階段無限等待。
* **原因：** 先前為了解決 `401 Unauthorized` 依賴注入的副作用，將模組層級的 `TestClient(app)` 改為使用 Context Manager (`with TestClient(app)`)。這意外觸發了 FastAPI 的 `lifespan` 事件，導致啟動了龐大的背景服務（SchedulerService, CrawlerManager）。測試結束時，背景迴圈卡住使得 Pytest 無法乾淨地關閉。
* **解法：** 重構 `client` fixture，改用非 Context-Managed 的 `yield TestClient(app)`，並繼續使用 `.pop()` 來獨立清理每次測試的 `dependency_overrides`。這樣既解決了狀態污染，也避免觸發 `lifespan` 啟動背景服務。

### 2.2 影子資料庫遷移順序錯誤 (Shadow DB Migration Sequence Conflict)
* **現象：** `make audit-qa` 在「Shadow DB Migration verifier」步驟崩潰，錯誤訊息為 `relation "public.archon_roles_permissions" does not exist`。
* **原因：** 資料庫遷移腳本有嚴格的順序相依性。在 `04_logic_security_rls.sql` 中對 `archon_roles_permissions` 設定了 Row-Level Security (RLS) 原則，但該資料表的建立 (`CREATE TABLE`) 卻被放置在較晚執行的 `05_seed_system_configs.sql` 中。這違背了 SSOT 與實體結構規範。
* **解法：** 
    1. 將 `archon_roles_permissions` 的 `CREATE TABLE` 定義往前移動至 `02_schema_features.sql` (結構定義區)。
    2. 將原本被錯誤附加在 `01_schema_core.sql` 中的 `archon_prompts` ALTER 語句，移動至 `02` 資料表建立後。
    3. 修復腳本中硬編碼的 fallback 版本（從 `"0.2.2"` 改為 `"0.2.3"`）。

## 3. 執行與公證 (Execution & Auditing)
* ✅ `make test-be`: 所有 640+ 項後端測試皆通過，無任何 401 錯誤或卡死問題。
* ✅ `make phase-audit`: 確認所有文件、程式碼皆對齊，無幽靈檔案，SSOT 與硬編碼檢查全數過關。
* ✅ `make audit-qa`: 所有閘門（包含靜態分析、前端、後端、影子資料庫驗證）皆 100% 成功，達到綠燈狀態。

## 4. 學習與防禦機制 (Learnings & Defense)
* **Context Manager 陷阱：** 在 FastAPI 測試中，必須警惕 `TestClient` Context Manager 可能會觸發不必要的 Lifespan 背景服務。
* **物理對帳與 SSOT：** 任何 RLS (04) 邏輯設定前，該資料表的建立 (02) 必須在實體檔案中先行完成，嚴禁將 Schema 定義混入 Seed Data (05) 之中。
