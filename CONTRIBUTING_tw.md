# 專案食譜 (Project Cookbook)

> 歡迎來到 Archon 廚房！本食譜記載了我們團隊合作的最佳實踐與標準作業流程 (SOP)。
> 
> 本文件旨在提供清晰、可執行的指南。所有關於「為什麼」的歷史決策與背景故事，都已被整理至 **附錄 A**，以保持本食譜的簡潔與易用性。

---

## 第一章：核心心法 (Core Mindset)

| 原則 | 解釋 |
| :--- | :--- |
| 1. **警惕「副本任務」陷阱** | 分析是為了解決「主線任務」，而不是為了開啟無止盡的調查循環。在得到分析結果後，應回頭思考如何將此結果應用於完成最初的目標。 |
| 2. **驗證而非假設** | 不要「幻想」一個可運行的環境或完美的程式碼狀態。永遠要透過指令或工具進行驗證，並在最後進行「眼見為實」的視覺化驗收。 |
| 3. **精準修改，避免副作用** | 修復 Bug 或修改程式碼時，應採取最小、最精準的修改。使用 `replace` 時務必提供足夠的上下文，以避免「改 A 壞 B」。 |
| 4. **徹底理解工具** | 永遠不要假設一個指令的行為。在使用 `make` 或其他腳本前，先閱讀其源碼，理解其是否包含 `--fix` 等有副作用的參數。 |
| 5. **撰寫冪等的資料庫腳本** | 所有資料庫遷移腳本都應具備「冪等性」，確保其可以安全地重複執行。應大量使用 `DROP ... IF EXISTS` 和 `CREATE ... IF NOT EXISTS`。 |
| 6. **`Makefile` 是唯一指令來源** | 文件應引用 `make <command>`，而不是直接複製貼上底層 shell 指令，以確保文件與腳本永遠同步。 |
| 7. **安全地修改與復原** | 複雜修改應使用 `write_file` 一次性覆寫。當修改後測試失敗，應立即用 `git checkout -- <file>` 還原，而不是在錯誤的基礎上繼續修補。 |

---

## 第二章：環境設定 (Environment Setup)

### 2.1 本地開發環境啟動 SOP (混合模式)

**目標**: 在本地成功啟動一個用於日常開發的混合模式環境。

**核心架構**:
- **後端 (Backend)**: 在 Docker 中運行 (`archon-server`, `archon-mcp`, `archon-agents`)。
- **前端 (Frontend)**: 在**本機**手動運行，以利用熱加載功能。
    - `archon-ui-main` (管理後台) -> Port `3737`
    - `enduser-ui-fe` (使用者介面) -> Port `5173`

**執行步驟**:

1.  **清理環境 (若有需要)**:
    ```bash
    make stop
    ```

2.  **啟動後端服務 (終端機 1)**:
    ```bash
    make dev
    ```
    *(此指令只會啟動 Docker 中的後端服務)*

3.  **啟動管理後台 (終端機 2)**:
    ```bash
    # 首次執行或依賴變更時，需先安裝依賴
    make install-ui
    # 啟動開發伺服器
    cd archon-ui-main && pnpm run dev
    ```

4.  **初始化資料庫 (重要)**:
    > **⚠️ 重要順序**: 必須先執行 `make dev` (或 `make dev-docker`) 確保容器正在運行後，才能執行此指令。
    ```bash
    # 執行資料庫遷移與 Mock Data 初始化 (包含 ID 同步修復)
    make db-init
    ```

5.  **啟動使用者介面 (終端機 3)**:
    ```bash
    # 首次執行或依賴變更時，需先安裝依賴
    make install
    # 啟動開發伺服器
    cd enduser-ui-fe && pnpm run dev
    ```

**最終驗證**:
當所有服務都成功啟動後，您可以在瀏覽器中分別打開 `http://localhost:3737` (管理後台) 和 `http://localhost:5173` (使用者介面)。

> **💡 資料庫設定小撇步 (Database Config Tip)**:
> 設定 `.env` 時，請留意 `SUPABASE_DB_URL` 的連接埠差異：
> *   **Port 5432 (Session Mode)**: 必須用於 **Migration** 與 **Init** 腳本 (`init_db.py`)，避免 Transaction Mode 不支援預備語句 (Prepared Statements) 導致的錯誤。
> *   **Port 6543 (Transaction Mode)**: 建議用於 **Production** 應用程式流量，以支援高併發連線。

