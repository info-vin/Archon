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
*   **當前狀態 (Current Context)**: 2026-11-25 完成 Phase 5.15 全階段（P0 探針 + Stage 1/P1 `d98e43a3` + Stage 2/P2 `e2398444` + Stage 2.5 閉環 `4f8fa9dc`/`ce66b78f`/`441f0bcf` 與反向驗證修復）：完成雲端 6 隻 Bot UUID 雙表 100% 對齊與死碼/`PresentationBot` 退場；落地統一 `AgentCard`、A2A `[HANDOFF:]` 協議（已同步雲端 4 筆 Worker Prompt）、生產 `agent_checkpoints` 實體落盤（雲端實測 `e7d1d7ab`, `COMPLETED`）、升級 Vercel Proxy (`enduser-ui-fe/api/telegram.js`) 支援 `reply_markup` Inline 審批按鈕與 `answerCallbackQuery`/`getUpdates`（實測 `has_reply_markup_in_result=True`）、Telegram Webhook `/status` 與 `/task` 即時派發執行並自動完工回推（實測 `8cf29389` 轉 `done`、`reply_sent=True`）；透過反向驗證揪出並修復過期/不存在審批按鈕導致 Webhook HTTP 500 缺陷，清理 2 筆探針殘留工單，並同步推送 `origin/dev/twins` 與 `origin/feat/twins`。
*   **今日目標 (Today's Goal)**: 觀察線上 Telegram 雙向指令與 A2A 協作實際運作；待本機執行一次 104 職缺抓取後完成 Phase 5.14 ≥30 筆人工標記校準；後續擴充 `telegram_bot_gateway.py`（現 398 行近 400 行上限）前須先拆分子模組。

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

* **10.5 基礎設施拓樸對帳鐵律 (Infrastructure Topology Audit Iron Law)**
    * **核心**: 徹底根除「視野狹隘 (Tunnel Vision)」導致的修改遺漏。
    * **【絕對鐵律】**: 在修改任何與 Docker (Dockerfile)、環境變數 (.env) 或建置依賴相關的檔案之前，**必須第一時間查閱 `docker-compose.yml`**。強制作業流程：
        1. 掃描 `docker-compose.yml` 中所有 `build.dockerfile` 屬性。
        2. 列出專案中**所有**正在服役的 Dockerfile (如 `Dockerfile.server`, `Dockerfile.mcp`, `Dockerfile.agents`)。
        3. 一項修復若適用於某一容器，必須同等評估並應用於拓樸中所有受影響的容器，嚴禁只改最顯眼的主檔而漏改附屬檔 (改東漏西)。

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

* **13. 防範虛假測試與型別斷層 (False Mock & Signature Sync)**
    * **核心**: 單元測試通過不代表代碼安全。修改任何核心服務 (Service/Repository) 的**回傳型別 (Return Type)**（例如將字串改為 Tuple）時，**必須**使用全域搜尋 (`grep`) 同步更新所有依賴該服務的測試 Mock，確保 `mock_service.return_value` 與物理現實 100% 一致。否則單元測試會淪為掩護 `too many values to unpack` 或寫入亂碼的遮羞布。

* **14. 探針先行與零虛假開發 (Probe-First & Zero Fake Development)**
    * **核心**: 在撰寫實作計畫前，**必須**先在 `scratch/` 寫「探針腳本 (Probe Script)」去真實觸碰外部 API 或環境變數。嚴禁在 Agent 或業務邏輯中寫死 `os.urandom` 假資料來欺騙測試或使用者 (虛假開發)。當外部憑證 (如 Google Drive Token) 缺失時，必須立刻 `Fail-Fast` 拋出錯誤並拒絕服務，絕不能「優雅降級」成假資料。

---

# 第三章：近期工作日誌 (Recent Activity Logs)

### 2026-11-25：Phase 5.15 Stage 1 (P1) Bot SSOT 收斂與 Stage 2 (P2) A2A 直接 Handoff + Telegram 雙向審批
1.  **P0 雲端唯讀探針與 Phase 5.14 補錄（`4b59ffa6`）**:
    *   補錄 2026-11-24 `4b59ffa6` 已完成 [Phase_5.14_Lead_Scoring_ABCX_and_G1_G3_G4_Hardening.md](file:///Users/vincenta/GoogleKwok022/Archon/PRPs/Phase_5.14_Lead_Scoring_ABCX_and_G1_G3_G4_Hardening.md)（A/B/C/X 評分、G1/G3/G4 結構化日誌、A:B=60:40 配額），且 `migration/20261118_revoke_truncate_and_test_rpcs.sql` 與 `migration/20261124_update_alice_lead_judge_abcx.sql` 皆已於雲端執行。
    *   確認 104 職缺抓取（`alice_auto_fetch`）維持只在本機執行，HF Space 跳過屬預期行為。
2.  **Bot SSOT/DRY 收斂與死碼退場 (Stage 1 / P1, `d98e43a3`)**:
    *   **UUID 對齊**：依雲端歷史工單真實分布（Supervisor `f0f00000` 106 筆），統一 Supervisor 為 `f0f00000-...`、將非法非十六進位 UUID `p0b00000-...` 全面修正為合法 `c0a00000-...`（POBot 歷史工單 0 筆）、補齊 Clockwork 至 `archon_agents`，已於雲端執行 `migration/20261125_align_bot_ssot_uuids.sql` 並經 P0 探針確認雙表 100% 一致。
    *   **死碼清理與營運成本精簡**：移除零使用死碼（`summary_agent.py`、`jules_compaction.py`、`workflow_engine.py` 與對應舊路由別名），並依營運成本考量整組退場 0 筆歷史工單之 `PresentationBot / PresentationAgent`。
    *   **Model SSOT & DRY**：`engine_beta_graph.py` 移除硬編碼模型名改讀 `model_ssot.py`；`agent_registry.py` 消除重複 `fallback_name_map`。
3.  **類 Grok Bot A2A 協作與 Telegram 雙向指令/審批 (Stage 2 / P2)**:
    *   **統一 Agent Card & A2A 直接 Handoff**：新增 `python/src/agents/workflow/a2a_handoff.py` 並接入 `nodes.py`，Worker 支援 `[HANDOFF: <target> | <reason>]` 白名單直接交棒（防自迴圈 + `max_steps` 熔斷），略過多餘的 `SupervisorNode` 轉發以節省 `gemini-3.6-flash` Free Tier RPD。
    *   **Checkpoint 斷點續跑**：將既有 `AgentCheckpointManager` 接入 `WorkflowEngine`（新增 `resume_from_checkpoint`），支援從 Supabase `agent_checkpoints` 還原 `SharedState` 並從斷點續跑。
    *   **Telegram 雙向指令與審批**：新增 `TelegramBotGateway`（`telegram_bot_gateway.py`）與 `POST /api/telegram/webhook`（`telegram_webhook_api.py`），實作 Fail-Closed `X-Telegram-Bot-Api-Secret-Token` 驗證、`chat_id` 白名單、`update_id` 冪等去重、`/task` / `@agent` / `/status`、Inline 審批按鈕喚醒 Checkpoint 續跑與 HF Space 休眠補拉 `poll_missed_updates()`。
4.  **Stage 2.5 閉環與反向驗證抓漏（`4f8fa9dc`, `ce66b78f`, `441f0bcf`）**:
    *   **線上真實探針揪出並修復 4 個關鍵樂觀路徑缺陷**：
        1. HF Space 防火牆擋直連 `api.telegram.org`（卡 32.35s）→ 全面改走 `TELEGRAM_PROXY_URL` 並回傳 `reply_sent`（降至 4.20s）。
        2. 實查 `enduser-ui-fe/api/telegram.js` 發現會剝離 `reply_markup` 且不支援 `answerCallbackQuery`/`getUpdates` → 升級 Vercel Proxy 白名單轉發並實測 `has_reply_markup_in_result=True`。
        3. 實查 `task_dispatcher.py` 只派發 `is_recurring=True` 工單 → 於 `TelegramBotGateway` 建單後立即非同步呼叫 `agent_service.run_agent_task`，並接通 `routes/workflow.py` 傳入 `AgentCheckpointManager()`、雲端執行 `migration/20261125_enable_a2a_handoff_prompts.sql`，實測 `/task` 轉 `done` 且 `agent_checkpoints` 寫入 `e7d1d7ab`（`COMPLETED`）。
        4. **反向驗證**送出不存在審批 ID callback 抓出線上有未捕獲 `ValueError` 炸 HTTP 500 → 改為優雅回應 `not_found`（防 Telegram 無限重試）；並清理 2 筆探針殘留 `todo` 工單，同步推送 `origin/dev/twins` 與 `origin/feat/twins`。
    *   **已知邊界（誠實註記）**：`telegram_bot_gateway.py` 接近 400 行上限，後續擴充須拆子模組；完整真機「高風險工具暫停 → 手機點按鈕 → Checkpoint 續跑」待真實寫入型 HITL 場景再做一次端對端確認。

### 2026-11-24：Phase 5.13 資安防提權、金鑰零中斷輪換、白名單排程與 Vercel 舊部署清理
完成 [Phase_5.13_Security_Key_Rotation_and_Crawler_Hardening.md](file:///Users/vincenta/GoogleKwok022/Archon/PRPs/Phase_5.13_Security_Key_Rotation_and_Crawler_Hardening.md)（Track A/B/C），並完成雲端 Supabase、Hugging Face Space 與 Vercel 基礎設施的零中斷金鑰輪換與舊部署清理。

**核心主題歸類**:
1.  **資安防提權與關閉開放註冊 (Track B)**:
    *   **後端修補**: 移除 `python/src/server/auth/dependencies.py`（`get_current_user`）與 `python/src/server/middleware/budget_guard.py` 對用戶可控 `user_metadata.role` 的信任；查無 `profiles` 時一律降級為 `"employee"`，並於 `test_x3_no_unverified_jwt_fallback.py` 新增 `test_user_metadata_role_cannot_escalate_to_admin` 回歸測試。
    *   **前端清理與後台關閉**: 移除 `enduser-ui-fe`（`AuthPage.tsx`、`useAuth.tsx`、`auth.ts`、`index.ts`、`AuthPage.test.tsx`）已失效的註冊切換 UI 與死端點呼叫，並於 Supabase Dashboard 關閉 Allow new users to sign up。
2.  **金鑰解耦與零中斷輪換 (Track A)**:
    *   **雙金鑰架構**: 於 `config.py`、`crypto_utils.py`、`manager.py` 引入獨立 `CREDENTIAL_ENCRYPTION_KEY` 與 `PREVIOUS_SUPABASE_SERVICE_KEY` 雙金鑰解密 fallback，且解密失敗時正確退回環境變數。
    *   **資料庫換鎖與升級**: 新增 `scripts/reencrypt_credentials.py` 將 `archon_settings` 內 4 把加密金鑰（`HF_TOKEN`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`）重加密至獨立金鑰；同步升級本機 `.venv` 至 `supabase==2.18.0`；將後端換為 `sb_secret_...`、Vercel `archon-enduser` 切換為 `sb_publishable_...`，並於 Supabase 停用舊版 JWT-based API keys 與舊 `default` secret key。HF Space `/health` 維持 200 Healthy（`ready: true`, `credentials_loaded: true`）。
3.  **白名單定期爬蟲排程與資料清理 (Track C & Ops)**:
    *   **白名單排程**: 新增 `python/src/server/services/scheduler/jobs/crawler_patrol.py` 並掛載至 `scheduler_service.py` 與 `SchedulerConfig`（`whitelist_crawler_patrol_hour=10`, `minute=15`），依 `is_active=True` 與 `update_frequency != 'manual'` 條件自動略過農民曆，僅定期抓取到期之 Google Gemini 2 頁官方文件。
    *   **資料與舊部署清理**: 清空雲端 Supabase `leads` 207 筆舊資料（`Remaining leads: 0`）待排程重抓；透過 Vercel CLI 批次刪除 160 筆歷史舊部署（`archon-enduser` 刪 78/78、`archon` 刪 82/82），各僅保留最新 1 筆線上 Production。
4.  **全門禁與測試公證**:
    *   `ruff check` 通過、`mypy src/` 397 檔 0 錯誤、`scripts/phase_audit.py` Step 5.5/7/8/9/10/11 全數通過、`enduser-ui-fe` `tsc --noEmit` 與 `AuthPage.test.tsx`（3/3）通過、`test_supabase_client_construction.py`（2/2）與後端單元測試（807 passed）通過，並完成提交推送 `ffb257ce` 至 `dev/twins`。

---

# 第四章：歷史檔案：原則的考古學 (Historical Archive: The Archaeology of Principles)

> **【封存說明】**
> 本章節存放了所有歷史日誌。當你需要深入了解某個特定問題的完整偵錯背景時，可以在此查閱最原始的紀錄。
> `2026年1月 ～ 10月` 歷史已轉化為 5 篇公開技術部落格（見 `migration/20261125_seed_ch4_engineering_blogs.sql` 與 `public.blog_posts`），原始紀錄可於 Git 歷史追溯。

## 2026年11月（自第三章封存整併）

### 2026-11-19：#670 升級驗證、金鑰輪替前置風險與 HyDE 重新評估（自 `pr669` 整併）
記錄 2026-11-19 的驗證結果與待決事項（均未部署、未在雲端執行任何變更）。

**核心主題歸類**:
1.  **#670 升級驗證**: 在本機把 PR #670（https://github.com/info-vin/Archon/pull/670）合進 `dev/twins`（`1f07df07`），沒有衝突。server、mcp、agents 與全部排程 job 都實際啟動過，Supabase 指向關閉的連接埠，沒有 mock `create_client`。升級前後行為一致，沒有出現 `TypeError` 或 `Invalid API key`。測試結果是 8 失敗、781 通過，失敗的 8 個與基準相同。
2.  **金鑰輪替前置風險（2026-11-24 已全數解除）**:
    *   **MCP 認證 / `auth/utils.py` 不驗簽 fallback**：已於 PR #671 修復並合入 `dev/twins`。
    *   **設定加密 (`crypto_utils.py`)**：已於 2026-11-24 Phase 5.13 引入獨立 `CREDENTIAL_ENCRYPTION_KEY` 並完成重加密與 `sb_secret_` 輪替。
    *   **`Dockerfile.twin`**：已於 `5f7d4b36` pin `supabase==2.18.0`。
3.  **HyDE 重新評估（DevBot 實驗，數字待人工標記校準，不對外引用）**: 現行 HyDE 基準與亂猜無法區分：合併 46 筆樣本 AUC 0.50（置換檢定 p≈0.98）。改用 ICP 文字當基準、再扣掉負向錨點，方向成立。λ 暫定 0.5（範圍 0.5–1.0）。B 類錨點不用於第一層。這批樣本與 ICP 文字高度重疊，不是獨立驗證。下一輪校準改用人工標記樣本，不再擴增 104 的爬取樣本。

### 2026-11-18：service_role 外洩鑑識、JWT 輪替回滾、ICP 60:40 配額與第二層 LLM 分類（自 `pr669` 整併）
記錄 2026-11-18 的決策：前端 `service_role` 外洩的根因與修復（PR #668，已合併）、Supabase Migrate JWT secret 後 Hugging Face 換用 `sb_secret` 啟動失敗並回滾、套件升級拆成 PR #670、人工標記與後續 PR 的閘門、ICP 排除規則與 A:B 配額、資料來源取捨，以及第二層評分改走 LLM 結構化分類。

**核心主題歸類**:
1.  **安全：前端 service_role 外洩、JWT 輪替回滾與 PR 拆分**:
    *   **外洩事件**: `service_role` 金鑰曾出現在 `archon-enduser.vercel.app` 的前端 JS。**原因**: `docker-compose.yml:256` 的 fallback 在 `SUPABASE_ANON_KEY` 未設定時，把 `service_role` 當成 `VITE_SUPABASE_ANON_KEY` 注入前端建置。**修復**: PR #668 已於 2026-11-18 squash 合併進 `dev/twins`（`1f07df07`）。
    *   **提醒**: `docker-compose.yml:256` 現在強制要求 `SUPABASE_ANON_KEY`，未設定時 compose 會失敗。`migration/20261118_revoke_truncate_and_test_rpcs.sql` 已於後續由 Vincent 在雲端 Supabase 執行完成。
    *   **JWT 輪替與 PR 拆分**: #668 只做安全修正，套件升級拆成 PR #670（`supabase` 2.15.1 → 2.18.0，並補上不 mock 的 smoke test）。後續輪替已於 2026-11-24 全數完成。
2.  **流程與紀錄：人工標記過渡、報告路由與後續 PR 閘門**:
    *   **人工標記先用試算表**: 人工標記先用試算表過渡兩週，不在 `leads` 加 `discarded` 狀態（避免與既有刪除路徑及至少 7 處未過濾 status 的查詢語意分叉）。
    *   **每日 leads 報告路由**: 每日 leads 報告送到 Vincent 與幕僚長（Charlie）的聊天。
    *   **G1 / G3 / G4 合成一個 PR**: G1（被刷掉的職缺結構化寫入）、G3（排程的開始與例外寫 log）、G4（judge 回傳拒絕理由）在 #668 合併後合成一個 PR，合併前問 Vincent。
3.  **市場與 ICP：排除邊界、配額、客單價與公司規模（待 Phase 5.14 實作）**:
    *   **C 類排除與 A/C 邊界**: C 類排除同業、SI、派遣、獵頭；自動化設備商算 C；研究機構與醫院算 A。
    *   **A:B 配額**: A:B = 60:40，採配額制，不直接乘進評分權重。
    *   **客單價與成交週期假設**: A 類 30–150 萬，B 類 10–50 萬（B 類先用轉介收費），成交週期 6 個月以上。
    *   **公司規模**: A 類 30–300 人，不設資本額上限；B 類規模待定（Alice 提案約 30 人以下）。
4.  **資料來源：開放資料替代、保留 104，以及指紋與 proxy 的事實修正**:
    *   **不申請商工登記 API 白名單**: 改用免費的政府開放資料 API。
    *   **保留 104 爬取**: 已知風險為 `robots.txt` 不允許 `/*keyword=*` 且 HF IP 被擋（近 30 天只成功 3 次）。
    *   **指紋偽裝與 proxy 事實修正**: 程式有 `curl_cffi` impersonate 指紋偽裝（每 session 隨機選一次），無輪替 proxy，僅有 `archon_settings` 可選之 `CRAWLER_PROXY_URL`。
5.  **評分：第二層改用 LLM 結構化分類**:
    *   **第二層分類與驗證門檻**: 第二層改用 LLM 結構化分類 A/B/C/X（附信心與理由），先用 ≥30 筆人工標記驗證（現行 HyDE 相似度區分力不足，AUC ≈ 0.50；LLM 呼叫次數推估約為現行 4 倍，待實測校準）。

### 2026-11-04：Telegram 失聯深度鑑識、HF 部署同步門禁硬化 (Step 5.5) 與 CI/CD 自動發佈復原
深度鑑識 11/04 Telegram 失聯事故，穿透實體日誌揭露 Hugging Face 因 `Dockerfile.server` 與 `deploy_to_hf.sh` 缺少 `GEMINI.md` 構建死鎖 3 天；實作 `scripts/phase_audit.py` Step 5.5 部署同步自動校驗門禁，釐清 GitHub Actions CI/CD 發佈鏈路，全線恢復雲端健康運作。

**核心主題歸類**:
1.  **Telegram 失聯穿透鑑識與根因破案 (Evidence First & Log Truth)**:
    *   **排程中斷真相**: 實體探針查詢 Supabase，`archon_tasks` 最後執行停在 `2026-11-01T08:18:05Z`，`archon_logs` 停在 `2026-11-02T03:55:05Z`，排程器已停擺整整 3 天。
    *   **Telegram 通路驗證**: 直接調用 `TelegramService` 直連發送測試訊息，回傳 `Result: True` 且使用者實體驗收，證明 Token、Vercel Proxy 與 Chat ID 完全正常無損。
    *   **HF 構建死鎖破案**: 鑑識 11/02 提交 `402ff3f9` 新增 `COPY GEMINI.md /app/GEMINI.md`，然而 `deploy_to_hf.sh` 漏掉了 `GEMINI.md` 的 checkout 與 `git add`，導致 HF 於 `2026-11-02T07:53:02Z` 構建失敗（`ERROR: "/GEMINI.md": not found`），Space 陷入 `BUILD_ERROR` 503 停機。
2.  **架構級雙向同步門禁硬化 (Step 5.5 & Pre-flight)**:
    *   **Step 5.5 自動化同步稽核**: 於 `scripts/phase_audit.py` 新增 `docker_deploy_sync_audit`，以正則動態解析 `Dockerfile.server` 所有 `COPY` 指令，強制比對 `scripts/deploy_to_hf.sh` 之 checkout 與 `git add` 清單；一旦有漏帶直接 `❌ VIOLATION` 並 Exit 1 阻斷。
    *   **Step 5 雲端故障紅燈阻斷**: 修正過去 `phase_audit.py` 遇 `BUILD_ERROR` 仍印出綠勾 `✅` 之假性通過漏洞，強制對非 RUNNING 狀態亮紅燈 `❌` 並穿透打印容器錯誤日誌。
    *   **部署 Pre-flight 物理斷言**: 於 `scripts/deploy_to_hf.sh` 構建提交前加入檔案存在迴圈校驗，未齊全前嚴禁推送。
3.  **CI/CD 發佈管線對帳與全鏈路復原**:
    *   **發佈權限對帳**: 鑑識本機環境與 Keychain 之 `HF_TOKEN` 僅為唯讀角色（`HF_RAG_API`, `role: read`），而具備 Write 權限之 `deploy-key` 實體存放於 GitHub Actions `secrets.HF_TOKEN`。
    *   **正規管線自動發佈**: 執行 `make merge-twins` 將修復合入 `dev/twins`，觸發 `.github/workflows/deploy-hf.yml`，成功上傳包含 `GEMINI.md` 與 `.agents/rules` 之完整上下文至 Hugging Face。
    *   **容器啟動公證**: HF Space 重新構建耗時約 3 分鐘成功轉為 `RUNNING`，實體穿透 `/health` 端點回傳 `200 Healthy`。
4.  **全門禁公證通過**:
    *   通過 `make lint-be`（395 檔 MyPy 100% 綠燈，0 錯誤）、`make test-be-fast`（**839 passed**, 11 skipped, 4 xfailed, 0 failed）與 `make phase-audit` 11 大門禁（Step 5.5 同步通過）。

### 2026-11-03：Jules 規則平移至 .agents/rules、agent_rules_compaction 重構與全門禁公證
因應 Google 官方宣布關閉 Jules 獨立服務，全量平移 `.jules/` 規則指南至通用 `.agents/rules/`，重構排程為 `agent_rules_compaction`，自癒 PR #666 遺留之規則超額與幻覺日期，並修復 `patrol_infra.py` 之 `NetworkConfig.huggingface_endpoint` SSOT 回退機制。

**核心主題歸類**:
1.  **規則庫通用平移與基礎設施拓樸對齊 (`.agents/rules/`)**:
    *   **規則檔案遷移**: 建立 `.agents/rules/` 並完整遷移 6 份規則指南（`bolt.md`, `contractor.md`, `palette.md`, `qa.md`, `reaper.md`, `type_guardian.md`），安全移除 legacy `.jules/`。
    *   **容器與建置拓樸同步**: 同步更新 `docker-compose.yml`（掛載 `./.agents/rules:/app/.agents/rules`）、`Dockerfile.server`（`COPY .agents/rules/ /app/.agents/rules/`）與 `scripts/deploy_to_hf.sh`（`git checkout -- .agents/rules/`）。
2.  **月度排程重構與向後相容墊片 (`agent_rules_compaction.py`)**:
    *   **排程服務重構**: 建立 `python/src/server/services/scheduler/jobs/agent_rules_compaction.py`，實作 `run_monthly_agent_rules_compaction`，支援自適應路徑解析（優先尋訪 `.agents/rules` 並相容 `.jules` 備援），在 `jules_compaction.py` 保留向後相容墊片（Shim）。
    *   **SSOT 設定與 API 路由對齊**: 於 `SchedulerConfig` 擴充 `monthly_agent_rules_compaction_*` 與 `agent_rules_max_entries_per_file`，透過 `model_validator` 雙向同步舊鍵名；同步於 `scheduler_service.py`、`admin_api.py` 與 `internal_api.py` 雙向註冊觸發端點。
3.  **PR #666 規則超限自癒與測試斷層修復 (Rule 1 & Rule 13)**:
    *   **`type_guardian.md` 規則壓縮自癒**: 識別遠端合入之 PR #666 引入幻覺日期前綴（`## 2026-04-16`）及規則數超限（6 條），外科手術式將學習要點融合至 Rule 1 與 Rule 5，降回 5 條核心規則。
    *   **`patrol_infra.py` SSOT 回退防禦**: 鑑識 PR #666 強化 `SettingsService` 型別防禦後，使得 `HUGGINGFACE_ENDPOINT` 在 DB 空值時回傳 `None` 觸發測試斷層；於 `NetworkConfig` 擴充 `huggingface_endpoint`（支援 `load_from_env`），在 `patrol_infra.py` 加入 SSOT 回退並提前導入 `SettingsService` 消除 BaseRepository 測試 Mock 碰撞。
4.  **全門禁公證通過**:
    *   通過 `make lint-fe`、`make lint-be`（395 檔 0 錯誤）、`make test-be-fast`（**839 passed**, 11 skipped, 4 xfailed, 0 failed）與 `make phase-audit` 11 大門禁（Step 11 驗證通過）。

### 2026-11-02：遠端分支三向衝突鑑識、四大角色週期作業 7 大斷層根除與 Token 預算閾值校準
針對遠端待審分支執行三向衝突鑑識與廢棄分支清理，並以實體探針直連雲端 Supabase 對 Alice、Bob、Charlie、David 四大角色之週期排程與工單產出物進行端到端穿透稽核，一舉根除 7 大潛伏斷層與虛假完成狀態，同時完成週預算閾值之真實數據校準。

**核心主題歸類**:
1.  **遠端 PR 驗收、5 大待審分支三向衝突鑑識與清理 (Ref: 11-02)**:
    *   **已合入 PR 驗收 (#658, #659, #661, #663)**: 驗證 `TaskAssignmentTab` `useMemo` 緩存、`auth_service` `UserProfileDictDTO` 陣列邊界防禦、`ProjectModal` WAI-ARIA 無障礙強化及 `CodeExamplesResponse` 搜尋合約對齊。
    *   **三向衝突鑑識與外科提取 (`git merge-tree`)**: 拒絕與 PR #663 發生 4 檔雙向衝突之重複分支 `7403...` 及 0 變更空提交分支 `1278...`；確認 `1124...` 已合入歷史；針對 `admin_service` (`a2b93b41`) 與 `ethics_service` (`ad800815`) 執行物理 Schema 對帳（確認 `archon_crawler_targets.target_url`）與無衝突代碼提取，並刪除遠端 5 條已廢棄分支。
    *   **Jules 規則門禁壓縮**: 壓縮 `.jules/*.md` 四大規則檔，移除日期標題並維持各檔 `<= 5` 條核心規則。

2.  **四大角色 (Alice, Bob, Charlie, David) 週期作業 7 大斷層清剿與 SSOT/DRY 治理 (Ref: 11-02)**:
    *   **排程共用工具收斂 (DRY)**: 新建 `python/src/server/services/scheduler/utils.py`，統一收斂 `resolve_project_root()`、`get_default_project_id()` 與 `normalize_agent_identity()`，拔除散落於 `architecture_patrol.py`、`tech_debt_patrol.py`、`leads_patrol.py`、`sentinel_patrol.py` 的重複私有函式。
    *   **Agent 身份雙模對齊與工單揀選修復**: 解決排程器寫入 UUID (`00000000-...`) 而 `WorkerService` / `AgentDispatcher` / `agent_registry` 僅匹配顯示名稱 (`Archon MarketBot` 等) 的斷層；在 `WorkerService` 展開雙向別名池查詢並廢除 `assignee="User"` 失敗轉嫁，改設 `status="failed"` 配合指數退避重試。
    *   **根除 `{"content": null}` 假完成報告**: 鑑識出 Gemini 回傳 `tool_calls` 時 `message.content` 為 `None`，舊 `DefaultLLMStrategy` 僅跑 1 輪 Tool 即把 `None` 寫入 `attachments.summary` 並標記 `done`。重構為最多 3 輪 Tool 呼叫迴圈，並在耗盡時注入 `tool_choice="none"` 強制最終文字收斂回合，同時攔截空字串標記為 `failed`。
    *   **Bob 市場戰報路由、狀態鎖與水位線防禦**: 擴充 `DailyMarketReportStrategy` 標題識別以攔截 `[Auto-Task] Daily Market Report` 進入真實 `MarketService` 管線；修復 `_trigger_stateful_daily_event` 未解構 `(bool, dict)` Tuple 及失敗時誤寫 `LAST_RUN_*` 水位線之漏洞；於 `update_logic.py` 將 `LAST_RUN_BOB_MARKET_REPORT` 移至 `status == "done"` 分支，確保失敗工單可於下次巡檢自動補跑。
    *   **David 工程回顧容器掛載與 SSOT 稽核對齊**: 於 `docker-compose.yml` 與 `Dockerfile.server` 補齊 `./GEMINI.md:/app/GEMINI.md:ro` 掛載，並在 `tech_debt_patrol.py` 新增雲端 `archon_tasks` 7 日紀錄 Fallback；同步更新 `run_ssot_audit` 支援 `# 合法` 豁免標記並將掃描範圍擴展至整個 `src/`。
    *   **Charlie 星環報告非同步競態修復**: 刪除 `report_service.py` 頂層幽靈 `asyncio.Lock()`，全面委派予 `SummaryTaskHelper` 之 Lazy Loop-Safe Lock。

3.  **Cost Sentinel 雲端 Token 遙測對帳與週預算閾值調升 (Ref: 11-02)**:
    *   **實體數據對帳**: 探針直連雲端 `token_usage` 統計近 7 日消耗為 `238,807 tokens / $0.1332 USD`（近 30 日 `789,163 tokens / $0.2325 USD`，日均約 `$0.019 USD`），證明舊設定 `WEEKLY_BUDGET_THRESHOLD = $0.05 USD` 嚴重偏低，導致每日巡檢皆觸發超標告警並額外消耗 7 次緊急語音 TTS 配額。
    *   **SSOT 與雲端同步調升**: 將 `settings.py` 之 `BudgetConfig.weekly_budget_threshold` 與雲端 Supabase `archon_settings.WEEKLY_BUDGET_THRESHOLD` 同步調升至 `$0.25 USD`（約正常週消耗之 1.8 倍安全水位），解除假性超標警報。

4.  **全系統品質門禁公證 (Ref: 11-02)**:
    *   **靜態、單元測試與階段稽核全綠**: 通過 `make lint`（前端雙專案、後端 394 檔 MyPy/Ruff 0 錯誤、Lean 4 18 jobs 通過）、`make test-be`（**839 passed**, 11 skipped, 4 xfailed, 0 failed）與 `make phase-audit` 11 大門禁。
