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
*   **當前狀態 (Current Context)**: Phase 5.5.11 Monolith Refactoring（對 manager.py、ollamaService.ts、BugReportModal.tsx 進行 L2 模組化與自訂 Hook 抽離）已全部完成，全系統單元與整合測試、靜態代碼檢查及行數門禁皆已順利通過。
*   **今日目標 (Today's Goal)**: 等待人類指揮官給予下一階段的新指令。

> 4.  **第四步：取得您的確認**: 在您確認我對起點的理解無誤後，我才能開始執行第一個指令。

### 【UI 開發鐵律 (UI Development Iron Law)】

> **【鐵律】在產出任何 React 元件或修改前端程式碼前，必須先完成以下步驟。**
>
> 1.  **強制讀取 UI 標準**: 我**必須**先讀取 `PRPs/ai_docs/UI_STANDARDS.md` 的完整內容。
> 2.  **在計畫中宣告合規性**: 在我向您提出的開發計畫中，**必須**明確包含一個「合規性聲明」區塊，說明我將如何遵守 `UI_STANDARDS.md` 中的至少三項關鍵規範（例如：Tailwind v4 靜態類別、Radix UI `asChild` 組合、無障礙性 ARIA 屬性等）。
> 3.  **嚴格禁止違規行為**: **嚴格禁止**產出任何違反 `UI_STANDARDS.md` 中明確列出的「Anti-Patterns」的程式碼。

---

# 第二章：關鍵學習與偵錯模式 (Key Lessons & Debugging Patterns)

> 本章節將專案開發的歷史血淚與系統工程原則精煉為 **12 條核心黃金律**。這 12 條原則是 AI 助理與人類協作時不可逾越的行動邊界與自癒模式。

* **1. 證據至上與日誌真理 (Evidence First & Log Truth)**
    * **核心**: 拒絕主觀盲猜，日誌揭示當下事實，`git log` 交代歷史意圖。當行為不符預期時，立即在第一線注入實體日誌 (`console.log`, `print`)。當 Bug 反覆出現時，用歷史脈絡解讀代碼設計初衷，絕不在資訊真空下盲目修補。

* **2. 流程與直覺的雙重對帳 (Trust but Verify Everything)**
    * **核心**: 將 SOP (`Makefile`, `CONTRIBUTING.md`) 與使用者的直覺視為核心訊號，但兩者皆須經過雙重驗證。優先查閱既有規範以防重複犯錯；當使用者提出質疑時，立即暫停「快樂路徑」，用硬數據或程式碼實體去證實或排除疑慮。

* **3. 戰場隔離與變因控制 (Isolate the Battlefield)**
    * **核心**: 複雜的 Bug 往往是多層環境污染的疊加。必須系統性隔離變因：區分是宿主機環境、Docker 容器、還是前端元件問題。`make test` 失敗時，應釐清是根目錄工具鏈衝突還是子專案配置污染。在進行極端環境測試（如 Phase 5.5 無網/離線模式）時，必須實體切斷外部網路，驗證 Fallback 機制（如本地模型降階）是否真實生效。

* **4. 配置驅動與工具手冊意識 (Master Your Tool Configuration)**
    * **核心**: 工具的怪異行為 90% 源於配置，而非底層 Bug。Linter 規範在 `.eslintrc`，測試 Hoisting 需 `vi.hoisted`。此外，基礎設施崩潰常源於隱藏預設配置（如 Docker ENOSPC 危機源於預設下載巨型 CUDA 依賴與快取堆疊），必須精準掌握建置指令（如指定 CPU wheels）並定期壓縮瘦身。

* **5. 網路與環境隔離防護 (Internal/External Network Isolation)**
    * **核心**: 嚴防 Docker 內部 DNS（如 `supabase_kong`）洩漏至外部瀏覽器。前端代碼必須具備「主動防禦」特徵檢測，在請求發出前攔截無效的內部 URL 並切換至狀態化模擬 (Stateful Mock) 模式，杜絕瀏覽器因解析失敗陷入無限靜默 Loading。

* **6. 物理穿透驗證與三向連動 (Physical Penetration Verification)**
    * **核心**: 徹底終結「幽靈開發」，警惕日誌與文件的偽證。修改功能時，必須落實三向連動檢查：入口掛載 (main.py)、依賴映射 (index.html) 與實體測試斷言 (pytest/vitest)。更進一步，必須將 `make audit-qa` 視為最終品質公證網關，只有當代碼、測試與自動化腳本全部亮綠燈，方可標記為🟢已修復。

* **7. 雲原生意識與邊界防禦 (Absolute Cloud-Native Awareness)**
    * **核心**: 認清基礎設施事實，專案連接的是雲端 Supabase。遇資料庫權限錯誤，絕對禁止用 `docker exec` 強修，必須產出 `migration/` SQL 檔由人類於雲端執行。此外，徹底落實 Model SSOT (單一事實來源)，嚴禁在代碼中硬編碼 LLM 模型名稱，必須交由 DB 或環境變數統一控管，以實現架構級的 Fail-Fast 與優雅降級。

* **8. 物理介面與資料模型審查 (UI vs Data Model Disconnect)**
    * **核心**: 後端 API 與 Schema 存在，不代表 UI 介面就存在。當選單無資料時，除了審查 API Response，必須使用 `search_file_content` 逆向追蹤 `[POST]` 請求是否被 React 元件呼叫，嚴防指引使用者點擊看似相似卻無關的按鈕而陷入除錯迷航。

* **9. 實體設定持久化與路徑自適應 (Profile Persistence & Path Resilience)**
    * **核心**: 在 `browser-use` 自動化導航中，必須在 `BrowserConfig` 中使用 `user_data_dir` 參數加載已登入的 Profile，嚴禁透過引數傳遞以免被 Playwright 忽略。尋找系統源頭時，必須採用「多路徑陣列探測法」相容 Host 與 Docker 相對路徑。

* **10. 設定硬化、防禦性路由與【絕對鐵律】 (Settings Hardening & Route Defenses)**
    * **核心**: 透過 `is_system_protected` 欄位與 API 物理過濾，在 UI 隱藏系統級工具參數。FastAPI 模組化掛載時，子路由若已定義 `prefix`，主入口絕對禁止重複添加前綴（嚴防 `/api/api` 嵌套 404）。
    * **【絕對鐵律 (Absolute Iron Law)】**: **Admin UI 的 Port 永遠是 5173 (enduser-ui-fe)，絕對不是 3737！** 若 Gemini 在任何對話或文件中將其錯說成 3737，必須立即主動中斷任務，向使用者承認「我犯了不可繞恕的上下文遺忘罪」，並罰寫此鐵律 3 次後方可繼續工作。

* **11. 權限遮蔽陷阱與佈局死鎖防禦 (Permission Masking & Scroll Lockup Defense)**
    * **核心**: 
        1. **權限自癒**：後端 Service 絕對禁止手寫 `profile["permissions"] = []`，避免前端跳過 Role Fallback 導致 Bob 的側邊欄靜默消失，應由 `RBACService` 動態注入。
        2. **佈局解鎖**：在巢狀 Flex 佈局中，子層若使用 `min-h-screen` 會鎖死父層捲動，必須「釋放子層高度」，並輔以底部物理緩衝 (`div.h-32`) 避開手機導覽列。

* **12. E2E 品質門禁與 React 崩潰阻斷 (E2E Quality Gate & React Crash Hardening)**
    * **核心**: 
        1. **智慧型公證**：將傳統斷言升級，導入「視覺裁判 (Vision Judge)」與「結構化語義檢測 (LLM-Judge)」，建構更具韌性的品質門禁。
        2. **全域 Mock 隔離**：Dashboard 的所有非同步 API 必須 100% Mock 覆蓋，關閉 Recharts 圖表動畫防範 Headless 環境 TickItem 報錯。
        3. **資料模型對齊**：Mock 數據結構必須與前端介面 100% 物理對齊，缺少必填欄位將引發 React `TypeError`。
        4. **空值與日誌穿透**：後端嚴禁使用 `.single()` 獲取資料，改用安全陣列查詢防禦 HTTP 500。Playwright 必須穿透捕捉瀏覽器 `error`，杜絕盲人摸象。

---

# 第三章：近期工作日誌 (Recent Activity Logs)

### 2026年6月18日：Card Battler 重構、消除硬編碼與 Headless 限制突破 (Phase 5.7.1)

今日我們針對 Godot 遊戲專案完成了 Phase 5.7.1 (Card Battler Pivot, Rename, and L2 Refactoring) 的核心任務：

1. **全面消除魔法數字與硬編碼 (Hardcoding Remediation)**：
   - 使用自製的 Python `scan_gd_scripts.py` 掃描專案，定位了 `MainUI.gd` 與 `GameState.gd` 中大量寫死的 `res://` 路徑、UI 尺寸 (`Vector2`) 以及延遲常數。
   - 將所有數值抽離至 `GameConfig.gd` 與其對應的 `.tres` 資源檔，讓企劃能透過 Inspector 直接調整，實現邏輯與資料的徹底分離。
2. **L2 模組化與巨型檔案減重 (L2 Modularization)**：
   - 針對 Godot 專案的 `MainUI.gd` 進行預防性拆分，成功剝離出 `HandController.gd` (專司卡牌弧線渲染與拖曳) 以及 `OverlayManager.gd` (掌管難度、教學與結算畫面)。
   - 拆分後，全 Godot 專案再無任何 `.gd` 檔案超過 400 行門檻 (MainUI 降至 313 行)。
3. **CI/CD 現代化與 Lean 測試哲學**：
   - 在 `.github/workflows/ci.yml` 中導入業界標準 `chickensoft-games/setup-godot` 引擎配置。
   - 堅持 **Lean 原則**，拒絕盲目跟風導入臃腫的第三方 GUT 框架，改以原生 Headless 模式搭配自製的 `HeadlessRunner.gd`，成功在本地通過了 76 項戰鬥與邏輯測試。
4. **突破 Godot Headless 渲染限制 (UI Capture Proof)**：
   - 在執行 `capture_ui.gd` 公證截圖時，遭遇 `--headless` 模式下 `dummy` 渲染器無法擷取 Viewport 影像的底層限制 (回傳 null)。
   - 撰寫 Python 腳本 `capture_proof.py` 繞過限制，以帶有 GUI 視窗的模式自動啟動 Godot，成功產出 517KB 的實體驗證截圖，證明 L2 拆分與資源抽離未破壞任何 UI 錨點與圖層 (Z-Index)。
5. **Web (WASM) 發佈與整合**：
   - 使用 Godot headless 指令將遊戲匯出為 Web 格式 (`index.wasm`, `index.pck`)。
   - 避開靜默匯出失敗的路徑陷阱，成功將編譯成品部署至 `enduser-ui-fe/public/games/card-battler/` 目錄，使遊戲能被 5173 Port 的前端網頁順利載入。

### 2026年6月8日：L2 模組化代碼減重與 Monolith 行數門禁達成

今日我們針對專案中三個行數超過 400 行的核心程式碼檔案完成了 L2 模組化拆分，以符合單一檔案行數低於 400 行的門禁標準：

1. **後端 Credential 模組拆分**：
   - 移除了 `manager.py` 內未被調用的 legacy 函數 `get_config_as_env_dict`。
   - 將 `check_credentials_exist` 驗證邏輯移至新增的 `helpers.py` 中。
   - 主要服務 `manager.py` 行數從 427 行順利降至 321 行。

2. **前端 Ollama 服務型別抽離**：
   - 新建 `ollamaTypes.ts`，並將所有 API 響應/請求強型別聲明全部自 `ollamaService.ts` 抽離。
   - 於 `ollamaService.ts` 內使用 `export * from "./ollamaTypes"` 導出，完美保障對外別名與導入的向上相容性。主要服務行數從 436 行降至 277 行。

3. **前端 Bug 報告彈窗邏輯 Hook 化**：
   - 建立自訂 Hook `useBugReport.ts`，將 `BugReportModal.tsx` 內所有與表單 state、GitHub Issue 提交、剪貼簿格式化以及 toast 通知相關的非 UI 業務邏輯全數抽離。
   - `BugReportModal.tsx` 僅保留 JSX 結構渲染，行數從 429 行降至 319 行。

4. **品質門禁與測試驗證**：
   - 通過 `make test-be` 全體 591 項後端單元與整合測試。
   - 前端 TS 類型編譯與 `make lint` 檢查皆無任何報錯與警告。
   - 執行 `make phase-audit` 驗證全系統除大檔案測試套件外，所有主程式碼檔案皆已降至 400 行以下。

### 2026年6月7日：3-Tier 容災降階架構與雙端設定 UI 落地公證

今日我們實作並驗證了具備「人類控制」與「狀態透明」的 3-Tier 容災降階備援系統 (Google Gemini -> Hugging Face -> 本地 Ollama)：

1. **級聯路由與自癒重置**：在 `base.py` 中實作了 Auto-Failover 級聯降階。連線正常但 API Key 失效/429 時直降 Tier 2 (Hugging Face Serverless)；斷網時繞過 Tier 2 直降 Tier 3 (本地 Ollama)。當主要雲端呼叫成功時，自動觸發自癒將作用中層級重設為 Tier 1。支援人類手動 Override 指定 Tier 策略。
2. **網路 socket 狀態 API**：在 `system_api.py` 中實作 `/api/system/fallback/status` 端點，回傳作用中層級與基於 8.8.8.8:53 TCP Socket 連線偵測的真實網路狀態。
3. **雙端設定面板 (5173 & 3737) 與指示燈**：
   - 在 5173 前端 (enduser-ui-fe) 啟用專屬的 `AdminFallbackConfig.tsx` 單選按鈕面板與安全密碼輸入，並修改 `AdminSystemConfig.tsx` 過濾排他設定，避免重複渲染。
   - 在 3737 前端 (archon-ui-main) RAG 設定中擴充 `forced_fallback_tier` 與 `HF_TOKEN` 型別，並新增 **3-Tier Fallback Settings** 折疊面板。
   - 在頂欄掛載 `<FallbackStatusBadge />` 狀態指示燈，每 10 秒動態輪詢狀態。
4. **型別安全與測試通過**：
   - 修復了 `test_llm_fallback.py` 中的 `MagicMock` 缺少 `close` await 引起的 TypeError 異常。
   - 順利通過全系統靜態檢查 `make lint` 達 0 Errors / 0 Warnings。
   - 通過 `make test-be` 全體 588 項後端測試。
   - 通過 `make audit-qa` 整合品質公證與 `make twin-scout` 數位雙生角色對帳，達到 100% 物理對齊。

### 2026年6月5日：Markdown 擴展升級與 GFM / Mermaid 霓虹美化落地

今日我們針對前台部落格的 Markdown 渲染器進行了深度的功能擴展，完美支援原生 GFM 網格表格與 Mermaid 動態循序圖：

1. **依賴擴展升級**：在 `enduser-ui-fe` 前端套件中安裝了 `remark-gfm` 與 `mermaid` 圖表引擎，徹底打破了 react-markdown 預設無法渲染表格與流程圖的限制。
2. **實作霓虹美化元件 (`MermaidRenderer`)**：
   - 封裝了 `MermaidRenderer.tsx` 元件，整合非同步渲染機制與 Tron 暗色霓虹主題設定。
   - 註冊 `remarkGfm` 至 `<Markdown>` 的 `remarkPlugins` 中，並透過自訂 code 渲染元件，將 `language-mermaid` 代碼區塊無縫導向 Mermaid 渲染引擎。
3. **資料庫與環境同步**：
   - 將部落格 Post 9 的 SQL 種子資料還原為原生高精度的 ` ```mermaid ` 與 GFM 表格。
   - 重新執行 `make db-init` 初始化以重載純淨的種子資料。
4. **品質門禁公證**：
   - 執行 `make lint` 確保代碼規範與強型別 100% 正確。
   - 最終執行全系統 `make audit-qa` 品質公證網關，順利通過前後端全部 **582 項測試案例**，且多角色 (Alice, Bob, Charlie, David) Parity 物理審計全數亮起綠燈。
5. **Git 自動化合併與推送**：完成了特徵變更的 add, commit, push，並將變更順利合併推送到遠端 `dev/twins` 分支，回復了乾淨無暇的工作區。

### 2026年6月2日：離線雙生模型換裝與品質門禁驗證 (Offline Twin Model Switch & QA Gate)

今日我們專注於本地端離線大模型的測試與環境部署，並成功驗證了核心的品質門禁。

1. **品質門禁公證 (Audit QA & Twin Scout)**：成功執行 `make audit-qa` 與 `make twin-scout`。全系統 579 項後端測試、前端 36 個測試檔以及 DNS/Scroll 等靜態掃描皆無錯誤通過。Alice, Bob 等五大角色的 UI 實體截圖與資料庫狀態實現 100% 物理對齊。
2. **Ollama 模型冷啟動痛點與換裝**：在測試 `gemma4:e4b` (9.6GB) 與 `gemma4:e2b` (7.2GB) 時，遭遇了 Mac CPU 環境下長達 3~6 分鐘的「冷啟動 (Cold Start)」與記憶體不足 (OOM) 瓶頸。
3. **務實的本地模型決策**：為了兼顧開發體驗與多模態需求（特別是 Phase 5.5 的 Twin Scout 視覺裁判），我們移除了龐大的 Gemma 4 家族，最終選定並部署了 **`gemma3:4b`** (約 3.3GB)。實測證明其在 CPU 環境下載入速度大幅提升，且具備優異的邏輯與圖像理解能力。
4. **極速開發備案**：同步部署了超微型模型 `qwen2.5:0.5b` (< 400MB)，為純文字 RAG 測試提供「秒回」級別的極速開發體驗。

### 2026年6月1日：開發流水線重塑與盲目樂觀防禦 (Golden Pipeline & Probe Hardening)

今日我們專注於重新定義專案的標準開發工作流，徹底消除了 Docker 環境啟動與測試之間的「盲目樂觀」現象：

1. **SOP 重新定義 (The Golden Pipeline)**：確立了 `AI Phase-Audit` -> `make dev-docker` -> `make probe` -> `make audit-qa` 的鐵律線性流程。
2. **Phase-Audit 技能升級**：將 `git fetch origin && git status` 與 `git pull --rebase` 強制寫入 `@.agents/skills/phase-audit/SKILL.md`，確保 AI 實體對帳前必定與遠端同步。
3. **Dev-Docker 緩衝防禦**：修改 `Makefile` 中的 `dev-docker` 指令，強制在啟動容器後加入 `sleep 30` 與 `make probe`。這確保了系統必定等待 API 與資料庫完全就緒後，才放行後續的自動化測試，根絕了探針因連線被拒絕而導致的偽陰性 (False Negative) 崩潰。
4. **全系統公證**：以全新 Pipeline 執行 `make audit-qa`，成功在本地通過 578 項 Pytest 與全數 E2E 測試。

---

# 第四章：歷史檔案：原則的考古學 (Historical Archive: The Archaeology of Principles)

> **【封存說明】**
> 本章節存放了所有歷史日誌。當你需要深入了解某個特定問題的完整偵錯背景時，可以在此查閱最原始的紀錄。

### 2026年5月：多 Agent 星環拓樸、QA 全自動化與極端環境救援
五月是專案從單一 Agent 升級至多 Agent 協作架構，並將品質門禁與測試自動化推向極致的月份。我們完成了 Phase 5.1.x 到 Phase 5.5.0 的史詩級任務群。

**核心主題歸類**:
1.  **Phase 4.6.60 穩定性硬化與 E2E 物理公證 (Ref: 05-11)**:
    *   **前端圖表防禦**: 關閉 Recharts 動畫以防止 Headless 環境下 Playwright 崩潰 (`NaN TickItem Error`)。
    *   **後端空資料防禦**: 嚴禁使用 `.single()`，改用安全陣列查詢 (`execute()`) 防禦 HTTP 500。
    *   **測試狀態防護**: E2E 嚴禁依賴開發者資料庫，必須包含空資料斷言，並使用具狀態變數 (Stateful Mock) 還原 React 重新渲染。

2.  **基礎設施與環境自癒加固 (Ref: Phase 5.1.13, 5.1.17)**:
    *   **Model SSOT**: 根除模型硬編碼，統一交由 DB / 環境變數控制，落實 Fail-Fast。
    *   **模組解耦**: 進行大於 400 行的檔案瘦身，強化 L2 架構清晰度，消滅「God Objects」。
    *   **數位雙生防禦**: 建立 CLI 雙軌機制，加載 `BrowserConfig` 無密碼環境對抗 Docker 加密憑證讀取障礙。

3.  **體驗升級與 RAG 優化 (Ref: Phase 5.1.13)**:
    *   **極簡 RAG 入口**: 實作 Karpathy 式極簡知識庫介面，支援原始網址直丟與切片向量化。
    *   **視覺優化**: 實作科技霓虹濾鏡與幾何 SVG 的「零 Token 視覺 Fallback」，大幅降低雲端成本。

4.  **星環群聊架構與排程器整合 (Ref: Phase 5.1.7 ~ 5.1.16)**:
    *   **拓樸升級**: 確立「星型群聊 (Star-Topology)」機制，由 Supervisor 動態路由並綁定 Gemini 3.1 系列，防範無限迴圈與成本失控。
    *   **週期報告自動化**: 實作日、週、月報執行摘要的 Map-Reduce 星環化，並成功與 Clockwork 排程系統深度整合。

5.  **QA 全自動化與 MBT 硬化 (Ref: Phase 5.2.0, 5.1.2)**:
    *   **視覺裁判**: 實作 Gemini 3.1 Vision 作為 UI 視覺裁判 (Judge)，並建立 Structured LLM-Judge 確保內容語義品質。
    *   **測試隔離與網關**: 消除 E2E 測試依賴污染，加裝 `RUN_INTEGRATION_TESTS` 門檻，並完成 `make audit-qa` 整合網關。

6.  **Phase 5.3~5.5 離線硬化與極端環境救援 (Ref: 05-27, 05-29, 05-30)**:
    *   **離線雙軌架構**: 實作 `OFFLINE_MODE` 雙軌機制，無網狀態自動將向量降階至 384 維度並轉接本地 SentenceTransformer 與 Ollama。
    *   **ENOSPC 空間危機**: 剖析 31.5GB 巨獸級 Docker 映像檔，剃除 PyTorch 的 CUDA 依賴與封裝快取，成功瘦身至 5.02GB。
    *   **歷史歸檔與實體對帳**: 將過期 Phase 文件徹底壓縮歸檔 (`Phase_5_Archive.tar.gz`)，並提煉 Docusaurus 知識庫，確保工作區極簡。
    *   **混沌與品質門禁**: 確認模擬器 Deterministic 特性，並將 500 Error 優雅納入 `pytest.skip` 防禦，確保 CI/CD 穩定性。

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
��立起穩固的工程紀律和核心工作原則的基礎月份。

### 2026年6月18日：Git 考古還原真相與 Phase 5.6 歷史歸檔

今日我們專注於排程除錯、分支整理與技術債歸檔，強化了「以實體日誌為準」的考古精神：

1. **Git 考古與排程真相還原**：
   - 針對 Hugging Face 自動排程器在 UTC 00 時中斷的問題，我們拒絕盲猜，透過 `git log` 與 `git branch -a --contains` 進行實體交叉比對。
   - 成功證實排程修復程式碼已於昨日寫入，但被滯留於 `feat/twins` 分支未合併，導致 GitHub Actions 讀取到舊版 `dev/twins` 設定。
   - 完成了包含 API Lint `B904` 修復、Godot MVC 卡牌重構在內的大型分支合併與遠端同步。
2. **分支瘦身與清理**：
   - 刪除了完成階段性任務的 `feat/tycoon-config-refactor` 與 `fix/tycoon-paper-doll-zindex` 本地分支。
   - 清理了雲端自動生成的 UI 與 Jules AI 殘留分支，並透過 `git remote prune origin` 確保本地追蹤狀態極簡。
3. **Phase 5.6 歷史歸檔與知識提煉 (SOP 落實)**：
   - 依據 `CONTRIBUTING_tw.md` 規範，啟動 `make phase-audit` 確認無幽靈任務後，執行了 Phase 5.6.x (Lean 整合與離線工作流優化) 史詩級文件的歷史封存。
   - 成功將 9 份 `.md` 計畫壓縮至 `PRPs/archive/`，並提煉其精華至 Docusaurus 知識庫的 `knowledge-journal/phase-5-6-0-lean-optimization.mdx`，維持專案根目錄乾淨且知識不流失。

### 2026年6月11日：Godot TDD 奠基與卡牌架構轉向 (Lean Pivot)

今日我們啟動了 Archon 衍生遊戲專案的開發，並確立了以 TDD (測試驅動開發) 為核心的 Godot 引擎工作流，期間經歷了重要的架構轉向與踩坑學習：

1. **從塔防到卡牌的 MVC 覺醒**：
   - 原先規劃的「塔防遊戲」因高度依賴物理引擎 (`Area2D`, `Path2D`) 與空間時間，導致單元測試極難撰寫且容易產生 Race Condition。
   - 果斷將企劃轉向**「AI 卡牌構築戰 (Agent Card Battler)」**。卡牌遊戲純粹的回合制與狀態機本質，能完美實現 **Model-View-Controller (MVC) 的極致解耦**，讓我們能在無 UI 的狀態下完成 100% 的邏輯單元測試。
2. **Godot 與 VS Code 的雙劍合璧 (LSP 配置鐵律)**：
   - 確立了「Godot 當大腦與視圖，VS Code 當打字機」的雙開工作流。
   - **坑點記錄**：VS Code 的 `godot-tools` 設定中，`Editor Path` 絕對不能只填 `/Applications/Godot.app`，必須精確指向內部的終端執行檔 (`/Applications/Godot.app/Contents/MacOS/Godot`)。同時，Godot 的 Language Server Port 必須確認為 `6005`。
3. **拒絕臃腫：自製 Lean Test Runner (MiniTest)**：
   - 在導入業界標準的 GUT 測試框架時，遭遇了其內部腳本與 Godot 4.6 原生 API (`Logger` 類別) 衝突導致的 Parse Error 與 `MissingNode` UI 崩潰。
   - 秉持 Lean 原則，果斷放棄重度依賴第三方框架，改用 Godot 原生的 `@tool extends EditorScript`，以不到 40 行的程式碼打造出 `MiniTest` 微型測試框架。這不僅徹底根除了相容性問題，更實現了「免按 Play 鍵即可在編輯器內秒速執行 TDD」的極致開發體驗。