> **💡 主動防禦 (Proactive Guard) 註記**:
> 若在全 Docker (`dev-docker`) 環境下啟動，前端 `api.ts` 會自動偵測 `SUPABASE_URL` 是否為無法解析的內部 DNS。若偵測到連線異常，系統會自動切換至 **Mock 模式** 以避免無限 Loading，這屬於正常預期行為。

### 2.2 後端依賴與環境管理

- **`uv.lock` 管理**: `python/uv.lock` **應被提交**至版本控制系統。這是為了確保所有團隊成員以及 CI/CD 環境在安裝依賴時，所使用的套件版本完全一致，避免「我的電腦可以跑，但你的不行」之問題。
- **依賴組安裝**: `Makefile` 中的 `make test-be` 和 `make lint-be` 會自動使用 `--group` 參數安裝 `test` 和 `dev` 的依賴，無需手動操作。

### 2.3 全 Docker 環境手動驗證 SOP

當遇到複雜的啟動問題時，請依序執行以下步驟以確保環境乾淨：

1.  **徹底清理 (Clean Slate)**
    *   **指令**: `make clean`
    *   **目的**: 移除所有容器、網路和**資料卷** (Volumes)。
    *   **注意**: 執行時需輸入 `y` 確認。

2.  **驗證清理狀態**
    *   **指令**: `docker ps -a`
    *   **檢查**: 確保列表為空，無殘留容器。

3.  **重新建置映像檔 (Rebuild)**
    *   **指令**: `docker compose --profile backend --profile frontend --profile enduser --profile agents build`
    *   **目的**: 確保使用最新的程式碼進行構建。

4.  **前景啟動與觀察 (Foreground Start)**
    *   **指令**: `docker compose --profile backend --profile frontend --profile enduser --profile agents up`
    *   **檢查**: 觀察終端機輸出的啟動日誌，確認無報錯且服務就緒。

---

## 第三章：測試指南 (Testing Guide)

### 3.1 通用測試指令

| 目的 | 指令 | 範例 |
| :--- | :--- | :--- |
| **執行所有測試** | `make test` | `make test` |
| **僅執行後端測試** | `make test-be` | `make test-be` |
| **測試特定前端專案** | `make test-fe-project project=<name>` | `make test-fe-project project=enduser-ui-fe` |
| **測試特定前端檔案** | `make test-fe-single project=<name> test=<pattern>` | `make test-fe-single project=enduser-ui-fe test="TaskModal"` |

### 3.2 後端 API 測試：模擬資料庫與服務

#### 3.2.1 資料庫模擬 (Database Mocking)

所有後端 API 測試都**嚴格禁止**連線到真實的資料庫。專案在 `python/tests/conftest.py` 中使用 `pytest fixture` 和 `patch` 自動模擬了 `SupabaseClient`。您只需在測試函式簽名中加入 `client` 和 `mock_supabase_client` 即可使用。

#### 3.2.2 服務模擬的黃金模式 (Service Mocking "Golden Pattern")

在測試 FastAPI 端點時，若該端點依賴於一個在應用程式啟動時就已初始化的服務單例 (Service Singleton)，則**必須**遵循以下模式：

1.  **在 `app` 導入前 Patch**: `patch` 必須在 `import app` 語句**之前**定義。
2.  **使用 `setup_module` 和 `teardown_module`**: 利用 `pytest` 的 `setup_module` 和 `teardown_module` 函式，手動管理 `patch` 的生命週期 (`start()` 和 `stop()`)。

**範例**:
```python
# python/tests/server/test_example_api.py

from unittest.mock import patch, AsyncMock

# 1. 在 app 導入前定義 patch
mock_agent_service = patch('src.server.services.agent_service.AgentService', new_callable=AsyncMock)

# 2. 在 setup_module 中啟動 patch
def setup_module(module):
    mock_agent_service.start()

def teardown_module(module):
    mock_agent_service.stop()

# 現在可以安全地導入 app
from src.server.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_some_endpoint():
    # ... 您的測試邏輯 ...
```

