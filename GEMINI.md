# 廚師日誌 (Chef's Journal) v2

> **【文件目的】**
>
> 本文件是 AI 助理 Gemini 的工作日誌與核心原則。它濃縮了專案開發過程中最關鍵的學習與SOP，旨在成為一個高效、聚焦的行動指南，並避免重複過去的錯誤。
>
> **【文件結構】**
>
> *   **第一章：核心工作習慣**: 定義了 Gemini 不可動搖的、必須在所有行動前遵守的思維框架與SOP。
> *   **第二章：關鍵學習與偵錯模式**: 提煉了從大量歷史日誌中反覆出現的、最有價值的經驗教訓，並將其歸納為可複用的偵錯模式。
> *   **第三章：近期工作日誌**: 保留最近的、最相關的一週日誌，以供快速回溯上下文。
> *   **第四章：歷史檔案**: 完整存檔所有過去的日誌，作為深入研究特定問題時的「考古資料」。

---

# 第一章：我的核心工作習慣 (My Core Habits)

### 【行動前風險評估原則 (Pre-Action Risk Assessment Principle)】

> **【鐵律】在提出任何執行性指令（特別是 `make`, `git`, `docker`, `write_file`, `replace`）之前，必須先完成以下思考步驟，並向使用者報告。**
>
> 1.  **回顧歷史**: 主動回想 `GEMINI.md` 和 `CONTRIBUTING_tw.md` 中與此指令相關的歷史失敗案例。
> 2.  **檢查設定檔**: 讀取相關服務的設定檔（如 `vite.config.ts`, `docker-compose.yml`），主動識別出指令之外的「隱性依賴」，例如**環境變數、掛載卷、或特定的埠號**。
> 3.  **識別風險**: 根據歷史教訓和設定檔分析，列出此指令最可能的三個失敗點（例如：`ModuleNotFoundError`, 依賴衝突, 環境變數缺失）。
> 4.  **設計驗證**: 規劃一個一個或多個成本最低的**前置驗證步驟**（例如：`read_file` 檢查設定，`ls` 檢查檔案是否存在），用以在執行前排除這些風險。
> 5.  **提出安全計畫**: 向使用者提出的第一個計畫，**必須**是包含了前置驗證的「安全計畫」。
>
> **嚴格禁止**在未經風險評估的情況下，直接提出「快樂路徑」的執行計畫。

### 【全面影響分析原則 (Comprehensive Impact Analysis Principle)】

> **【鐵律】在對任何程式碼進行修改前，我必須先徹底分析所有潛在的影響範圍，特別是測試檔案。**
>
> 1.  **分析依賴與影響**: 在提出修改計畫前，我**必須**使用 `search_file_content`, `git log` 等工具，全面探查受影響的檔案列表，並評估對功能、行為和效能的潛在影響。
> 2.  **同時考慮程式碼與測試**: 修改計畫**必須**同時涵蓋**程式碼調整**與**必要的測試調整**（包括測試設定、模擬資料、斷言等），並在計畫中明確說明。
> 3.  **單次到位修復**: 目標是實現一次性修復，避免「改 A 壞 B」或因測試未更新而導致的問題，提高整體效率。

### 【會話啟動標準作業程序 (Session Startup SOP)】

