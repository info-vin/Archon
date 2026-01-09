# 廚師日誌 (Chef's Journal) v2

> **【文件目的】**
>
> 本文件是 AI 助理 Gemini 的工作日誌與核心原則。它濃縮了專案開發過程中最關鍵的學習與SOP，旨在成為一個高效、聚焦的行動指南，並避免重複過去的錯誤。
>
> **【文件結構】**
>
> *   **第一章：核心工作習慣**: 定義了 Gemini 不可動搖的、必須在所有行動前遵守的思維框架與SOP。
> *   **第二章：關鍵學習與偵錯模式**: 提煉了從大量歷史日誌中反覆出現的、最有價值的經驗教訓，並將其歸納為可複用的偵錯模式。
> *   **第三章：近期工作日誌**: 保留最近的、最相關的幾份日誌，以供快速回溯上下文。
> *   **第四章：歷史檔案**: 完整存檔所有過去的日誌，作為深入研究特定問題時的「考古資料」。

---

# 第一章：我的核心工作習慣 (My Core Habits)

### 【行動前風險評估原則 (Pre-Action Risk Assessment Principle)】

> **【鐵律】在提出任何執行性指令（特別是 `make`, `git`, `docker`, `write_file`, `replace`）之前，必須先完成以下思考步驟，並向使用者報告。**
>
> 1.  **回顧歷史**: 主動回想 `GEMINI.md` 和 `CONTRIBUTING_tw.md` 中與此指令相關的歷史失敗案例。
> 2.  **檢查設定檔**: 讀取相關服務的設定檔（如 `vite.config.ts`, `docker-compose.yml`），主動識別出指令之外的「隱性依賴」，例如**環境變數、掛載卷、或特定的埠號**。
> 3.  **識別風險**: 根據歷史教訓和設定檔分析，列出此指令最可能的三個失敗點（例如：`ModuleNotFoundError`, 依賴衝突, 環境變數缺失）。
> 4.  **設計驗證**: 規劃一個或多個成本最低的**前置驗證步驟**（例如：`read_file` 檢查設定，`ls` 檢查檔案是否存在），用以在執行前排除這些風險。
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
> 2.  **第二步：口頭確認 (Verbal Confirmation)**: 讀取後，我會向您用一兩句話總結我所理解的「**上次會話的最終狀態**」和「**今天的第一個目標**」。
> 3.  **第三步：取得您的確認**: 在您確認我對起點的理解無誤後，我才能開始執行第一個指令。

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
    *   **核心**: 工具的行為由其配置決定。看似 Bug 的行為，往往是配置不當。Linter 警告的根源可能在 `.eslintrc`；測試失敗的根源可能在於混淆了 `Mock` 與 `AsyncMock`。在發明輪子前，先讀懂工具手冊。

*   **5. 精準測試：填補盲區，應對非同步 (Test with Precision: Fill Blind Spots, Handle Async)**
    *   **核心**: `lint` 發現但 `test` 沒發現的問題，是測試覆蓋率不足的信號。應編寫一個能精準復現問題的最小化單元測試。對於非同步或單例服務，必須使用特殊的 `patch` 模式（如 `setup_module`）才能正確隔離和測試。

*   **6. 全生命週期視角：從願景到部署後驗證 (Full Lifecycle View: From Vision to Post-Deployment Validation)**
    *   **核心**: 開發不僅僅是寫程式碼。它始於透過分析假資料 (`MOCK_DATA`) 或文件來理解真實的專案願景，並終結於 `push`、部署、以及最重要的——由終端使用者在瀏覽器（注意快取）驗證無誤。一個修復只有在被使用者確認後才算完成。

*   **7. 內外網隔離原則：主動防禦環境變數污染 (Internal/External Isolation: Proactive Guard against Env Pollution)**
    *   **核心**: 在 Docker 化環境中，後端傳遞給前端的環境變數（如 `SUPABASE_URL`）可能包含內部 Docker DNS（如 `supabase_kong`）。這對瀏覽器是無效的。前端代碼必須具備「主動防禦」邏輯，透過靜態特徵檢測（如檢查 URL 是否包含 `_kong`），在請求發出前攔截並切換至 Mock 模式，避免瀏覽器因 DNS 解析失敗而陷入無限 Loading。

*   **8. 測試邊界與狀態化模擬 (Test Boundaries & Stateful Mocks)**
    *   **核心**: 
        1.  **配置互斥**: Unit Test (`vite.config.ts`) 與 E2E Test (`vitest.e2e.config.ts`) 的包含路徑必須互斥 (`exclude`)，避免同一測試在錯誤環境下重複執行。
        2.  **狀態連動**: E2E 測試若涉及 CRUD 流程，Mock 必須具備狀態 (Stateful)，不能只回傳靜態空值，否則無法驗證「新增後顯示」的邏輯。
        3.  **變數提升**: 謹記 `vi.mock` 的 Hoisting 特性，依賴的變數必須使用 `vi.hoisted` 定義。

