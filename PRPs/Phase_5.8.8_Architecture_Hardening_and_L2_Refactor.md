# Phase 5.8.8: 架構硬化與 L2 模組化重構 (Architecture Hardening & L2 Refactoring)

> **前置相依：本階段承接 Phase 5.8.7 的全域美術遷移。**
> 本階段旨在徹底根除專案內部的硬編碼 (Hardcoding) 定時炸彈，並嚴格落實 TDD 規範與 `godot-4-audit` 的 L2 職責分離，同時導正目前存在的 MVC 架構反向依賴與狀態偷跑 (State Leaking) 嚴重問題。

## 目前實體進度 (Strict Reality Check)
* [ ] **根除路徑與魔法數字寫死 (Eradicate Hardcoding)**：尚未開始。
* [ ] **L2 核心職責剝離 (L2 Modularity)**：尚未開始。
* [ ] **MVC 架構導正 (MVC Alignment)**：尚未開始。
* [ ] **10/10 無頭測試公證 (Headless CI Verification)**：等待重構完成後執行。

---

## 1. 根除路徑與魔法數字寫死 (Eradicate Hardcoding)

經過物理掃描與比對 `TDD_Recontextualization.md`，目前系統中充滿違反最佳實踐的字串硬編碼。必須全面清查並改為 `@export` 靜態綁定或全域配置。

*   **1.1 網路 API 與 Fallback 路徑解耦**：
    *   將 `BackendClient.gd` 中寫死的 `http://127.0.0.1:8181/api/rag/hybrid-search` 移出，改由 `GameState` 或 `Constants.gd` 載入。
    *   將寫死的 JSON 測試檔案路徑 (`res://assets/data/...`) 提升為可外部設定的變數。
*   **1.2 UI 視覺素材靜態綁定**：
    *   `CardChip.gd`、`CharacterDashboard.gd` 與 `GameBoard.gd` 中的 `res://assets/...` 必須全數刪除，改為 `@export var icon_xxx: Texture2D` 等導出變數。
    *   透過 Godot Editor 進行介面上的實體節點綁定，利用引擎的靜態安全校驗機制杜絕執行期 404 (Path parsing errors)。

---

## 2. L2 核心職責剝離 (L2 Modularity)

針對目前 `GameBoard.gd` 與 `GameState.gd` 出現的「上帝類別 (God Object)」退化跡象，強制實施 `godot-4-audit` 第 4 條的 L2 拆分。

*   **2.1 視覺回饋層：`CombatJuice.gd`**
    *   建立專屬視覺特效節點，並掛載於 `GameBoard`。
    *   將 `GameBoard.gd` 中所有處理螢幕震動、UI 閃爍 (`Tween` / `modulate:a`) 等與核心流程無關的純視覺回饋邏輯移至此處。
*   **2.2 卡牌邏輯層：`CardEffectResolver.gd`**
    *   建立專門負責卡牌特技結算的類別 (Strategy Pattern)。
    *   抽出 `GameState.gd` 中硬編碼的 `if card_id == "reranker"` 與 "keyword_search" 等效果邏輯。

---

## 3. MVC 架構導正 (MVC Alignment)

導正當前「有 EventBus 之名，無 MVC 之實」的架構，確保單向資料流 (One-way Data Flow) 與正確的狀態同步。

*   **3.1 防堵 View 狀態偷跑 (`PlayArea.gd`)**
    *   **現狀問題**：View 在放開卡牌時，先自行播放溶解動畫並 `queue_free()` 刪除節點，才發送 `EventBus` 通知 Model。若 Model 驗證失敗，卡牌已消失。
    *   **修復方案**：View 在 `_drop_data` 僅發送 `EventBus.request_play_card(card)`。實體的卡牌刪除與溶解動畫，必須等待 Model 驗證並發送 `card_played` 信號後，View 接收到才執行。
*   **3.2 移除 View 內嵌商業邏輯 (`PlayArea.gd`)**
    *   移除 `PlayArea.gd` 內部對 `card.get("type") == 1` 與 `similarity < 0.5` 的直接判斷。UI 層只能依據 Model 的指示進行渲染與對話，不應攔截與判斷邏輯。
*   **3.3 修正 Model 越權控制器 (`GameState.gd`)**
    *   **現狀問題**：`GameState` 玩家血量歸零時，直接呼叫 `SaveManager.penalize_battle_loss()`。
    *   **修復方案**：改為純粹發送 `EventBus.game_over` 信號，由 `SaveManager` 或專職的 `Controller` 去監聽並執行對應儲存操作。

---

## 4. 測試驅動與驗證計畫 (TDD & Verification)

*   **靜態編譯公證**：重構過程中，所有變更皆須通過 `godot-4-audit` 的強型別檢查。
*   **100% 測試覆蓋維持**：透過 `HeadlessRunner.gd` 執行既有的 `test_composite_threats.gd` 等 10 項自動化測試，確保重構過程達到 **Zero Regression** (零退化)。
