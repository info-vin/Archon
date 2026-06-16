# Technical Design Document (TDD): Archon Agency Tycoon

```text
=============================================================================
                  Archon: Agency Tycoon (Godot 4.x)
                     Core Event & Node Architecture
=============================================================================

 [ AUTOLOADS (Global) ]
 -------------------------------------------------------------------------
 | TycoonManager.gd     |  SignalBus.gd          |  ResolutionLogger.gd  |
 | - company_funds      |  - [task_completed]    |  - log_resolution()   |
 | - reputation         |  - [crisis_spawned]    |                       |
 | - active_crises      |  - [log_emitted]------>|                       |
 -------------------------------------------------------------------------
        ^                            ^                     |
        | (Listen)                   | (Emit)              v (Emit text)
        v                            |               [ UI Log Panel ]
 [ UI LAYER (CanvasLayer) ]          |
 ------------------------            |
 | TopBar & RWD Panels  |            |
 | - Funds & Rep        |            |
 | - Resolution Feed    |<-----------+
 ------------------------            |
 | ActionMenu           |            |
 | - Hire / Rush / Save |            |
 ------------------------            |
                                     |
 [ LOGIC LAYER (Nodes) ]             |
 -------------------------------------------------------------------------
 | AgentManager.gd                   | JobBoardBridge.gd                 |
 | - hire_agent(role)                | - fetch_104_leads_from_supabase() |
 |                                   |   (via JavaScriptBridge)          |
 | TaskManager.gd                    |                                   |
 | - generate_tasks_from_leads()     | SaveSystem.gd                     |
 | - assign_task(task, agent)        | - sync_to_supabase()              |
 -------------------------------------------------------------------------
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

遊戲以公司發展的三個階段作為關卡。

### 📊 核心數學與判定公式

#### 1. 失敗判定條件 (Failure Condition)
遊戲在任何 Tick $t$，若滿足以下條件即判定失敗 (Game Over)：
$$Funds_t < 0 \lor Reputation_t \le 0$$

#### 2. 關卡過關判定公式 (Victory Validation Formulas)
*   **第一關：車庫創業 (Startup Phase)**
    *   **情境**：低資金啟動，純粹的任務指派與時間管理。
    *   **過關公式**：
        $$Funds_t \ge 2000 \land |Agents| \ge 3$$
*   **第二關：擴張危機 (Scale-up Phase)**
    *   **情境**：引入「突發危機 (Chaos Events)」，如伺服器 500 錯誤。危機未在時限內處理會持續扣除信譽。
    *   **過關公式**：
        $$Funds_t \ge 10000 \land Reputation_t \ge 80 \land CompletedAdvancedTasks \ge 10$$
*   **第三關：星環企業 (Archon Nexus)**
    *   **情境**：無盡生存模式 (Endless Mode)，複合型任務（需多職業協作）與極端資源管理。
    *   **過關公式**：
        $$Score = \max(Tick) \text{ (無盡挑戰，記錄存活最高 Tick 數)}$$

#### 3. 回合時間流逝與資源演進公式 (Tick State Transitions)
對於每個時間心跳 $t \to t+1$：
*   **員工工作狀態 (`WORKING` on Task $T$)**：
    $$Energy_{t+1} = \max(0, Energy_t - 10)$$
    $$Progress_{T, t+1} = Progress_{T, t} + 1$$
    *   *完成判定*：若 $Progress_{T, t+1} \ge Duration_T$，則 Task 狀態設為 `COMPLETED`，Agent 狀態設為 `IDLE`。
        $$Funds_{t+1} = Funds_t + Reward_T$$
    *   *力竭判定*：若 $Energy_{t+1} \le 0 \land Progress_{T, t+1} < Duration_T$，則 Agent 狀態設為 `EXHAUSTED`，Task 退回 `PENDING`。
*   **員工休息狀態 (`RESTING` in Break Room)**：
    $$Energy_{t+1} = \min(100, Energy_t + 20)$$
    *   *休息結束判定*：若 $Energy_{t+1} \ge 100$，則 Agent 狀態自動設為 `IDLE`。

---

## 👁️ 視覺佈局與互動 (Visual & UI Layout)

靈感取自《Fallout Shelter》，採用 **2D 橫向剖面視角 (Cross-section Ant Farm View)**。

*   **剖面場景**：畫面劃分為多個部門房間 (Dev Room, Sales Room, Break Room)。
*   **視覺化狀態**：員工在房間內以實體呈現，頭部顯示動態進度條 `[■■□□]` 或是狀態氣泡 `[Zzz]`。危機發生時房間閃爍紅光。
*   **拖曳互動 (Drag & Drop)**：
    *   將下方待辦清單 (Backlog) 的「任務工單」拖曳至對應的「部門房間」以自動指派閒置員工。
    *   點擊並拖曳「員工實體」至休息室以恢復體力 (Energy)。

### 🪟 介面架構與創角系統 (UI Architecture & Character Creator)

為確保高品質的視覺表現與活體動畫，UI 系統捨棄靜態的 `TextureRect` 堆疊，採用 **SubViewport 虛擬攝影棚** 架構，並嚴格遵守 MVC 資料流向（如架構圖所示）。

1. **MVC 核心資料流向 (Data Flow based on Architecture Diagram)**
   * **Controller/Logic 互動**：
     * `CharacterCreatorUI` 不會直接去修改 `ModularAgentView` 的貼圖。
     * 當玩家拖曳滑桿 (Slider) 或點擊下拉選單 (Dropdown) 時，`CharacterCreatorUI` 會先更新底層的 **Data Layer (Model)** ── 即 `AgentResource` 中的 `Gender`, `HairStyle`, `Color`, `Outfit`, `Tool` 屬性。
   * **View 的被動渲染 (Passive View Rendering)**：
     * `ModularAgentView` (像素小人節點) 會被安插在 UI 的 `SubViewport` 中以及主畫面的房間內。
     * 它只負責一件事：接收 `AgentResource` 資料，並**「依資料渲染動態 Part 圖層與調色」**。這保證了創角預覽與遊戲內實體的 100% 外觀一致性。
   * **管理與分派流 (Management Flow)**：
     * 當玩家在 `CharacterCreatorUI` 按下確認招募後，產生好的 `AgentResource` 會被送交給 `AgentManager` 進行「狀態管理」。
     * `MainView` (主畫面) 會展示房間底圖，並根據 `AgentManager` 的狀態與 `TaskManager` 的「Tick 分派任務」結果，決定 `ModularAgentView` 要在哪個房間播放什麼動畫。

2. **SubViewport 動態渲染細節 (Live Animation in UI)**
   * **架構**：在 `CharacterCreator.tscn` 內使用 `SubViewportContainer` > `SubViewport` > `Camera2D` 的層級。
   * **優勢**：將實體化的 `ModularAgent` 節點直接投入 UI 視窗中。這讓玩家在捏臉時，可以直接看到角色流暢地播放「呼吸 (Rest)」、「敲擊鍵盤 (Work)」、「閒置 (Idle)」等動態 `Tween` 補間動畫，而非死板的靜態圖。

3. **創角進出流程與資源掛鉤 (Entry/Exit Flow & Costs)**
   * **進入 (Entry)**：
     * 玩家在 `Main.tscn` 點擊招募按鈕。
     * 系統檢查資金是否滿足招募成本 (預設 $500)。若不足則阻擋。
     * 生成半透明的模態遮罩 (Modal Overlay, 黑底 70% 透明度)，暫停主畫面互動。
     * `CharacterCreator` 以 `Tween.TRANS_BACK` 的動畫從畫面中心彈出。
   * **操作與預覽**：
     * 提供 `UI_RANDOMIZE` 按鈕，利用 `randi()` 和 `randf()` 隨機改變角色的性別、髮型、衣服與 RGB 色相。
   * **離開與實體化 (Exit & Instantiation)**：
     * 若點擊 `UI_CANCEL`：關閉介面，清除遮罩，不扣資金。
     * 若點擊 `UI_RECRUIT`：發出 `character_created` 信號 ➔ 主程式收到後扣除 $500 ➔ 將新的 `AgentResource` 送入 `AgentManager` ➔ 根據職位 (DEV/SALES/QA) 將這名新員工「實例化」到場景對應的辦公室房間內，並開始正常遊戲循環。

---

## 🎨 素材生成與動畫策略 (Asset & Animation Strategy)

放棄單一靜態圖，改採高擴充性的**模組化紙娃娃系統 (Modular Paper Doll System)**，以實現高復用性與未來裝備系統的擴充，並滿足**遊戲狀態記憶與持久化 (Save & Load)** 的核心需求。

### 1. 模組化角色與狀態記憶 (Modular Characters & State Persistence)
*   **MVC 架構對齊**：
    *   **Model (`AgentResource`)**: 新增 `equipped_hair`, `equipped_outfit`, `equipped_tool` 等字串或 ID 欄位，輕量化記憶角色的當下裝備狀態，確保存檔/讀檔能 100% 還原外觀。
    *   **View (`ModularAgent.tscn`)**: 透過動態讀取 Model 狀態，利用多個 `Sprite2D` 節點進 行 Z-Index 疊加：
        *   `Layer 0: BaseBody` (素體，z_index=0)
        *   `Layer 1: Outfit` (職業服裝，如：魔法袍、西裝，z_index=1)
        *   `Layer 2: Hair` (髮型，z_index=2)
        *   `Layer 3: Eyes/Face` (表情，z_index=3) ─ 強制渲染在頭髮之上，確保瀏海不會遮擋眼神。
        *   `Layer 4: Tool/Accessory` (手持物，如：塔羅牌、咖啡杯、筆電，z_index=4)
*   **優勢**：透過動態抽換 Texture，可以用極少的素材庫排列組合出無數種員工，未來也可輕易導入「裝備提升效率」的機制。

### 2. Python 自動化資產管線與紙娃娃對位 (Automated Asset Pipeline & Alignment)
*   為解決純 GDScript 處理影像效能過低的問題，確立 **方案 A：保持 Python 作為 Pipeline 工具**。
*   **實作流程**：
    1.  建立 `scripts/process_sprites.py`，使用 `scipy.ndimage` 與 `PIL`。
    2.  將 AI 或美術生成的整張精靈圖 (Spritesheet) 放入 `raw_assets/`。
    3.  執行腳本自動進行：硬邊去背 -> 物理連通域分析 -> **動態斷崖偵測 (排除雜訊)** -> **全域等比例縮放 (Uniform Scaling)** -> 標準化置中為 `64x64` 透明小圖。
    4.  直接輸出至 `Assets/Characters/Alice_Parts/` 供 Godot 直接引用。
*   **對位與縮放校正優勢**：
    *   **全域等比例縮放 (Uniform Scaling)**：為避免個別部件因高度不同被個別縮放為 60px 造成比例失衡（如頭部與身體一樣大），改以最大部件的最大維度（417px）計算出全域的單一縮放係數 (`0.14388`)，以保持各部件正確的原始比例關係。
    *   **最近鄰縮放 (Nearest Neighbor)**：縮放時使用 nearest neighbor 插值法以防 Lanczos 造成的像素模糊，使導出的 pixel art 維持原生的銳利感。
    *   **精確位移對位 (Precise Offsets)**：所有部件在 64x64 中皆為物理置中，因此在 `ModularAgent.gd` 和 `CharacterCreator.gd` 中必須套用精確偏移量：
        *   素體 (`BaseBody`)：`Vector2(0, 0)`
        *   臉部/頭部 (`Eyes`)：`Vector2(0, -27)`，使其完美卡在脖子上方
        *   髮型 (`Hair`)：`Vector2(0, -18)`，使後髮貼合頭部
        *   服裝 (`Outfit`)：`Vector2(0, 2)`
        *   道具 (`Tool`)：`Vector2(18, 6)`，縮放為 `0.8`
    *   **圖層渲染順序 (Z-Index Layering)**：為了避免瀏海遮蓋五官表情，場景與程式中的渲染順序必須正確覆蓋：`BaseBody` (z=0, 最底) ➔ `Outfit` (z=1) ➔ `Hair` (z=2) ➔ `Eyes` (z=3, 強制渲染於頭髮之上) ➔ `Tool` (z=4, 最頂)。這能確保面部表情永遠從髮型之上正確透出，不會被瀏海像素覆蓋。

### 3. 動畫驅動機制 (View Layer Animations)
> ⚠️ **架構鐵律**：所有的動畫都屬於 View 層，透過監聽 Model 層發出的信號 (`Signals`) 來觸發。**動畫表現絕對不會、也不應該被納入 TDD 的自動化測試範圍。**

*   **`Tween` (程式化補間動畫)**：負責整體的動態回饋（如拖曳工單時的彈性縮放、金幣彈出）。
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

### 4. 工單解決方案與特質加權機率系統 (Resolution Categories & Weighted Probability)

當員工完成工單時，系統會依據工單的職缺背景與 Assignee 的 **角色/特質**，動態且隨機生成最終的「解決說明」以提升沈浸感：

#### A. 解決方案類別與預設機率 (Resolution Distribution)
*   **DEV (開發) 工單**：
    *   功能開發型工單 ➔ 70% `API_IMPLEMENTATION` (API 實作) | 30% `FRONTEND_UI` (UI 開發)
    *   重構修復型工單 ➔ 80% `REFACTOR_MODULARIZATION` (模組重構) | 20% `API_IMPLEMENTATION`
*   **SALES (業務) 工單**：
    *   情資分析型工單 ➔ 50% `LEAD_ENRICHMENT` (客戶痛點分析) | 50% `PITCH_SENT` (發送提案)
    *   專案簽約型工單 ➔ 100% `CONTRACT_SIGNED` (簽定合約)
*   **QA (品保) 工單**：
    *   系統除錯型工單 ➔ 60% `CRITICAL_HOTFIX` (緊急修復) | 40% `PERFORMANCE_AUDIT` (效能稽核)
    *   測試補強型工單 ➔ 100% `AUTOMATED_TESTING` (寫測試案例)

#### B. 員工特質機率加權修正 (Trait Modifiers)
員工的個性特質 (Traits) 會對上述隨機結果產生加權影響：
*   **[UI 狂熱者] (UI Enthusiast)** 特質：DEV 結案時，`FRONTEND_UI` 解決方式的機率加權 $+30\%$。
*   **[重構強迫症] (Refactor Obsessive)** 特質：DEV 結案時，`REFACTOR_MODULARIZATION` 解決方式的機率加權 $+40\%$。
*   **[效能狂人] (Performance Freak)** 特質：QA 結案時，`PERFORMANCE_AUDIT` 解決方式的機率加權 $+30\%$。

---

## 🚀 TDD 第二階段：多職業協作與資源循環 (Multi-Agent Synergy)

我們的第二個目標是實現《play_mock.sh》中定義的三職業循環，確保 SALES 能夠獨立推動遊戲的任務產出，讓遊戲脫離「手動塞任務」的假象。

*   **TDD 更新要點 (實作規格)**:
    1.  **業務系統 (Sales Loop)**：
        *   擴充 `TaskManager` 的邏輯：當有 `SALES` (Role=0) 處於 `WORKING` 狀態時，每經過一定的 Ticks，自動生成一個給 `DEV` (Role=1) 的新任務至 Backlog。
    2.  **初始狀態對齊 (Initial State Parity)**：
        *   遊戲初始化時，必須正確招募並實例化 Alice(DEV), Bob(SALES), Charlie(QA)。

*   **LEAN TDD 斷言**: 
    1.  **無業務不產出**：驗證當所有的 SALES 皆處於 `IDLE` 或 `RESTING` 狀態時，經過時間流逝，系統不會產生任何新任務。
    2.  **業務工作產出**：驗證將 SALES 設為 `WORKING` 後，經過指定的 Ticks 流逝，系統會成功新增一個任務到 `TaskManager` 的未指派列表。
    3.  **體力消耗獨立**：驗證 SALES 進行業務開發時，體力會正常消耗，且會在耗盡時進入 `EXHAUSTED` 並停止產出新任務。

---

## 🚀 TDD 第六階段：紙娃娃模組化系統 (Modular Paper Doll & Sprite Pipeline)

為了保證遊戲角色的視覺對位、正確比例與遮擋順序，我們在 Phase 6 實作了自動化管線與 Z-Index 控制：

*   **痛點與問題**：
    1.  **比例失衡**：各部件在匯出時被獨立強制縮放為 60px 邊界，導致頭部和身體一樣大。且使用了 `LANCZOS` 降採樣造成模糊。
    2.  **圖層遮擋**：`Hair`（包含後髮）節點位於 `Eyes` 之後或 Z-Index 相同，導致面部五官被厚重的後髮完全遮蓋。
    3.  **位置對齊**：無統一偏移量基準，導致創角預覽 (`CharacterCreator`) 與關卡內 (`ModularAgent`) 出現不同步的「鬼圖」拼接。

*   **實作規格與解決方案**：
    1.  **全域等比例縮放 (Uniform Scale Factor)**：
        *   修改 `scripts/process_sprites.py`，以最大部件（417px）計算單一縮放係數 `0.14388`，對所有 34 個 Alice 部件進行全域等比例縮放。
        *   採用 `NEAREST` 最近鄰插值法，保留像素藝術的銳利邊緣。
    2.  **圖層 Z-Index 重構規格**：
        *   `Hair`：`z_index = 0` (最底，後髮渲染在身體後方，而面部可以透過髮型鏤空處透出)
        *   `BaseBody`：`z_index = 1`
        *   `Outfit`：`z_index = 2`
        *   `Eyes`：`z_index = 3` (臉部與前髮/瀏海渲染在最前)
        *   `Tool`：`z_index = 4` (道具最頂)
    3.  **精確偏移對位 (Precise Offsets)**：
        *   修改 `ModularAgent.gd` 和 `CharacterCreator.gd`：
            *   `BaseBody`：`Vector2(0, 0)`
            *   `Eyes` (Face)：`Vector2(0, -27)`
            *   `Hair`：`Vector2(0, -18)`
            *   `Outfit`：`Vector2(0, 2)`
            *   `Tool`：`Vector2(18, 6)`，縮放 `0.8`
    4.  **場景與創角 UI 預覽樹同步**：
        *   調整 `CharacterCreator.tscn` 中的 Preview 節點順序，使其圖層渲染效果與關卡場景中的實體 `ModularAgent.tscn` 達到 100% 物理對齊。

*   **LEAN TDD 斷言與驗證**:
    1.  **Z-Index 斷言**：驗證 `ModularAgent` 中各子圖層的 `z_index` 是否符合規格（`Hair` 為 0，`Eyes` 為 3）。
    2.  **Offset 偏移斷言**：驗證程式運行時 `Eyes` 的 offset 確實被強制對齊為 `Vector2(0, -27)`。
    3.  **視覺裁判 (game_screenshot.png)**：執行實體渲染測試 `test_capture.gd`，獲取包含正確五官比例與分層的外觀截圖，成功完成視覺對帳。

---

## 🚀 TDD 第七階段：俯視霓虹辦公室與視覺重構 (Cyberpunk UI/UX Overhaul)

基於商業化競品分析（參考《Mad Games Tycoon 2》與霓虹像素風格），我們必須徹底揚棄初期的 Programmer Art (原生的 Godot 灰色視窗)，進行全面的視覺與排版整容手術。整個整容手術分為三個執行步驟：

### Step 1: 像素字體與霓虹主題奠基 (Typography & Neon Theme)
*   **字體統一**：導入開源像素字體（如 `Kenney Pixel` 或 `VT323`），在 `NeonTheme.tres` 中強制設定為全域 `default_font`。徹底消滅平滑的系統字體，確保 100% 的像素復古感。
*   **色彩編碼 (Color Coding)**：定義三大部門的專屬主色調，並套用至房間外框與標籤的 Glow 效果：
    *   `DEV` (開發部)：螢光綠 (#39ff14)
    *   `SALES` (業務部)：霓虹黃 (#fde910)
    *   `QA` (品保部)：警示紅 (#ff003c)

### Step 2: 資訊架構與佈局重構 (Layout & Information Architecture)
放棄原本佔用大量畫面的 VBox 排版，改用 `Anchor-based` 滿版佈局，將畫面空間還給「娃娃屋房間」。嚴格遵守以下由商業競品分析得出的排版鐵律：

*   **頂部戰情 HUD (Top Bar Ticker)**：
    *   **極致壓縮**：高度壓縮至 30px 以內。
    *   **跑馬燈排版 (Ticker Style)**：所有關鍵指標 (DATE, FUNDS, REP) 必須串在**單一行**內，並使用垂直線 `|` (Pipe) 分隔，禁止使用鬆散的 `Spacer`。
    *   **雙色編碼 (BBCode)**：強制使用 `RichTextLabel` 的 BBCode 實作。標籤名 (如 `FUNDS:`) 必須為暗灰色/低調色，數值 (如 `$500`) 必須為高亮綠色/白色。利用對比度引導玩家視覺。
    *   **微型系統列**：將右側的「語言/設定」功能壓縮為 24x24 的小型 Icon，貼齊最右側。
*   **底部動作列 (Bottom Action Bar - Icon+Text)**：
    *   將原本佔據 30% 畫面的巨大 Backlog 列表刪除，改為高度 80px 的正方形動作區。
    *   **按鈕排版鐵律 (Top Icon, Bottom Text)**：絕對禁止純文字或純大圖示按鈕。按鈕必須保留 `text` 屬性，並將 `icon_alignment` 設為 `TOP`。上半部 50% 顯示高辨識度 SVG Icon，最底部顯示微小字級 (Size 12-14) 的全大寫說明文字 (如 `BUILD`, `HIRE`)，以降低玩家認知負擔。

### Step 3: 右側戰情日誌與動態回饋 (Event Logger, Status & Minimap)
補齊參考圖中最關鍵的「全局掌控感」。
*   **右側面板 (Right Panel)**：寬度設定為 250px。
    *   **上半部：事件廣播 (Event Feed, 佔 30%)**：使用 `RichTextLabel` 實作由下往上滾動的日誌。當發生「招募員工」、「危機爆發」、「任務完成」時，印出帶有顏色標記與微小字型 (`[font_size=12]`) 的文字，使用對比色彩增強易讀性。
    *   **中半部：員工監控 (Agent Status, 佔 30%)**：條列顯示所有員工目前的狀態（如 `Alice: WORKING`, `Bob: EXHAUSTED`），並用狀態對應的顏色區分，讓玩家不用肉眼在房間裡找人。
    *   **底部：房間縮小雷達圖 (Minimap, 佔 40%)**：揚棄單純的色塊，改以掃描 `OfficeGrid` 動態抓取真實房間的像素背景貼圖，進行全域等比例縮小渲染。加上動態讀取的霓虹 Metadata 顏色外框，並將人員用各部門對應色之像素光點同步投射於其上。
*   **背景底圖**：將最底層的純黑色替換為帶有科技感的暗色電路板紋理 (Circuit Board Pattern)。

---

## 🌐 Web 整合、響應式適配 (RWD) 與 iPad 最佳化

為了將 Godot 遊戲無縫嵌入 Archon 網頁版，我們必須針對 Web 環境進行深度適配，特別是支援跨裝置（Desktop、Tablet、Mobile）的響應式設計。

### 1. 登入機制與雲端存檔 (Web Auth & Cloud Save)
* **主動憑證讀取**：Godot 透過 `JavaScriptBridge` 在啟動時呼叫網頁 JavaScript 環境，獲取 Supabase 的 Token/Session。
* **資料庫同步**：
  * 當玩家點擊「存檔」時，Godot 將存檔資料序列化為 JSON，透過 API 送回 Supabase 的 `user_game_saves` 表格進行儲存。
  * 若為訪客模式（未登入），自動降階 (Fallback) 儲存至瀏覽器本地的 IndexedDB/LocalStorage (`user://savegame.save`)。