#### 3.2.3 Supabase Mocking 與非同步陷阱 (⚠️ 重要)

在為涉及 Supabase 的 Service 撰寫測試時，必須注意以下陷阱：

*   **同步客戶端特性**: 目前 `get_supabase_client` 回傳的是**同步**客戶端。因此，Service 中不應 `await` 其 `.execute()` 方法。
*   **Mock 類型匹配**:
    *   **錯誤**: 在測試中使用 `AsyncMock` 來模擬 `execute()` 方法。這會導致 Service 收到 Coroutine 而非數據，報錯 `AttributeError: 'coroutine' object has no attribute 'data'`。
    *   **正確**: 應使用普通的 `Mock` 或配置 `execute` 的 `return_value` 為直接的結果。
*   **Patch 路徑原則**: 應 Patch Service 的 **Class** (例如 `patch('...TaskService')`) 而非全域實例，以確保在 API 函數內部實例化時能正確被 Mock 取代。

### 3.3 前端 E2E 測試 (`enduser-ui-fe`)

#### 3.3.1 E2E 測試核心架構

為確保前端 E2E 測試的穩定性與可維護性，專案採用了以下架構：

1.  **專屬設定檔**: 使用獨立的 `vitest.e2e.config.ts` 設定檔，將 E2E 測試與單元測試完全隔離。
2.  **隔離的 Mocking 環境**: 所有 E2E 測試所需的 API Mock 都集中在 `tests/e2e/e2e.setup.ts` 中管理。
3.  **標準化元件渲染**: 為解決 React Router 的問題，所有測試都直接渲染 `AppRoutes` 元件，並為其提供 `AuthProvider` 和 `MemoryRouter` 作為包裹 (Wrapper)。
4.  **混合 Mocking 策略**:
    *   **認證 (Authentication)**: 使用 `vi.mock` 來模擬 `getCurrentUser` 等認證相關函式。
    *   **數據 (Data)**: 使用 **Mock Service Worker (MSW)** 攔截所有數據相關的 `fetch` 請求。請確保 `src/mocks/handlers.ts` 中的模擬資料結構與前端 `types.ts` 中的類型定義**完全一致**。
    *   **全域 Server 共用原則**: 在個別測試檔案中，**嚴禁**使用 `setupServer` 建立新的實例。必須引用 `src/mocks/server` 中的全域 `server` 物件，並使用 `server.use()` 來注入該測試專屬的 Handler。這能避免與 `e2e.setup.ts` 中的全域設定發生衝突。

#### 3.3.2 完整整合測試的準備工作

為了讓 E2E 測試能針對真實後端運行，專案提供了以下機制：

1.  **自動化資料庫重置**:
    *   後端提供一個受 `ENABLE_TEST_ENDPOINTS` 環境變數保護的 `POST /api/test/reset-database` 端點。
    *   E2E 測試套件的 `globalSetup.ts` 會在測試運行前自動呼叫此端點，確保資料庫處於乾淨、可預測的狀態。
2.  **測試環境中的 Supabase 初始化**:
    *   E2E 測試設定會以程式化方式，在 `jsdom` 的 `localStorage` 中設定 Supabase 的 URL 和金鑰。
    *   這使得前端的 Supabase 客戶端能在測試環境中正確初始化，並發出真實的 API 請求。

### 3.4 前端測試常見問題 (FAQ)

| 問題 | 症狀 | 解決方案 |
| :--- | :--- | :--- |
| **Import Error** | `Failed to resolve import` | `package.json` 中缺少開發依賴。執行 `pnpm install --save-dev <package>`。 |
| **Aria Label** | 找不到純圖示按鈕 | 為按鈕加上 `aria-label="描述"` 屬性。 |
| **Event Click** | `required` 表單提交無反應 | 使用 `fireEvent.submit(submitButton)` 直接觸發提交。 |
| **Hoisting** | `vi.mock` 變數提升錯誤 | 將 `vi.mock` 需要的變數直接定義在工廠函式**內部**。 |
| **MSW Intercept** | `intercepted a request without a matching request handler` | 檢查測試中的 URL 參數是否與 Handler 定義完全匹配。動態注入請用 `server.use()`。 |
| **Timeout** | `Test timed out` | 檢查 `await waitFor` 是否在等待一個永遠不會出現的元素，或 API Mock 未正確回傳。 |
| **Async State** | `act(...) warning` | 確保所有觸發狀態更新的操作都被 `await`，或包在 `act(() => ...)` 中。 |
| **Element type is invalid** | `check the render method of ...` | 通常是 Import 錯誤。檢查是否混淆了 `default export` 與 `named export`，或引用了不存在的元件。 |

