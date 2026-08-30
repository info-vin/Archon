# 專案食譜 (Project Cookbook)

> 歡迎來到 Archon 廚房！本食譜記載了我們團隊合作的最佳實踐與標準作業流程 (SOP)。
> 
> 本文件旨在提供清晰、可執行的指南。所有關於「為什麼」的歷史決策與背景故事，都已被整理至 **附錄 A**，以保持本食譜的簡潔與易用性。

---

## 第一章：核心心法 (Core Mindset)

| 原則 | 解釋 |
| :--- | :--- |
| 1. **警惕「副本任務」陷阱** | 分析是為了解決「主線任務」，而不是為了開啟無止盡的調查循環。在得到分析結果後，應回頭思考如何將此結果應用於完成最初的目標。 |
| 2. **物理穿透驗證 (拒絕幻想)** | 拒絕「日誌領跑代碼」。不要幻想環境或狀態是完美的，必須讀取磁碟實體檔案內容 (`read_file`) 確認邏輯存在，並透過指令或工具 (`curl`, `test`) 物理性通過方可標記為「已修復」。嚴禁在未經實體掃描的情況下宣稱任務完成。 |
| 3. **精準修改，避免副作用** | 修復 Bug 或修改程式碼時，應採取最小、最精準的修改。使用 `replace` 時務必提供足夠的上下文，以避免「改 A 壞 B」。 |
| 4. **徹底理解工具** | 永遠不要假設一個指令的行為。在使用 `make` 或其他腳本前，先閱讀其源碼，理解其是否包含 `--fix` 等有副作用的參數。 |
| 5. **撰寫冪等的資料庫腳本** | 所有資料庫遷移腳本都應具備「冪等性」，確保其可以安全地執行。應大量使用 `DROP ... IF EXISTS` 和 `CREATE ... IF NOT EXISTS`。 |
| 6. **`Makefile` 是唯一指令來源** | 文件應引用 `make <command>`，而不是直接複製貼上底層 shell 指令，以確保文件與腳本永遠同步。 |
| 7. **安全地修改與復原** | 複雜修改應使用 `write_file` 一次性覆寫。當修改後測試失敗，應立即用 `git checkout -- <file>` 還原，而不是在錯誤的基礎上繼續修補。 |
| 8. **維持「啞巴控制器」** | API 控制器應保持輕量。版本控制、來源連結等複雜商業邏輯應封裝於 Service 層。 |
| 9. **拒絕「手動拆包」** | 嚴禁在 API 層使用連續的 `if request.field is not None`。應善用 Pydantic 的 `model_dump(exclude_unset=True)` 一行搞定。 |
| 10. **型別是開發者的盔甲** | 使用 `cast` 進行顯式擔保，並區分 Pydantic (執行期安檢) 與 MyPy (開發期藍圖審查) 的職責。 |
| 11. **營運 SDK 必須對齊** | 凡是 5173 (營運端) 功能，應統一使用 Google 原生 SDK (`genai.Client`) 以確保與 Bob 一樣穩定。嚴禁對生產路徑使用不穩定的 OpenAI Shim。 |
| 12. **腳本存放唯一真相** | 所有 Python 腳本（診斷、初始化、遷移輔助）**必須**存放於外層 `scripts/` 目錄。嚴禁在 `python/scripts/` 建立副本，以確保 Docker 呼叫路徑一致。 |
| 13. **資料庫語意化整併** | 當 Migration 腳本碎片化過多時，應使用 `pg_dump` 抽出當下完美結構，並以「語意化終極整併 (Semantic True Consolidation)」重構。放棄單純時序拼接（避免先 CREATE 又 ALTER 的冗餘），而是按照外鍵順序（設定 -> 核心表 -> 關聯表 -> 函數與安控）改寫為 5~6 個純淨的最終態檔案，並刪除舊債。 |
| 14. **絕對雲原生意識** | 專案連接的是雲端服務 (如 Supabase Cloud)，並非本地容器。嚴禁嘗試用 `docker exec psql` 強行修正資料庫狀態。正確作法是產出 SQL 修正檔並請求使用者在雲端執行。 |
| 15. **環境與硬體對齊 (Intel Mac 警示)** | 涉及 ML 模型 (如 Torch, Rerank) 時，嚴禁假設所有開發環境為 M1/M2。必須鎖定 NumPy 為 1.x (如 `1.26.4`) 以相容舊架構，並實施物理探針 (`docker exec`) 驗證模型載入秒數。拒絕在未經 x86_64 驗證的情況下宣稱「效能優化」。 |
| 16. **拒絕路由幻想 (API Route Sovereignty)** | 嚴禁假設 API 路由存在（如 `/login`）。必須讀取 `main.py` 與 `api_routes/` 檔案公證實體路徑。目前 Archon Server **不處理** 登入請求（由前端與 Supabase 直連），僅處理具備 JWT 的業務邏輯與管理操作。 |
| 17. **角色連通性稽核 (Persona Smoke Test Audit)** | 拒絕因「文件標示 Done」或「後端 API 綠燈」就宣佈功能完成。必須針對每個角色 (Alice, Bob, Charlie, David)，從 **UI 實體元件 (`.tsx`)** 開始往下物理尋線，確認該按鈕是否真實呼叫 `api.ts`，並能打通後端 Endpoint。嚴禁「空殼 (Stubbed)」UI 與「複製貼上」的假象混充落地功能。 |
| 18. **杜絕迴圈內單筆寫入 (Enforce Bulk Insert)** | 嚴禁在 `for` 或 `while` 迴圈內部直接呼叫 `client.table(...).insert().execute()`。必須在迴圈內收集 payload (如 `batch_data.append(row)`)，並在迴圈外一次性使用 Bulk Insert，以杜絕 Event Loop 與資料庫 I/O 阻塞。 |
| 19. **消滅硬編碼與 Fallback 韌性** | 系統的閾值、限制與提示詞必須從資料庫 `SettingsService` 或 `archon_settings` 動態讀取，落實 Model SSOT 精神。同時，在讀取配置時必須提供安全的回退預設值 (Fallback Default, 如 `value or "default"`)，確保資料缺失時系統能 Fail-Safe，這屬於防禦性編程，不應視為硬編碼。 |
| 20. **Dockerfile SSOT 與快取防禦** | 嚴禁為了優化「冷啟動時間 (Cold Build)」而破壞依賴的單一事實來源 (SSOT)。例如，`Dockerfile` 中 `playwright` 的安裝**必須**位在 `COPY /venv` 之後，以確保抓取的瀏覽器二進位版本與 `pyproject.toml` 絕對吻合。拒絕使用可能引發 C-extension/OS 衝突的龐大官方 Base Image (如 `mcr.microsoft.com`)。我們接受依賴變更時的較長組建時間，以換取生產環境 100% 的執行期穩定性與日常改代碼時的極速 Layer Cache。 |

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
- **Logfire 初始化**: 若新檔案是作為獨立腳本執行 (非由 API 導入)，必須在進入點呼叫 `setup_logfire()`，否則日誌將無法上傳。
- **Logger 引用規範**: 嚴禁使用原生 `logging`，請統一由 `src.server.config.logfire_config import get_logger` 取得實例。

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

