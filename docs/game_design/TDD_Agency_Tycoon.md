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

---

## 🎮 遊戲關卡與過關條件 (Game Phases)

遊戲以公司發展的三個階段作為關卡，失敗條件皆為：**資金 (Funds) < 0 或 信譽 (Reputation) 降至 0**。

1.  **第一關：車庫創業 (Startup Phase)**
    *   **情境**：低資金啟動，純粹的任務指派與時間管理。
    *   **過關條件**：賺取 $2,000 資金，並成功招募 3 名員工 (例如 1 Dev, 1 Sales, 1 QA)。
2.  **第二關：擴張危機 (Scale-up Phase)**
    *   **情境**：引入「突發危機 (Chaos Events)」，例如伺服器 500 錯誤、客戶投訴。危機若未在時限內處理將大量扣除信譽。
    *   **過關條件**：累積 $10,000 資金，信譽維持在 80 以上，並完成 10 個高級任務。
3.  **第三關：星環企業 (Archon Nexus)**
    *   **情境**：無盡生存模式 (Endless Mode)。出現複合型任務（需多職業協作）與極端資源管理。
    *   **過關條件**：無盡挑戰，比拼存活最高 Tick 數與總資產排行榜。

---

## 👁️ 視覺佈局與互動 (Visual & UI Layout)

靈感取自《Fallout Shelter》，採用 **2D 橫向剖面視角 (Cross-section Ant Farm View)**。

*   **剖面場景**：畫面劃分為多個部門房間 (Dev Room, Sales Room, Break Room)。
*   **視覺化狀態**：員工在房間內以實體呈現，頭部顯示動態進度條 `[■■□□]` 或是狀態氣泡 `[Zzz]`。危機發生時房間閃爍紅光。
*   **拖曳互動 (Drag & Drop)**：
    *   將下方待辦清單 (Backlog) 的「任務卡片」拖曳至對應的「部門房間」以自動指派閒置員工。
    *   點擊並拖曳「員工實體」至休息室以恢復體力 (Energy)。

---

## 🎨 素材生成與動畫策略 (Asset & Animation Strategy)

堅守 Lean 原則，不依賴外部素材庫，採本地程式化生成圖形，並將**視覺靈魂交給 Godot 內建的動畫系統**。

### 1. 靜態素材 (Procedural Assets)
*   **場景與 UI**：極致利用 Godot 內建 `ColorRect` 與 `StyleBoxFlat`。定調為**深色科技霓虹風**。
*   **圖示與角色**：撰寫 Python 腳本產生 SVG 向量圖形 (如金幣、警報 Icon)，以及極簡方塊像素人 (Minimalist Voxel Pixel Art) 的序列圖。

### 2. 動畫驅動機制 (View Layer Animations)
> ⚠️ **架構鐵律**：所有的動畫都屬於 View 層，透過監聽 Model 層發出的信號 (`Signals`) 來觸發。**動畫表現絕對不會、也不應該被納入 TDD 的自動化測試範圍。**

*   **`Tween` (程式化補間動畫)**：負責物理打擊感與動態回饋。
    *   例如：任務完成時，金幣數字 `+$400` 使用 Tween 做出拋物線彈出與淡出效果。
    *   例如：拖曳卡片時，使用 Tween 讓卡片瞬間放大 1.1 倍並帶有彈性縮放 (Elastic/Bounce Easing)。
*   **`AnimationPlayer` (時間軸動畫)**：負責場景級別的狀態演出。
    *   例如：發生「突發危機 (Crisis)」時，控制房間的背景顏色在深灰與紅色間閃爍，並加入畫面震動 (Screen Shake)。
    *   例如：重要 UI 按鈕的呼吸燈光暈效果 (Breathing Glow)。
*   **`AnimatedSprite2D` (幀動畫)**：賦予極簡像素人生命力。
    *   例如：透過 Python 生成的 2 張簡單幀 (手放下/手抬起)，設定每秒 4 次的切換，形成員工在電腦前敲擊鍵盤的「工作中」動畫。

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