### 2. 視窗適配與 RWD 策略
* **Godot 引擎拉伸設定**：
  * `stretch/mode` 設為 `canvas_items` (向量渲染，防模糊)。
  * `stretch/aspect` 設為 `expand` (動態擴展，不留黑邊)。
* **UI 容器與佈局**：
  * 拋棄絕對座標，全面改用 Godot 的 `Container`（如 `MarginContainer`、`BoxContainer`）搭配 **Anchors (錨點)**。
  * 手機版 (寬度 < 600px) 自動切換成垂直緊湊佈局，折疊部分非必要面板，部門房間改為「單房滑動」切換。

### 3. iPad 裝置規格最佳化 (iPad Optimization Specs)
由於 iPad 與平板裝置具備獨特的 4:3 / 16:11 螢幕比例與觸控操作習慣，我們進行以下專屬設計：
* **比例防裁切 (Aspect Ratio Handling)**：
  * 由於 4:3 畫面較高，2D 橫向剖面（Ant Farm View）的兩側可能會被裁切。
  * **解法**：實作 `PanZoomCamera2D`。允許 iPad 玩家使用「單指滑動」在房間之間平移畫面，「雙指捏合 (Pinch to Zoom)」來放大/縮小視角。
* **觸控操作優化 (Touch Targets & Gestures)**：
  * 所有 UI 按鈕（例如 ActionMenu、Rush 按鈕）的物理點擊區域 (Touch Target) 至少為 `48x48` 像素，並在四周加入防誤觸間距。
  * **拖曳強化**：任務工單拖曳至房間時，工單碰撞範圍 (Collision Shape) 物理放大 1.5 倍，確保手指粗細操作也能精準判定。
