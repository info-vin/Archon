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

放棄單一靜態圖，改採高擴充性的**模組化紙娃娃系統 (Modular Paper Doll System)**，以實現高復用性與未來裝備系統的擴充。

### 1. 模組化角色 (Modular Characters)
*   **架構參考**：《Terraria》的圖層疊加設計。
*   **實作方式**：在 Godot 中建立 `ModularAgent.tscn`，利用多個 `Sprite2D` 節點進行 Z-Index 疊加：
    *   `Layer 0: BaseBody` (素體)
    *   `Layer 1: Eyes/Face` (表情)
    *   `Layer 2: Hair` (髮型)
    *   `Layer 3: Outfit` (職業服裝，如：魔法袍、西裝)
    *   `Layer 4: Tool/Accessory` (手持物，如：塔羅牌、咖啡杯、筆電)
*   **優勢**：透過動態抽換 Texture，可以用極少的素材庫排列組合出無數種員工，未來也可輕易導入「裝備提升效率」的機制。

### 2. 動畫驅動機制 (View Layer Animations)
> ⚠️ **架構鐵律**：所有的動畫都屬於 View 層，透過監聽 Model 層發出的信號 (`Signals`) 來觸發。**動畫表現絕對不會、也不應該被納入 TDD 的自動化測試範圍。**

*   **`Tween` (程式化補間動畫)**：負責整體的動態回饋（如拖曳卡片時的彈性縮放、金幣彈出）。
*   **`AnimationPlayer` (時間軸動畫)**：驅動紙娃娃圖層。我們可以針對 `ModularAgent` 製作簡單的「呼吸 (Breathing)」或「工作敲擊 (Working)」的骨骼/圖層位移動畫，所有套用該模組的角色都能共用同一套動畫邏輯。

## ⚙️ 進階系統與數學模型 (Advanced Systems & Math Model)

為了確保遊戲具備商業產品的深度與體驗，我們在底層設計中導入了以下三大核心系統：

### 1. 角色平衡與資源循環 (Role Synergy & Resource Loop)
三個角色必須形成相生相剋的資源循環，並受到嚴格的體力限制：
*   **體力模型 (Energy)**：滿值 100。`WORKING` 每 1 Tick 消耗 10 點。`RESTING` 每 1 Tick 恢復 20 點（鼓勵玩家手動調度）。
*   **SALES (業務)**：負責產生任務。若 SALES 不足，公司將陷入無任務可做的空轉狀態。
*   **DEV (開發)**：負責消耗任務，將其轉化為資金 (Funds)。
*   **QA (品保)**：負責解決突發危機 (Crisis Events)。若 Bug 堆積，信譽將持續下降。QA 是維護公司信譽的唯一防線。

### 2. 多國語言系統 (i18n Localization)
全面支援 **繁體中文 (zh_TW)、英文 (en)、日文 (ja)** 的無縫切換。
*   **實作規範**：禁止在 UI 或程式碼中硬編碼字串。全面使用 Godot 的 `TranslationServer` 與 `translations.csv`。
*   所有文字顯示必須透過 `tr("KEY_NAME")` 動態載入。

### 3. 持久化存檔系統 (Save & Load)
提供跨次遊玩的進度繼承，避免每次都從第一關重打。
*   **實作規範**：在 `TycoonManager` 中實作序列化邏輯。
*   **儲存標的**：當前關卡 (`current_phase`)、資金與信譽、解鎖的房間、以及所有員工的屬性與狀態 (`agents` 陣列)。
*   **儲存位置**：安全存入作業系統的 `user://savegame.save`。

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