### 2.4 Playwright 與 Docker 的 Cookie 加密限制 (Digital Twin 必讀)

在使用 `browser-use` 或 Playwright 進行跨平台自動化操作（如 `twin_scout.py`）時，您**必須**了解一個關於 OS 級別安全性的硬限制：

* **OS 級別加密 (OS-level Encryption)**: 當您在 Mac 本機 (Host) 啟動 Playwright 並登入 Google/Gemini 時，產生的 `.browser_data` (Cookie 與 Session) 會受到 macOS Keychain 的底層加密保護。
* **Docker 的跨系統盲區**: 即使您將這個 `.browser_data` 透過 `docker-compose.yml` 的 `volumes` 正確掛載進入 Docker 內部的 Linux 容器，Linux 內的 Chromium 也**絕對無法解密**這些 Mac 專屬的 Cookie。
* **物理後果**: 這會導致腳本在 Docker 內執行時，**永遠被判定為「未登入」狀態**，並卡在要求輸入密碼或驗證的畫面。

> **🛑 開發鐵律**: 
> 任何極度依賴「維持由 Host 本機建立的敏感登入狀態 (如 Google 帳號)」的自動化工具 (例如生圖工具 `ImageGenerationTool`)，都**不應該**被封裝成 Docker 內的微服務 API 給代理 (Agents) 呼叫。這會導致極度脆弱的架構。
> **正確作法**: 這類腳本（如展示用的 `make twin-scout-action`）應該直接在宿主機本機終端機使用原生指令執行：`make twin-scout-action`，以確保它能 headed 運行、繼承 Session 並正確讀取本機的解密憑證。而一般容器內的無狀態安全對帳則執行 `make twin-scout`。

### 2.5 Lean 4 本地開發環境安裝指南

本專案使用 Lean 4 作為形式化驗證與定理證明的子模組（位於 `lean_proofs/`）。為了在本地端正常編譯、撰寫與驗證 Lean 證明，請遵循以下步驟：

1. **安裝 Lean 版本管理器 (elan)**：
   在宿主機終端機執行官方安裝指令：
   ```bash
   curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
   ```
   *安裝過程中依提示選取預設值即可。安裝後請重新啟動終端機，或載入環境變數（如 `source $HOME/.elan/env`）。*

2. **確認編譯器與依賴建置**：
   導航至 Lean 子專案目錄。`elan` 會自動偵測並下載 `lean-toolchain` 中設定的 Lean 4 版本（如 `v4.30.0`）：
   ```bash
   cd lean_proofs
   lake build
   ```
   *若編譯成功且輸出 `Hello, world!` 等測試字串，代表本地 Lean 環境已就緒。*

3. **編輯器支援與語法提示 (強烈建議)**：
   * 推薦使用 **VS Code** 作為開發工具。
   * 安裝 VS Code 官方擴充套件：**`Lean 4`** (由 `leanprover` 提供)。
   * 開啟 `lean_proofs` 目錄，VS Code 會自動啟動 Lean 4 語言伺服器 (Infoview)，在您撰寫證明時提供即時的邏輯狀態與語法反饋。

---

## 第三章：測試指南 (Testing Guide)

### 3.1 通用測試與驗證指令總覽

#### 3.1.1 基礎單元與整合測試

| 目的 | 指令 | 資料庫狀態 |
| :--- | :--- | :--- |
| **執行所有測試** | `make test` | ⚠️ **重置** (Reset) |
| **僅執行後端測試** | `make test-be` | ✅ **安全** (Safe) |
| **測試前端元件 (Unit)** | `cd enduser-ui-fe && pnpm run test:unit` | ✅ **安全** (Safe) |
| **測試前端流程 (E2E)** | `cd enduser-ui-fe && pnpm run test:e2e` | ⚠️ **重置** (Reset) |
| **RAG 健康檢查 (Probe)** | `make probe` | ✅ **安全** (Safe) |

> **⚠️ 重要警告 (Data Safety Warning)**:
> 凡是涉及 **E2E 測試** 的指令（如 `make test`, `make test-fe`），為了確保測試環境的一致性，**都會自動呼叫 API 清空並重置資料庫**。
>
> **💡 RAG 診斷 (System Probe)**:
> 若您遇到搜尋不到資料或 400 錯誤，請執行 `make probe`。它會模擬一個完整的 Alice (寫入) -> Librarian (索引) -> Bob (讀取) 流程，並檢查向量維度是否匹配 (768 vs 1536)。

> **日常開發建議流程**:
> 1.  **驗證後端邏輯**: 使用 `make test-be`。
> 2.  **驗證前端元件**: 使用 `pnpm run test:unit`。
> 3.  **整合測試**: 僅在您準備提交代碼，且**不介意資料被清空**時，才執行完整的 `make test`。

#### 3.1.2 進階驗證與自動化品質門禁 (Quality Gates)

除了基礎測試外，`Makefile` 提供了一系列針對業務邏輯、系統健康度與技術債的驗證指令：