* **觸控鍵盤防禦**：
  * 存檔與玩家名稱命名改用「預設清單/隨機產生器」，避免在 iPad 上彈出 iOS 虛擬鍵盤，進而擠壓或損壞網頁 Layout。
* **Safari 效能最佳化**：
  * WebGL2 於 iPad Safari 記憶體限制極嚴格。精靈圖尺寸嚴格控制在 `2048x2048` 以內，且在 Web 匯出設定中啟用 `Thread Support: Disabled` 以避免部分 iOS 瀏覽器多線程崩潰問題。

---

## 📊 開發進度追蹤 (Progress Checklist)

- [x] **Phase 0**: 終端互動概念驗證 (Terminal MVP - `play_mock.sh` 已落地)
- [x] **Phase 1**: 基礎資源與任務管理 (TDD 單元測試通過)
  - [x] Agent 新增、尋找、狀態連動
  - [x] 休息與體力恢復 (RESTING)
  - [x] 力竭狀態切換 (EXHAUSTED)
- [x] **Phase 2**: 多職業協作與資源循環 (Sales 自動產生任務機制)
- [ ] **Phase 3**: RWD 佈局與 iPad `PanZoomCamera2D` (Godot 畫布自適應)
- [x] **Phase 4**: 登入同步與 Supabase 雲端存檔 (JavaScriptBridge 橋接)
- [x] **Phase 5**: 《Fallout Shelter》機制 (SPECIAL 屬性、Rush 衝刺、危機蔓延)
- [x] **Phase 6**: 《Terraria》紙娃娃系統與工作/休息動畫 (動態精靈)
- [x] **Phase 7**: 俯視霓虹辦公室與視覺重構 (Mad Games Tycoon 2 風格)
- [x] **Phase 8**: 模擬與玩三遍對比、動態幀動畫設計 & 創角 UI 霓虹美化
- [ ] **Phase 9**: 員工心情系統與深度隨機危機 (Chaos 2.0 & Happiness)

