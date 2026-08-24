# Phase 5.11.4: NotebookLM SSOT & Session Persistence Hardening Plan

## 核心問題陳述 (Problem Statement)
在 Phase 5.11.3 的驗收階段，由於缺乏對 Playwright 底層機制的理解，暴露出三個致命的架構斷層與樂觀路徑假設：

1. **單向同步的樂觀路徑 (One-Way Sync Anti-Pattern)**: 
   目前 `project_service.py` 只會在檔案不存在時，將 `SettingsService` 的 JSON 寫入 `storage_state.json`。然而，Playwright 執行過程中**會動態更新 Cookie 與 Token 並寫回該檔案**。目前系統完全沒有將更新後的檔案回寫到 DB，這導致 DB 中的憑證會逐漸過期，這是一個致命的樂觀路徑 (Happy Path)。
2. **改 A 壞 B 的風險 (Session Destruction Risk)**: 
   如果單純將儲存路徑改為 `/tmp` 且用完即刪（即前次被否決的造輪子方案），將直接摧毀 `notebooklm-py` 內建的 Session 狀態維持機制，導致每次都必須重新登入，必然引發 Google 封鎖或 Token 失效。
3. **SSOT 破壞斷層 (SSOT Violation)**: 
   `presentation_agent.py` 直接使用 `os.getenv("NOTEBOOKLM_AUTH_JSON")`，與 `project_service.py` 讀取 `SettingsService` 的邏輯完全脫鉤。
4. **硬編碼路徑 (Hardcoded Path)**: 
   直接寫死 `os.path.expanduser("~")` 無法相容 Docker Volume 掛載，容易在容器重啟時遺失資料。

## 解決方案 (Proposed Solution)
導入「雙向同步」與「持久化 Volume 映射」的架構，尊重第三方套件的輪子，而非破壞它。

1. **落實雙向狀態同步 (Bi-Directional State Sync)**: 
   實作一個嚴謹的生命週期包裝器：
   - **Pre-run**: 若 DB 有值且檔案不存在，從 DB 同步至檔案 (DB -> File)。
   - **Post-run**: 執行完畢後，將檔案內被 Playwright 更新過的最新 Cookie，反向 Update 回 `SettingsService` (File -> DB)。實現真正的閉環狀態自癒。
2. **修復 SSOT (SSOT Enforced)**: 
   全面剷除 `presentation_agent.py` 中的 `os.getenv`，統一切換至 `SettingsService`。
3. **環境變數驅動的資料目錄 (Data Directory via Env)**: 
   不再寫死 `~/.notebooklm`，改為 `os.getenv("NOTEBOOKLM_DATA_DIR", os.path.join(os.path.expanduser("~"), ".notebooklm"))`。藉此，Docker 環境可以輕鬆將其映射至 `/app/data/notebooklm` 進行 Volume 持久化。
4. **自動化公證 (Zero Fake Verification)**: 
   在測試環境中遮蔽 `os.environ`，斷言 Agent 能正確從 Mock DB 讀取憑證、寫入指定目錄，並在結束後觸發 `set_setting` 回寫 DB。

## 實作步驟 (Execution Steps)

### Step 1: 建立雙向同步輔助函數
**[NEW]** `python/src/server/utils/notebooklm_auth.py`
實作 `sync_notebooklm_session(settings: SettingsService, profile_name="default")` (Context Manager)：
* Entry: 決定資料夾路徑，執行 DB -> File 同步。
* Exit: 讀取 File 最新內容，呼叫 `settings.set_setting("notebooklm_auth_json", new_json)`。

### Step 2: 消除 SSOT 違規與整合同步機制
**[MODIFY]** `python/src/server/services/projects/project_service.py`
**[MODIFY]** `python/src/agents/presentation/presentation_agent.py`
* 移除硬編碼的 `auth_json_path` 邏輯與 `os.getenv`。
* 將 `ctx_client = NotebookLMClient.from_storage(...)` 包裝入 `async with sync_notebooklm_session(...)` 的作用域中。

### Step 3: 自動化驗證探針
**[NEW]** `scripts/verify_phase_5_11_4_ssot.py`
* 注入假資料庫，模擬 Playwright 在檔案中寫入新 Cookie (`{"new": "cookie"}`)。
* 斷言離開 context 後，DB 的 `notebooklm_auth_json` 是否成功被更新為新 Cookie。
