# Phase 5.8.10 - 微控制器解耦與測試防禦 (Micro-Controller Refactoring & Test Hardening)

## 🎯 階段目標 (Phase Objective)
由於 `GameState.gd` 在開發過程中承載了過多職責 (God Object 反模式)，本階段目標是將其內部邏輯解耦至獨立的微控制器 (Micro-Controllers) 中，並徹底淨化無頭測試 (Headless Tests) 的依賴污染，同時消滅寫死在程式碼中的硬編碼 (Hardcoding)。

## 🛠️ 開發任務 (Tasks)

### 1. 微控制器解耦 (L2 Architecture Refactoring)
*   **提取環境管理器 (EnvironmentManager)**：接管 SLA 計時器與資料庫投毒機制的 `_process` 生命週期。
*   **提取搜尋控制器 (SearchController)**：接管 Query 解析與手牌抽取邏輯。
*   **提取配對建構器 (MatchBuilder)**：接管不同 Sector 難度初始化與任務分發。
*   **重構 GameState 作為組合根 (Composition Root)**：`GameState` 現在只負責狀態數據的儲存與跨控制器事件派發。

### 2. 無頭測試防禦機制 (Headless Test Hardening)
*   **單例淨化 (Singleton Purging)**：解決無頭測試中因手動實例化全域變數導致的跨測試記憶體污染。在每個測試的 setup 階段強制執行 `Engine.unregister_singleton()`。
*   **消除 ClassName 解析錯誤**：強制要求測試腳本與底層庫使用 `preload("res://path").new()`，避免依賴 Godot 編輯器才有的全域類別緩存。
*   **依賴注入封裝 (DI Pattern)**：將冗長的三元運算子單例獲取方式 (e.g. `Engine.has_singleton`) 封裝至 `AutoloadLocator` 靜態工具中。

### 3. 消滅硬編碼 (Eradicate Hardcoding)
*   **集中魔術數字 (Magic Numbers)**：將 `BattleRuleEngine.gd` 內的寫死數值（如 1.5 倍連鎖乘數、50% HP 判斷等）全部遷移至 `GameBalanceConfig.gd`。

## ✅ 驗收標準 (Acceptance Criteria)
- [x] 所有 14 項無頭單元與整合測試順利通過，零編譯與執行期錯誤。
- [x] 成功通過 `ssot_alignment_audit` 單一事實來源審計。
- [x] 代碼中無殘留的三元運算子 `has_singleton` 散落，統一經由 Locator 獲取。
- [x] `BattleRuleEngine` 等核心引擎 100% 依賴 `GameBalanceConfig`。