---

## 🚀 TDD 第九階段：員工心情系統與深度隨機危機 (Mood & Complex Crises)

為了提升遊戲的經營深度與隨機性，我們計畫引入動態的心情系統，並將簡單的危機事件升級為具備連鎖反應的深度挑戰。

*   **實作規格與架構設計**：
    1.  **員工心情系統 (Happiness System)**：
        *   **數值模型**：新增 `happiness` (0-100) 屬性。
        *   **增減因子**：
            *   消耗：持續工作、發生危機、公司資金為負。
            *   恢復：在休息室放空 (Resting)、任務順利結案、漲薪（未來擴充）。
        *   **效率影響**：
            *   心情 > 80：`WORKING` 速度 +20%，RUSH 成功率提升。
            *   心情 < 20：員工機率性「罷工 (Strike)」或「離職」，工作進度停滯。
    2.  **深度隨機危機 (Complex Crises 2.0)**：
        *   **連鎖反應 (Chain Reactions)**：危機不再局限於單一房間。例如：開發部伺服器當機（Dev Crisis）機率觸發業務部合約遺失（Sales Crisis）。
        *   **地獄客戶 (Client from Hell)**：特殊隨機事件。產生的任務具備「不可 RUSH」或「Tick 消耗加倍」的負面 Buff。
        *   **多階段解決**：大型危機（如：資安漏洞）需 DEV 先修復伺服器，再由 QA 進行全盤稽核方可解除，大幅考驗玩家的調度能力。

