# Phase 5: Multi-Agent 與 MCP 強化架構評估 (LangGraph Evolution)

> **建立日期**: 2026-05-12
> **狀態**: 架構風險盤點與草案 (Draft)

在將目前的五大「無狀態、單點」Bots 升級為基於 LangGraph 的「有狀態、多節點協作」網路，以及對 MCP 進行動態掛載與拆分時，必須嚴肅面對以下五大「現實斷層」與技術債風險：

## 1. 依賴地獄與版本相容性 (Version Compatibility)

*   **當前狀態**: 我們底層的 Agent 引擎是 `PydanticAI`。
*   **斷層風險**: LangGraph 是 LangChain 生態系的核心組件。將 `LangGraph` (高度依賴 `langchain-core` 甚至舊版 `pydantic v1`) 與原生使用 `pydantic v2` 的 `PydanticAI` 強行揉合，極易引發「依賴解析地獄 (Dependency Hell)」與型別系統的衝突。
*   **實作對策 (防禦性架構)**:
    *   **不強求原生 LangGraph**: 若版本衝突過大，我們其實可以參考 LangGraph 的「StateGraph 概念」，自己在 `archon-agents` 用原生的 `asyncio` 與 `Pydantic` 刻一個輕量級的狀態流轉機（本質上就是帶有迴圈與狀態字典的異步函式），避免引入龐大的 LangChain 依賴包。
    *   **邊界隔離**: 若真要用 LangGraph，必須建立獨立的 `Dockerfile.langgraph` 微服務，透過 HTTP 呼叫現有的 `PydanticAI` Agents，而不是在同一個 Python 執行緒內混用。

## 2. GPT-4o 的可用性與推理成本 (Model Capability & Limits)

*   **當前狀態**: 系統支援多模型，並將模型配置寫入環境變數（如 `OPENAI_API_KEY`）與資料庫設定 (`archon_settings`)。
*   **斷層風險**:
    1.  LangGraph 的 Supervisor 節點負責「規劃任務」與「決定呼叫哪個 Bot」，這需要極強的 Context 處理與邏輯推理能力。若使用較弱的模型（如 Gemini Flash 或 Claude Haiku），極易引發「死循環」或「錯誤工具呼叫」。
    2.  GPT-4o 絕對可以使用，但它又貴又容易撞到 Rate Limits (429)。
*   **實作對策**:
    *   **異質模型策略**: 大腦 (Supervisor) 強制綁定 `GPT-4o` 或 `Claude 3.5 Sonnet`。而底層做苦工的 Worker (如 MarketBot 寫草稿) 則降級使用成本低的 `gpt-4o-mini` 或 `gemini-1.5-flash`。
    *   **Token 熔斷機制**: 必須將目前的 `TokenUsageTable` 邏輯與 LangGraph 綁定，單次 Graph 執行超過 20,000 tokens 必須強制熔斷 (Circuit Breaker)。

## 3. 反思迴圈次數 vs 模型額度 (Reflection Loop & Quota Limits)

*   **當前狀態**: DevBot 只有一次的 `try-catch` 修復，缺乏真正的 Reflection。
*   **斷層風險**: 導入 `Act -> Critic -> Act` 迴圈後，如果 Critic (LLM) 判斷修復失敗，它會再次呼叫 Act。在複雜的 Bug 中，LLM 很容易「鬼打牆」卡在同一個錯誤裡嘗試 50 次，瞬間把 API 額度燒光。
*   **實作對策 (硬體級限制)**:
    *   **Recursion Limit**: 在 Graph 設定中寫死 `recursion_limit=3`。
    *   **Human Fallback**: 當達到 3 次失敗，Graph 狀態標記為 `suspended`，並推播 Alert 給 Admin (Charlie)，要求人類進入 UI 介入。
    *   **狀態快取 (Checkpointer)**: 必須將每一步的對話存入 Supabase (`langgraph_checkpoints` 表)。若重啟或斷線，能接續上一次的 Token 繼續跑，而不是從頭再花一次錢。

## 4. MCP 動態掛載與拆分的斷層 (Dynamic MCP Federation Risks)

*   **當前狀態**: 我們有一個巨大的 `archon-mcp` (Port 8051)，裡面包山包海。
*   **您提出的盲點：拆分會不會有很多斷層？**
    *   **絕對會。而且非常痛苦。**
    *   **網路延遲**: 本來 HTTP 打 8051 就搞定，拆分成 5 個 MCP 後，服務發現 (Service Discovery) 會變得很複雜。
    *   **狀態不一致**: 如果 DB-MCP 寫入了資料，但 Git-MCP 尚未 Commit，交易 (Transaction) 如何回滾？MCP 協議本身並不支援分散式交易。
    *   **權限黑洞**: 拆分後，要如何在多個 MCP Server 之間傳遞 `User Context` 以進行 RBAC 驗證？
*   **實作對策 (務實演進)**:
    *   **拒絕物理拆分，採用邏輯拆分 (Logical Federation)**: 不要把 MCP 拆成多個 Docker Containers。維持單一的 `archon-mcp` 服務，但在內部進行重構。
    *   **Dynamic Tool Exposing (動態工具暴露)**: 修改 `mcp_client.py`，當前端或 Agent 發起連線時，必須帶上 `agent_type` 與 `user_role`。`archon-mcp` 內部會進行過濾，**動態組合**出一個「只包含該角色可用工具」的 Schema 回傳給 Agent。這達成了動態掛載的效果，又免去了分散式系統的災難。

## 5. 環境變數的傳播 (Environment Variables Management)

*   **斷層風險**: LangGraph 如果作為背景常駐進程 (Daemon)，它需要知道 Supabase 的金鑰來存取 Checkpoint，需要 OpenAI Key 來執行。在 Docker Compose 中，如果新增了服務，往往會漏掉 `.env` 的掛載。
*   **實作對策**:
    *   **統一的 Secrets API**: 不要依賴 `.env` 檔案在各個容器間複製貼上。利用現有的 `archon_settings` 表，由 `archon-server` 開放一個內部的 `/internal/credentials` 端點。
    *   當 LangGraph 服務啟動時，第一件事是去 `archon-server` 抓取所有需要的 Keys（這也是我們在 `agents/server.py` 中已經實作的 `fetch_credentials_from_server` 模式，必須將此模式沿用到 Graph 服務中）。