---

# 第三章：近期工作日誌 (Recent Journal Entries)

### 2026-01-09: 權限架構的遷移與完結 (Auth Architecture Migration & Completion)
*   **核心任務**: 完成 Phase 4.2.2 的最後一哩路，並徹底執行 Phase 5 的 Auth 遷移，根除 Admin 操作時的 Session 異常。
*   **架構決策**: 
    *   **後端中心化 Auth**: 廢除了 `api.ts` 中直接呼叫 `supabase.auth.signUp` 的模式。改由後端 `AuthService` 使用 `service_role` key 執行 `admin.create_user`，徹底解決了 Admin 建立使用者時被強制登出的邏輯缺陷。
    *   **雙重驗證**: 透過 `make test` 與 Gap Analysis 表格的逐項審查，確認了從資料庫自動化到 UI 功能的全面合規。
*   **遺留項目**: 識別出「刷新頁面時的 Session Hydration Lag」為唯一的視覺瑕疵，雖不影響功能但影響體驗，列為後續優化項目。

### 2026-01-08: 誠實的架構與 Mock 的邊界 (Honest Architecture & The Boundaries of Mocks)
*   **核心任務**: 執行 Phase 4.2.2 Hotfix，移除 `api.ts` 中的「自動 Mock Fallback」機制，並修復因此崩潰的測試。
*   **架構決策**: 
    *   **移除掩飾**: 刪除了 `SmartAPI`，讓前端在無法連線後端時直接報錯，而非靜默切換到假資料。這迫使開發者正視 `docker-compose` 的網路配置問題。
    *   **Mock 分離**: 確立了 Mock 資料應僅存在於 `tests/` 或 `Storybook` 中，嚴禁汙染生產代碼 (`src/`)。
*   **偵錯歷程**:
    *   **測試重疊**: `make test` 失敗是因為 `vite.config.ts` (Unit Test) 未排除 `tests/e2e`，導致 E2E 測試在錯誤的環境下被重複執行。修正：在 `test.exclude` 中明確排除 E2E 目錄。
    *   **變數提升 (Hoisting)**: `vi.mock` 會被提升到檔案最上方，導致無法存取外部定義的 `mockUser`。修正：使用 `vi.hoisted(() => ...)` 來定義 Mock 資料。
    *   **狀態迷失**: E2E 測試失敗是因為 Mock API 是無狀態的（永遠回傳空陣列）。修正：在 `e2e.setup.tsx` 中實作了簡單的 `mockTasksStore` 陣列，讓 `createTask` 與 `getTasks` 能連動。
    *   **DOM 殘留**: `MarketingPage` 的 `setTimeout` 在測試結束後仍嘗試存取 `document`。修正：加入 `typeof document !== 'undefined'` 檢查。

### 2026-01-07: 批量修復與 SOP 的再教育 (The Batch Fix & SOP Re-education)
*   **核心任務**: 解決 Phase 4.2.2 遺留的四大 UI/通訊問題 (406 錯誤、專案操作、捲動、Markdown)。
*   **偵錯歷程**: 
    *   **SOP 違規**: 試圖通過「修改 -> 報錯 -> 再修改」的低效迴圈修復 Bug，導致舊有測試大規模崩潰。
    *   **SOP 回歸**: 建立 `api.stability.spec.ts` 驗證核心邏輯，並根據報錯精準修復 `TaskModal.test.tsx` 的 Mock 策略。
*   **關鍵學習**: 
    *   **Mock 的完整性**: 修改代碼（如加入 `getAssignableAgents`）後，必須同步更新相關測試的 Mock。
    *   **可訪問性**: 隱藏文字 (`sr-only`) 需使用 `{ hidden: true }` 抓取。
    *   **Git 考古**: 動手前先查 `git log -p`，避免覆蓋他人的重要修復（如 Promise.race）。

### 2026-01-06: 全棧對齊與文檔化 (Full-Stack Reconciliation)
*   **核心任務**: 解決後端分頁結構 (`{ tasks: [] }`) 與前端預期 (`Array`) 不匹配導致的崩潰。
*   **架構決策**: 在 `api.ts` 中實作了防禦性邏輯，同時支援陣列與物件格式，確保前後端解耦。
*   **文件**: 歸檔了 Phase 3.8 並正式啟動 Phase 4.2.2。

