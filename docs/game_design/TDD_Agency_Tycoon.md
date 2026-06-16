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
- [ ] **Phase 4**: 登入同步與 Supabase 雲端存檔 (JavaScriptBridge 橋接)
- [x] **Phase 5**: 《Fallout Shelter》機制 (SPECIAL 屬性、Rush 衝刺、危機蔓延)
- [x] **Phase 6**: 《Terraria》紙娃娃系統與工作/休息動畫 (動態精靈)
- [x] **Phase 7**: 俯視霓虹辦公室與視覺重構 (Mad Games Tycoon 2 風格)
- [x] **Phase 8**: 模擬與玩三遍對比、動態幀動畫設計 & 創角 UI 霓虹美化

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
| **存檔系統** | 支援 Local 儲存與 Supabase 雲端無縫同步。 | 本地儲存與雲端存檔。 | 純本地儲存與 Steam Cloud。 |

### 比對結論與自癒方針
*   我們的 **RGB 任意 Hue 髮色調色盤** 在創角時相較於 *Fallout Shelter* 的固定預設色更具商業吸引力與個性化。
*   但 *Fallout Shelter* 的 **危機蔓延動畫** 與 *Terraria* 的 **受擊閃紅、動作幀** 遠比我們生動。
*   **下一階段實作目標**：利用 `GPUParticles2D` 建立 Tron 科技感的像素霓虹火花，並在小人頭頂加入動態心情氣泡（如生氣、力竭、興奮），完全取代文字標籤，進一步達成 100% 商業化美感！

---

## 🚀 TDD 第一階段：基礎資源與任務管理
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