| 目的與驗證層級 | 指令 | 使用時機與說明 |
| :--- | :--- | :--- |
| **靜態語法與型別分析** | `make lint`<br>`make lint-fe`<br>`make lint-be` | **時機**: 提交程式碼 (Commit/Push) 前。<br>**說明**: 確保代碼符合 Biome/ESLint/Ruff 規範及 MyPy 型別安全。 |
| **全域 Persona 物理巡檢** | `make persona-audit` | **時機**: 涉及 RBAC 權限或核心流程修改後。<br>**說明**: 確保五大核心角色 (Alice, Bob, Charlie, David, Agents) 的工作流程暢通，且回傳非零退出碼以防錯誤被吞。 |
| **階段與型別健康度稽核** | `make phase-audit` | **時機**: 階段性驗收、開啟新 Phase 或架構重構後。<br>**說明**: 物理掃描 PRPs 斷層，公證後端四大架構 (MCP/Agents/Services/API Routes) 17 個子分區之動態型別健康度。 |
| **數位雙生偵察員 (容器化)** | `make twin-scout` | **時機**: UI 流程大改或部署前。<br>**說明**: 透過 Headless 瀏覽器在容器內進行使用者體驗的盲測公證。 |
| **數位雙生偵察員 (本機行動)** | `make twin-scout-action` | **時機**: 需肉眼觀察或繼承本機登入狀態時。<br>**說明**: 帶有 UI (Headed) 的原生執行模式，適合測試星型群聊動態渲染等場景。 |
| **數位雙生百關動態模擬** | `make twin-simulator` | **時機**: 驗證極端混沌環境下的 UI 自癒能力時。<br>**說明**: 跑百關 E2E 模擬矩陣驗證（限額執行前幾關防超時），會搭配 `make twin-gen-levels` 生成與 `make twin-record` 單關錄影除錯。 |
| **終極自動化品質門禁** | `make audit-qa` | **時機**: Major Release、PR 合併至主幹前的最終驗收。<br>**說明**: 執行最嚴格的串流驗證，包含 DNS 洩漏掃描、UI 巢狀死鎖檢查、Migration 驗證 (⚠️**宿主機必須啟動 Docker**)、LLM 語意裁判、後端測試與前端 E2E 邊界測試。 |
| **毀滅性 E2E 測試門禁** | `make audit-qa-e2e` | **時機**: PR 合併至主幹前的 E2E 重點驗收。<br>**說明**: 執行會破壞並重置資料庫的 Playwright 關鍵 spec 測試門禁。 |
| **終極物理同步與重建** | `make sync-grounding` | **時機**: 代碼基線嚴重混亂或依賴損毀時。<br>**說明**: 強制重新拉取分支，全新 build 全 Docker 容器，清理並初始化資料庫，實施實體映像檔大小監控。 |
| **自動化技術債巡邏** | `make tech-debt-audit` | **時機**: 定期檢查（排程）或專案整理時。<br>**說明**: 掃描未歸檔的歷史文件 (PRPs) 與過期殭屍腳本，輸出任務供 DevBot 處理。 |
| **Token 效能與用量診斷** | `make test-perf` | **時機**: 發生 LLM Rate Limit (429) 或效能瓶頸時。<br>**說明**: 重現多併發下的 Token blocking 行為進行偵錯。 |
| **驗證種子資料寫入** | `make verify-data` | **時機**: 初始化資料庫 (`make db-init`) 之後。<br>**說明**: 驗證 Mock 資料是否正確寫入。 |

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

#### 3.2.4 防範虛假測試與型別斷層 (False Mock & Signature Sync - ⚠️ 核心防禦)

> **血淚教訓**: 在 Phase 5.9.4 中，我們發現 `text_to_speech_service` 的回傳型別早已從 `str` 改為 Tuple `(success, bytes)`，但 `test_report_service.py` 中的 Mock 卻依然回傳 `str`。這導致單元測試全數綠燈，但實際運行時卻因為 `too many values to unpack` 或寫入亂碼而崩潰。這就是標準的**「虛假測試 (False Test)」**。

**防禦規範**:
1. **型別簽章同步 (Signature Sync)**: 當您修改任何核心服務 (Service/Repository) 的**回傳型別 (Return Type)** 或**參數結構 (Argument Structure)** 時，**必須**使用全域搜尋 (`grep`) 找出所有依賴該服務的測試檔案 (`tests/`)。
2. **消滅陳舊 Mock (Eradicate Stale Mocks)**: 強制將所有測試中的 `mock_service.return_value` 更新為與物理現實 100% 一致的資料結構。
3. **拒絕測試偽證**: 單元測試通過不代表代碼安全，如果 Mock 的資料結構與物理現實脫節，單元測試就會淪為掩護 Bug 的遮羞布。修改型別後，務必執行 `make test-be` 並確認沒有出現 `too many values to unpack` 或 `TypeError`。

### 3.3 前端 E2E 測試 (`enduser-ui-fe`)

#### 3.3.1 E2E 測試核心架構與 MSW 規範

專案採用獨立 `vitest.e2e.config.ts` 設定檔將 E2E 測試與單元測試完全隔離，並由 `tests/e2e/e2e.setup.ts` 統一管理 API Mocking：

1. **標準化元件渲染**: 所有測試直接渲染 `AppRoutes` 元件，並提供 `AuthProvider` 和 `MemoryRouter` 作為 Wrapper。
2. **Hybrid Mocking 策略 (雙軌對齊)**:
   * **Auth 認證**: `e2e.setup.tsx` 使用 `vi.mock` 攔截 `api.getCurrentUser`，提供穩定的測試用戶身份。
   * **Data 數據 (Pass-through)**: 其他 API 預設透傳呼叫真實 `api.ts`，由底層 `fetch` 觸發 **Mock Service Worker (MSW)** 攔截。模擬資料結構（`src/mocks/handlers.ts`）必須與 `types.ts` 100% 物理對齊。
3. **全域 MSW Server 唯一性**: 嚴禁在個別測試檔中使用 `setupServer`。必須引用 `src/mocks/server` 之全域實例，並用 `server.use()` 注入專屬 Handler。
4. **Spying 與 `this` 綁定**: setup 中包裝 API 方法時，必須使用 `actual.api[key](...args)` 呼叫，確保 `api.ts` 內部的 `this._getHeaders()` 上下文正確綁定。
5. **關鍵方法時序豁免 (Exclusion)**: 關鍵方法（如 `getTasks`）因涉及複雜 Promise / Loading 狀態，豁免於 `vi.fn` 包裝，直接執行真實代碼防時序卡死。
6. **MSW 元素等待規範**: 測試 UI 狀態時，務必先 `await waitFor(() => expect(loading).not.toBeInTheDocument())`，避開非同步渲染差。

