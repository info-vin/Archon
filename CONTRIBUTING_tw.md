# 專案食譜 (Project Cookbook)

> 歡迎來到 Archon 廚房！本食譜記載了我們團隊合作的最佳實踐與標準作業流程 (SOP)。
> 本文件旨在提供清晰、精煉且可執行的指南。所有歷史決策與背景故事已歸檔至附錄。

---

## 第一章：核心心法 (Core Mindset)

| 原則 | 解釋 |
| :--- | :--- |
| 1. **警惕「副本任務」陷阱** | 分析是為了解決「主線任務」，而不是開啟無止盡的調查循環。拿到分析結果後，應立即專注於完成最初目標。 |
| 2. **物理穿透驗證 (拒絕幻想)** | 拒絕「日誌領跑代碼」。不要幻想狀態完美，必須使用工具讀取磁碟實體內容並執行測試驗證，方可標記為已修復。 |
| 3. **精準修改，避免副作用** | 採取最小、最精準的修改。使用 Code Edit 工具時務必提供完整上下文，杜絕「改 A 壞 B」。 |
| 4. **徹底理解工具** | 使用 `make` 或腳本前，先閱讀其源碼，理解是否包含 `--fix` 等帶有副作用的參數。 |
| 5. **撰寫冪等的資料庫腳本** | 所有 Migration 腳本皆需具備冪等性，大量使用 `DROP ... IF EXISTS` 和 `CREATE ... IF NOT EXISTS`。 |
| 6. **`Makefile` 是唯一指令來源** | 文件與開發統一引用 `make <command>`，避免直接複製貼上底層 shell 指令。 |
| 7. **安全修改與快速復原** | 當修改後測試失敗，應立即使用 `git checkout -- <file>` 還原，嚴禁在錯誤的基礎上繼續堆疊修補。 |
| 8. **維持「啞巴控制器」** | API 控制器應保持輕量。版本控制、來源連結等複雜商業邏輯統一封裝於 Service 層。 |
| 9. **拒絕「手動拆包」** | 嚴禁在 API 層使用連續 `if request.field is not None`。應善用 Pydantic `model_dump(exclude_unset=True)`。 |
| 10. **型別是開發者的盔甲** | 使用 `cast` 進行顯式擔保，明確劃分 Pydantic (執行期安檢) 與 MyPy (開發期藍圖審查) 職責。 |
| 11. **營運 SDK 必須對齊** | Port 5173 營運端功能統一使用 Google 原生 SDK (`genai.Client`)。嚴禁對生產路徑使用不穩定的 OpenAI Shim。 |
| 12. **腳本存放唯一真相** | 所有 Python 診斷與遷移腳本**必須**存放於外層 `scripts/` 目錄，確保 Docker 與 Host 呼叫路徑一致。 |
| 13. **資料庫語意化整併** | 當 Migration 碎片化過多時，使用 `pg_dump` 抽出當下結構，按外鍵順序整併為純淨檔案並清除舊債。 |
| 14. **絕對雲原生意識** | 專案連接的是雲端 Supabase，嚴禁使用 `docker exec psql` 強修資料庫。正確作法是產出 SQL 檔由使用者於雲端執行。 |
| 15. **環境與硬體對齊 (Intel Mac 警示)** | 涉及 ML 模型 (如 Torch, Rerank) 時，鎖定 NumPy 為 1.x (如 `1.26.4`) 並實施物理探針驗證載入秒數。 |
| 16. **拒絕路由幻想 (API Route Sovereignty)** | 嚴禁假設路由存在。必須讀取 `main.py` 與 `api_routes/` 實體檔案。後端不處理 Auth 登入（由前端與 Supabase 直連）。 |
| 17. **角色連通性稽核 (Persona Smoke Test)** | 針對五大角色從 UI 元件 (`.tsx`) 往下尋線，確認實體呼叫打通 Endpoint，杜絕空殼 UI 假落地。 |
| 18. **杜絕迴圈內單筆寫入 (Bulk Insert)** | 嚴禁在迴圈內呼叫 `insert().execute()`。必須先收集 payload，在外層進行 Bulk Insert，防範 I/O 阻塞。 |
| 19. **消滅硬編碼與 Fallback 韌性** | 閾值與提示詞統一從 `SettingsService` 動態讀取 (Model SSOT)，並提供安全 Fallback Default。 |

---

## 第二章：環境設定 (Environment Setup)

### 2.1 本地開發環境啟動 SOP (混合模式)

**架構分工**:
- **後端 (Backend)**: 在 Docker 中運行 (`archon-server`, `archon-mcp`, `archon-agents`)
- **前端 (Frontend)**: 在**本機**運行以支援熱加載
    - `archon-ui-main` (管理後台) -> Port `3737`
    - `enduser-ui-fe` (使用者介面) -> Port `5173`

**執行步驟**:
```bash
# 1. 啟動後端服務 (終端機 1)
make dev

# 2. 初始化資料庫 (⚠️ 必須在 Docker 啟動後執行)
make db-init

# 3. 啟動管理後台 (終端機 2)
make install-ui && cd archon-ui-main && pnpm run dev

# 4. 啟動使用者介面 (終端機 3)
make install && cd enduser-ui-fe && pnpm run dev
```

