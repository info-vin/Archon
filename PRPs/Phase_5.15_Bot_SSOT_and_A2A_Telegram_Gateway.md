# Phase 5.15: Bot SSOT 收斂（P1）、類 Grok Bot A2A 協作與 Telegram 雙向閉環（P2 / P2.5）(PRP)

## 1. 背景與目標 (Background & Objectives)

依據 2026-11-25 P0 雲端唯讀物理探針與 Git 歷史盤點：
* **問題根因**：
  1. 雲端 `archon_agents`、`profiles`、`shared_constants.py` 與前端 UI 各自維護 Bot 清單，造成 Supervisor UUID 分裂（`d0e0` vs `f0f0`）、POBot 含非法非十六進位 UUID（`p0b00000`），且留有零使用死碼與 0 筆歷史工單、高營運維護成本的 `PresentationBot`。
  2. `WorkflowEngine` 為星型中心轉發（每次 Worker 結束強制回傳 `SupervisorNode` 燒 `gemini-3.6-flash` RPD），且 Phase 5.9.13 既有的 `agent_checkpoints` / `AgentCheckpointManager` 尚未接線。
  3. `TelegramService` 僅為單向廣播，且經實查 [enduser-ui-fe/api/telegram.js](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/api/telegram.js#L25-L62) 確認線上 Vercel Proxy 會靜默剝離 `reply_markup`（Inline 審批按鈕），亦不支援 `answerCallbackQuery` / `getUpdates`。
* **既定邊界（Out of Scope）**：
  * 104 職缺抓取（`alice_auto_fetch`）維持只在本機執行，不更動 `scheduler_service.py` 在 HF Space 跳過的設計。

---

## 2. 階段拆解與狀態總覽

### Stage 1（P1）：Bot SSOT / DRY 收斂與死碼退場（✅ 已完成 `d98e43a3`）
- [x] 以雲端真實工單分布對齊 UUID（Supervisor=`f0f00000-...` 保留 106 筆工單；POBot 修正為合法 `c0a00000-...`；Clockwork 補進 `archon_agents`），產出並於雲端執行 `migration/20261125_align_bot_ssot_uuids.sql`（重跑 P0 探針確認雙表 100% 一致）。
- [x] 移除零使用死碼（`summary_agent.py`、`jules_compaction.py`、`workflow_engine.py`），並依營運成本考量整組退場 `PresentationBot / PresentationAgent`。
- [x] `engine_beta_graph.py` 改走 `model_ssot.py`、`agent_registry.py` 消除重複 `fallback_name_map`。
- [x] 補錄 `GEMINI.md` Phase 5.14 紀錄，清理本地 `pr669` 並快轉對齊 `feat/twins`。

### Stage 2（P2）：A2A 協作骨架與 Telegram 雙向基礎（✅ 已完成 `e2398444` / `4f8fa9dc`）
- [x] 新增 `python/src/agents/workflow/a2a_handoff.py`（統一 `AgentCard`、從 `agent_registry.py` 動態推導 `model_tier` 與 write 工具、實作 `[HANDOFF: <target> | <reason>]` 白名單直通交棒、防自迴圈與 `max_steps` 熔斷）並接入 `nodes.py`。
- [x] 接線既有 `AgentCheckpointManager` 至 `WorkflowEngine`，新增 `resume_from_checkpoint(conversation_id)` 與 `WorkflowStatusEnum` SSOT。
- [x] 新增 `TelegramBotGateway`（`telegram_bot_gateway.py`）與 `POST /api/telegram/webhook`、`POST /api/telegram/poll-missed`（`telegram_webhook_api.py`），含 Fail-Closed 403 密鑰驗證、`chat_id` 白名單、`update_id` 冪等去重、`TELEGRAM_PROXY_URL` 路由與 `reply_sent` 回傳。
- [x] 實測線上 HF Space `/api/telegram/webhook` `/status` 4.20s 回覆並送達手機（`reply_sent: True`）。

### Stage 2.5（P2 閉環收尾 — 待核准執行）
1. **升級 Vercel Telegram Proxy（[enduser-ui-fe/api/telegram.js](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/api/telegram.js)）與統一 `TelegramBotGateway` 代理路由**：
   - 讓 `api/telegram.js` 支援轉發 `reply_markup`（Inline 審批按鈕）及白名單方法（`sendMessage`、`answerCallbackQuery`、`getUpdates`），並維持既有 `sendMessage` / `sendVoice` 100% 向後相容。
   - 讓 `telegram_bot_gateway.py` 的 `sendMessage`、`answerCallbackQuery`、`getUpdates` 在設定 `TELEGRAM_PROXY_URL` 時全數走 Proxy，徹底解決 HF Space 30 秒防火牆超時。
2. **生產路徑接通 `AgentCheckpointManager`**：
   - 於 `routes/workflow.py` 與 `agent_service.py` 呼叫 `WorkflowEngine.run_workflow()` 時實際傳入 `AgentCheckpointManager()`（`conversation_id=task_id`），讓線上多代理執行真實寫入 `agent_checkpoints`。
3. **線上 Worker Prompt 啟用 A2A `[HANDOFF: ...]` 協議**：
   - 更新 `pm_prompts.py` 並產出冪等 SQL Migration `migration/20261125_enable_a2a_handoff_prompts.sql`，在一般協作 Worker Prompt 補上可選 `[HANDOFF: <target> | <reason>]` 交棒指導語（不干擾 Daily Summary 既有順序）。
4. **`[Telegram]` 工單完工自動回報**：
   - 於 `agent_service.py` 與 `dispatcher.py`（`DefaultLLMStrategy`）工單完成或失敗時，若標題以 `[Telegram]` 開頭（且非 Daily Summary），自動透過 `telegram_service.send_message` 回推結果摘要到手機。
5. **HF Space 喚醒自動觸發補拉**：
   - 於 `.github/workflows/hf-restart.yml` 喚醒 Space 後等待 `/health` 就緒並呼叫 `POST /api/telegram/poll-missed`（non-fatal，避免冷啟動阻斷主流程）。
6. **切分 3 尾項 — 前端角色顯示名 SSOT 對齊**：
   - 同步 `enduser-ui-fe/src/components/task-modal/TaskAgentGroupChat.tsx` 與 `TaskAgentGroupChat.test.tsx` 為 `MarketBot (Sales)`、`DevBot (Engineering)`（嚴守 `UI_STANDARDS.md` 靜態 Tailwind v4 類別規範，不動捲動與 DOM 結構）。

---

## 3. 驗收標準與實體物理探針（零虛假驗證）

### 本機與自動化門禁
- [x] `make lint`（Exit 0：前後端 + `check-no-single` + Ruff + MyPy 395 檔 0 錯誤 + Lean 4 18 jobs）
- [x] 後端 P2 / Stage 2.5 單元測試（`18 passed, 0 failed`，含 Proxy 轉發、生產 Checkpoint 接線、`[Telegram]` 完工回推測試）
- [x] `enduser-ui-fe` `TaskAgentGroupChat.test.tsx`（3/3 passed；全套 76/78 passed，僅既有 `ThemeToggle.test.tsx` 受本機 Node `--localstorage-file` 環境旗標影響）
- [x] `python/.venv/bin/python scripts/phase_audit.py`（Exit 0，Step 5.5/6/7/8/9/10/11 全數通過，0 違規）

### 雲端真實物理探針（部署至 Vercel + HF Space 後執行）
- [x] **探針 1（Inline 審批按鈕實測）**：透過升級後的 `archon-enduser.vercel.app/api/telegram` 送出帶 `inline_keyboard` 之測試卡，Telegram API 回傳 `ok=True` 且 `has_reply_markup_in_result=True`。
- [x] **探針 3a（`@librarian` Webhook 建單與回覆）**：透過 HF Space Webhook 送出 `@librarian` 指令，5.11s 回傳 HTTP 200、`reply_sent=True`，雲端 `archon_tasks` 真實寫入 `f4cb77fe-77bb-4e32-b63a-01d4cfbd02ad`（`assignee_id=b0b00000-...`），待 `task_dispatcher` 執行完工自動回推。
- [ ] **探針 2（Checkpoint 實體寫入）**：待透過 `/task`（指派 Supervisor 進 `WorkflowEngine`）觸發一次線上多代理執行後，查雲端 `agent_checkpoints` 表確認新增紀錄（目前 `count=0`）。