#### 3.3.2 完整整合測試之資料庫與憑證準備

1. **自動化資料庫重置**: 後端提供受 `ENABLE_TEST_ENDPOINTS` 保護之 `POST /api/test/reset-database` 端點，由 `globalSetup.ts` 於測試前自動重置資料庫。
2. **Supabase 憑證初始化**: 測試設定自動於 `jsdom` 之 `localStorage` 寫入 Supabase URL 與金鑰，確保客戶端正確發送請求。

### 3.4 前端測試常見問題 (FAQ)

| 問題 | 症狀 | 解決方案 |
| :--- | :--- | :--- |
| **Import Error** | `Failed to resolve import` | `package.json` 中缺少開發依賴。執行 `pnpm install --save-dev <package>`。 |
| **Aria Label & Accessibility** | 找不到純圖示按鈕 / Accessibility 稽核失敗 | 依規範為所有圖示/重整/關閉按鈕加上 `aria-label="描述"` 與 `title="描述"` 屬性，方便 E2E 透過 ARIA 穩定定位。 |
| **Event Click** | `required` 表單提交無反應 | 使用 `fireEvent.submit(submitButton)` 直接觸發提交。 |
| **Hoisting** | `vi.mock` 變數提升錯誤 | 將 `vi.mock` 需要的變數直接定義在工廠函式**內部**。 |
| **MSW Intercept** | `intercepted a request without a matching request handler` | 檢查測試中的 URL 參數是否與 Handler 定義完全匹配。動態注入請用 `server.use()`。 |
| **Timeout** | `Test timed out` | 檢查 `await waitFor` 是否在等待一個永遠不會出現的元素，或 API Mock 未正確回傳。 |
| **Async State** | `act(...) warning` | 確保所有觸發狀態更新的操作都被 `await`，或包在 `act(() => ...)` 中。 |
| **Element type is invalid** | `check the render method of ...` | 通常是 Import 錯誤。檢查是否混淆了 `default export` 與 `named export`，或引用了不存在的元件。 |
| **Mock Pollution** | 全域 Mock 跨測試互相污染，導致結果不穩定 | 必須在 `afterEach` 或 `teardown` 階段執行 `vi.resetAllMocks()` 或手動重置該 Mock 狀態以維持環境純淨。 |
| **Audit Error Silencing** | 巡檢腳本失敗但 CI 仍顯示綠燈 | 確保 `persona_smoke_test.py` 等驗證腳本具備實體錯誤傳播機制（拋出非零 Exit Code），嚴禁靜默吞除 Exception。 |

### 3.5 AI Agent 自癒能力驗證 (Self-Healing Verification)

本節介紹如何手動驗證 Archon 系統的 AI 自癒與智能分析能力。

**現狀說明 (Phase 4.5.7 Updated)**:
目前系統已升級至 **L2 級自動修復 (Autonomous Repair Loop)**。當 Agent 執行的指令失敗時，系統會自動啟動以下安全修復迴圈：
1.  **Analyze**: 呼叫 LLM 分析錯誤，生成結構化修復建議 (JSON)。
2.  **Sandbox**: 自動建立臨時分支 `autosave/fix-{id}`，確保不汙染主幹。
3.  **Apply**: 在沙箱中應用代碼修復 (`CodeModifier`)。
4.  **Verify**: 重跑指令驗證修復結果。
5.  **Handover**: 若驗證通過，保留分支並通知用戶進行 Merge Request。

**演練場景：自動修復語法錯誤**

1.  **製造錯誤**: 在根目錄建立 `broken_script.py`，內容為 `print "Hello" # Python 2 syntax error`。
2.  **觸發修復**: 呼叫 Agent Service 執行此腳本。
3.  **觀察結果**:
    *   Console 顯示 "Command failed. Starting Active Repair Loop."
    *   系統自動切換至 `autosave/fix-...` 分支。
    *   檔案被自動修正為 `print("Hello")`。
    *   最終回傳 "Command Succeeded after Auto-Repair"。

> **📝 流程總結 (Workflow Note)**:
> *   **Current**: 目前您會在 **Task Modal** 看到修復結果 (分支名稱)，然後您需要去 Git 手動合併。
> *   **Future**: 未來的版本會讓您在 **`/approvals`** 頁面直接點擊「批准」來合併 (視覺化 Diff)。

### 3.6 Clockwork 與排程除錯 (Clockwork Debugging)

Phase 4.4.5 引入了 **Clockwork** 進行系統自動檢測。
*   **查看執行紀錄**: 查詢資料庫中的 `archon_logs` 表。
    ```sql
    SELECT * FROM archon_logs WHERE source = 'clockwork-scheduler' ORDER BY created_at DESC;
    ```
*   **手動觸發**: 目前 Clockwork 隨 Server 啟動 (每 6 小時一次)。若需立即測試探針邏輯，請直接執行 `make probe`。

### 3.7 戰略級全系統驗證協議 (System Validation Protocols)

為了確保系統從底層代碼到頂層戰情數據皆處於健康狀態，本專案定義了兩套標準驗證序列：

#### **序列 A：邏輯與代碼驗證 (Developer/CI Sequence)**
**重心**: 確保「代碼沒有 Bug」。
**執行順序**: `make dev-docker` -> `make test` -> `make probe`
*   **`make test`**: 執行 610+ 項測試，確認 API 邏輯、權限與組件渲染正確。
*   **`make probe`**: 在容器內執行，驗證資料庫連線、AI 金鑰與 RAG 檢索維度。
*   **適用場景**: 提交代碼前的最後品質把關。

#### **序列 B：戰略展示與數據落地 (Strategic/Showcase Sequence)**
**重心**: 確保「系統具備真實營運感」。
**執行順序**: `make dev-docker` -> `make db-init` -> `make db-fuel` -> `make probe`
*   **`make db-init`**: **建立基石**。重置並執行所有遷移，建立 Alice/Bob 等基礎帳號。
*   **`make db-fuel`**: **注入靈魂**。注入 6 個月歷史紀錄（產出、協作、ROI、SLA），讓 Nexus 戰情室充滿戰略趨勢數據。
*   **適用場景**: 環境初次部署、系統功能演示、或針對指標口徑進行驗收。

