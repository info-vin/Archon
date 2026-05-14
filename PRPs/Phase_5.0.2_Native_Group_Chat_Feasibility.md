# Phase 5.0.2: Native Group Chat UI 可行性深度調查與實作計畫 (Feasibility Study & Implementation Plan)

> **調查日期**: 2026-05-14
> **負責人**: David (IT Architect)
> **狀態**: 前置調查完畢，準備執行

## 🚨 核心問題：我們真的能用幾十行 Code 做出群聊嗎？

基於 2026-05-14 的深度代碼掃描 (Codebase Audit)，我們發現了一個嚴重的「系統斷層 (System Disconnect)」。如果我們現在貿然在前端加「幾十行 React Code」，它是不會動的。我們不能基於幻想 (Optimistic Path) 來設計系統。

以下是物理掃描發現的三大現實斷層：

### 斷層一：後端引擎未橋接 (The Backend Disconnect)
*   **物理現狀**: 在 Phase 5.2/5.3 開發的 `WorkflowEngine` (星型群聊引擎) 雖然完美運作，但它被隔離在 `archon-agents` 容器中 (Port 8052)，目前的唯一入口是 `POST /agents/workflow/run`。
*   **問題點**: 當前端 UI (Charlie) 把工單 (Task) 指派給 Agent 時，觸發的是 `archon-server` 的 `AgentService._run_general_agent_task`。**這個舊函式仍然使用 Phase 4.6 的單次 LLM 呼叫 (`client.chat.completions.create`)**，它「完全沒有」呼叫到我們辛苦寫好的 `WorkflowEngine`！
*   **結論**: 星型群聊目前只活在 Integration Tests 裡，根本沒有被真正的業務流程 (Sales/Manager/Marketing) 使用。

### 斷層二：資料庫結構不相容 (The Database Schema Disconnect)
*   **物理現狀**: 目前的 `archon_tasks` 表，用來儲存 Agent 執行結果的欄位是 `agent_output (JSONB)`。
*   **問題點**: `AgentService.save_agent_output` 目前只寫入最終的字串：`{"content": final_output}`。它並沒有將 `WorkflowEngine` 產生的對話陣列 (`messages: [{role: "supervisor", content: "..."}, ...]`) 寫入資料庫。如果資料沒存下來，Charlie 重整網頁後群聊紀錄就會消失。

### 斷層三：前端缺乏即時通訊機制 (The Frontend UI Disconnect)
*   **物理現狀**: 掃描 `enduser-ui-fe/src/components/task-modal/TaskAIAgentReport.tsx` 發現，前端目前只是用一個 `<div className="font-mono">` 來顯示靜態的 JSON 或字串。
*   **問題點**: 前端沒有 WebSocket 或 Server-Sent Events (SSE) 機制來實現「即時打字推播」。要嘛只能等 2-3 分鐘工作流跑完才一次顯示，要嘛就必須實作 polling。

---

## 🛠️ 實作里程碑與工作清單 (Execution Milestones)

為了讓 Charlie 能在前端看到 Supervisor, Librarian, MarketBot 等機器人熱烈討論的畫面，並支援行銷數據分析等動態場景，David 必須依序執行以下實作計畫：

### Milestone 0: 基礎設施與配置準備 (Infrastructure & Configuration)
目標：確保環境變數、Docker 網路與資料庫就緒，無需新增額外套件 (pnpm/uv)。
- [ ] **任務 5.0.2.0.1 (Docker & Env)**: 修改 `docker-compose.yml`，在 `archon-server` 服務中注入 `AGENTS_SERVICE_URL=${AGENTS_SERVICE_URL:-http://archon-agents:${ARCHON_AGENTS_PORT:-8052}}` 環境變數，避免在 Python 中硬編碼 IP。
- [ ] **任務 5.0.2.0.2 (Supabase Migration)**: 在 `migration/0.2.2/` 下建立新的 SQL 遷移檔 (例如 `19_seed_marketing_group_chat_prompts.sql`)，透過 SQL 將群聊的 4 個角色 Prompt (`WORKFLOW_SUPERVISOR_MARKETING` 等) 寫入 `archon_prompts` 表中。
- [ ] **任務 5.0.2.0.3 (Dependencies)**: 經評估，本階段無需修改 `pyproject.toml` (uv) 或 `package.json` (pnpm)，現有 `httpx` (Python) 與 Tailwind/React (前端) 已滿足需求。

### Milestone 1: 橋接主伺服器與智能體微服務 (Backend Wiring)
目標：打通 `archon-server` 與 `archon-agents` 的網路斷層。
- [ ] **任務 5.0.2.1**: 修改 `python/src/server/services/agent_service.py` 中的 `_run_general_agent_task`。當 `agent_id` 指向 Supervisor 時，停止呼叫本機的 `get_llm_client()`。
- [ ] **任務 5.0.2.2**: 改為透過 `httpx.post("http://archon-agents:8052/agents/workflow/run")` 將前端的 Prompt 與 `task_type` 傳遞給 WorkflowEngine。
- [ ] **任務 5.0.2.3**: 接收並解析 WorkflowEngine 回傳的 JSON (必須包含 `messages` 陣列與 `step_count`)。

### Milestone 2: 擴充資料庫 Schema (Database Persistence)
目標：確保群聊過程與多智能體對話紀錄不遺失。
- [ ] **任務 5.0.2.4**: 更新 `task_service.py` 中的 `save_agent_output` 邏輯。
- [ ] **任務 5.0.2.5**: 確保寫入 `archon_tasks.agent_output` 的 JSONB 結構包含完整的 `messages` 陣列（`[{role: "...", content: "..."}]`），而不僅僅是最終字串。

