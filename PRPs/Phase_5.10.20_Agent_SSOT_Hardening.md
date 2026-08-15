# Phase 5.10.20: Agent SSOT Hardening & DRY Compliance

## 階段目標 (Phase Objective)
透過物理掃描與 AST 探測，我們發現在 `src/agents/workflow` 系列代碼中隱藏了大量硬編碼的魔術字串，這些字串並未納入 SSOT 管理，導致 `TaskFeatureEnum` 與 `PromptService` 等架構治理失效。本階段將徹底消除這些硬編碼，並建立對應的 SSOT Enum。

## 待修復的物理違規清單 (Physical Violations to Fix)

1. **`python/src/agents/workflow/nodes.py`**
   - 路由字串硬編碼: `task_type == "Marketing Data Deep Dive"`
   - Prompt Keys 魔術字串: `"WORKFLOW_SUPERVISOR_GENERAL"`, `"WORKFLOW_STRATEGIST_BOB"`, `"WORKFLOW_WORKER_MARKETBOT"`, `"WORKFLOW_WORKER_SUMMARY"`, `"WORKFLOW_SCIENTIST_DEVBOT"`, `"WORKFLOW_DATA_DAVID"`
   - 回退邏輯字串: `"General"`

2. **`python/src/agents/routes/workflow.py`** 與 **`python/src/agents/workflow/state.py`**
   - 寫死的預設任務型態: `task_type = "General"`

3. **`python/src/agents/workflow/engine_beta_graph.py`** (Map-Reduce 架構)
   - 寫死的 LLM 模型名稱: `"gemini-3.1-flash-lite"`
   - 寫死的所有 Agent System Prompts (包含 Alice, Bob, System Monitor, Supervisor 等)

4. **其他 Agent 檔案 (`rag_agent.py`, `summary_agent.py`, `nexus_oracle_agent.py`)**
   - 檔案層級直接將長篇大論的 System Prompt 寫死為常數字串，未能由 `PromptService` 及後台 DB 控制。

## 解決方案 (Proposed Solution)

### 1. 新增 SSOT Enum
於 `python/src/server/services/shared_constants.py` (或其他共用常數檔) 新增:
- `PromptNameEnum`: 集中管理所有系統中使用的 Prompt Keys。
- `WorkflowTypeEnum` (或擴充 `TaskFeatureEnum`): 納入 "General", "Daily Executive Summary", "Marketing Data Deep Dive" 供全域路由判斷。

### 2. 重構 Nodes 與 Routes
- 將所有的字串比對替換為 Enum 比對。
- 將預設參數 `"General"` 變更為 Enum 值。

### 3. 解耦 Prompt 與 Model
- 從 `engine_beta_graph.py` 與各 Agent 類別中移除硬編碼的 System Prompt，改由呼叫 `prompt_service.get_prompt(PromptNameEnum.XXX)` 來取得。
- 使用 `ModelSSOT` 獲取對應的模型名稱，而非寫死 `"gemini-3.1-flash-lite"`。

## 驗證計畫 (Verification Plan)
1. 執行 `make test-be` 確保單元測試與 Mock 不受影響。
2. 進行 `TaskFeatureEnum` 的實體路由測試，驗證 Group Chat 與 Map-Reduce 架構依然能順利派發任務。