> **💡 連接埠指引**:
> * **Port 5432 (Session Mode)**: 用於 Migration 與 Init 腳本 (`init_db.py`)。
> * **Port 6543 (Transaction Mode)**: 用於 Production 併發高流量。

---

### 2.2 後端依賴與環境管理
- **`uv.lock` 管理**: `python/uv.lock` 必須提交至 Git，確保團隊與 CI 套件版本完全一致。
- **Logfire 與 Logger**: 獨立腳本入口需呼叫 `setup_logfire()`。全專案統一使用 `from src.server.config.logfire_config import get_logger`。

---

### 2.3 全 Docker 環境手動驗證 SOP
當遇到複雜的啟動問題時，依序執行：
```bash
# 徹底清理容器與 Volumes (需輸入 y 確認)
make clean

# 重新建置全模組映像檔
docker compose --profile backend --profile frontend --profile enduser --profile agents build

# 前景啟動觀察日誌
docker compose --profile backend --profile frontend --profile enduser --profile agents up
```

---

### 2.4 Cookie 加密與物理邊界 (Digital Twin 必讀)
* **macOS Keychain 加密**: 本機 Host 產生的 `.browser_data` 受 macOS 密鑰保護，掛載至 Docker Linux 容器後 Chromium **無法解密**。
* **開發鐵律**: 依賴本機敏感登入狀態的腳本 (如 `make twin-scout-action`) 應於 Host 本機執行；容器內僅執行無狀態對帳 (`make twin-scout`)。

---

### 2.5 Lean 4 本地開發環境
Lean 4 位於 `lean_proofs/`，本地驗證步驟：
```bash
# 1. 安裝 elan
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# 2. 編譯測試
cd lean_proofs && lake build
```

---

## 第三章：測試與品質門禁 (Testing & Quality Gates)

### 3.1 測試與門禁指令總覽

| 目的與驗證層級 | 指令 | 說明 / 資料庫影響 |
| :--- | :--- | :--- |
| **執行全套測試** | `make test` | ⚠️ **重置資料庫** (清空數據) |
| **僅執行後端測試** | `make test-be` | ✅ **安全** (不重置資料庫) |
| **前端單元測試** | `cd enduser-ui-fe && pnpm run test:unit` | ✅ **安全** (不重置資料庫) |
| **前端 E2E 測試** | `cd enduser-ui-fe && pnpm run test:e2e` | ⚠️ **重置資料庫** (清空數據) |
| **RAG 健康檢查** | `make probe` | ✅ **安全** (測試 Alice->Librarian->Bob 管道) |
| **靜態語法與型別檢查** | `make lint`<br>`make lint-be` / `make lint-fe` | 執行 Biome, ESLint, Ruff, MyPy |
| **全域 Persona 巡檢** | `make persona-audit` | 驗證 5 大角色 RBAC 流程 |
| **數位雙生 E2E 模擬** | `make twin-scout` / `make twin-simulator` | 容器內 Headless 與百關混沌模擬 |
| **終極自動化品質門禁** | `make audit-qa` | Release 前無破壞性全方位品質公證 |
| **毀滅性 E2E 門禁** | `make audit-qa-e2e` | 破壞性 E2E 關鍵流程門禁 |
| **自動化技術債巡邏** | `make tech-debt-audit` | 掃描過期 PRPs 與殭屍腳本 |

---

### 3.2 後端 API 測試規範

1. **資料庫 Mocking**:
   後端測試**嚴禁連線真實 DB**。`conftest.py` 已提供 `client` 與 `mock_supabase_client` 模擬物件。
2. **Service 模擬黃金模式 (Patch Order)**:
   使用 `pytest` 的 `setup_module` / `teardown_module` 管理 patch，且 `patch` **必須在 `import app` 之前**宣告：
   ```python
   from unittest.mock import patch, AsyncMock

   mock_agent_service = patch('src.server.services.agent_service.AgentService', new_callable=AsyncMock)

   def setup_module(module):
       mock_agent_service.start()

   def teardown_module(module):
       mock_agent_service.stop()

   from src.server.main import app
   ```
3. **防範虛假測試 (False Mock & Signature Sync - 核心防禦)**:
   * **型別簽章同步**: 當修改 Service 回傳型別（例如從 `str` 改為 Tuple `(success, bytes)`）時，必須使用 `grep` 全域搜尋所有測試檔，同步更新 `mock_service.return_value`。
   * **杜絕測試偽證**: 嚴禁讓脫節的 Mock 掩護 `too many values to unpack` 或 `TypeError` 隱患。

---

### 3.3 前端 E2E 測試架構 (`enduser-ui-fe`)

1. **雙軌對齊 (Hybrid Strategy)**:
   * **Auth 認證**: `e2e.setup.ts` 使用 `vi.mock` 攔截 `api.getCurrentUser`，提供穩定測試身份。
   * **Data 數據**: 使用 **MSW (Mock Service Worker)** 攔截 `fetch` 請求，模擬數據結構必須與 `types.ts` 100% 物理對齊。