*   **LEAN TDD 斷言與驗證**:
    1.  **心情衰減斷言**：驗證員工在發生危機的房間內工作時，每 Tick 心情衰減速度為正常狀態的 2 倍。
    2.  **罷工機制驗證**：驗證當 `happiness` 降至 0 時，員工狀態強制鎖定為 `STRIKE`，直到玩家點擊「安慰/發獎金」或放入休息室恢復至 20 以上。
    3.  **危機連鎖觸發斷言**：驗證當 `TycoonManager` 觸發 A 類危機時，有 X% 的機率正確 Emit 出 B 類危機的生成信號。

---

## 🧐 商業化與視覺吸引力 Code Review 報告 (Commercialization Review)

### 1. 痛點分析：為什麼目前「難以吸引玩家眼睛」？
*   **紙娃娃動態死板 (Bobbing Limitations)**：目前小人的動態（工作、休息）僅使用 `create_tween()` 進行物理縮放 (`scale:y`) 與擺動，沒有腳步移動、四肢揮動或鍵盤敲擊的格數精靈幀動畫 (Sprite Frame Animations)。這會讓玩家覺得角色缺乏生氣，類似於靜態圖片在上下飄移。
*   **缺少視覺反饋與爽快感 (Game Feel / Juiciness)**：
    *   任務完成、資金入帳時，沒有金幣噴灑 (Coin particles) 或發光文字。
    *   創角 (Character Creator) 介面只是純色滑桿與按鈕，未採用 Tron 風格的發光軌跡與科技邊框。