### Milestone 3: 前端群聊渲染器實作 (Frontend ChatRoom UI)
目標：把冰冷的 JSONB 變成 WhatsApp/Slack 風格的群聊介面。
- [ ] **任務 5.0.2.6**: 在 `enduser-ui-fe` 新增 `TaskAgentGroupChat.tsx` 元件以取代原本純文字的 `TaskAIAgentReport`。
- [ ] **任務 5.0.2.7**: 實作 `ROLE_CONFIG` (為不同角色如 Librarian 📚, MarketBot ✍️ 等設定大頭貼、名稱與泡泡顏色)。
- [ ] **任務 5.0.2.8**: 透過 `map` 將 `task.agent_output.messages` 渲染成左/右對齊的對話泡泡。

### Milestone 4: 動態 Prompt 治理與多場景路由 (Prompt Governance & Dynamic Routing)
目標：解決「多智能體群聊」場景的 Prompt 硬編碼問題，支援新場景擴充。
- [ ] **任務 5.0.2.9**: **Prompt 實體隔離**: 移除 `workflow_engine.py` 內所有硬編碼的 System Prompt。
- [ ] **任務 5.0.2.10**: **資料庫治理**: 將「行銷數據分析」所需的 4 個角色 Prompt (`WORKFLOW_SUPERVISOR_MARKETING`, `WORKFLOW_DATA_DAVID`, `WORKFLOW_SCIENTIST_DEVBOT`, `WORKFLOW_STRATEGIST_BOB`) 寫入 `archon_prompts` 資料庫。
- [ ] **任務 5.0.2.11**: **情境動態注入**: 當 `archon-server` 呼叫 WorkflowEngine 時，傳遞 `task_type`。WorkflowEngine 根據類型動態向 `PromptService` 拉取對應的 System Prompts 並注入給 Agent Nodes。

### Milestone 5: 體驗優化 (Streaming UI - 進階選項)
目標：提供即時打字體驗。
- [ ] **任務 5.0.2.12**: (Optional) 實作 `StreamingResponse` 或 Server-Sent Events (SSE)，讓前端能在工作流執行期間即時渲染 Agent 的對話過程。

---

## 🚫 歷史教訓與防禦性開發 (Anti-Patterns & Defensive Development)

根據過去兩個月 Git Log 的除錯紀錄，我們在實作上述 Milestone 時，**絕對不可**犯下以下曾經發生過的架構錯誤（拒絕樂觀路徑）：

1. **React 渲染死鎖 (Rendering Deadlocks)**
   - **歷史罪證**: Commit `aae75a1` (Cost & Usage tab rendering deadlock) 與 `2dae433` (Admin HUD loading deadlocks)。
   - **防禦要求**: 在實作 Milestone 3 (`TaskAgentGroupChat.tsx`) 時，因為 `agent_output.messages` 是一個深層巢狀的 JSON Array，**絕對禁止**將這個 Array 直接放入 `useEffect` 的 Dependency 陣列中，這會引發 React 無限重新渲染的死鎖 (Infinite Loop)。必須使用 `useMemo` 或透過基礎型別 (Primitive properties) 來觸發更新。

2. **跨容器通訊超時與解析失敗 (Inter-Container Timeout & Network Errors)**
   - **歷史罪證**: Commit `551a763` (test: increase timeout... for multi-agent workflow) 與 `bd7c102` (URL parsing network error)。
   - **防禦要求**: 在實作 Milestone 1 (`httpx.post` 呼叫 8052 port) 時，不可樂觀以為 API 會在 1 秒內回傳。LLM 群聊可能耗時數十秒。**必須顯式設定超時時間** (`timeout=300.0`)，且必須包裝 `try-except httpx.RequestError` 以防止前端收到無意義的 500 Error。

3. **Supabase `.single()` 空狀態崩潰 (PGRST116 Error)**
   - **歷史罪證**: 記錄於 `GEMINI.md` 的「資料庫空狀態防禦」教訓。
   - **防禦要求**: 在實作 Milestone 2 (寫入 JSONB) 時，若需先讀取 Task 狀態，**絕對禁止**使用 `supabase.table().select().single().execute()`。若資料庫出現同步延遲，`.single()` 會直接引發 HTTP 500。必須使用陣列查詢 `.execute()` 並檢查 `len(res.data) > 0`。

4. **型別撕裂與隱性 Crash (MyPy / Typing Errors)**
   - **歷史罪證**: Commit `c1bd77f` (resolve mypy type error) 與 `60220b3` (extraction API crash)。
   - **防禦要求**: 在 Python 處理 JSON 欄位擴充 (`messages` 陣列) 時，必須使用嚴格的 `dict.get("messages", [])` 與 `cast` 轉型，否則 `make lint-be` 將會在 CI/CD 階段阻擋部署。

---

## 結論與決策

回到你的問題：**「要如何開發新的群聊？都是要寫新的代碼？」**

是的。經過物理驗證，我們不能樂觀地以為只要改個 UI 就好。**我們必須先完成「斷層一」的 Backend Wiring，讓真實的業務 Task 能夠打通到 8052 Port 的 `WorkflowEngine`**，前端的群聊介面才有資料可以渲染。

如果你們的團隊（特別是 David）希望保持 100% 的程式碼掌控權，且不想每個月付錢給 SaaS 服務，照著上述的 Step 1~3 去寫 Code 是唯一的、且最符合企業架構安全的落地路徑。