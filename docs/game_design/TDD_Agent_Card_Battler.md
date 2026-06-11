# Technical Design Document (TDD): Agent Card Battler

```text
=============================================================================
                  Archon: Agent Card Battler (Godot 4.x)
                         Core Event & Node Architecture
=============================================================================

 [ AUTOLOADS (Global) ]
 -----------------------------------------------------------
 | GameManager.gd       |        SignalBus.gd              |
 | - current_mana       |<------ [card_played]             |
 | - player_hp          |<------ [enemy_turn_ended]        |
 | - enemy_hp           |<------ [player_turn_ended]       |
 -----------------------------------------------------------
        ^                            ^
        | (Listen)                   | (Emit)
        v                            |
 [ UI LAYER (CanvasLayer) ]          |
 ------------------------            |
 | TopBar               |            |
 | - Health Bar         |            |
 | - Enemy Intent       |            |
 ------------------------            |
 | HandContainer        |            |
 | - CardUI (Node)      |---(Drag)---+
 | - CardUI (Node)      |            |
 ------------------------            |
                                     |
 [ LOGIC LAYER (Nodes) ]             |
 -----------------------------------------------------------
 | DeckManager.gd (Array[CardRes])   |                     |
 | - draw_cards(amount)              |                     |
 | - shuffle_discard()               |                     |
 |                                   |                     |
 | TurnManager.gd                    |                     |
 | - start_player_turn()             |                     |
 | - execute_enemy_action()          |                     |
 -----------------------------------------------------------
```

### 🧠 架構設計亮點 (符合 MVC 與 TDD 原則)

1. **極致解耦 (Extreme Decoupling)**：
   *   **Model**: `DeckManager` 和 `GameManager` 只處理純資料陣列與數值運算。這使得我們可以在沒有任何 UI 的情況下，撰寫 100% 覆蓋率的單元測試（例如測試「抽 3 張牌後，牌庫數量是否減少 3」）。
   *   **View**: `CardUI` 只負責顯示圖片和滑鼠懸停動畫。
   *   **Controller**: 玩家將卡牌拖曳到敵人身上時，只會觸發一個信號 `card_played(card_id)`，然後視覺卡牌立刻被銷毀，由 `GameManager` 接手計算扣血與扣除 Token。

2. **資料驅動 (Data-Driven Design)**：
   每張卡牌都是一個繼承自 `Resource` 的自訂資源檔 (`CardStats.tres`)，包含 `cost` (消耗 Token), `damage` (傷害), `block` (護盾) 等屬性。企劃可以直接在 Godot 編輯器中新增卡牌，完全不需要動到程式碼。

3. **回合制狀態機 (Turn-Based State Machine)**：
   拋棄了複雜的 `_process(delta)` 即時物理碰撞。遊戲狀態嚴格受控於 `PlayerTurn` 與 `EnemyTurn` 兩個狀態，徹底消除了時間軸上的 Race Condition 與非同步 Bug。

---

## 🚀 混血 UI/UX 實作指南 (Slay the Spire 資訊密度 + 爐石打擊感)

為了打造沉浸式的 Agent 卡牌體驗，我們的 View 層與 Model 層必須融合頂尖業界標準，並通過 LEAN 的嚴謹驗證。

### 第一層：真實數據抽取與 LEAN 驗證 (Git Log -> Model)
卡牌的數值並非憑空捏造，而是取自真實開發環境的 Git Log，確保遊戲與現實工程的連結。

*   **數值映射邏輯**:
    *   **Cost (費用)**：修改的檔案數量 (影響範圍越大，所需心智負擔/能量越高)。
    *   **Attack (攻擊力)**：`Insertions (+)` (代表建設性開發或重構帶來的動能)。
    *   **Defense (防禦力)**：`Deletions (-)` (代表消除技術債、提高系統韌性)。
    *   **Title/Flavor Text**：Commit 標題 (例如 "Fix memory leak")。
*   **LEAN TDD 斷言**: 所有字串解析與數據轉換必須在沒有 UI 的環境下，透過 `MiniTest` 進行 100% 的純數學與邏輯斷言。不依賴外部環境的 Flaky Tests。

### 第二層：Slay the Spire 的極致資訊密度 (View - Data)
遵循「一眼看穿戰局 (Information First)」的原則，特別針對無頭自動化戰鬥做視覺化處理：
*   **富文本卡牌資訊 (RichTextLabel)**：使用 BBCode 渲染來自 Git 的數據：`"[b]{commit_msg}[/b]\n[color=#4ade80]+{insertions} Additions[/color]\n[color=#f87171]-{deletions} Deletions[/color]"`。
*   **敵人意圖 (Intents)**：在敵人頂部掛載 `HBoxContainer`。當底層邏輯設定傷害時，立即在 UI 反映（例如一把劍圖示加上 "30"），並且支援滑鼠懸停顯示 Tooltip 解釋詳細計算。

### 第三層：爐石戰記的物理實體感 (View - Juice)
View 層的作用是「聆聽」Model 變化，並利用 `create_tween()` 創造「實體物件 (Physical Object)」的操作回饋，絕不干涉狀態機邏輯。
*   **非靜默彈出 (Material & Tactility)**：選單與對話框透過 Tween 實作彈出與翻轉，配合厚重音效。
*   **卡牌實體感 (Hover Weight)**：滑鼠懸停時，使用 Cubic Easing 將卡牌微微放大、向 Z 軸提升，並附帶紙張摩擦音效，創造實體桌遊感。
*   **全息對話框 (Piano Glass)**：融合科幻風格，對話框使用半透明 `StyleBoxFlat` 毛玻璃材質，並利用 `visible_characters` 實作 AI Agent 的打字機特效 (Typewriter Effect)。