*   **關卡缺乏動態裝飾**：Dev 房沒有主機閃爍的綠光，Break 房缺少可互動的微縮物件（例如咖啡機噴煙、沙發壓下去的微變形）。

### 2. 改善方案 (Action Plan)
*   **動態格數幀化**：引入 `AnimationPlayer`，將 `Alice_Parts` 中的多格像素圖，拼裝成具備走路動作的「像素幀動畫」（利用 Sprite 的不同 Frame 偏移）。
*   **粒子特效與霓虹發光**：為 RUSH 成功/失敗、任務完成、房間擴建、危機警報，全面加上 `GPUParticles2D` 及 2D 發光材質 (`WorldEnvironment` Bloom 效果)。

---

## 🤖 無頭 (Headless) 試玩三遍與競品比對分析 (Headless Simulation & Parity)

我們實作了 `test_simulations.gd` 自動化無頭跑了三遍，分別驗證了 1) SALES 自動生成任務 2) DEV 工作進度與體力消耗 3) RUSH 機率失敗引發危機 4) QA 成功化解危機 5) 存檔與讀檔資料無損還原。

### 競品橫向比對矩陣

| 特性 / 遊戲 | **Archon: Agency Tycoon** (本專案) | **Fallout Shelter** (避難所) | **Terraria** (泰拉瑞亞) |
| :--- | :--- | :--- | :--- |
| **創角紙娃娃度** | 髮型、髮色 (RGB 任意調色)、性別、服裝、工具配件。 | 固定髮型與臉型，以裝備改變外觀。 | 高度像素自訂（前髮/後髮/眼睛/膚色/裝飾）。 |
| **時間管理機制** | Ticks 心跳，Sales 產任務 ➔ Dev 消耗，無縫自動循環。 | 即時制 (Real-time)，派駐房間自動工作。 | 即時晝夜交替，探索與建造。 |
| **突發危機事件** | RUSH 失敗高機率引發房間危機，QA 可主動消滅，否則持續扣信譽。 | 隨機外敵入侵、火災、蟲災，居民自動反擊。 | Boss 甦醒、軍團入侵、環境腐化。 |
| **存檔系統** | 支援 Local 儲存與 Supabase 雲端無縫同步. | 本地儲存與雲端存檔。 | 純本地儲存與 Steam Cloud。 |

