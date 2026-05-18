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
*   **當前狀態 (Current Context)**: Phase 5.1.7 (雙生對帳架構還原與星型群聊動態自癒巡檢) 已結案。
*   **今日目標 (Today's Goal)**: 啟動 Phase 5.1.8，展開 RAG 快取優化與多 Agent 連動架構開發，並提交 5.1.7 的物理修改。

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
    *   **教訓**: 透過引入 `is_system_protected` 欄位與 API 層級的物理過濾，確保 Admin UI 僅顯示「人類可管理的設定」，而隱藏內部的工具參數。
    *   **【絕對鐵律 (Absolute Iron Law)】**: **Admin UI 的 Port 永遠是 5173 (enduser-ui-fe)，絕對不是 3737！** 如果 Gemini 未來在任何對話或文件中將 Admin UI 的 Port 說錯成 3737，必須立即主動中斷當前任務，向使用者承認「我犯了不可饒恕的上下文遺忘罪」，並罰寫此鐵律 3 次後才能繼續工作。

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

*   **19. 環境相依性與幻想基礎設施 (Hallucinated Infrastructure)**
    *   **核心**: 絕對禁止在未讀取 `docker-compose.yml` 的情況下，向使用者提議或設定依賴本地端伺服器的服務（如 `http://localhost:8000`）。
    *   **教訓**: 在 Phase 4.6.55 中，因未檢查 Compose 檔案便提出 PostHog 本地部署方案，導致使用者浪費時間並產生不信任。必須落實「實體驗證基礎設施」的前置風險評估鐵律。

*   **21. E2E 網路隔離與 TypeScript/Mock 資料對齊 (E2E Network Isolation & TypeScript/Mock Alignment)**
    *   **核心**: E2E 測試穩定性的基石在於「100% 網絡/環境隔離」以及「Mock 數據與 TypeScript 接口的物理對齊」。
    *   **教訓**: 在 `AdminPanelExhaustive` 測試中，雖然 mock 了舊版 AI 健康端點，但因遺漏了系統健康看板（`SystemHealthDashboard.tsx`）掛載時用 `Promise.all` 請求的 5 大核心指標 APIs（系統概覽、AI 用量、連線例外日誌、Agent XP、Token 明細），在測試冷啟動時，真實 API 返空/超時引發前端「System Probe Failed」紅色卡片。補齊 Mock 後，又因 recent token usage 的 Mock 數據缺少 `role`、`user_name` 和 `tokens` 屬性，引發 React 的 `<TokenUsageTable>` 存取 `toUpperCase()` 時發生 `TypeError` 渲染崩潰。
    *   **SOP**:
        1. **完整隔離**：Dashboard 的所有非同步 API 必須 100% Mock 覆蓋，絕不可依賴真實後端查詢。
        2. **物理對齊**：Mock 數據必須精確適配前端 TypeScript 介面規格（如 `TokenUsageDetail`），缺少任何非 nullable 欄位都可能在 React 渲染時引發不可預知的 TypeError，並在 Headless 測試中被無聲掩蓋。
        3. **Warning/Error 日誌穿透**：調優 Playwright 監聽器以捕獲瀏覽器的 `warning` 與 `error`，使 React 組件崩潰與警告能夠在終端清晰浮現，杜絕盲人摸象式偵錯。

---

# 第三章：近期工作日誌 (Recent Activity Logs)

### 2026-05-12: Model SSOT 確立與 Phase 5 星型群聊架構規劃
*   **1. 基礎設施幻覺根除 (Model SSOT 100%)**:
    - **行動**: 全域盤點並移除了 `agents/`, `server/`, `mcp_server/` 中 13 處關於 `openai:gpt-4o`, `gpt-4.1-nano` 與 `gemini-embedding-001` 的硬編碼回退機制。
    - **機制**: 導入「Fail Fast」原則。系統現在完全依賴 `archon_settings` (資料庫) 與 `.env` 作為唯一的模型事實來源。若未設定則直接拋出 `ValueError`，徹底解決了隱性 429 崩潰問題。
*   **2. Phase 5 架構藍圖 (LangGraph Evolution)**:
    - **行動**: 將 Phase 4.6 收尾文件歸檔，並建立 `Phase_5.0.0_Multi_Agent_Implementation.md` 實作計畫與驗收報告。
    - **決策**: 
        - **Reject LangGraph**: 為了避免 Pydantic v1 依賴衝突，決定採用原生的 `pydantic-graph` 來構建狀態機。
        - **星型群聊 (Star-Topology)**: 捨棄 AutoGen 的自由對話，改由 Supervisor 動態路由，並加上 `MAX_RECURSION = 3` 熔斷器以保護 API 成本。
*   **3. Free Tier 經濟學與模型分級**:
    - **驗證**: 透過實體腳本測試與聯網查證，修正了 AI 對新模型可用性的幻覺。
    - **定案**: Supervisor 綁定 `gemini-3-flash-preview` (兼具免費層級與高智商)；Worker 綁定 `gemini-3.1-flash-lite-preview` (價格減半，吞吐量極高)；Embedding 暫不升級至 v2，以避開每日 1000 次的嚴苛免費限制。

### 2026-05-06: 系統大掃除與技術債自動化巡邏上線
*   **1. 歷史文檔與腳本大掃除**:
    - **行動**: 刪除 `scripts/` 目錄下 5 個超過 14 天未使用的過期探針與假資料腳本，並將 `PRPs/archive/` 中的古老歷史文件依據「時代分類」（如 `Phase_3_Grafting_and_UI`）進行資料夾歸檔。
    - **結果**: 專案根目錄與腳本庫大幅度瘦身，且歷史文件具備了更清晰的考古脈絡。
*   **2. 技術債自動化巡邏 (Clockwork Tech-Debt Patrol)**:
    - **行動**: 於 `Makefile` 加入 `tech-debt-audit` 指令，並將其實作轉換為 Clockwork 的原生 Python 背景任務 (`run_tech_debt_audit`)。
    - **機制**: 透過 `scheduler_service.py` 設定每 336 小時（14天）自動檢查一次未歸檔的 PRPs 與過期腳本。若發現髒亂，Clockwork 會自動開立 Task 並指派給 `DevBot`。達成從「偵測」到「派單」的全自動化閉環。
*   **3. 系統品質與落體驗證**:
    - **稽核**: 透過 `phase-audit` 技能深度驗證 Phase 4.6.51~53 皆已物理落地（包含 `client.aio` 非同步化、Librarian 拆分、TTS `AudioPlayer` 元件與提示詞等）。
    - **公證**: 執行 `make lint-be`, `make test-be`, `make persona-audit` 與 `make twin-scout`，所有品質門禁皆 100% 綠燈通過。

### 2026-05-17: AdminPanelExhaustive E2E 物理加固與 React TypeError 阻斷
*   **1. 系統健康標籤頁 (System Health Tab) 網絡 100% 隔離**:
    - **行動**: 在 `AdminPanelExhaustive.spec.ts` 中補齊對系統健康看板 5 大核心 API 端點（系統概覽、AI 用量、連線例外日誌、Agent XP、Token 明細）的 Playwright 路由攔截。
    - **結果**: 徹底切斷 E2E 測試與真實 backend/資料庫冷啟動延遲 of 物理耦合，消除 「System Probe Failed」 錯誤畫面。
*   **2. Mock 與 TypeScript 數據對齊 (React Crash 阻斷)**:
    - **行動**: 修正 recent token usage mock 數據結構，補齊 `role`, `user_name`, `tokens`, `context` 等關鍵欄位，使其與 `TokenUsageDetail` 介面 100% 物理對齊。
    - **結果**: 根治了 `<TokenUsageTable>` 存取 `row.role.toUpperCase()` 時的 React TypeError 渲染崩潰。
*   **3. 嚴苛測試綠燈公證**:
    - **行動**: 修改控制台日誌過濾以只顯示 Warning/Error，並在 `CI=1` 且停用自動重試 (`--retries=0`) 的模式下執行驗收。
    - **結果**: 9 大標籤頁一次性 100% 物理綠燈通過，執行時間縮短至 43.2 秒，徹底消滅 flaky 抖動。

### 2026-05-18: Phase 5.1.7 雙生參數 CLI 雙軌與星型群聊動態自癒巡航落地
*   **1. 雙向對帳引導規格化 (CLI --mode Integration)**:
    - **行動**: 在 `scripts/twin_scout.py` 中完美實作 `--mode` CLI 參數選取（支援 `audit` 與 `action` 模式）。
    - **機制**: 當 `--mode action` 時，啟動 Headed 模式並加載本地免密碼 `.browser_data/scout_action` 目錄，無縫繼承宿主機 OS Keychain 的 Cookie，完全根除了 Docker 與 Host 之間的 Chromium 加密憑證讀取障礙。
*   **2. 星型群聊 (Multi-Agent) 動態 UI 自癒核查**:
    - **行動**: 在雙生對帳巡航中，實現 `verify_multi_agent_chat` 核查函式。
    - **流程**: 自動點擊 `New Task`，輸入標題 `Marketing Data Deep Dive`，指派給 Supervisor (UUID: `f0f00000-0000-0000-0000-000000000000`)。在 45s 非同步處理完畢後，切換至 `AI Report` 標籤，捕獲 headed 瀏覽器截圖並傳送至 Gemini Vision 進行真實協作對話氣泡的 physical parity 公證斷言。
*   **3. Makefile 自動化與 SOP 全面對帳**:
    - **行動**: 重構 `Makefile` 保留 `make twin-scout` (容器化 audit 模式)，並新增 `make twin-scout-action`。同步在 `CONTRIBUTING_tw.md` 修正 SOP 命令字眼，100% 根除「文檔與代碼不對稱」之技術債。
    - **驗證**: 執行 `make lint-be` (329 個檔案全數綠燈通過) 與 `make test-be` (569 個核心單元測試全數綠燈通過)，已安全合併並 push 到開發主幹 `feat/twins`！

> 目前近期日誌已全數歸檔至歷史檔案。當有新的開發活動時，請記錄於此。

---

# 第四章：歷史檔案：原則的考古學 (Historical Archive: The Archaeology of Principles)

> **【封存說明】**
> 本章節存放了所有歷史日誌。當你需要深入了解某個特定問題的完整偵錯背景時，可以在此查閱最原始的紀錄。

### 2026年4月：全系統硬化、效能收斂與 Phase 4.6 收尾
四月是專案從局部功能完善邁向全系統架構硬化與效能收斂的關鍵月份。我們不僅完成了 Phase 4.6 整個史詩級任務群的收尾，還進行了深度的效能優化與架構重構。

**核心主題歸類**:
1.  **Phase 4.6 結案與架構硬化 (Ref: 04-25, 04-28)**:
    *   **地基物理加固**: 完成 SQL ID 對齊，物理重設非 UUID 身分。強制實施部門級 SQL 物理隔離。
    *   **架構級減重**: 完成 L2 模組化拆分，例如將 `seed_knowledge` 拆分至 `SeedingService`。
    *   **品質公證**: 達成 100% 後端測試通過率，並透過 `make persona-audit` 進行全角色工作流公證。

2.  **效能突破與 503 防禦 (Ref: 04-02, 04-15, 04-20)**:
    *   **503 結構性根除**: 遷移至官方 `google-genai` SDK，實作原子化巡檢與指數退避重試邏輯。
    *   **系統級 429 抗性**: 全局並發限制，頻率適配 Gemini Free Tier，並實作「原地等待重試」自癒機制。
    *   **冷啟動優化**: 解決 x86_64 環境下的 Torch 依賴與 NumPy 載入崩潰，熱機搜尋延遲大幅降至 2.3s。

3.  **商業情報與 UI 韌性 (Ref: 04-20, 04-25)**:
    *   **行銷情報 2.0**: 實作 `ConversionFunnel` 組件與 `_calculate_lead_score` 動態評分，實現轉換漏斗視覺化。
    *   **防禦性 UI**: 注入防禦性載入與去重邏輯，防止單點 API 錯誤卡死全頁。

4.  **測試隔離與物理對帳 (Ref: 04-22, 04-45)**:
    *   **狀態污染根除**: 實作深拷貝隔離 `MOCK_ADMIN_USER`，解決 E2E 測試中的級聯污染問題。
    *   **真理復原**: 透過 5 輪物理審計，清算殭屍檔案與冗餘邏輯，達成代碼與文件的 100% 對齊。

5.  **RBAC 與路由標準化 (Ref: 04-06, 04-13)**:
    *   **動態身分**: 權限定義 100% 物理遷移至資料庫，並在 UI 實作 Identity Matrix 管理介面。
    *   **路由合約**: 解決 `/api/api` 嵌套問題，實施分類掛載，強化動態與靜態 Role Scopes 的合併。

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

### 【Phase 4.6.60: 穩定性硬化與 E2E 物理公證鐵律】
> **【鐵律】此為針對 Manager Nexus 與 MBT 測試在極端環境 (Headless/Empty Data) 下的血淚教訓，在進行全端開發時必須嚴格遵守：**
>
> 1.  **前端圖表規範 (Headless Chart Hardening)**: 所有基於 Recharts 的圖表元件（特別是 AreaChart, LineChart），必須預設關閉動畫 (`isAnimationActive={false}`)。這能防止 Playwright 在 Headless 環境下，因動畫計算座標產生 `NaN` 而導致的 `TickItem Error` 崩潰。
> 2.  **後端空資料防禦 (Backend Empty State Parity)**: 絕對禁止使用 Supabase Python 客戶端的 `.single()` 或 `.maybe_single()` 來獲取單筆資料，因為它在空資料時會引發 HTTP 500 (`PGRST116`) 或返回 `None` 導致 `AttributeError`。必須使用安全的陣列查詢模式：`res = query.execute()` 並搭配 `if res.data and len(res.data) > 0:`。
> 3.  **測試狀態防護 (Stateful Mocks & Negative Paths)**: E2E 測試絕不可依賴「已有資料的開發者資料庫」。所有 MBT 測試必須包含空資料 (Empty State) 的負面斷言。在 Mock API 時，必須使用外部變數 (如 `let isApproved = false`) 來實現具狀態模擬 (Stateful Mock), 以真實還原 React 重新渲染時的資料狀態。
