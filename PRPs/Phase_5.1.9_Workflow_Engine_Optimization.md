# Phase 5.1.9: Workflow Engine Optimization (效能與成本收斂)

## Goal Description
隨著 Phase 5 星型群聊架構 (Star-Topology) 落地，`workflow_engine.py` 承載了所有多智能體協作的調度工作。為了準備迎接更高併發的商業場景，本階段旨在針對 Workflow Engine 進行「架構、效能、成本」三方面的深度優化。

本計畫包含前置的 L2 模組化分拆，以及四大核心優化任務。

## Current Status
* **[✅] 前置作業：L2 模組化分拆**
  - 將 400 行的 `workflow_engine.py` 分拆至 `python/src/agents/workflow/` 模組 (包含 `state.py`, `tools.py`, `utils.py`, `nodes.py`, `engine.py`)。
  - 保留 `workflow_engine.py` 作為 Facade 以確保 100% 向後兼容。
  - 已經過 `make lint-be` 與 `make test-be` 物理公證。

## Implementation Plan

### 1. 成本優化：對話歷史的滑動視窗 (Context Pruning)
* **問題**: 目前每次 Agent 執行都會將 `ctx.state.messages` 全部串接，導致在長對話 (例如 Step > 5) 時 Input Token 呈指數爆炸。
* **解法**: 在 `utils.py` 實作 `_build_pruned_history` 輔助函式。
  - **策略**: 保留 `messages[0]` (使用者的原始請求 / Ground Truth)，並只擷取最近的 `N` 筆紀錄 (例如 `N=6`)。
  - **預期效益**: 確保 Input Token 消耗被收斂在常數範圍，降低 API Cost 並避免觸發 Rate Limit。

### 2. 效能優化：遙測數據非同步化 (Fire-and-Forget Telemetry)
* **問題**: `WorkflowEngine.run_workflow` 在回傳最終結果前，會使用 `await client.post(...)` 同步等待 Token 紀錄寫入資料庫，阻塞了使用者的等待時間 (約 50~200ms)。
* **解法**: 
  - 引入 `asyncio.create_task()`，將 Token 使用量寫入的 API 請求包裝為背景任務 (Background Task)。
  - **預期效益**: 提升 API 的回應速度 (Latency)，改善前端 UX。

### 3. 路由優化：靜態短路機制 (Hard-coded Fast Paths)
* **問題**: Supervisor 節點在每次轉移時都會被呼叫，即使是高度確定性的流程 (例如 `SummaryNode` 執行完通常就結束了)。
* **解法**: 
  - 在特定的 Worker Node 中 (例如 `SummaryNode` 或 `MarketBotNode` 的某些場景)，可以直接回傳 `End(result)` 而非 `SupervisorNode()`。
  - **預期效益**: 每省下一次不必要的 Supervisor 思考，就省下一次 LLM 呼叫的成本與時間 (約 1~2 秒)。

### 4. 架構優化 (Optional/Future)：非同步並發執行 (Fan-out / Parallel Execution)
* **問題**: 目前星型拓撲是絕對串行的。
* **解法探索**: 
  - 擴充 `SupervisorDecision.next_node` 支援回傳 `list[str]` (例如 `["librarian", "david"]`)。
  - 修改圖形引擎層邏輯，利用 `asyncio.gather` 並發觸發多個 Agent，再由 Supervisor 進行 Map-Reduce。
  - *(註：此項目變動範圍較大，將視系統複雜度決定是否在此 Phase 實作或遞延)*

## Definition of Done (DoD)
1. **Context Pruning**: 系統可以順利執行超過 10 步的工作流，且 Input Token 用量不再隨著 Step 數線性暴增。
2. **Fire-and-Forget**: Token 日誌能正確寫入 `archon_logs` 或 `token_usage`，且前端收到 Workflow 完成的延遲降低。
3. **QA Pass**: `make lint`, `make test-be`, `make persona-audit` 全部通過，確保重構沒有破壞既有功能。
