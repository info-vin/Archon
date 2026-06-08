# Phase 5.5.11 Monolith Refactoring & Code Debt Mitigation

## 背景與目標 (Background & Objectives)

在全系統門禁 `make phase-audit` 的檢測中，排查出 3 個核心業務程式碼檔案超過了 400 行的系統防範閾值：
1. `python/src/server/services/credentials/manager.py` (427 行)
2. `archon-ui-main/src/services/ollamaService.ts` (436 行)
3. `archon-ui-main/src/components/bug-report/BugReportModal.tsx` (428 行)

本階段的目標是：
* **解耦巨型檔案**：通過 L2 模組化拆分，將這三個檔案的行數安全降至 400 行以下。
* **守護測試綠燈**：在拆分過程中，絕不破壞現有的環境變數設定、Supabase 金鑰加解密、以及前端測試的 Mock 機制。

---

## 歷史 Git 軌跡分析 (Git History Analysis)

| 檔案路徑 | 歷史重大提交與修改原因 | 現有行數 | 重構優先級與重要性 |
| :--- | :--- | :--- | :--- |
| `manager.py` | 於 `c3fa6574` 進行過 Phase 5.5.2 拆分。但在 `b1e84373` (3-Tier 備援架構) 實作時，因寫入 active tier 控制與快取刷新邏輯，行數再次回彈超標。 | 427 行 | **1. 優先級高 / 重要性極高**<br>攸關後端資料庫連線、API key 加解密。一旦出錯將導致全系統崩潰。 |
| `ollamaService.ts` | 於 `ee3af433` 引入，後續經歷 linting 與 type 錯誤修復。由於檔案內部包含了大量 API 回傳結構 (Interfaces) 導致行數膨脹。 | 436 行 | **2. 優先級中 / 重要性中**<br>攸關前端 Ollama 實例探索與 RAG 路由。型別定義大，重構風險在於別名匯入相容性。 |
| `BugReportModal.tsx` | 於 `59084036` (新版核心) 引入。因包含了 canvas 截圖、indexedDB 日誌處理與 UI 表單狀態管理，導致邏輯高度耦合。 | 428 行 | **3. 優先級低 / 重要性低**<br>輔助型 Modal 工具，不影響 RAG 或核心 Agent 運作，但拆分複雜度高。 |

---

## 實作計畫 (Implementation Plan)

### 1. `manager.py` L2 拆分 (優先級：1)

*   **問題診斷**：
    *   `check_credentials_exist` (30 行) 與 `get_config_as_env_dict` (17 行) 屬於邊緣輔助邏輯。
    *   `get_credentials_by_category` (50 行) 內部包含了複雜的 `rag_strategy` 快取與 TTL 檢查。
*   **重構策略**：
    *   將 `check_credentials_exist` 移至同目錄下的 [helpers.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/helpers.py) (新建)。
    *   依照 CLAUDE.md 死代碼清理原則，直接移除未被系統任何地方呼叫的 `get_config_as_env_dict` 冗餘函數。
    *   在 `CredentialManager` 內導入並代理呼叫 `check_credentials_exist`。
    *   **環境與 Mock 影響防禦**：
        *   經過審查，測試檔案中主要對 `credential_service.get_credential`、`_get_supabase_client` 等核心方法進行了 Mock（如 `test_async_credential_service.py` 內使用 `patch.object(credential_service, ...)`）。
        *   因為 `check_credentials_exist` 僅在 `settings_api.py` 路由中被呼叫，且測試中無針對其內部的 mock patch，此拆分對現有 Mock 框架的侵入性極低。我們仍將在測試中增加防禦性斷言。

### 2. `ollamaService.ts` 介面抽離 (優先級：2)

*   **問題診斷**：
    *   近 168 行為 TS 介面定義 (e.g., `OllamaModel`, `ModelDiscoveryResponse`)。
*   **重構策略**：
    *   新建 [ollamaTypes.ts](file:///Users/vincenta/GoogleKwok022/Archon/archon-ui-main/src/services/ollamaTypes.ts)。
    *   在 `ollamaService.ts` 中透過 `export * from "./ollamaTypes"` 重新導出所有介面，確保其他 feature 模組的導入路徑 `@/services/ollamaService` 不會發生編譯中斷。

### 3. `BugReportModal.tsx` 邏輯抽離 (優先級：3)

*   **問題診斷**：
    *   包含 UI 表單結構、螢幕 canvas 擷取以及 indexedDB 提取。
*   **重構策略**：
    *   將 canvas 擷取與 indexedDB 日誌收集邏輯，抽離成獨立的自訂 Hook `useBugReport.ts`。
    *   將 Modal 內容拆分為 [BugReportForm.tsx](file:///Users/vincenta/GoogleKwok022/Archon/archon-ui-main/src/components/bug-report/BugReportForm.tsx)。

---

## 成功標準與自動化驗證 (Acceptance Criteria & Verification)

### 1. 物理行數限制
*   執行 `make phase-audit`，確保以上三個檔案全部降至 400 行以下。

### 2. 測試與 Lint
*   **後端驗證**：
    *   執行 `uv run pytest tests/unit/services/test_scheduler_service.py`
    *   執行 `uv run pytest tests/test_async_credential_service.py` (憑證測試)
    *   執行 `make test-be` (通過後端全體單元與整合測試)
    *   執行 `make lint-be` (0 錯誤/0 警告)
*   **前端驗證**：
    *   執行 `make lint-fe` (0 錯誤/0 警告，tsc 編譯通過)