2. **全域 MSW Server 原則**:
   * 嚴禁在個別測試中 `setupServer`。必須引用 `src/mocks/server` 的全域實例，並使用 `server.use()` 注入專屬 Handler。
3. **Mock 防污染**:
   * 在 `afterEach` 必須呼叫 `vi.resetAllMocks()`，避免跨測試狀態污染。

---

### 3.4 Multi-Agent 群聊驗證 SOP (Dev Auto-Login)

驗證星型群聊 (DevBot, MarketBot, David 協作) 流程：
1. 執行 `make db-init`，複製輸出的 **Dev Auto-Login URL** (`http://localhost:5173/dev-token?token=...`)。
2. 貼上瀏覽器免密碼登入。
3. 新增 Task 工單：
   - **Assignee**: 選擇 `Archon Supervisor`
   - **Title**: 包含 `Marketing Data Deep Dive` (觸發行銷劇本) 或一般標題
4. 觀察後端 30~60 秒思考後，前端渲染出的 WhatsApp 風格角色對話泡泡。

---

## 第四章：貢獻與部署流程 (Contribution & Deployment)

### 4.1 前端開發規範 (End-user UI)
- **網域劃分**: 所有 AI Agent 互動與儀表板 (XP、任務派遣) **必須**寫在 `enduser-ui-fe` (Port 5173)。Port 3737 僅供 Admin 管理。
- **捲動安全性**: 容器嚴禁在最外層使用 `min-h-screen` 搭配 `overflow-hidden`。保持高度 `auto` 並加上底部留白 (`pb-32`)。
- **Hook 穩定性**: `useEffect` 依賴陣列嚴禁放複雜物件 (Object/Array)，應解構為原始型別屬性以防無窮重繪。

---

### 4.2 Git 部署標準作業流程 (SOP)

1. **分支與部署**: 所有開發在 `feature/...` 分支，經測試後 Rebase/Merge 至 `dev/twins` 主幹，觸發 CI/CD 部署。
2. **Render 路由設定 (SPA & Proxy)**:
   在 Render 儀表板 "Redirects/Rewrites" 設定兩條順序關鍵之規則：
   * **規則一 (API Proxy - 優先級高)**: `/api/*` -> `https://<ARCHON_SERVER_URL>/api/*`
   * **規則二 (SPA Fallback - 優先級低)**: `/*` -> `/index.html`

3. **SQL 遷移腳本規範**:
   - 所有 `.sql` 檔放於 `migration/` 下，按前綴數字順序命名 (如 `33_create_agent_checkpoints.sql`)。
   - 必須具備冪等性 (`IF NOT EXISTS` / `DROP ... IF EXISTS`)，並於末尾包含版本註冊：
     ```sql
     INSERT INTO schema_migrations (version) VALUES ('33_create_agent_checkpoints') ON CONFLICT (version) DO NOTHING;
     ```

---

## 第五章：常見問題排查 (Troubleshooting SOP)

### 5.1 資料庫與 Auth 排查

| 症狀 / 問題 | 根源解析 | 標準解決方案 |
| :--- | :--- | :--- |
| **`make db-init` 資料未寫入** | E2E 測試清空資料庫但未清 `schema_migrations` | 執行手動強重置或依據 `RESET_DB.sql` 後再跑 `make db-init` |
| **Auth 406 Not Acceptable** | `auth.users` 與 `public.profiles` 的 ID 未同步 | 執行 `make db-init` (自動發動 Dual Sync 雙重對齊) |
| **Dev Token 500 Error** | 密碼不匹配或模組匯入錯誤 | 確認開發預設密碼 `qwer45tyuiop` 及相對路徑引用 |

---

### 5.2 Hugging Face UnicodeEncodeError (注音輸入法陷阱)
- **症狀**: 部署 HF Spaces 日誌顯示 `UnicodeEncodeError: 'latin-1' codec... \u3112`。
- **根源**: 在 Mac 貼上 `HF_TOKEN` 時未關閉注音輸入法，帶入注音符號「ㄒ」(\u3112)。
- **解法**: 切換英數輸入法，重新貼上乾淨的 `HF_TOKEN` Secrets 並儲存。

---

## 附錄：系統維護與架構備忘

* **附錄 A：技術債自動化**: 由 `make phase-audit` 與 `make tech-debt-audit` 自動監控未歸檔 PRPs 與殭屍腳本。
* **附錄 B：系統演進概況**: 全面使用 `AgentService` + `MCPClient` 雙階段迴圈，後端 100% MyPy Zero Errors。
* **附錄 C：映像檔體積控制**: PyTorch 約束 `--extra-index-url .../whl/cpu`，控制 `archon-server` 體積在 ~5.0GB。
* **附錄 D：數位雙生模擬器**: 核心腳本包含 `twin_scout.py` (`make twin-record`) 與 `simulator_runner.py` (`make twin-simulator`)。
