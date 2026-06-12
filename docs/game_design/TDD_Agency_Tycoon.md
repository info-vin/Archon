# Technical Design Document (TDD): Archon Agency Tycoon

```text
=============================================================================
                  Archon: Agency Tycoon (Godot 4.x)
                         Core Event & Node Architecture
=============================================================================

 [ AUTOLOADS (Global) ]
 -----------------------------------------------------------
 | TycoonManager.gd     |        SignalBus.gd              |
 | - company_funds      |<------ [task_completed]          |
 | - reputation         |<------ [agent_deployed]          |
 | - active_crises      |<------ [crisis_spawned]          |
 -----------------------------------------------------------
        ^                            ^
        | (Listen)                   | (Emit)
        v                            |
 [ UI LAYER (CanvasLayer) ]          |
 ------------------------            |
 | TopBar               |            |
 | - Funds Display      |            |
 | - Rep Display        |            |
 ------------------------            |
 | ActionMenu           |            |
 | - Hire Agent         |            |
 | - Dispatch Task      |            |
 ------------------------            |
                                     |
 [ LOGIC LAYER (Nodes) ]             |
 -----------------------------------------------------------
 | AgentManager.gd (Array[AgentRes]) |                     |
 | - hire_agent(role)                |                     |
 | - get_available_agents()          |                     |
 |                                   |                     |
 | TaskManager.gd                    |                     |
 | - generate_random_task()          |                     |
 | - assign_task(task, agent)        |                     |
 |                                   |                     |
 | TimeManager.gd                    |                     |
 | - process_tick()                  |                     |
 -----------------------------------------------------------
```

### 🧠 架構設計亮點 (符合 MVC 與 TDD 原則)

1. **極致解耦 (Extreme Decoupling)**：
   *   **Model**: `AgentManager` 和 `TaskManager` 只處理純資料陣列與狀態變化（閒置、工作中、休息）。我們可以撰寫 100% 覆蓋率的單元測試（例如測試「指派任務給忙碌中的 Agent 會失敗並拋出錯誤」）。
   *   **View**: UI 層只負責顯示資金與代理人狀態，並在房間內渲染小人。
   *   **Controller**: `TimeManager` 作為心跳 (Tick)，驅動所有工作的進度條與資源消耗。

2. **基於時間的心跳機制 (Tick-Based Simulation)**：
   模擬遊戲的核心是時間。我們使用 `TimeManager` 來發射固定的時間滴答信號，讓所有任務與 Agent 的狀態基於這個 Tick 進行更新，這比依賴即時的 `_process(delta)` 更好測試與快進/暫停。

3. **實體化除錯事件 (Crisis Events)**：
   定時或隨機觸發的 Crisis 資源，挑戰玩家的資源調度能力。

---

## 🚀 TDD 第一階段：基礎資源與任務管理

我們的第一個目標是建立 `AgentManager` 和 `TaskManager`，並確保其核心邏輯能通過 `MiniTest` 的無頭測試。

*   **TDD 更新要點 (實作規格)**:
    1. **資源定義**：
        *   建立 `AgentResource.gd` 定義代理人（角色：Sales, Dev, QA, 等；狀態：Idle, Working）。
        *   建立 `TaskResource.gd` 定義任務（類型、所需時間、獎勵資金、所需角色）。
    2. **核心邏輯**：
        *   `AgentManager` 可以新增 Agent，並能根據 ID 或狀態篩選。
        *   `TaskManager` 可以將 Task 指派給符合角色的 Idle Agent。指派成功後，Agent 狀態轉為 Working。

*   **LEAN TDD 斷言**: 
    *   驗證無法將任務指派給不符合角色的 Agent。
    *   驗證指派任務後，Agent 與 Task 的狀態是否正確連動更新。