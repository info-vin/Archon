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