### 2026-01-05: 銷售情資與 Async 陷阱 (Sales Intel & Async Pitfalls)
*   **核心任務**: 實作 Phase 4.2 "Sales Intelligence" 並修復後端 API 回歸錯誤。
*   **偵錯歷程**:
    *   **Async 混淆**: `projects_api.py` 錯誤地 `await` 了同步的 Supabase 客戶端，導致 `AttributeError`。修正為同步呼叫。
    *   **Mock 策略**: 確立了「Patch 必須針對 Class」的黃金法則，並在測試中將 `AsyncMock` 降級為 `Mock` 以匹配行為。
*   **結論**: 成功交付業務開發工具，並確立 Vitest + MSW 整合測試方案。

### 2026-01-04: 主動防禦與無限 Loading (Proactive Defense)
*   **核心任務**: 根治 `enduser-ui-fe` 在全 Docker 環境下的無限 Loading 問題。
*   **架構決策**: 在 `api.ts` 引入「主動防禦 (Proactive Guard)」邏輯。透過靜態檢查 URL 是否包含 `supabase_kong` 等內部關鍵字，直接判定為 Docker 內部環境並立即切換至 Mock 模式，實現 0 延遲體驗。
*   **關鍵學習**: 不要讓使用者等待必敗的請求；當環境變數明顯無效時，應立即 Failover。

### 2026-01-03: 自癒能力基礎設施 (Self-Healing Infrastructure)
*   **核心任務**: 穩定全 Docker 開發環境並啟動 Phase 5 自癒能力。
*   **偵錯歷程**:
    *   **環境修復**: 解決了 `archon-ui-main` 的崩潰 (缺少 `useState`) 與 API Key 注入問題。
    *   **初始化**: 修復了 End-User UI 在 Docker 下因缺少 `localStorage` 崩潰的問題，透過 `docker-compose.yml` 注入變數實現自動 Fallback。
*   **結論**: 成功清除了 Admin UI 環境雜訊，並在 `AgentService` 中打通了自癒閉環。

---

# 第四章：歷史檔案：原則的考古學 (Historical Archive: The Archaeology of Principles)

> **【封存說明】**
>
> 本章節存放了所有歷史日誌。當你需要深入了解某個特定問題的完整偵錯背景時，可以在此查閱最原始的紀錄。

### 2025年12月：Async 重構、前端規範與 AI 開發者奠基

十二月是技術債償還與新功能開發並行的月份。我們完成了全系統的 Async 化，並實作了 AI 開發者流程的核心基礎。

**核心主題歸類**：
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

**核心主題歸類**：
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

**核心主題歸類**：
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
    *   **釐清矛盾**: 透過釐清「UI 載入成功但 API 404」的精確場景，區分了「啟動問題」與「資料問題」。

### 2025年9月：SOP、歷史追溯與偵錯紀律的建立

九月份是專案從混亂的「救火隊模式」轉向「紀律化開發」的關鍵月份。這個月的歷程充滿了在 `make` 指令、Docker 環境、部署流程和非同步測試中的反覆試錯。

**核心主題歸類**：
1.  **SOP 的建立與探索**: 這個月，我們確立了多項至今仍在使用的核心工作原則。我們學會了不再信任過時的文件，而是將 `Makefile` 視為「單一事實來源」(Ref: 09-19)，並反覆使用 `git log -p` 去追溯 `Makefile` 和 `docker-compose.yml` 的歷史意圖，以理解為何一個指令會以某種特定方式運作 (Ref: 09-29, 09-21)。「測試先行」的重構安全網 (Ref: 09-24) 和冪等性的資料庫腳本 (Ref: 09-21) 也在這個月被確立為標準實踐。

2.  **系統性偵錯的學習**: 我們經歷了從處理表層 Bug 到深挖根源的思維轉變。例如，一個看似簡單的 `AttributeError`，其根源卻是更深層的 `ImportError` (Ref: 09-22)。我們也學會了警惕 `make lint --fix` 等指令帶來的副作用 (Ref: 09-23)，並確立了在修改程式碼前，必須先分析所有相關檔案，以避免「改 A 壞 B」的循環 (Ref: 09-17)。

3.  **部署與非同步測試的挑戰**: 九月下旬，我們專注於打通完整的開發到部署流程。我們演練了部署流程，解決了因服務耦合、Git Remote 混淆和鎖定檔案缺失導致的部署失敗問題 (Ref: 09-30)。同時，我們在為非同步 API 撰寫測試時遇到了困難，最終透過在 `patch` 中使用 `AsyncMock` 和在獨立檔案中進行「沙盒驗證」，才成功突破了 Mocking 的迷霧 (Ref: 09-25)。

總結來說，九月是透過解決一系列棘手的環境、部署和測試問題，從而建立起穩固的工程紀律和核心工作原則的基礎月份。