#### **序列 C：AI Agent 提交通訊協議 (Agent Commit Protocol)**
為了防止 Agent 過度自信導致系統崩潰，AI 開發者（如 DevBot）在提交任何重構變更前，**必須**強制理解並通過以下核對：

1.  **分級晉升**: 遵循 `SOP_Refactoring_Methodology.md`。Level 1 修復必須累積 > 500 次成功紀錄才可解鎖 Level 2。
2.  **物理核對**: 嚴禁猜測測試結果。必須執行 `make lint` (全端) 與 `pnpm test:unit`。
3.  ** Regression 防止**: 即使只改後端，也必須驗證 `enduser-ui-fe` 的行銷頁面與統計圖表是否正常顯示。

### 3.8 Multi-Agent 群聊驗證 SOP (Dev Auto-Login)

在 Phase 5.0.2 之後，系統導入了基於 Supervisor 的「星型群聊」架構。為了驗證這個新功能（例如：DevBot、MarketBot、David 的協作），**請不要使用 `make twin-scout`，因為它無法測試動態渲染的 UI。** 

請遵循以下步驟，使用開發者後門 (Dev Auto-Login) 進行真實體驗驗證：

1. **獲取萬能鑰匙**: 執行 `make db-init`。在終端機輸出的最後幾行，找到並複製這段網址：
   ```text
   🔑 Dev Auto-Login URL: http://localhost:5173/dev-token?token=eyJhb...
   ```
   *(⚠️ 鐵律：請注意 Port 號永遠是 5173，絕對不是 3737)*
2. **免密碼登入**: 將該網址貼上瀏覽器，系統會自動以 Admin 身分登入並跳轉。
3. **觸發特定劇本 (Context Routing)**: 在 UI 中建立一張新的工單 (Task)。
   * **Assignee (指派)**: 選擇 **`Archon Supervisor`** (大腦)。
   * **Title (標題)**: 這是觸發隱藏劇本的關鍵！
     * 若要測試「行銷數據深度分析」(場景 B，呼叫 DevBot/David)：請在標題中包含 **`Marketing Data Deep Dive`** 或 **`行銷數據`**。
     * 若要測試「一般任務」(場景 A，呼叫 Librarian/Summary)：隨意輸入不含上述關鍵字的標題即可。
   * **Description (描述)**: 寫下你希望 Agent 執行的具體指令。
4. **觀察非同步群聊**: 按下送出後，前端會進入 Loading 狀態。此時後端 `WorkflowEngine` 正在進行 30~60 秒的思考與資料庫存取。
5. **物理驗收**: 點開該工單，你應該會看到原本的純文字報告，被渲染成擁有各角色大頭貼與顏色的「WhatsApp 風格對話泡泡群聊」。

---

## 第四章：貢獻與部署流程 (Contribution & Deployment)

### 4.1 前端開發規範 (End-user UI)
- **Agent 與儀表板位置 (UI Domain Rule - Critical)**: 所有的 AI Agent 相關功能展示（例如：Agent XP 排行榜、Agent 任務派遣列表），**必須**實作在 `enduser-ui-fe` (Port 5173) 中。嚴禁將終端使用者的協作功能錯誤地放入 `archon-ui-main` (Admin UI, Port 3737)。開發時若存在網域存放的疑慮，應以此條例為準。
- **捲動安全性 (Mobile Scroll Safety - Critical)**: 嚴禁在頁面最外層容器使用 `min-h-screen`、`h-screen` 或 `h-full` 搭配 `overflow-hidden`。這會導致在手機瀏覽器中，內容高度無法正確向外傳遞至 `MainLayout`，進而鎖死垂直捲動。應保持容器高度為 `auto`，並使用底部間距 (`pb-32`) 確保內容不被導覽列遮擋。
- **AI 反饋與超時 (UX Strategy)**: 
    - 任何預期執行時間超過 15 秒的 AI 任務（如 RAG 檢索、Pro 模型生成），**必須**實作動態狀態訊息（每 10-15 秒切換一次文字），讓使用者知道系統仍在運行。
    - 前端超時門檻應統一提升至 60 秒，以應對複雜的 RAG 推理。
- **React Hook 穩定性 (Critical)**: 在實作如 `RAGSettings` 等複雜組件時，**嚴禁**將「對象實例 (Object/Array)」直接放入 `useEffect` 的依賴陣列中。這會導致無限渲染循環 (Infinite Re-render)。應解構為「原始型別屬性 (Primitives)」作為依賴。
- **型別安全性**: 必須同步更新 `src/types.ts` 並通過 `tsc --noEmit` 檢查。

### 4.2 Git 工作流程


- **分支策略**: 所有工作都**必須**在 `feature/...` 分支上進行。完成後必須 Rebase/Merge 回 `dev/twins` 主幹分支，並由 `dev/twins` 觸發 Vercel/Render/Hugging Face 的生產部署。`main` 分支請勿使用。
- **`cherry-pick` 卡住**: 若 `git cherry-pick --continue` 卡住，請改用 `git cherry-pick --continue --no-edit --no-gpg-sign`。

### 4.3 部署標準作業流程 (SOP)

- `migration/0.2.3/01_schema_core.sql`
- `migration/0.2.3/02_schema_features.sql`
- `migration/0.2.3/03_logic_functions.sql`
- `migration/0.2.3/04_logic_security_rls.sql`
- `migration/0.2.3/05_seed_system_configs.sql`
- `migration/0.2.3/06_seed_prompts_core.sql`
- `migration/0.2.3/07_seed_prompts_assets.sql`
- `migration/0.2.3/08_schema_task_retry_count.sql`
- `migration/0.2.3/RESET_DB.sql`
- `migration/0.2.3/rescue/fix_missing_agents.sql`
- `migration/0.2.3/rescue/leads.sql`

> **📝 遷移檔更新通知 (Migration Updates)**
> 部署前請確保已套用最新版本的 SQL 遷移檔。所有遷移檔皆存放於 `migration/0.2.3/` 目錄中，並嚴格依照檔案前綴數字標號順序執行 (如 `01` -> `02` -> `07`，最後再執行 seed_*.sql)。

