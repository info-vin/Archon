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
*   **當前狀態 (Current Context)**: 2026-11-26 完成 `gemini-decision-1`（Decisions API）整合與 Phase 5.14 39 筆樣本 ICP 校準收斂（`a4d72e1c`～`9ebf8ccf`），修復 104 爬蟲 Cloudflare/Referer/403 與 `hf-restart.yml` 語法，並完成 Monolith 大型檔案拆解（`5b03df10`：`rag-settings/index.tsx` 427→324 行、`telegram_bot_gateway.py` 399→194 行拆出 `telegram_proxy_client.py` + `telegram_command_handlers.py`，`phase_audit.py` 紅燈歸 0）；同步完成 PR #672（`fix/671-followups-auth-hardening`）審查（`MERGEABLE`）。
*   **今日目標 (Today's Goal)**: 由使用者拍板合併 PR #672 至 `dev/twins`（合併即觸發 HF 部署）；觀察線上 Decisions API 評分與 Telegram 雙向指令運作。

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

### 2026-11-26：Decisions API 整合、Phase 5.14 校準收尾、Monolith 拆解與 PR #672 審查
1.  **Decisions API 整合與 104 爬蟲修復（`a4d72e1c`～`9ebf8ccf`）**:
    *   整合 `gemini-decision-1` 並以 SSOT/DRY Fallback 接通潛在客戶篩選（`CrawlerJobConfig.qualify_score_threshold` 預設 50）與 Supervisor 路由；修正 `NetworkConfig.google_base_url` OpenAI 後綴截斷與 `hf-restart.yml` 無效 `secrets` 條件。
    *   修正 104 爬蟲 Cloudflare CORS/`Sec-Fetch` 標頭、Referer 非 ASCII 編碼與 HTTP 403 阻斷偵測，並依 39 筆樣本人工校準收斂 `ALICE_LEAD_ICP_CRITERIA` 完成 Phase 5.14。
2.  **Monolith 大型檔案拆解與門禁歸零（`5b03df10`）**:
    *   **前端 P0**：`archon-ui-main/src/features/rag-settings/index.tsx`（427 → 324 行）拆出 `RagCheckboxes.tsx`、`OllamaConfigPanel.tsx`、`AdvancedSettingsAccordion.tsx`、`RagModalsContainer.tsx`；通過 `biome check`、`tsc --noEmit`、`vite build` 與 `vitest`（17 檔 / 144 passed）。
    *   **後端 P1**：`python/src/server/services/system/telegram_bot_gateway.py`（399 → 194 行）拆出 `telegram_proxy_client.py`（116 行）與 `telegram_command_handlers.py`（189 行），拔除硬編碼 `_MENTION_AGENT_MAP` 改由 `AI_AGENT_ROLES` SSOT 動態推導，並保留 Facade 委派與 `http_client_cls` 注入；通過 `ruff`、`mypy`、`pytest`（7/7）與 `phase_audit.py`（`Found 0 monoliths (>400 lines)`）。
    *   **Code Review 修正**：將 `ModelConfigForm.tsx` 既有動態 Tailwind 字串插值（`bg-${...}`）改為靜態類別查表 `OLLAMA_STATUS_CARD_STYLES`，完全對齊 `UI_STANDARDS.md`。
3.  **PR #672（`fix/671-followups-auth-hardening`）審查**:
    *   確認補齊 `useAuth.tsx` `TOKEN_REFRESHED` / `SIGNED_OUT` 清快取、`POST /api/tasks/{id}/agent-status` 與 `agent-output` 驗證（納入 internal token 放行清單）、`GET /api/mcp-logs` 限 `get_current_admin`、以及錯誤訊息隱藏 `assignee`。
    *   狀態為 `OPEN` / `MERGEABLE`（`CLEAN`），3 項 Vercel checks 通過；因該分支基於較舊的 `3ead4318`，其 PR 描述提及的 `user_metadata.role` 提權已於 `dev/twins`（Phase 5.13）先修完，且 `useAuth.test.tsx` 多 mock 了已移除的 `register`（不影響執行）。

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

### 2026年11月：資安防護加固、規則通用遷移、HF 部署門禁與四大角色排程收斂
十一月份完成了前端 `service_role` 外洩鑑識與 `supabase` 套件升級驗證、`.jules/` 規則全量平移至 `.agents/rules/`、HF 部署漏檔門禁（Step 5.5）與 3 天停機復原，並透過雲端探針根除四大角色週期作業 7 大斷層與校準週預算閾值。

**核心主題歸類**:
1.  **資安外洩鑑識、#670 升級驗證與金鑰輪替前置準備 (Ref: 11-18, 11-19)**:
    *   **`service_role` 外洩修復**: 鑑識 `docker-compose.yml:256` fallback 在未設 `SUPABASE_ANON_KEY` 時將 `service_role` 注入前端建置；PR #668 合併修復並強制要求 `SUPABASE_ANON_KEY`，同時於雲端執行 `migration/20261118_revoke_truncate_and_test_rpcs.sql`。
    *   **#670 升級與前置風險解除**: 合入 PR #670（`supabase` `2.15.1 → 2.18.0`），781 passed / 8 failed 與基準一致；MCP 認證 / `auth/utils.py` 不驗簽 fallback 於 PR #671 修復，設定加密與 `Dockerfile.twin` pin 於後續 Phase 5.13 全數解除。
2.  **104 商業漏斗、ICP 配額與 HyDE / LLM 分類校準 (Ref: 11-18, 11-19)**:
    *   **ICP 與配額決策**: 確立 C 類排除同業/SI/派遣/獵頭/自動化設備商（研究機構與醫院算 A）、A:B = 60:40 配額制、開放資料替代商工登記 API、保留 `curl_cffi` 指紋偽裝並註記 104 風險。
    *   **評分校準**: 實測現行 HyDE 基準 46 筆樣本 AUC 0.50（p≈0.98），改用第二層 LLM 結構化 A/B/C/X 分類並待 ≥30 筆人工標記驗證；G1/G3/G4 合成 PR 推進至 Phase 5.14。
3.  **Telegram 失聯鑑識、HF 部署同步門禁 (Step 5.5) 與 CI/CD 復原 (Ref: 11-04)**:
    *   **構建死鎖破案**: 穿透日誌確認 `11/02` 提交新增 `COPY GEMINI.md` 卻漏改 `deploy_to_hf.sh`，導致 HF 陷入 `BUILD_ERROR` 停擺 3 天。
    *   **Step 5.5 同步稽核與復原**: 於 `scripts/phase_audit.py` 新增 `docker_deploy_sync_audit` 正則比對 `Dockerfile.server` 與打包清單、Step 5 非 RUNNING 強制亮紅燈，並經 GitHub Actions `deploy-hf.yml` 復原 `/health` `200 Healthy`。
4.  **規則庫通用遷移與 `agent_rules_compaction` 重構 (Ref: 11-03)**:
    *   **`.agents/rules/` 平移**: 因應 Jules 服務關閉，將 6 份規則遷移至 `.agents/rules/` 並同步 `docker-compose.yml`、`Dockerfile.server`、`deploy_to_hf.sh`，壓縮 PR #666 超限規則回 `<= 5` 條；補齊 `NetworkConfig.huggingface_endpoint` 回退。
5.  **四大角色週期作業 7 大斷層根除與 Token 週預算校準 (Ref: 11-02)**:
    *   **PR 驗收與分支清理**: 驗收 #658/#659/#661/#663，外科提取 `admin_service` / `ethics_service` 並刪除 5 條廢棄分支。
    *   **DRY 與 7 大斷層修復**: 收斂 `scheduler/utils.py`、修復 UUID/名稱雙模對齊與 `{"content": null}` 假完成（3 輪 Tool + `tool_choice="none"`）、修正 `LAST_RUN_BOB_MARKET_REPORT` 水位線與 `report_service.py` Lock 競態。
    *   **週預算校準**: 實測雲端 `token_usage` 7 日消耗 `238,807 tokens / $0.1332 USD`（30 日 `$0.2325 USD`），將 `WEEKLY_BUDGET_THRESHOLD` 自 `$0.05` 調升至 `$0.25 USD`，全門禁 839 passed 通過。
