# Phase 5.8.2: Recontextualization - 端到端遊戲迴圈與視覺整合 (E2E Gameplay Loop & Art Integration)

> **核心戰略：物理驗證優先，務實視覺回饋 (Physical Validation & Pragmatic UI)**
> 本階段承接自 Phase 5.8.0 與 Phase 5.8.1 的後端 API 與資料層架構。我們拒絕虛假開發與不必要的 AI 生成素材，專注於利用既有的 `Maaack` 佔位符號，將 RAG (Retrieval-Augmented Generation) 資料流轉化為玩家可拖曳的實體卡牌，並完成狀態機結算與 Tween 視覺回饋。

## 階段一：玩家操作交互 (Player Interactions)
**門禁**：必須使用 `Control` 節點的原生 Drag & Drop API，嚴禁使用 `_process` 進行物理追蹤計算。

*   ✅ **任務 1.1：卡牌拖曳介面 (`CardChip.gd`)**
    *   ✅ 實作 `_get_drag_data()`，將整張卡牌 (Control) 作為負載。
    *   ✅ 建立半透明的 `set_drag_preview`，讓玩家有直覺的拖曳手感。
*   ✅ **任務 1.2：出牌區判定 (`PlayArea.gd`)**
    *   ✅ 實作 `_can_drop_data()` 嚴格校驗資料來源是否為合法的卡牌晶片。
    *   ✅ 實作 `_drop_data()` 觸發卡牌的層級轉移 (Reparenting)。
*   ✅ **任務 1.3：無頭公證 (`test_drag_and_drop.gd`)**
    *   ✅ 在 Headless 模式下實體化 UI 節點，注入 `InputEvent` 模擬拖曳，斷言 `_drop_data` 成功觸發且節點正確轉移。

## 階段二：核心遊戲迴圈 (Core Game Loop & State Machine)
**門禁**：UI 節點絕對禁止包含任何遊戲邏輯。所有的 AP/HP 計算必須由獨立的 `GameState` Autoload 處理。

*   ✅ **任務 2.1：狀態管理器 (`GameState.gd`)**
    *   ✅ 建立全域 Autoload，持有一個 `DeckData` 作為當前 `active_context`。
    *   ✅ 監聽 `EventBus.card_played` 訊號，依照卡牌類型 (Data/Action) 扣除 AP 並計算對 Boss HP 的傷害。
*   ✅ **任務 2.2：HUD 介面解耦 (`GameBoard.tscn`)**
    *   ✅ 加入 `APLabel`, `ContextLabel`, `BossHPLabel`。
    *   ✅ 單向綁定 `GameState` 發出的 `ap_changed`, `hp_changed` 訊號進行文字更新。
*   ✅ **任務 2.3：無頭狀態機公證 (`test_state_machine.gd`)**
    *   ✅ 在無畫面狀態下發射 `card_played` 訊號，斷言 Boss 扣除的 HP 與 AP 符合預期。

## 階段三：視覺串接與動畫回饋 (Art Integration & Tweening)
**門禁**：拒絕使用 `generate_image` 進行虛假開發。直接套用 Maaack 素材包，並使用 `EventQueue` 確保動畫不重疊。

*   ✅ **任務 3.1：卡牌打擊與 Maaack 素材綁定 (Tween & Assets)**
    *   ✅ 物理複製 `maaack` 素材包於 `recontextualization/assets/maaack`，確保 `CardChip.gd` 的 `res://` 正確對應 PNG。
    *   ✅ 當卡牌放入 `PlayArea` 時，加入 Tween 彈性吸附動畫 (`TRANS_SPRING`)。
    *   ✅ 根據 Action/Data 類型播放不同的消失/微縮動畫，不再是虛假的生成路徑。
*   ✅ **任務 3.2：UI 震動回饋 (Shake/Flash)**
    *   ✅ 當 `GameState` 觸發 `hp_changed` (扣血) 時，Tween `BossHPLabel` 的位置左右震動並閃爍紅色。
*   ✅ **任務 3.3：非同步測試公證**
    *   ✅ 更新所有 Headless 測試，確保 `await tween.finished` 不會在無算繪環境下導致 Engine 崩潰，全測試 100% 通過。

---
**Phase 5.8 MVP 狀態：已完成 (Completed) 🟢**
*自此，從 FastAPI 後端取得 RAG JSON -> Godot 生成卡牌 -> 玩家拖曳打擊 -> 數學結算與動畫 的核心端到端迴圈已經完全打通。*