### 3.5 AI Agent 自癒能力驗證 (Self-Healing Verification)

本節介紹如何手動驗證 Archon 系統的 AI 自癒與智能分析能力。

**演練場景：自動分析語法錯誤**

當 Agent 執行的指令失敗時，系統應自動呼叫 LLM 分析錯誤並提供修復建議。

1.  **製造錯誤**: 在根目錄建立一個包含語法錯誤的 `broken_script.py` (例如漏掉右括號)。
2.  **觸發任務**: 使用 `curl` 呼叫 `/api/test/trigger-agent-task` (需開啟 `ENABLE_TEST_ENDPOINTS`)。
3.  **觀察結果**: 訪問 UI 任務詳情頁，確認狀態變為 `failed` 且 `output` 欄位包含 AI 的診斷建議。

---

## 第四章：貢獻與部署流程 (Contribution & Deployment)

### 4.1 Git 工作流程

- **分支策略**: 所有工作都**必須**在 `feature/...` 分支上進行。部署也**必須**從 `feature/...` 分支進行。`main` 分支請勿使用。
- **`cherry-pick` 卡住**: 若 `git cherry-pick --continue` 卡住，請改用 `git cherry-pick --continue --no-edit --no-gpg-sign`。

### 4.2 部署標準作業流程 (SOP)

此流程的最終目標，是成功將一個穩定的 `feature/...` 分支部署到 **Render**。

