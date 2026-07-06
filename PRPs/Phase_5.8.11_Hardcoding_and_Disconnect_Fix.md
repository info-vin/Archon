# Phase 5.8.11: 微控制器解耦與測試防禦 (Hardcoding & Disconnect Fix)

## 1. 目標 (Goal)
解決專案中的「硬編碼 (Hardcoding)」與「斷層 (Disconnect)」技術債，特別是濫用 `preload()` 載入具備 `class_name` 的全域類別，以及寫法冗贅的條件判斷。

## 2. 核心問題與解決方案 (Problems & Solutions)

### 2.1 濫用 `preload()` 的硬編碼問題
* **問題**：許多腳本（例如 `GameState.gd`, `MatchBuilder.gd`, `EnvironmentManager.gd`, `CardEffectResolver.gd` 等）使用了類似 `var GameBalanceConfig = preload("res://src/models/GameBalanceConfig.gd")` 的寫法。
* **斷層風險**：Godot 4 的核心機制是 `class_name`。既然這些檔案已經宣告了 `class_name`，透過字串路徑進行 `preload()` 不僅多餘，且當檔案被移動時會導致嚴重斷線，是典型的反模式 (Anti-pattern)。
* **解決方案**：全面掃描 `src/` 目錄，移除對全域類別的冗餘 `preload()`，直接使用 `class_name`（如 `GameBalanceConfig`, `DeckData`）。

### 2.2 `BattleRuleEngine.gd` 寫法優化
* **問題**：三元運算子寫法過於冗長，且重複呼叫 `card.get("type")`：
  `var type_val = card.get("type") if card.get("type") != null else CardData.CardType.DATA_CHIP`
* **解決方案**：簡化為更具 Pythonic/GDScript 風格的寫法，例如 `var type_val = card.get("type") if "type" in card else CardData.CardType.DATA_CHIP` 或者直接強型別轉換。

## 3. 執行清單 (Execution Plan)

1. [ ] 掃描並替換 `GameState.gd` 中的 `DeckData`, `HandData`, `MatchBuilder`, `SearchController`, `EnvironmentManager` 的 `preload`。
2. [ ] 掃描並替換 `EnvironmentManager.gd` 與 `MatchBuilder.gd` 中的 `GameBalanceConfig` 的 `preload`。
3. [ ] 掃描並替換 `CardEffectResolver.gd` (以及其他) 對 `BattleRuleEngine` 的冗餘宣告。
4. [ ] 掃描並替換 `AgentCompanion.gd` 對 `ChaosEventPool` 等類型的 `preload`。
5. [ ] 修正 `BattleRuleEngine.gd` 中的迴圈內條件判斷式。
6. [ ] 執行 `make test-godot` (或 `HeadlessRunner`) 確保改動不會破壞既有單元與 E2E 測試。