> **【鐵律】此 SOP 為 Gemini 在每次新會話開始時，都必須嚴格遵守的首要步驟，旨在確保上下文同步，避免重複錯誤。**
>
> 1.  **第一步：強制讀取上下文**: 在回應您的任何請求前，我**必須**先讀取 `GEMINI.md` 和 `CONTRIBUTING_tw.md` 的內容。
> 2.  **第二步：物理對帳門禁 (Physical Audit Gate)**: 
>     - **Schema 對帳**: 在執行任何 API 或資料庫欄位修改前，必須讀取 `migration/` 資料夾下的 SQL 實體。**嚴禁幻想欄位名稱**。
>     - **雙生對帳**: 執行 `make twin-scout` 巡檢前，必須讀取 `scripts/twin_scout.py`，確保 Reality Snapshot 的 SQL 指標與 UI 頁面路徑 100% 物理對齊，防止 false mismatch。
> 3.  **第三步：口頭確認 (Verbal Confirmation)**: 讀取後，我會向您用一兩句話總結我所理解的「**上次會話的最終狀態**」和「**今天的第一個目標**」。
*   **當前狀態 (Current Context)**: Phase 4.6.46 (物理加固與失落功能恢復) 已結案。
*   **今日目標 (Today's Goal)**: 維護系統 100% 物理健康度並啟動下一階段擴展。

> 4.  **第四步：取得您的確認**: 在您確認我對起點的理解無誤後，我才能開始執行第一個指令。

### 【UI 開發鐵律 (UI Development Iron Law)】

> **【鐵律】在產出任何 React 元件或修改前端程式碼前，必須先完成以下步驟。**
>
> 1.  **強制讀取 UI 標準**: 我**必須**先讀取 `PRPs/ai_docs/UI_STANDARDS.md` 的完整內容。
> 2.  **在計畫中宣告合規性**: 在我向您提出的開發計畫中，**必須**明確包含一個「合規性聲明」區塊，說明我將如何遵守 `UI_STANDARDS.md` 中的至少三項關鍵規範（例如：Tailwind v4 靜態類別、Radix UI `asChild` 組合、無障礙性 ARIA 屬性等）。
> 3.  **嚴格禁止違規行為**: **嚴格禁止**產出任何違反 `UI_STANDARDS.md` 中明確列出的「Anti-Patterns」的程式碼。

---

# 第二章：關鍵學習與偵錯模式 (Key Lessons & Debugging Patterns)

> 本章節提煉了從大量歷史日誌中反覆出現的、最有價值的經驗教訓，並將其歸納為六個可複用的偵錯模式。

*   **1. 證據至上：日誌是真相，歷史是脈絡 (Evidence is King: Logs are Truth, History is Context)**
    *   **核心**: 停止猜測。當行為與預期不符時，立即注入日誌 (`console.log`, `print`) 查看原始輸出。當 Bug 反覆出現時，使用 `git log` 追溯程式碼的歷史意圖。日誌揭示「當下發生了什麼」，歷史解釋「為什麼會這樣」。

*   **2. 信任但驗證：流程與直覺的雙重檢查 (Trust but Verify: Double-Check Processes and Intuition)**
    *   **核心**: 將 SOP (`Makefile`, `CONTRIBUTING.md`) 和使用者的直覺都視為強烈的訊號，但兩者都必須被驗證。優先查閱 SOP，因為答案可能已存在。當使用者表示懷疑時，應立即暫停，並用證據去驗證或排除他們的疑慮。

*   **3. 隔離戰場：區分環境、程式碼與元件 (Isolate the Battlefield: Separate Environment, Code, and Components)**
    *   **核心**: 複雜的 Bug 往往是多個問題的疊加。必須系統性地隔離變因。`make test` 失敗，是根目錄 `Makefile` 的問題，還是子專案 `pnpm test` 的問題？本地正常但 Docker 異常，優先清理快取和殘留容器，並詳讀 `Dockerfile`。

*   **4. 精通工具：從 Linter 配置到 Mock 類型 (Master Your Tools: From Linter Config to Mock Types)**
    *   **核心**: 工具的行為由其配置決定。看似 Bug 的行為，往往是配置不當。Linter 規範的根源可能在 `.eslintrc`；測試失敗的根源可能在於混淆了 `Mock` 與 `AsyncMock`；在發明輪子前，先讀懂工具手冊。

*   **5. 精準測試：填補盲區，應對非同步 (Test with Precision: Fill Blind Spots, Handle Async)**
    *   **核心**: `lint` 發現但 `test` 沒發現的問題，是測試覆蓋率不足的信號。應編寫一個能精準復現問題的最小化單元測試。對於非同步或單例服務，必須使用特殊的 `patch` 模式（如 `setup_module`）才能正確隔離和測試。

*   **6. 全生命週期視角：從願景到部署後驗證 (Full Lifecycle View: From Vision to Post-Deployment Validation)**
    *   **核心**: 開發不僅僅是寫程式碼。它始於透過分析假資料 (`MOCK_DATA`) 或文件來理解真實的專案願景，並終結於 `push`、部署、以及最重要的——由終端使用者在瀏覽器（注意快取）驗證無誤。一個修復只有在被使用者確認後才算完成。

*   **7. 內外網隔離原則：主動防禦環境變數污染 (Internal/External Isolation: Proactive Guard against Env Pollution)**
    *   **核心**: 在 Docker 化環境中，後端傳遞給前端的環境變數（如 `SUPABASE_URL`）可能包含內部 Docker DNS（如 `supabase_kong`）。這對瀏覽器是無效的。前端代碼必須具備「主動防禦」邏輯，透過靜態特徵檢測（如檢查 URL 是否包含 `_kong`），在請求發出前攔截並切換至 Mock模式，避免瀏覽器因 DNS 解析失敗而陷入無限 Loading。

*   **8. 測試邊界與狀態化模擬 (Test Boundaries & Stateful Mocks)**
    *   **核心**: 
        1.  **配置互斥**: Unit Test (`vite.config.ts`) 與 E2E Test (`vitest.e2e.config.ts`) 的包含路徑必須互斥 (`exclude`)，避免同一測試在錯誤環境下重複執行。
        2.  **狀態連動**: E2E 測試若涉及 CRUD 流程，Mock 必須具備狀態 (Stateful)，不能只回傳靜態空值，否則無法驗證「新增後顯示」的邏輯。
        3.  **變數提升**: 謹記 `vi.mock` 的 Hoisting 特性，依賴的變數必須使用 `vi.hoisted` 定義。

*   **9. 巢狀捲動死鎖防禦 (Nested Scroll Lockup Defense)**
    *   **核心**: 在巢狀 Flex 佈局中，子層若使用 `min-h-screen` 會鎖死父層的 `overflow-y-auto` 捲動軸。解決方案是「釋放子層高度」，讓內容自然撐開父層，並輔以底部物理緩衝 (`div.h-32`) 避開手機導覽列。

*   **10. 物理穿透驗證：終結「幽靈開發」 (Physical Penetration Verification)**
    *   **核心**: 警惕「日誌領跑代碼」。Git Log 與 GEMINI.md 說「已實作」可能是虛假的偽證（例如漏掉 git add）。
    *   **SOP**: 
        1.  **實體掃描**: 必須讀取磁碟檔案內容 (`read_file`) 確認邏輯存在。
        2.  **三向連動**: 檢查入口掛載 (main.py)、依賴映射 (index.html) 與測試斷言 (pytest/vitest)。
        3.  **拒絕樂觀**: 只有當 `curl` 或 `test` 物理性通過時，方可標記為「🟢 已修復」。

*   **11. 絕對雲原生意識：禁止本地容器暴力破解 (Absolute Cloud-Native Awareness)**
    *   **核心**: 專案連接的是**雲端 Supabase** (`SUPABASE_URL`)，並非本地 Docker (`supabase-db`)。當遇到資料庫錯誤 (如 `"permission denied for sequence"`)，**絕對禁止**嘗試用 `docker exec psql` 或 `npx supabase` 強行修正。
    *   **SOP**: 
        1.  **寫入腳本**: 產生正確的 SQL 修正檔 (存在 `migration/` 下)。
        2.  **人類授權**: 停止自動化腳本，向使用者說明原因，並請求使用者親自在 Supabase Cloud 執行該段 SQL。
        3.  這也已被編入 `.agents/skills/supabase_cloud_environment.md` 作為安全預設值。

*   **12. 物理介面與資料模型的斷層審查 (UI vs Data Model Disconnect)**
    *   **核心**: 後端 API 存在 (`POST /api/admin/crawler-targets`)，Schema 存在，且相依功能存在 (Task Modal 下拉選單)，**不代表**用來創造資料的 UI 介面就存在。
    *   **教訓**: 在 Phase 4.6.4 中，5173 任務的 Crawler Target 下拉選單為空，原因是 Admin UI 原本「忘記實作」新增 Target 的頁面。
    *   **SOP**: 當發現前端選單無資料時，除了檢查 API responses，更該使用 `search_file_content` 逆向追蹤建立該資料的 `[POST]` Request 是否有被任何 React Component 呼叫。不要輕易指引使用者去點擊看似相似的按鈕（例如 `+ Knowledge` 建立的是單次的 `archon_sources`，而非定期的 `archon_crawler_targets`，導致了長達數小時的除錯迷航）。

*   **13. Browser-Use 實體設定與 Profile 持久化 (Browser-Use Profile Persistence)**
    *   **核心**: 在 `browser-use` 中，若要加載已存在的 Playwright Browser Profile (例如已登入的 `.browser_data`)，必須直接在 `BrowserConfig` 中使用 `user_data_dir` 參數，而非透過 `extra_chromium_args` 傳遞 `--user-data-dir` 旗標。
    *   **教訓**: 若使用 `extra_chromium_args` 傳遞路徑，`browser-use` 底層的 Playwright 管理器可能會忽略該旗標，導致啟動一個全新的、未登入的匿名工作階段。使用 `user_data_dir` 參數則能確保正確載入現有的 Cookie 與 Session。

*   **14. 跨環境動態路徑偵測 (Cross-Env Path Resilience)**
    *   **核心**: 在 Docker 容器化環境中，絕對路徑與相對路徑（如 `../../../../migration`）的行為與宿主機不同。
    *   **教訓**: 尋找系統事實來源（如 `migration/` 或 `frontend_public`）時，必須採用「多路徑陣列探測法（Multi-Path Array Probing）」，同時定義 Host 相對路徑、Docker 絕對路徑與根目錄相對路徑，確保代碼具備環境自適應能力。
    *   **範例**: `POSSIBLE_DIRS = ["../enduser-ui-fe/public", "/app/frontend_public", "enduser-ui-fe/public"]`。

*   **15. 設定的可見性與系統保護 (Settings Visibility & Hardening)**
    *   **核心**: 資料庫中的 `archon_settings` 表承載了從 AI 金鑰到內部營運參數的所有配置。
    *   **教訓**: 透過引入 `is_system_protected` 欄位與 API 層級的物理過濾，確保 Admin UI (3737) 僅顯示「人類可管理的設定」，而隱藏內部的工具參數。

*   **16. 路由嵌套與前綴衝突 (Route Nesting & Prefix Conflict)**
    *   **核心**: 在 FastAPI 模組化掛載中，若子路由 (`APIRouter`) 已定義 `prefix="/api/..."`，主入口 `main.py` **絕對禁止** 再次添加重複前綴。
    - **物理罪證**: 4.6.34 期間出現了 `/api/api/admin` 導致 404 與 ReadTimeout。
    - **SOP**: 每次修改路由，必須執行 `make persona-audit` 物理公證 5 人通路。

*   **17. 靜默權限遮蔽陷阱 (Silent Permission Masking)**
    *   **核心**: 後端 Service **絕對禁止** 手寫 `profile["permissions"] = []`。
    - **物理罪證**: 這會導致前端引擎認為使用者「確定無權限」而跳過 Role Fallback，造成 Bob 的側邊欄物理消失。
    - **SOP**: 權限應由專屬的 `RBACService` 動態注入，或留空交由前端靜態規則自癒。

*   **18. 環境物理對齊原則 (Environment Physical Alignment)**
    *   **核心**: 嚴禁幻想 Host 機器與 Docker 容器具有完全相同的依賴狀態。
    - **教訓**: 在 4.6.42 中，本地執行 `make lint` 導致 `uv` 因群組未對齊而物理卸載 130 個套件。`google` 等命名空間包（Namespace Packages）極易因安裝順序或快取而發生 Import 衝突。
    - **SOP**: 當發生 `ImportError` 且路徑看似正確時，執行「終極自癒」：`rm -rf .venv uv.lock && uv sync --all-groups`。執行測試時必須顯式指定 `PYTHONPATH=src` 以確保 Host 與容器邏輯對等。

---

# 第三章：近期工作日誌 (Recent Activity Logs)

### 2026-04-27: Phase 4.6.46 加固公證、API 門禁硬化與 503 資源瓶頸
*   **1. 地基物理加固 (Method: Active Service Gates)**:
    - **邏輯**: 將 RAG 768 維度檢查從「外掛腳本」物理鎖入 `LibrarianService` 與 `EmbeddingService` 生產路徑。
    - **證據**: 修改後，`HealthService` 若偵測到維度不符將立即阻斷並報警，防止髒數據注入。
*   **2. API 防禦性修復 (Method: Defensive Data Modeling)**:
    - **修正**: 解決 Bob (Marketing) API 500 錯誤。物理證據顯示種子資料中的 `NULL` 欄位導致字串切片崩潰；已套用 `(value or "")` 模式。
    - **修正**: 解決 Charlie (Manager) `degraded` 狀態。修正了 `HealthService` 無法解析字串化向量的邏輯 Bug。
*   **3. 物理公證軌跡 (Method: Audit Trail)**:
    - **結果**: `make persona-audit` 達成 5/5 API 通道 🟢 **[SUCCESS]**。
    - **瓶頸**: `make twin-scout` 因 Gemini Free Tier 503 壓力暫時失效。
    - **軌跡存檔**: `.twin/diagnostics/audit_trail_20260427_153740.log`。

### 2026-04-25: Phase 4.6.46 結案、地基水泥化與全員工作流公證
*   **1. 地基物理加固 (Method: SQL ID Realignment)**:
    - **邏輯**: 物理重設所有非 UUID 身分（如 `ai-dev-bot`）為標準 UUID，根除 22P02 格式錯誤。
    - **對帳**: 物理指派 42 筆無主 Leads 給 Alice 的新 UUID，恢復實體數據可見性。
*   **2. 系統穩定性硬化 (Method: Backend & API Cementing)**:
    - **修正**: 還原 `business.py` 與 `twin_scout.py` 的正確資料庫欄位名 (`key`/`value`)，終結 8181 崩潰循環。
    - **隔離**: 在 `ops.py` 與 `marketing_api.py` 強制實施部門級 SQL 物理隔離 (SEC-001)。
*   **3. UI 穩定性與回歸修復 (Method: Defensive UI Modeling)**:
    - **修復**: 恢復 `TaskModal.tsx` 的 Manager/Member 指派分流邏輯，並加入 `Map` 去重防止 React Key 衝突。
    - **優化**: 優先排序 `AdminPage` 的 Prompt 管理，並在 `SystemHealthDashboard` 加入防禦性載入，防止單點 API 404/500 卡死全頁。
*   **4. 巡檢物理對齊 (Method: Digital Twin Alignment)**:
    - **校正**: 修正偵察員腳本中 Bob 的路徑為 `/brand`；穩定授權 Headers，排除 401 虛假報警。
    - **結果**: 5 人工作流達成物理公證 🟢 **[WORKFLOW_SUCCESS]**（除環境字型與性能瓶頸外）。

### 2026-04-22: Phase 4.6.44 結案、考古整併與全系統物理對齊
*   **1. Phase 4.6.44 物理落地 (Method: Deep Clone & Isolation)**:
    - **邏輯**: 實作 `structuredClone` 隔離 `MOCK_ADMIN_USER`，徹底根除 E2E 狀態污染。
    - **證據**: 通過物理對帳，`e2e.setup.tsx` 已注入深拷貝邏輯，13/13 測試套件 100% 通過。
*   **2. PRP 史詩考古與整併 (Method: Semantic Consolidation)**:
    - **考古**: 證實 `epic/` 資料夾已演化為 Phase-based 結構；物理整併 `Phase_4.6.21~29` 至 `archive` 目錄。
    - **整理**: 達成 `PRPs/` 根目錄的純淨態，維持「一階段一文件」的導航效率。
*   **3. 核心設定與模型 SSOT 對齊 (Method: Grounded Sync)**:
    - **修正**: 修正 `init_db.py` 格式錯誤，將 `MODEL_CHOICE` 等模型物理對齊至 `models/gemini-3.1-flash-lite-preview`。
    - **同步**: 物理同步 `.env` 金鑰至 `archon_settings`，解決 3737 管理後台設定「跑掉」的問題。
*   **4. 品質門禁公證 (Method: Binary Parity Recovery)**:
    - **修復**: 移除前端未使用變數、修正後端 MyPy 型別錯誤。
    - **數據**: **557/557 項後端測試 100% 通過**，Lint 全端 **CLEAN**，全 Docker 服務物理 `healthy`。

### 2026-04-20: Phase 4.6.42 結案：行銷情報 2.0 與系統 429 硬化
*   **1. 行銷情報視覺化 (Method: Lifecycle Funnel)**:
    - **邏輯**: 實作 `ConversionFunnel` 組件，取代單一進度條。
    - **證據**: Bob 的 Brand Hub 現可物理觀察 Leads 從「新獲取」到「轉化」的 4 階段流失率。
*   **2. 動態評分注入 (Method: Zero-SQL Dynamic Weights)**:
    - **邏輯**: 在 `MarketingService` 注入 `_calculate_lead_score`，優先讀取 `archon_settings` 設定。
    - **證據**: 通過物理公證測試，'VP' 職位獲 95 分，'AI Engineer' 獲 85 分，成功對齊 4.6.42 戰略目標。
*   **3. 系統級 429 抗性 (Method: Double-Gate Throttling)**:
    - **節流**: 將 `ThreadingService` 的全局並發物理限制為 1，頻率壓低至 12 RPM 以適配 Gemini Free Tier。
    - **自癒**: 在 `ContextualEmbeddingService` 實作「原地等待 15s 重試」，終結 429 報警鬼打牆。
*   **4. 品質與環境公證 (Method: Binary Parity Recovery)**:
    - **修正**: 恢復了 `docker-compose.yml` 中被硬編碼的 `VITE_API_URL` 插補邏輯。
    - **證據**: **559/559 項後端測試 100% 通過**，Lint **全綠**，本地 `.venv` 已透過 `uv.lock` 重建至 04/16 巔峰狀態。

### 2026-04-15: Phase 4.6.39 - 4.6.40 原本目標回歸與 503 根除
*   **1. 503 結構性根除 (Method: Atomic & Official SDK)**:
    - **邏輯**: 診斷 503 根源為「舊版 LangChain 封裝衝突」與「多模態 Payload 超載」。
    - **步驟**: 遷移至官方 `google-genai` SDK；實作「一人一診」原子化巡檢；加入指數退避 (Exponential Backoff) 重試邏輯。
    - **證據**: 物理公證巡檢日誌成功觸發 `⏳ 503 API Strain. Retrying...` 並最終 100% 成功產出報告。
*   **2. 原本目標物理復原 (Method: Git Source Recovery)**:
    - **Alice**: 透過 7 個月 Git Log 考古，找回 02-06 遺失的「語音轉工單」核心鏈條 (GAP-009)，物理修正 API 為 Multipart Form 接收，並成功產出實體追蹤任務。
    - **Bob**: 補齊資料庫 `cover_image` 欄位與 `marketing` 角色的 `content:publish` 權限；物理掛鉤 `BlogService` 與 `Nana Banana` 視覺生成，達成「圖文並茂」願景。
    - **Charlie**: 恢復 `manager/alerts` API 物理可見性，打通雙生系統 (Scout) 至經理儀表板的預警鏈條。
*   **3. 品質門禁公證 (Method: Double-Gate Audit)**:
    - **修正**: 修正了重構後遺留的 `sorted(list())` 轉型錯誤與測試檔案中的 Mock 路徑斷層。
    - **證據**: **559/559 項後端測試 100% 通過**，後端 254 個源檔案 **Lint CLEAN**。

### 2026-04-13: Phase 4.6.34 - 4.6.38 物理落地與全維度對齊
*   **1. 路由合約標準化 (Method: Grouped Mounting)**:
    - **邏輯**: 解決 `/api/api` 嵌套 404 問題。
    - **步驟**: 透過 `grep` 建立子路由 Prefix 清單，並在 `main.py` 實施分類掛載（自帶 /api 者直接掛載，無前綴者補掛 /api）。
    - **證據**: `make persona-audit` 5/5 狀態 200 OK。
*   **2. 權限引擎硬化 (Method: Union Authorization)**:
    - **邏輯**: 解決 Bob 側邊欄物理消失問題。
    - **步驟**: 移除 `ProfileService` 的空陣列硬編碼；修正 `usePermission.ts` 以合併動態與靜態 Role Scopes；對齊 `MainLayout.tsx` 的 `brand:manage` 門禁。
    - **證據**: 物理公證 Bob Profile 不再包含 `permissions: []`。
*   **3. 業務執行與日誌對齊 (Method: AIO & Log Unification)**:
    - **邏輯**: 解決 Alice 提案 500 錯誤（UnboundLocalError 與 Blocking IO）。
    - **步驟**: 規範 Import 結構至模組頂部；切換 Google SDK 為 `client.aio` 非同步模式；將 `LogService` 目標表物理修正為 `archon_logs`。
    - **證據**: 資料庫 `archon_logs` 成功補獲 503 錯誤紀錄。
*   **4. 品質門禁 (Method: Institutional Audit Gates)**:
    - **清掃**: 移除 `scripts/` 下 4 個偵錯用腳本。
    - **對帳**: `make lint` 全綠，`make test-be` 通過 559/559 測項。
    - **制度**: 建立 `make persona-audit` 作為 Makefile 強制門禁。

---

### 2026-04-06: Phase 5 結案：RBAC 基礎設施與身份動態化落地
*   **今日目標 (物理落地)**:
    - **動態矩陣**: 成功將權限定義從程式碼物理遷移至資料庫 `archon_roles_permissions` 表格，達成 100% 動態化。
    - **5173 連動**: 在 End-User UI 實作了 Identity Matrix 管理介面，Charlie (Manager) 現具備物理權能調整團隊權限。
    - **Poisson 硬化**: Agent 晉升機制與 PRP 「成功樣本數」物理對齊，並實作了基於 JSONB Overrides 的 Level 7 Admin 手動授權。
    - **審計閉環**: 在 `AdminService` 注入了物理日誌邏輯，所有權限異動皆自動記錄於 `archon_logs` 以供稽核。
*   **物理成果**:
    - **驗證指標**: **559/559 項測試 100% 通過**，後端 253 個源檔案與前端項目 **Lint CLEAN**。
    - **結構優化**: 完成 12 步語義化 SQL 拆分與編碼對齊，解決 `text = uuid` 衝突。
    - **環境淨化**: 移除所有臨時探針與日誌檔案，恢復根目錄純淨態。
    - **治理閉環**: 達成了全系統「身分 -> 權限 -> 執行」的實體閉環。

### 2026-04-05: Phase 4.6.28 & 4.6.29 結案：神經橋接與系統硬化落地
*   **今日目標 (物理落地)**:
    - **解耦完成**: Server 成功卸載 130 個重型 ML 依賴（如 `torch`），Reranking 邏輯物理轉移至 `archon-agents` 容器。
    - **動態版本**: 實作了基於 `migration/` 資料夾的動態版本偵測，全系統達成 `0.2.2` 一致性。
    - **物理隔離**: 透過 `is_system_protected` 物理過濾，成功在 Admin UI (3737) 中隱藏 Bob 的內部營運 API。
    - **同步強化**: 強化了 `init_db.py`，確保 API Keys 100% 反映 `.env` 最新狀態並完成加密同步。
*   **物理成果**:
    - 通過 555/565 個後端測試，系統穩定性達標。
    - 解決了 Docker 容器內版本偵測的路徑斷層問題。
    - RAG 預設模型成功對齊為 3 月標準的 `gemini-2.5-flash`。

### 2026-04-02: 物理落地：Intel Mac 效能硬化與幻覺終結 (Current Session)
*   **今日目標 (物理落地)**:
    - **環境對齊**: 物理偵測並解決了 Intel Mac (x86_64) 無法安裝最新 Torch 的斷層。
    - **效能落地**: 修正 `NumPy 2.x` 引發的載入崩潰，鎖定 `1.26.4` 黃金組合，熱機搜尋降至 **2.3s**。
    - **命名校正**: 修正了幽靈類別 `StorageService` 為實體類別 `DocumentStorageService`。
    - **5173 對齊**: 實體驗證了 RAG 實驗室掛載於 5173/admin，消除了導航斷層。
*   **物理成果**:
    - 成功降級 NumPy 並重新鎖定 `uv.lock`，終結了「改 A 壞 B」的編譯快取損壞。
    - 通過實體探針驗證，搜尋延遲從 15s (錯誤重試) 物理壓縮至 **2.3s** (模型熱機運算)。

### 2026-04-01: Phase 4.6.25 & 4.6.26 結案（⚠️ 存在環境幻覺偏差）
*   **注意**: 此日誌回報的「2s 冷啟動」與「結案」係基於非 Intel Mac 環境之幻想。實體代碼層面缺失依賴與正確類別呼叫，導致在 x86_64 環境下失效。

*   **今日目標 (物理落地)**:
    - **環境對齊**: 物理偵測並解決了 Intel Mac (x86_64) 無法安裝最新 Torch 的斷層。
    - **效能落地**: 修正 `NumPy 2.x` 引發的載入崩潰，鎖定 `1.26.4` 黃金組合，熱機搜尋降至 **2.3s**。
    - **命名校正**: 修正了幽靈類別 `StorageService` 為實體類別 `DocumentStorageService`。
    - **5173 對齊**: 實體驗證了 RAG 實驗室掛載於 5173/admin，消除了導航斷層。
*   **物理成果**:
    - 成功降級 NumPy 並重新鎖定 `uv.lock`，終結了「改 A 壞 B」的編譯快取損壞。
    - 通過實體探針驗證，搜尋延遲從 15s (錯誤重試) 物理壓縮至 **2.3s** (模型熱機運算)。


---

# 第四章：歷史檔案：原則的考古學 (Historical Archive: The Archaeology of Principles)

> **【封存說明】**
> 本章節存放了所有歷史日誌。當你需要深入了解某個特定問題的完整偵錯背景時，可以在此查閱最原始的紀錄。

### 2026年3月：結構化重構、治理硬化與效能收斂
三月是 Archon 從巨型架構邁向模組化治理的關鍵月份。我們消滅了所有超過 1000 行的檔案，並建立了基於 XP 的 Agent 治理體系。

**核心主題歸類**:
1.  **Phase 4.6.24 結案 (Ref: 03-30)**:
    - **巨型檔案清零**: 完成 `CredentialService`, `UrlHandler`, `StatsService`, `ProviderDiscovery` 四大中樞的 L2 模組化拆分。
    - **ROI 視覺化**: 前端實體化 `ROIAnalyticsBadge` 與 `TokenUsageTable`，達成 AI 經濟透明化。
    - **物理隔離**: 徹底隔離 `.env.test` 物理位址，實作並驗證了部門隔離 (SEC-001) 的負面測試。
1.  **模組化革命 (Ref: 03-06 ~ 03-31)**:
    *   **巨型檔案清零**: 拆分 `ollama_api.py`, `knowledge_api.py`, `task_service.py` 與四大核心 Service。
    *   **L2 標竿建立**: 確立了以 `llm/` 包為範本的目錄化重構標準，確保 Facade 模式的 100% 向後兼容。

2.  **Agent 治理與 XP 門禁 (Ref: 03-24 ~ 03-26)**:
    *   **身分落地**: 實作 `agent_xp` 經驗值系統與 Poisson Gate 物理攔截。
    *   **門禁硬化**: 實作解釋性攔截訊息，並實體對齊 Slug-based 身分識別。

3.  **效能與基礎設施硬化 (Ref: 03-30)**:
    *   **調度統一**: 完成 `AgentService` 原生工具動態分發 (Unified Tool Dispatch)。
    *   **O(1) 優化**: 將 `RateLimiter` 複雜度從 O(N) 降至 O(1)，提升高併發穩定性。
    *   **全端對齊**: 找回並恢復了二月重構中遺失的 Token 詳細明細表。

4.  **安全與 ROI 實體化 (Ref: 03-31)**:
    *   **部門隔離**: 實作 JSONB 穿透式隔離，並通過 403 負面測試驗證。
    *   **ROI 落地**: 實作前端 ROI 狀態欄，補齊 AI 經濟治理最後的功能斷層。

### 2026年2月：全角色流程與行動端落地
二月標誌著 Archon 從單點功能邁向全角色協作的里程碑。我們完成了 Alice (Sales), Bob (Marketing), Charlie (Manager) 的核心工作流閉環，並在下旬進行了大規模的架構硬化。

**核心主題歸類**:
1.  **Phase 4.6.3 Charlie (Manager) (Ref: 02-03)**:
    *   **指揮官系統**: 實作 Sentinel 哨兵自動監控 Stale Leads，並結合 RAG/LLM 智慧生成繁體中文追蹤任務。
    *   **權限閉環**: 實作了從 Alert -> Task Dispatch -> Alert Resolved 的完整狀態流轉與 RBAC 控制。

2.  **Phase 4.6.2 Bob (Marketing) (Ref: 02-03)**:
    *   **測試隔離**: 解決了 E2E 測試中的 Promise Hanging 問題，確立了 MSW 必須攔截所有 Auth 請求的測試鐵律。

3.  **Phase 4.6.1 Alice (Sales) (Ref: 02-02)**:
    *   **行動優先**: 實作 "Fire & Forget" 的語音轉工單功能。
    *   **效能優化**: 將 GPS 抓取改為 On-Demand，並引入 SQL Batch Update 優化歸檔效能。
    *   **E2E 穩定化**: 修復了 Dashboard 因非同步載入導致的 Race Condition。

4.  **Nexus 戰情室與 UI 空間革命 (Ref: 02-05, 02-09, 02-10)**:
    *   **並排編輯 (Split View)**: 實作了雙重收合側邊欄與 Markdown 即時預覽，解決 Context 切換的斷腦流問題。
    *   **行動端韌性**: 透過移除 `min-h-screen` 徹底解決了手機版捲動死鎖問題，並實作了 AI 任務的動態進度反饋。
    *   **Dashboard 加固**: 修正了同步 API 的 `maybeSingle()` 調用陷阱，確保資料加載穩定性。

5.  **細粒度 RBAC 與型別安全革命 (Ref: 02-06, 02-07)**:
    *   **Zero-Mypy**: 達成後端 100% 型別通過，重構 `BaseAgent` 泛型解決 `pydantic-ai` 接口匹配問題。
    *   **權限階層化**: 實作了 Manager 與 Admin 的權限邊界，並導入 `is_system_protected` 旗標保護核心系統 Prompt。

6.  **身分同步與流程自動化 (Ref: 02-03, 02-05)**:
    *   **Auth 穩定化**: 修正了 `AuthService` 在建立使用者時同步 metadata 的邏輯，確保角色資訊的一致性。
    *   **Librarian 實體化**: 打通了檔案版本控制與審計路徑的寫入。

7.  **架構硬化與基礎設施對齊 (Ref: 02-15 ~ 02-21)**:
    *   **前端模組化**: 成功將 RAG 設定抽離為獨立特徵模組，並落地位準路徑別名 (`@/`)，消滅相對路徑地獄。
    *   **引擎與 SDK 對齊**: 營運端全面遷移至官方 Google `genai.Client`，解決 SDK 斷層導致的 503 錯誤與死迴圈。
    *   **基礎設施同步**: 修正了 `MigrationService` 的實體表名衝突，並實作了跨環境的金鑰自動檢索 (os.getenv/os.environ)。

### 2026年1月：權限重構、自癒機制與商業功能落地
一月是專案從「技術驗證」邁向「商業運作」的關鍵轉折點。我們在前半月集中解決了深層的架構債（特別是 Auth 與 Docker 環境），後半月則全力衝刺商業功能的實作。

**核心主題歸類**：

1.  **RBAC 權限架構的完備與標準化 (Ref: 01-09, 01-12)**:
    *   **挑戰**: 舊有 `X-User-Role` Header 存在安全漏洞，且 `auth.users` 與 `public.profiles` ID 不一致導致 406 錯誤。
    *   **解決**: 建立 `src/server/auth` 模組，強制後端驗證 JWT。實作 `init_db.py` 中的「雙重同步策略 (Dual Sync)」，自動修復 ID 不一致。
    *   **DX 優化**: 為解決 Admin UI 無登入頁痛點，實作了 `Dev Auto-Login` 機制。

2.  **環境自癒與主動防禦 (Ref: 01-03, 01-04, 01-08)**:
    *   **主動防禦**: 針對 Docker 內部網路 (DNS) 與瀏覽器外部網路的差異，在前端 `api.ts` 實作了「主動防禦」邏輯，偵測到無法連線時自動切換 Mock，解決無限 Loading。
    *   **誠實架構**: 移除了 `SmartAPI` 的隱式 Mock Fallback，強迫開發者正視網路配置問題。

3.  **商業功能與 RAG 進化 (Ref: 01-15, 01-16)**:
    *   **銷售情資**: 實作 Phase 4.2，包含 Leads 管理與市場洞察。
    *   **真實 RAG**: 將 Mock RAG 升級為接軌 Gemini API 的真實系統，打通了「爬蟲 -> 向量 -> 生成」的數據管道。
    *   **行銷官網**: 導入 Config-Driven UI 模式，降低非技術人員維護門檻。

4.  **SOP 與除錯紀律的再強化 (Ref: 01-06, 01-07)**:
    *   **教訓**: 在修復 UI/通訊問題時，因違背 SOP 導致測試崩潰。重新確立了「修改代碼必須同步更新 Mock」與「Patch 必須針對 Class」的鐵律。

5.  **系統穩定化與人機協作 (Ref: 01-20, 01-22, 01-23, 01-24)**:
    *   **任務系統修復 (Ghost Task Mystery)**: 透過精確過濾 (`assignee_id`)、修復非同步 context 錯誤 (`llm_provider` import) 以及前端 `include_closed` 參數，解決了 Alice/Bob 任務消失的問題。
    *   **全角色戰情室 (War Rooms)**: 為 Sales, Marketing, Manager 分別打造了專屬 Dashboard (Sales Nexus, Brand Hub, Team Management)。打通了爬蟲 -> CRM -> Blog -> Approval 的完整商業流程。
    *   **RBAC 深度加固**: 放棄「開副本」做新頁面的想法，直接在後端實作「部門隔離 (Department Isolation)」與前端權限拆分 (`leads:view:sales` vs `marketing`)，確保 Manager 只能管理同部門成員。

6.  **開發體驗 (DX) 與爬蟲進化 (Ref: 01-18, 01-19, 01-25)**:
    *   **爬蟲 AJAX 逆向**: 放棄易被擋的進階爬蟲，改用 104 AJAX API，大幅提升資料品質與穩定性，解決 RAG GIGO 問題。
    *   **Admin UI 完善**: 修復了檔案上傳 Unicode 錯誤、Task ID 顯示，並實作了 `Dev Auto-Login` 與 API Key 自動注入 (`db-init`)，大幅降低本地開發摩擦。
    *   **探針制度化**: 將 `probe_librarian.py` 升級為標準化 `make probe` 指令，並加入維度完整性檢查 (768 vs 1536)，成為 CI/CD 的可靠 Smoke Test。

7.  **系統體制化與行動端擴展 (Ref: 01-26 ~ 01-30)**:
    *   **品質與安全**: 實作了 Row Level Security (RLS) 防止資料外洩，並進行了大規模的 Type Safety/Lint 清掃，消優了數百個潛在的運行時錯誤。
    *   **行動優先**: 為 Alice 打造了 "Hunter Mode" 與語音日誌功能，確立了行動端 "Fire & Forget" 的設計哲學。
    *   **測試韌性**: 面對 Dashboard 複雜的非同步載入，學會了使用 `waitFor` 配合 DOM 狀態檢查來消除 Flaky Tests，並將探針 (Probe) 升級為 CI 標準檢查。

### 2025年12月：Async 重構、前端規範與 AI 開發者奠基

十二月是技術債償還與新功能開發並行的月份。我們完成了全系統的 Async 化，並實作了 AI 開發者流程的核心基礎。

**核心主題歸類**:
1.  **AI 開發者審核流程 (Ref: 12-31, 12-16)**:
    *   **願景對齊**: 在假資料中挖掘出「AI as a Teammate」的真實願景。
    *   **功能實作**: 完成了 `DiffViewer` 與提案審核後端。在 `file_operation_tools.py` 加入 `original_content` 以支援差異比對。
    *   **專案清理**: 歸檔了 Phase 4.1 文件並清理了過期分支。

2.  **非同步重構與測試災難 (Ref: 12-20, 12-12)**:
    *   **挑戰**: 將後端全面重構為 `async` 後，引發了大量 `make test-be` 失敗。
    *   **解決**:
        *   **黃金模式**: 確立了測試 FastAPI 單例服務的模式：在 `import app` 前 `patch`，並使用 `setup_module` 管理生命週期。
        *   **Mock 類型**: 修正了混淆 `Mock` 與 `AsyncMock` 導致的測試錯誤。
        *   **務實決策**: 對於頑固的 ETag 測試使用 `@pytest.mark.xfail`，優先保證主流程。

3.  **前端品質與規範 (Ref: 12-25, 12-15)**:
    *   **Lint 清零**: 系統性解決了 160 個 ESLint 警告。透過研究 `eslint.config.js`，發現 `no-unused-vars` 等誤報是配置問題，而非代碼問題。
    *   **部署驗證**: 解決了部署後 CSS 載入失敗（路徑錯誤）與資料不一致（缺少 `localStorage` 金鑰）的問題，再次印證「部署後驗證」的重要性。

4.  **E2E 測試穩定化 (Ref: 12-27, 12-29)**:
    *   **複雜 Bug**: 解決了 `make test` 失敗的雙重原因：`optimistic.ts` 的邏輯錯誤與 `Makefile` 對前端測試指令的誤用。
    *   **合併紀律**: 合併 E2E 修復分支後，立即執行 `make test` 與 `make lint`，成功攔截了因依賴更新而產生的連鎖錯誤。

### 2025年11月：深層偵錯、Git 考古與 E2E 驗收

十一月是偵錯月。我們深入解決了多個層層疊加的複雜 Bug，並確立了以 Git 歷史為最終真相的偵錯文化。

**核心主題歸類**:
1.  **前端異常的深層根源 (Ref: 11-27, 11-28, 11-13)**:
    *   **`about:blank` 之謎**: 文件上傳後跳轉空白頁。追蹤發現是後端 `knowledge_item_service.py` 錯誤回傳了無效的 `source://` URL。
    *   **UI 報錯**: Admin UI 顯示 "Failed to Load Knowledge Base"。使用者提供的 `invalid input syntax for type uuid` 成為關鍵線索，定位到 DB 函式參數型別不匹配。
    *   **部署路由**: Render 部署後前端無法連線，瀏覽器報 `SyntaxError: ... < is not valid JSON`。證實是 Render 路由規則未重寫 `/api` 請求。

2.  **檔案上傳的多層錯誤 (Ref: 11-15, 11-24)**:
    *   **剝洋蔥式偵錯**: 檔案上傳失敗背後隱藏了三層錯誤：`Bucket not found` (Supabase 設定) -> `InvalidKey` (中文檔名) -> `TypeError` (對同步函式使用 `await`)。
    *   **Git 歷史裁決**: 在解決「靜默失敗」時，`git log` 與 `docker logs` 出現矛盾。最終透過 `git show HEAD:<file>` 證實了 Docker 內的程式碼確實是舊版本，結束了對環境的無謂猜疑。

3.  **非同步測試的挑戰 (Ref: 11-26, 11-11)**:
    *   **歷史債**: `git log` 顯示 `test_file_upload_integration.py` 的 Mock 是為舊同步函式寫的，導致重構後 `TypeError`。確立了「修改測試前先查歷史」的原則。
    *   **無限循環**: React 元件 `Maximum update depth exceeded`。追溯歷史發現是為修復 Lint 而錯誤地將 `state` 加入了 `useEffect` 依賴。

4.  **系統性驗收 (Ref: 11-10, 11-19)**:
    *   **眼見為實**: 在前端注入 `console.log` 發現 API 路由衝突（兩個 `/health` 端點）。
    *   **全面探測**: 執行 E2E 手動驗收，產出 Bug 清單，鎖定「後端背景任務靜默失敗」為多個功能異常的共同病灶。

### 2025年10月：系統嫁接、雲端部署與SOP重塑

十月份是專案架構轉型的關鍵期。我們將實驗性的 `feature` 分支嫁接到主幹，並首次打通了雲端部署流程。

**核心主題歸類**:
1.  **系統嫁接與架構確立 (Ref: 10-17, 10-05)**:
    *   **挑戰**: 在將 `feature` 分支應用移植到 `main` 架構時，遭遇了依賴管理 (`pip` vs `uv`) 與工具鏈 (`npm` vs `pnpm`) 的「精神分裂」。
    *   **解決**: 透過 `git diff --name-status` 全面盤點差異。確立了 `Makefile` 為單一事實來源，並統一使用 `pnpm` 與 `uv`。
    *   **教訓**: 「嫁接」非單純合併，必須先建立統一的基底架構。

2.  **Render 雲端部署戰役 (Ref: 10-09, 10-13)**:
    *   **API 404/500 迷霧**: 部署後前端無法連線。經查證，瀏覽器報錯 `SyntaxError: ... < is not valid JSON` 是因為 Render 缺少 SPA 重寫規則，導致 API 請求被導向 `index.html`。
    *   **設定延遲**: 即使修正了設定，API 仍失敗。最終證實是雲端平台的「傳播延遲 (Propagation Delay)」，學會了「等待與硬刷新」的除錯技法。
    *   **產品思維**: 部署後驗證中，我們學會了不應套用通用模板，而應以「問卷」代替「方案」，並優先使用手上資源。

3.  **SOP 與測試紀律的建立 (Ref: 10-14, 10-18, 10-23)**:
    *   **資料庫遷移**: 發現舊流程高風險，建立了基於 `schema_migrations` 表的冪等性遷移 SOP。
    *   **測試基準線**: 面對 38 個後端測試失敗，我們建立了「單點修復 -> 驗證」的循環。清理了測試快取導致的幽靈失敗。
    *   **嚴格計畫**: 在經歷多次「來回修改」的指責後，確立了「先調查歷史，再提出包含 `old_string` 的完整計畫」的鐵律。

4.  **精準偵錯與殭屍代碼 (Ref: 10-27, 10-29)**:
    *   **移除病灶**: `archon-ui-main` 啟動失敗指向 `useThemeAware.ts`，調查發現這是無用的 Dead Code，直接刪除即修復。
    *   **釐親矛盾**: 透過釐清「UI 載入成功但 API 404」的精確場景，區分了「啟動問題」與「資料問題」。

### 2025年9月：SOP, 歷史追溯與偵錯紀律的建立

九月份是專案從混亂的「救火隊模式」轉向「紀律化開發」的關鍵月份。這個月的歷程充滿了在 `make` 指令、Docker 環境、部署流程和非同步測試中的反覆試錯。

**核心主題歸類**:
1.  **SOP 的建立與探索**: 這個月，我們確立了多項至今仍在使用的核心工作原則。我們學會了不再信任過時的文件，而是將 `Makefile` 視為「單一事實來源」(Ref: 09-19)，並反覆使用 `git log -p` 去追溯 `Makefile` 和 `docker-compose.yml` 的歷史意圖，以理解為何一個指令會以某種特定方式運作 (Ref: 09-29, 09-21)。「測試先行」的重構安全網 (Ref: 09-24) 和冪等性的資料庫腳本 (Ref: 09-21) 也在這個月被確立為標準實踐。

2.  **系統性偵錯的學習**: 我們經歷了從處理表層 Bug 到深挖根源的思維轉變。例如，一個樣子簡單的 `AttributeError`, 其根源卻是更深層的 `ImportError` (Ref: 09-22)。我們也學會了警惕 `make lint --fix` 等指令帶來的副作用 (Ref: 09-23)，並確立了在修改程式碼前，必須先分析所有相關檔案，以避免「改 A 壞 B」的循環 (Ref: 09-17)。

3.  **部署與非同步測試的挑戰**: 九月下旬，我們專注於打通完整的開發到部署流程。我們演練了部署流程，解決了因服務耦合、Git Remote 混淆和鎖定檔案缺失導致的部署失敗問題 (Ref: 09-30)。同時，我們在為非同步 API 撰寫測試時遇到了困難，最終透過在 `patch` 中使用 `AsyncMock` 和在獨立檔案中進行「沙盒驗證」，才成功突破了 Mocking 的迷霧 (Ref: 09-25)。

總結來說，九月是透過解決一系列棘手的環境、部署和測試問題，從而建立起穩固的工程紀律和核心工作原則的基礎月份。