### 商業化與互動要素比對矩陣

| 遊戲 | 自訂紙娃娃深度 | 房間/地圖擴建互動 | 吸引眼球的商業化關鍵 |
| :--- | :--- | :--- | :--- |
| **《Terraria》** | 極深。支援男女多種初始髮型、衣服款式，且能對頭髮、眼睛、皮膚、衣服共 4 個通道進行 RGB 滑桿調色。 | 全自由 TileMap 搭建。玩家自己蓋木屋、石屋，擺放椅子與光源，滿足「NPC 進駐條件」才能招募員工。 | 豐富的動態幀動畫（走路、揮劍、施法）與沙盒建造的無限成就感。 |
| **《Mad Games Tycoon 2》** | 預設職業套裝，自訂性適中。 | 俯視 3D 自由畫牆壁、門，隨意擺放電腦桌、伺服器機櫃、冷氣與自動販賣機。 | 房間與家具的擺放位置會物理影響員工的工作效率（走動距離、舒適度），策略性極高。 |
| **《Archon: Agency Tycoon》 (我們)** | （已實作） 支援男女骨架、三種像素髮型、魔法斗篷/執事服、法杖卡牌，並支援頭髮的 RGB Hue 滑桿調色。 | （已實作） 可動態點擊招募新角色，且提供 `[ Expand Room ]` 按鈕，扣除 500 資金動態新增品保部擴建（QA Room Extension）房間。 | 霓虹科技 Tron 風格，具備危機擴散紅光與簡易說明選單，能量條與氣泡狀態透明。但人物細節動態仍有優化空間。 |

### 比對結論與自癒方針
*   我們的 **RGB 任意 Hue 髮色調色盤** 在創角時相較於 *Fallout Shelter* 的固定預設色更具商業吸引力與個性化。
*   但 *Fallout Shelter* 的 **危機蔓延動畫** 與 *Terraria* 的 **受擊閃紅、動作幀** 遠比我們生動。
*   **下一階段實作目標**：利用 `GPUParticles2D` 建立 Tron 科技感的像素霓虹火花，並在小人頭頂加入動態心情氣泡（如生氣、力竭、興奮），完全取代文字標籤，進一步達成 100% 商業化美感！

---

## 🚀 TDD 第四階段：持久化存檔系統 (Save & Load System)

為了確保玩家的經營進度（資金、信譽、員工、任務）能夠在不同裝置與會話間延續，我們實作了高可擴充性的序列化架構。

*   **實作規格與架構設計**：
    1.  **資料序列化 (Serialization)**：
        *   為 `AgentResource` 與 `TaskResource` 實作 `to_dict()` 導出純 JSON 相容格式。
        *   為 `AgentManager` 與 `TaskManager` 實作狀態快照功能，完整記錄所有物件陣列。
    2.  **雙軌存檔適配器 (Adapter Pattern)**：
        *   **`LocalSaveAdapter`**：針對桌面版與開發測試，使用 `user://savegame.json` 進行實體檔案寫入。
        *   **`SupabaseSaveAdapter`**：針對 Web 版本，透過 `JavaScriptBridge` 獲取 Auth Token，並與 FastAPI/Supabase 雲端資料庫同步。
    3.  **條件初始化流程**：
        *   啟動時自動偵測存檔存在性。
        *   若 `load_game()` 成功，則呼叫 `_setup_loaded_game()` 進行人員與任務的「場景實例化 (Instantiation)」，而非執行 `_setup_initial_game()` 的初始範例。