- `migration/0.2.3/01_schema_core.sql`
- `migration/0.2.3/02_schema_features.sql`
- `migration/0.2.3/03_logic_functions.sql`
- `migration/0.2.3/04_logic_security_rls.sql`
- `migration/0.2.3/05_seed_system_configs.sql`
- `migration/0.2.3/06_seed_prompts_core.sql`
- `migration/0.2.3/07_seed_prompts_assets.sql`
- `migration/0.2.3/08_schema_task_retry_count.sql`
- `migration/0.2.3/RESET_DB.sql`
- `migration/0.2.3/rescue/fix_missing_agents.sql`
- `migration/0.2.3/rescue/leads.sql`
- `migration/0.2.3/rescue/prompts.sql`
- `migration/0.2.3/rescue/schema_migrations.sql`
- `migration/0.2.3/rescue/sources_and_targets.sql`
- `migration/0.2.3/seed_blog_posts.sql`
- `migration/0.2.3/seed_mock_data.sql`
- `migration/0.2.3/seed_rag_defaults.sql`
- `migration/20260810_seed_rag_blog.sql`
- `migration/20260815_seed_insight_report_blog.sql`
- `migration/20260819_add_hybrid_router_settings.sql`
- `migration/20260819_update_rag_threshold.sql`
- `migration/20260821_update_leads_patrol_prompt.sql`


此流程的最終目標，是成功將一個穩定的 `feature/...` 分支部署到 **Render**。