1.  **階段一：部署前本地檢查**
    此步驟提供兩種流程選項：
    *   **流程一 (快速檢查)**: 至少執行 `make test` 與 `make lint`。
    *   **流程二 (完整驗證)**: 執行「[2.3 全 Docker 環境手動驗證 SOP](#23-全-docker-環境手動驗證-sop)」，以進行最徹底的檢查。

2.  **階段二：資料庫遷移 (Database Migration) - v2 (Tracked)**

    此流程的最終目標是安全、可追蹤地更新資料庫結構。

    **核心原則**:
    *   **冪等性**: 所有遷移腳本都必須是冪等的 (`IF NOT EXISTS`)。
    *   **版本註冊**: 每個腳本都必須在執行成功後，將自己的版本號註冊到 `schema_migrations` 表中。

    **開發新遷移腳本的流程**:
    1.  **建立檔案**: 建立一個新的 SQL 檔案，並使用下一個可用的數字作為前綴 (例如 `003_add_new_feature.sql`)。
    2.  **撰寫冪等 SQL**: 使用 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` 或 `CREATE TABLE IF NOT EXISTS ...` 等語法。
    3.  **註冊版本**: 在腳本的結尾，加上註冊指令：
        ```sql
        -- 註冊此遷移腳本的版本
        INSERT INTO schema_migrations (version) VALUES ('003_add_new_feature') ON CONFLICT (version) DO NOTHING;
        ```
        *(請將 `'003_add_new_feature'` 替換為不含 `.sql` 副檔名的檔名)*

    **🛡️ SQL 腳本品質檢查清單 (SQL Quality Checklist)**:
    在提交任何 `.sql` 檔案前，必須檢查：
    - [ ] **冪等性**: 是否使用了 `IF NOT EXISTS` 或 `DROP ... IF EXISTS`？
    - [ ] **版本追蹤**: 是否包含了 `INSERT INTO schema_migrations` 語句？
    - [ ] **資料保留**: 如果是修改種子資料 (`seed_*.sql`)，是否確認了是 `APPEND` (追加) 還是 `OVERWRITE` (覆蓋)？**嚴禁**在未讀取原內容的情況下直接覆蓋。

    **執行遷移的SOP (部署時)**:

    **本地開發首次設定SOP (從零開始)**:

    > **⚡ 自動化指令 (推薦)**:
    > 專案已支援 `make db-init` 指令，它會自動執行以下所有步驟（遷移 + 種子資料 + ID 同步）。
    > **⚠️ 注意**: 執行前請確保後端服務已啟動 (`make dev`)，否則會報錯找不到容器。
    > 僅在自動化指令失敗時，才需要參考下方的檔案列表進行手動除錯。

    當您需要在本地建立一個全新的、乾淨的資料庫時：
    1.  確保 Docker 後端已啟動 (`make dev`)。
    2.  執行指令：
        ```bash
        make db-init
        ```
    3.  腳本會自動完成：清空舊資料、建立 Schema、寫入 Mock Data、並修復 Auth ID 不一致的問題。

    > **🚑 資料庫救災指南 (Database Recovery SOP)**
    >
    > **症狀**: 執行完 `make test` 後，發現資料庫變空，或某些功能面板（如 Sales Intel）消失。
    > **原因**: E2E 測試會重置資料庫，但可能未正確還原所有種子資料。且若遷移紀錄 (`schema_migrations`) 未被清除，`make db-init` 會誤以為資料已存在而跳過播種。
    > **解法**: 請依序執行以下步驟，強制重置環境：
    > 1.  **手動執行重置**: 在 Supabase SQL Editor 或透過工具執行 `migration/RESET_DB.sql`。此腳本現在會**刪除** `schema_migrations` 表，確保系統「失憶」。
    > 2.  **重新初始化**: 執行 `make db-init`。系統會發現沒有遷移紀錄，從而乖乖地從頭執行所有腳本，包含正確的種子資料。

    **🚑 緊急備案：手動初始化流程 (Manual Fallback)**
    > **僅當 `make db-init` 失敗時使用**
    > 若自動腳本無法執行，請依序手動執行以下 SQL 檔案：

    1.  登入 Supabase 儀表板並進入 **SQL Editor**。
    2.  依序複製貼上並執行：
        1.  `migration/RESET_DB.sql` (清空所有舊資料)
        2.  `migration/000_unified_schema.sql` (建立基礎結構)
        3.  `migration/001_add_due_date_to_tasks.sql` (追加欄位更新)
        4.  `migration/002_create_schema_migrations_table.sql` (建立版本追蹤表)
        5.  `migration/003_add_get_counts_by_source_function.sql` (追加函式)
        6.  `migration/005_create_proposed_changes_table.sql` (建立 AI 提案表)
        7.  `migration/seed_mock_data.sql` (填充核心假資料)
        8.  `migration/seed_blog_posts.sql` (填充部落格假資料)
        9.  `migration/004_create_test_utility_functions.sql` (**E2E 測試所需**)
            > **說明**: 此腳本建立了用於自動化端對端測試的資料庫函式 (`reset_test_database`, `seed_test_database`)。如果您需要運行完整的前端 E2E 測試套件，則**必須**執行此腳本。
        10. `migration/006_create_sales_intel_tables.sql` (**Phase 4.2 銷售情資所需**)
            > **說明**: 建立 `leads` 與 `market_insights` 資料表，用於支援業務開發功能。
        11. `migration/007_add_assignee_id_to_tasks.sql` (**RBAC 補完計畫**)
            > **說明**: 建立 `assignee_id` 欄位並與 `profiles` 表關聯，確保任務指派具備強大的 RBAC 基礎。
        12. `migration/008_system_correction_phase44.sql` (**Phase 4.4 系統修正**)
            > **說明**: 針對任務分配與 Agent 狀態邏輯進行修正，確保 Phase 4.4 流程穩定。
        13. `migration/009_fix_rbac_roles_and_permissions.sql` (**RBAC 權限修復**)
            > **說明**: 修正 Manager 角色對部門成員的管理權限，並釐清與 System Admin 的權限邊界。
        14. `migration/010_bob_and_alice_schema_updates.sql` (**Phase 4.4 戰情室基礎**)
            > **說明**: 為 `blog_posts` 新增狀態欄位，並擴充 `leads` 表以支援 CRM 功能。
        15. `migration/011_update_alice_bob_roles.sql` (**Persona 權限修正**)
            > **說明**: 將 Alice 與 Bob 的角色分別升級為 `sales` 與 `marketing`，確保其具備存取 Sales Intel 與 Brand Hub 的權限。

3.  **階段三：執行部署**

    **3.1 前端服務的路由設定 (重要)**

    對於單頁應用 (SPA) 前端服務 (如 `archon-ui-main`, `enduser-ui-fe`)，您**必須**在 Render 儀表板上設定以下**兩條**路由規則，才能確保 API 代理和頁面重新整理都正常運作。

    1.  在 Render 儀表板，進入您的前端服務設定頁面。
    2.  找到 **"Redirects/Rewrites"** 區塊。
    3.  **依序**新增以下兩條**重寫 (Rewrite)** 規則：

        **規則一：API 代理規則 (優先級最高)**
        *   **Source (來源路徑):** `/api/:path*`
        *   **Destination (目標位址):** `https://<您的後端服務網址>/api/:path*`
        > **說明**: 此規則將所有 `/api/` 開頭的請求，從前端服務代理到後端服務。

        **規則二：SPA 回退規則 (優先級較低)**
        *   **Source (來源路徑):** `/*`
        *   **Destination (目標位址):** `/index.html`
        > **說明**: 此規則會將所有**未匹配到**其他規則的請求 (例如 `/settings`, `/projects/123`) 都導向 `index.html`，讓前端路由能夠接管。

    > **注意**: 這兩條規則的**順序至關重要**。必須先設定 API 代理，再設定 SPA 回退規則。請將 `<您的後端服務網址>` 替換為您 `archon-server` 的真實公開網址。
    > 設定錯誤會導致前端無法正確與後端溝通，或頁面重新整理時出現 404 錯誤，請務必仔細檢查。

    **3.2 觸發部署**
    1.  確認 Render 儀表板監控的是正確的 `feature/...` 分支。
    2.  將本地變更推送到 GitHub: `git push origin <your-branch>`
    3.  Render 會自動偵測到新的提交並開始部署。

4.  **階段四：部署後驗證**
    1.  在 Render 儀表板監控所有服務的部署日誌。
    2.  存取後端服務的 `/health` 端點，確認回傳 `{"status":"ok"}`。
    3.  打開前端服務的公開網址，進行功能驗證 (Smoke Test)。

### 4.3 AI 開發者協作流程 (AI Developer Workflow)

隨著 `Phase_4.1` 的完成，專案引入了一套由 AI Agent 輔助開發的全新工作流程。此流程的核心是「**提議 -> 審核 -> 執行**」，旨在確保 AI 在安全、可控的環境下為程式碼庫做出貢獻。

#### 4.3.1 資料庫基礎：`proposed_changes` 資料表

此工作流程由 `migration/005_create_proposed_changes_table.sql` 所建立的 `proposed_changes` 資料表支撐。

- **核心欄位**:
    - `id`: 提案的唯一標識符。
    - `type`: 提案類型（`file`, `git`, `shell`）。
    - `status`: 提案狀態（`pending`, `approved`, `rejected`, `executed`, `failed`）。
    - `request_payload`: 一個 `jsonb` 欄位，儲存了提案的具體內容。例如，對於一個 `file` 類型的提案，這裡會包含 `file_path`, `new_content`, 以及用於 Diff 顯示的 `original_content`。

#### 4.3.2 開發者審核工作流程

開發者的主要職責是**審核** AI 提出的程式碼變更。

1.  **接收通知與進入審核頁面**:
    *   當 AI 提出一個新的變更時，開發者會（在未來的版本中）收到通知。
    *   登入 `enduser-ui-fe`，並導航至側邊欄新增的 **`/approvals`** 頁面。

2.  **審核變更**:
    *   頁面會列出所有狀態為 `pending` 的提案。
    *   對於 `file` 類型的提案，您現在可以看到一個**程式碼差異比對 (Diff Viewer)**，清晰地展示了檔案的原始內容 (`oldValue`) 與 AI 提議的新內容 (`newValue`)。

3.  **做出決策**:
    *   **批准 (Approve)**: 如果您認為變更是正確且安全的，點擊「Approve」按鈕。後端將會執行此變更（例如，覆寫檔案），並將提案狀態更新為 `executed`。
    *   **拒絕 (Reject)**: 如果變更不符合要求，點擊「Reject」按鈕。該提案的狀態將會變為 `rejected`，不會對程式碼庫產生任何影響。

#### 4.3.3 與 Git 流程的結合

- AI 的所有工作都會在一個獨立的 `feature/` 分支上進行。
- AI 提交的變更，在被批准和執行後，最終會以一個 `commit` 的形式出現在該 `feature/` 分支上。
- 開發者後續可以像對待任何人類開發者提交的 `commit` 一樣，對其進行 code review、合併或進一步修改。

## 第五章：Git 歷史追溯指南 (Git Archaeology Guide)

> **原則**: 當文件與程式碼出現矛盾，或不確定某個功能的設計初衷時，Git Log 是唯一的真相來源。

### 5.1 常用考古指令

| 情境 | 指令範例 | 說明 |
| :--- | :--- | :--- |
| **查閱檔案變更歷史** | `git log -p -- Makefile` | 顯示該檔案每次提交的具體差異 (Diff)。 |
| **搜尋代碼何時被加入** | `git log -S "await task_service"` | 找出包含特定字串的新增或刪除的提交。 |
| **查看特定提交的內容** | `git show <commit_hash>` | 檢視某個 Commit 的完整變更。 |
| **比較兩個分支的差異** | `git diff main...feature/new-ui` | 檢視 Feature 分支相對於 Main 分支的變更。 |

---

## 第六章：常見問題排查 (Troubleshooting SOP)

### 6.1 Supabase Auth 406 Error (Not Acceptable)

**症狀**: 前端登入成功，但呼叫 `/profiles` API 時收到 `406 Not Acceptable` 錯誤，且回傳 Body 為空。

**根源**: **ID 不匹配 (ID Mismatch)**。
- 前端使用 `.single()` 查詢 `profiles` 表，期望獲得單筆資料。
- `auth.users` 中的 `id` (UUID) 與 `public.profiles` 表中的 `id` 不同步。

**標準解法**:
此問題已在 Phase 5.3 透過 `init_db.py` 的自動化修復邏輯解決。

1.  **請執行**: `make db-init`
2.  **原理**: 腳本內建了「雙重同步策略 (Dual Sync Strategy)」，會自動偵測重複使用者並執行 `UPDATE profiles SET id = auth_uuid`，強制對齊資料庫 ID。

---

## 附錄 A：系統分析 (System Analysis)

> **注意**: 關於「環境比較 (`make dev` vs `docker`)」與「歷史架構決策」的內容，已歸檔至 `PRPs/Phase_3.8_System_Grafting_and_Deployment.md`，以保持本文件聚焦於當前操作。

### 系統架構演進：從基礎設施 (Phase 3.8) 到商業智能 (Phase 4.2)

本表格展示了專案從基礎建設期到商業擴展期的關鍵架構變化，幫助開發者理解新功能的定位。

| 構面 | Phase 3.8 (基礎建設期) | Phase 4.2 (商業擴展期) | 差異與演進 |
| :--- | :--- | :--- | :--- |
| **核心目標** | 系統嫁接、部署與穩定性 | 銷售情資、市場洞察、自動化 | 從「能跑起來」轉向「產生價值」 |
| **資料庫實體** | `tasks`, `projects` | `leads`, `market_insights` | 新增了 CRM 相關的資料表 (Schema Migration 006) |
| **外部整合** | 無 (僅內部 Mock) | **104 Job Bank (模擬)** | 首次打通外部數據源，具備爬蟲與分析能力 |
| **AI 角色** | 輔助編碼 (Developer) | **業務助理 (Sales Rep)** | Agent 能力從 RD 領域跨足到業務領域 |
| **前端功能** | 基礎 CRUD (新增/修改任務) | **儀表板 (Dashboard)** | 新增了圖表與數據可視化介面 (`MarketingPage`) |
| **文件重點** | 環境設定、部署 SOP | 業務邏輯、內容資產 (Case Study) | 文件開始包含具體的商業劇本 (`PRPs/Phase_4.2.1`) |