*   **LEAN TDD 斷言與驗證**:
    1.  **無損序列化斷言**：驗證 `AgentResource` 導出為字典後，再透過 `from_dict()` 導入得到的物件，其 `energy` 與 `hair_color` 屬性與原始物件完全一致。
    2.  **存檔反饋斷言**：驗證按下存檔按鈕後，`RightPanel` 的事件日誌確實收到 `Game Saved Successfully!` 的訊號通知。
    3.  **多裝置同步驗證**：在 Web 環境下，驗證存檔動作確實觸發了對 `/api/game/save` 的 POST 請求並附帶了正確的 Authorization Bearer 頭像。

---
    1. **資源定義**：
        *   建立 `AgentResource.gd` 定義代理人（角色：Sales, Dev, QA, 等；狀態：Idle, Working）。
        *   建立 `TaskResource.gd` 定義任務（類型、所需時間、獎勵資金、所需角色）。
    2. **核心邏輯**：
        *   `AgentManager` 可以新增 Agent，並能根據 ID 或狀態篩選。
        *   `TaskManager` 可以將 Task 指派給符合角色的 Idle Agent。指派成功後，Agent 狀態轉為 Working。

*   **LEAN TDD 斷言**: 
    *   驗證無法將任務指派給不符合角色的 Agent。
    *   驗證指派任務後，Agent 與 Task 的狀態是否正確連動更新。

---

## 🚀 TDD 第二階段：多職業協作與資源循環 (Multi-Agent Synergy)

我們的第二個目標是實現《play_mock.sh》中定義的三職業循環，確保 SALES 能夠獨立推動遊戲的任務產出，讓遊戲脫離「手動塞任務」的假象。

*   **TDD 更新要點 (實作規格)**:
    1.  **業務系統 (Sales Loop)**：
        *   擴充 `TaskManager` 的邏輯：當有 `SALES` (Role=0) 處於 `WORKING` 狀態時，每經過一定的 Ticks，自動生成一個給 `DEV` (Role=1) 的新任務至 Backlog。
    2.  **初始狀態對齊 (Initial State Parity)**：
        *   遊戲初始化時，必須正確招募並實例化 Alice(DEV), Bob(SALES), Charlie(QA)。

*   **LEAN TDD 斷言**: 
    1.  **無業務不產出**：驗證當所有的 SALES 皆處於 `IDLE` 或 `RESTING` 狀態時，經過時間流逝，系統不會產生任何新任務。
    2.  **業務工作產出**：驗證將 SALES 設為 `WORKING` 後，經過指定的 Ticks 流逝，系統會成功新增一個任務到 `TaskManager` 的未指派列表。
    3.  **體力消耗獨立**：驗證 SALES 進行業務開發時，體力會正常消耗，且會在耗盡時進入 `EXHAUSTED` 並停止產出新任務。

---

## 🛠️ L2 重構與中心化設定實作結果 (L2 Refactoring & Centralized Config)

本階段的 L2 重構與中心化配置已於 **2026/06/16** 實作落地，順利解決了「大檔案過重」與「數值硬編碼散落」的架構痛點，並使單元/整合測試套件 100% 通過。

### 1. 核心數值中心化配置化 (Game Parameter Externalization)
*   **自訂 Resource 定義**：新建 [TycoonConfig.gd](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Scripts/Resources/TycoonConfig.gd)，將招募成本 (`recruit_cost`)、體力限制、危機懲罰、RUSH 失敗率等數值全部宣告為 Resource 屬性。
*   **實體配置文件**：創建自訂資源檔 [GameConfig.tres](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/GameConfig.tres) 儲存遊戲預設數值。
*   **Manager 注入**：`TycoonManager.gd`、`TaskManager.gd`、`AgentManager.gd` 及 `CharacterCreator.gd` 全面改為動態讀取此外部配置，徹底消除各處的硬編碼。

### 2. Main.gd 大檔案 L2 模組化拆分 (Decoupling Main.gd)
為了符合單一檔案行數低於 300 行的門禁標準，`Main.gd` (原 420+ 行) 已成功減重至 **273 行**，拆分出以下獨立控制器與 UI 模組：
*   [Minimap.gd](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Scripts/UI/Minimap.gd)：獨立負責雷達小地圖繪製與實體位置換算。
*   [HUDController.gd](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Scripts/UI/HUDController.gd)：獨立負責文字多國語系化、動態走馬燈 ticker 渲染。
*   [GameLifecycle.gd](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Scripts/Logic/GameLifecycle.gd)：承接存檔加載與初始人物實例化邏輯。
*   [OfficeRoom.gd](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Scripts/UI/OfficeRoom.gd)：負責各辦公室房間背景與危機發生時的物理紅光閃爍 Tween。

### 3. TDD 測試套件無頭化優化與 100% 通過 (Headless QA Testing & Run Optimization)
*   **消除測試狀態污染**：在 [MiniTest.gd](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Tests/MiniTest.gd) 的 `run_test_suite()` 中，於每個測試函數（例如 `test_office_view.gd` 等）執行前後，**主動檢測並以物理方式刪除 `user://savegame.save`**。這根除了以往測試載入到殘留存檔資料而導致 `agent_views[0]` 字典鍵值找不到的崩潰問題。
*   **快取硬化自癒**：當 Godot 出現內部快取報錯或 `class_name` 索引遺失時，透過物理清理 `.godot/` 暫存資料夾重跑，徹底實現 100% 自癒。
*   **測試結果**：全部 **100 個 Assertions 通過率達 100%**，在 Headless 模式下運行流暢，測試執行時間縮短至數秒。