1.  **階段一：部署前本地檢查**
    *   **快速檢查**: 執行 `make test` 與 `make lint`。
    *   **完整驗證**: 執行「[2.3 全 Docker 環境手動驗證 SOP](#23-全-docker-環境手動驗證-sop)」。

2.  **階段二：資料庫遷移 (Database Migration) - v2 (Tracked)**

    **核心原則**:
    *   **冪等性**: 所有遷移腳本都必須是冪等的 (`IF NOT EXISTS` / `DROP ... IF EXISTS`)。
    *   **版本註冊**: 每個腳本執行成功後，必須將自己的檔名版本號註冊到 `schema_migrations` 表中。

    **開發新遷移腳本的流程**:
    1. **建立檔案**: 使用下一個數字前綴建立 SQL 檔 (如 `34_add_new_feature.sql`)。
    2. **寫入冪等 SQL 與版本註冊**:
        ```sql
        -- 1. 冪等 DDL/DML 語法
        CREATE TABLE IF NOT EXISTS my_table (...);

        -- 2. 註冊此遷移腳本的版本 (不含 .sql 副檔名)
        INSERT INTO schema_migrations (version) VALUES ('34_add_new_feature') ON CONFLICT (version) DO NOTHING;
        ```

    **🛡️ SQL 腳本品質檢查清單 (SQL Quality Checklist)**:
    - [ ] **冪等性**: 是否使用了 `IF NOT EXISTS` 或 `DROP ... IF EXISTS`？
    - [ ] **版本追蹤**: 是否包含了 `INSERT INTO schema_migrations` 語句？
    - [ ] **資料保留**: 修改種子資料 (`seed_*.sql`) 時是否確認了是 `APPEND` (追加) 還是 `OVERWRITE` (覆蓋)？**嚴禁**在未讀取原內容的情況下直接覆蓋。

    **本地開發與救災 SOP**:
    * **自動化指令 (推薦)**: 執行 `make db-init`（會自動按序執行 `migration/*.sql` -> 填充 Mock Data -> 修復 Auth ID 同步）。
    * **手動初始化救援**: 若自動化指令失敗，請登入 Supabase SQL Editor，依 `migration/0.2.3/` 資料夾下檔案數字標號前綴（01 核心結構 -> 03 邏輯 -> 04 安全政策 -> 05+ 種子資料）順序手動貼上執行。

3.  **階段三：執行部署**

    **3.1 前端服務的路由設定 (Render Rewrite 規則)**

    單頁應用 (SPA) 前端服務 (如 `archon-ui-main`, `enduser-ui-fe`) 必須在 Render **"Redirects/Rewrites"** 區塊依序新增以下**兩條**規則：

    1. **規則一：API 代理規則 (優先級最高)**
       * **Source**: `/api/:path*` (或 `/api/*`)
       * **Destination**: `https://<ARCHON_SERVER_URL>/api/:path*` (替換為後端真實網域)
       * **說明**: 將 `/api/` 請求代理至後端服務。
    2. **規則二：SPA 回退規則 (優先級較低)**
       * **Source**: `/*`
       * **Destination**: `/index.html`
       * **說明**: 未匹配到的路由全數導向 `index.html` 由前端 Router 接管。

    **3.2 上線前檢查清單 (Pre-Flight Checklist)**

    - [ ] **資料庫遷移驗證**: 本地執行 `make db-init` 顯示 `🎉 SQL migrations applied!` 與 `✅ Auth Sync Complete.`。
    - [ ] **前端路由驗證**: Render 雙重 Rewrite 規則已依序設定，部署後訪問 `/api/health` 回傳 JSON (非 HTML 404)。
    - [ ] **環境變數金鑰安檢**: 
      * 後端 `SUPABASE_SERVICE_KEY` **必須使用 `service_role` (Secret) Key**。使用 public `anon` key 後端會崩潰。
      * `SUPABASE_URL` 強制以 `https://` 開頭。
    - [ ] **功能煙霧測試 (Smoke Test)**:
      使用 Dev Token 或執行 `make probe` 打通 `GET /api/system/health/rag`，確認回傳 `"status": "healthy"` 且 DB / Vector / LLM 端點均正常。

    **3.3 觸發部署**
    1. 確認 Render 監控 `dev/twins` 或預期之分支。
    2. 推送代碼: `git push origin <branch>`，Render 自動觸發 Build。

4.  **階段四：部署後驗證**
    1. 在 Render Dashboard 觀察 Build & Deploy Logs。
    2. 訪問 `/health` 確認回傳 `{"status":"ok"}`。
    3. 開啟前端網址進行 Smoke Test 通過。

### 4.4 AI 開發者協作流程 (AI Developer Workflow)

隨著 `Phase_4.1` 的完成，專案引入了一套由 AI Agent 輔助開發的全新工作流程。此流程的核心是「**提議 -> 審核 -> 執行**」，旨在確保 AI 在安全、可控的環境下為程式碼庫做出貢獻。

#### 4.4.1 資料庫基礎：`proposed_changes` 資料表

此工作流程由 `migration/005_create_proposed_changes_table.sql` 所建立的 `proposed_changes` 資料表支撐。

- **核心欄位**:
    - `id`: 提案的唯一標識符。
    - `type`: 提案類型（`file`, `git`, `shell`）。
    - `status`: 提案狀態（`pending`, `approved`, `rejected`, `executed`, `failed`）。
    - `request_payload`: 一個 `jsonb` 欄位，儲存了提案的具體內容。例如，對於一個 `file` 類型的提案，這裡會包含 `file_path`, `new_content`, 以及用於 Diff 顯示的 `original_content`。

#### 4.4.2 開發者審核工作流程

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

#### 4.4.3 與 Git 流程的結合

- AI 的所有工作都會在一個獨立的 `feature/` 分支上進行。
- AI 提交的變更，在被批准和執行後，最終會以一個 `commit` 的形式出現在該 `feature/` 分支上。
- 開發者後續可以像對待任何人類開發者提交的 `commit` 一樣，對其進行 code review、合併或進一步修改。

## 第五章：Git 歷史追溯指南 (Git Archaeology Guide)

> **原則**: 當文件與程式碼出現矛盾，或不確定某個功能的設計初衷時，Git Log 是唯一的真相來源。

### 5.1 常用考古指令

| 情境 | 指令範例 | 說明 |
| :--- | :--- | :--- |
| **快速檢視最近修復進程** | `git log -n 20 --oneline` | 顯示最近 20 次簡短提交紀錄，適合快速確認 PR 合併與開發進度。 |
| **查閱檔案變更歷史** | `git log -p -- Makefile` | 顯示該檔案每次提交的具體差異 (Diff)。 |
| **跨重命名追蹤檔案歷史** | `git log --follow <file>` | 當檔案經過 L2 拆解或更名時，穿透追蹤其重命前的原始歷史。 |
| **搜尋代碼何時被加入/刪除** | `git log -S "await task_service"` | 找出包含特定字串之新增或刪除的提交。 |
| **強效 Regex 內容變更搜尋** | `git log -G "def run_.*"` | 使用正規表示式搜尋函式簽署與型別改動的歷史 Commit。 |
| **追查行數最後修改源頭** | `git blame <file>` | 顯示檔案每一行的最後修改者與提交 Hash。 |
| **查看特定提交的內容** | `git show <commit_hash>` | 檢視某個 Commit 的完整變更。 |
| **比較兩個分支的差異** | `git diff main...feature/new-ui` | 檢視 Feature 分支相對於 Main 分支的變更。 |

---

## 第六章：常見問題排查 (Troubleshooting SOP)

### 6.1 資料庫災難復原 (RESET_DB.sql)
* **症狀**: `make db-init` 執行後資料庫仍為空，或 `make test` 後資料未還原。
* **根源**: E2E 測試重置資料庫時 `schema_migrations` 表未清空，導致初始化腳本誤判已完成。
* **解法**: 
  1. 執行手動強重置: 執行 `migration/RESET_DB.sql` (清空包含 `schema_migrations` 在內的所有表)。
  2. 重新初始化: 執行 `make db-init`。
  3. 恢復 RAG 知識庫: 若 `make probe` 分數偏低，執行 `docker exec archon-server python scripts/seed_knowledge.py`。

---

### 6.2 Supabase Auth 406 Error (Not Acceptable)
* **症狀**: 前端登入成功，但呼叫 `/profiles` API 時收到 `406 Not Acceptable` 且回傳 Body 為空。
* **根源**: **ID 不匹配 (ID Mismatch)** — 前端使用 `.single()` 查詢，但 `auth.users` 的 UUID 與 `public.profiles` 的 `id` 不同步。
* **解法**: 執行 `make db-init`（內建「雙重同步策略 Dual Sync」，會自動執行 `UPDATE profiles SET id = auth_uuid` 強制對齊）。

---

### 6.3 開發者自動登入 (dev-token) 500 Error
* **症狀**: 存取 `localhost:3737` 時，瀏覽器顯示 `POST /api/auth/dev-token 500`。
* **排查步驟**:
  1. **密碼檢查**: 開發環境統一標準密碼為 `qwer45tyuiop` (`auth_api.py`)。
  2. **相對路徑檢查**: 確保 `main.py` 無 `ModuleNotFoundError` 匯入錯誤。
  3. **金鑰權限**: 確保 `SUPABASE_SERVICE_KEY` 具備 `service_role` 權限且未過期。

---

### 6.4 Hugging Face UnicodeEncodeError (注音輸入法剪貼簿陷阱)
* **症狀**: 部署至 HF Spaces 後伺服器崩潰，日誌顯示 `UnicodeEncodeError: 'latin-1' codec can't encode character '\u3112'`。
* **根源解析**: **台灣 Mac 開發者專屬陷阱** — 在 HF Settings -> Secrets 貼上 `HF_TOKEN` 時未切換至英文輸入法，按 `Cmd+V` 誤將注音符號「ㄒ」(`\u3112`) 帶入金鑰末端。發送 HTTP Header 時 `http.client` 無法編碼「ㄒ」為 `latin-1` 引發致命崩潰。
* **解法**: 切換為純英文輸入法，刪除舊 Secrets 並重新貼上乾淨金鑰後儲存。

---

### 6.5 爬蟲與 WAF 403 錯誤防禦 (Proxy Pool)
* **症狀**: `JobBoardService` 在暖機或爬取時遭遇 `403 Forbidden`。
* **根源**: 目標 WAF 偵測到同 IP 短時間大量無 Cookie 請求而引發攔截。
* **防禦策略**:
  1. **短期**: 啟用 `RateLimiter` 速率限制與亂數延遲 (`time.sleep`)。
  2. **中期**: 確保 `curl_requests.Session` 在 Warm-up 時正確繼承 WAF Challenge Cookie。
  3. **長期**: 高頻爬蟲導入動態代理池 (Proxy Pool) 分散 IP 請求。

---

## 附錄 A：歷史決策與背景導覽 (Historical Context & PRPs)

* 詳情請參閱 [`PRPs/Phase_4.2_Business_Feature_Expansion_Plan.md`](file:///Users/vincenta/GoogleKwok022/Archon/PRPs/Phase_4.2_Business_Feature_Expansion_Plan.md) 及相關歷史 PRPs 檔案庫。

---

## 附錄 B：技術債監控 (Technical Debt Monitor)

> **結算日期**: Phase 5.11.3
> **狀態**: 🟢 **全系統 0 Monolith 巨型檔案 (>400行)**，由 `make phase-audit` (Step 6) 與 `make tech-debt-audit` 自動化動態監控過期腳本與 PRPs 雜亂檔案。

### 第三方依賴已知問題 (Third-Party Known Issues)
1. **`notebooklm-py` MCP 註冊失敗 (0.8.1 vs FastMCP 2.12.4)**
   - **現象**: 啟動時報錯 `Failed to register official notebooklm-py tools: The @tool decorator was used incorrectly.`
   - **原因**: `notebooklm-py` 源碼遺留 `@mcp.tool` 寫法 (無括號)，觸發新版 FastMCP 的嚴格型別校驗。
   - **處置**: **維持現狀 (Ignored)**。我們在 `notebooklm_tools.py` 已透過 `try-except` 物理攔截防禦，並成功掛載自定義的 Fallback Tools。系統功能 100% 正常，無須改動代碼，等待官方套件更新。

---

## 附錄 C：系統演進現狀 (System Evolution Status)

* **工具與權限 (MCP)**：使用 `AgentService` + `MCPClient` 雙階段迴圈（Think -> Tool -> Act），受 `TOOL_CONFIG` 白名單保護。
* **Agent 註冊**：所有 Agent 定義、Prompts 集中於 `src/server/services/agent_registry.py`，關閉 LLM 思考指令雙軌制。
* **長期型別與測試防線**：後端物理性 Zero MyPy Errors，後端測試 610+ 項與前端測試 183+ 項達成 100% 通過率。

---

## 附錄 D：基礎設施物理審計 (Infrastructure Audit)

> **結算日期**: Phase 5.5.0 (Offline Hardening) — `archon-server` 體積成功由 31.5GB 瘦身至 **5.02GB**。

* **體積減重核心**：
  1. **CPU PyTorch 強制約束**：安裝時指定 `--extra-index-url https://download.pytorch.org/whl/cpu` 剃除數 GB 的 CUDA 庫死重。
  2. **編譯快取防禦**：Dockerfile 嚴禁 `COPY` 建置快取（如 `/root/.cache`）進入生產映像檔，防範 `ENOSPC` 磁碟耗盡。

---

## 附錄 E：資料庫表格設計初衷 (Schema Rationale)

記錄看似無即時呼叫之保留表設計初衷，防止誤刪：
* **`market_insights`** (Phase 4.2)：為 Bob 產出的「戰略級市場分析報告」預留之長期趨勢分析基石。
* **`subscriptions`** (2025-09 重構)：為未來「商業化付費模式」預留之 API 訂閱與計費數據模型。

---

## 附錄 F：數位雙生與 E2E 驗證規範 (Digital Twin & E2E Standard)

* **IPA 自癒定位原則**：優先使用語意定位（如 `button:has-text('...')`），嚴禁易斷裂的 CSS 階層路徑。具備 Sandbox Idempotency 與 Pixelmatch 預篩的 Gemini Vision 視覺評判。
* **核心工具組**：動態關卡生成 (`make twin-gen-levels`)、百關模擬器 (`make twin-simulator`) 與 Headed 視覺對帳 (`make twin-record`)，詳細指令說明請參閱第三章 3.1.2 門禁表格。

---


## 附錄 G：外部 API 與環境變數設定手冊 (External API Setup Guide)

### G.1 如何更換或設定 Google Drive 與 NotebookLM 帳號
為確保開發者與使用者的系統能在背景穩定運行，絕不採用易過期的短效 Token (例如 60 分鐘到期的 OAuth Access Token)。當您需要設定或更換連動的 Google 帳號時，請嚴格遵守以下物理操作步驟，並更新 `.env` 檔案。

**【更換帳號的核心概念】**
若要更換目標帳號（即「檔案要上傳到誰的雲端硬碟」或「要讀取誰的 NotebookLM」），您只需透過指令重新登入，或更換 `.env` 中的 `Refresh Token` 即可，程式碼完全不需要改動（零硬編碼）。

#### 步驟一：取得 NotebookLM 憑證 (NOTEBOOKLM_AUTH_JSON)
1. 在終端機執行 `uv run notebooklm login`。
2. 系統會自動彈出 Chrome 瀏覽器，請**選擇您要更換的 Gmail 帳號登入**。
3. 登入完成後，憑證會自動存入本地端 (`~/.notebooklm/profiles/default/storage_state.json`)，本機開發不需額外設定變數。
4. 若要部署至 Hugging Face (Docker)，請執行 `cat ~/.notebooklm/profiles/default/storage_state.json`，將印出的整串 JSON 複製，並貼到 HF Secrets 的 `NOTEBOOKLM_AUTH_JSON`。

#### 步驟二：取得 Google Drive 永久 Refresh Token
1. **登入目標帳號**：請先開啟無痕視窗，或在瀏覽器中切換並登入您想要綁定的「新 Google 帳號」。
2. 前往 GCP 控制台建立**網頁應用程式 (Web application)** 的 OAuth 用戶端 ID。
   *(注意：應用程式類型必須是「網頁應用程式」，絕不能選「電腦版」，否則會觸發 `redirect_uri_mismatch` 錯誤)*。
3. 在「已授權的重新導向 URI」精準填入：`https://developers.google.com/oauthplayground`。
4. 將取得的 Client ID 與 Client Secret 填入 `.env` 的 `GOOGLE_DRIVE_CLIENT_ID` 與 `GOOGLE_DRIVE_CLIENT_SECRET`。
5. 前往 Google OAuth 2.0 Playground，點擊右上角「齒輪」，勾選 `Use your own OAuth credentials`，填入新的 ID 與 Secret。
6. 在 Step 1 選擇 Drive API v3 (`https://www.googleapis.com/auth/drive`) 並點擊授權。
7. **(關鍵防呆)**：登入時，請確認畫面上的信箱是您在步驟 1 登入的新帳號！如果 GCP 專案處於測試中，請先去「OAuth 同意畫面」將該信箱加入「測試使用者 (Test users)」。
8. 在 Step 2 點擊 Exchange 取得 `Refresh Token`，將其以 `1//...` 開頭的字串填入 `.env` 的 `GOOGLE_DRIVE_REFRESH_TOKEN`。
