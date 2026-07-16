# Phase 5.8.18 - TDD 物理對齊與幽靈淨化 (TDD Alignment & Ghost Purification)

> **建立日期**: 2026-07-16
> **核心目標**: 償還 UI 流程與 TDD 規格之間的技術債，消滅幽靈文件，徹底實作被遺忘的底層遊戲性 (Action Cards 與 PlayArea 限制)。

## 背景與問題陳述 (Context & Problems)
在經過詳細的 `git log` 與物理代碼探勘後，我們發現目前的 Godot 客戶端存在以下嚴重偏離 `@TDD_Recontextualization.md` 的技術債與錯誤：
1. **主選單 UI 斷層 (UI Flow Disconnect)**：`MainMenu` 從未實作「駭客檔案 (Tab 1)」與「卡牌工坊 (Tab 3)」的入口，導致玩家無法完成 TDD 所定義的 Hub 樞紐流程。
2. **無聊的文字輸入框 (The Enter Key Hotfix)**：`GameBoard` 目前仍依賴在輸入框按下 `Enter` 鍵來觸發檢索，完全缺失了 TDD 規劃的核心「行動卡 (Action Cards)」系統。
3. **無限手牌導致 Token 溢出 (Infinite Context Window)**：`PlayArea` 缺乏最大手牌容量 (5 張) 的限制，這會造成 RAG 檢索時後端 LLM 的 Token 溢出崩潰。
4. **過場動畫引發的記憶體洩漏 (Tween Memory Leak)**：`MainMenu` 的場景切換動畫未採用延遲呼叫 (`call_deferred`)，導致底層 `CanvasItem` 資源無法正確釋放。
5. **偽證的 UML 文件**：`player_journey_uml.md` 宣稱反映現有代碼，卻描繪了代碼中不存在的 UI 流程，淪為幽靈文件。

---

## 實作任務清單 (Action Items)

### 任務一：修復 MainMenu 樞紐斷層
* [ ] 在 `MainMenu.gd` 的 `_trigger_action()` 中，補齊 Tab 1 (CharacterDashboard) 與 Tab 3 (CardWorkshop) 的信號 (`request_character_dashboard`, `request_card_workshop`)。
* [ ] 在 `MainMenuController.gd` 實作對應的接收邏輯與 `@export` 場景變數。
* [ ] 更新 `MainMenu.tscn` 中的 `CarouselContainer`，加入兩個全新的按鈕與對應的 Gem 圖示。

### 任務二：拔除 Enter 鍵熱修復並實作行動卡 (Action Cards)
* [ ] 拔除 `GameBoard.gd` 中的 `query_input.text_submitted` 綁定。
* [ ] 在 `CardData.gd` 或相關資源目錄中，實作 TDD 規定的三種 L1~L3 行動卡（BM25 實彈卡、Dense Vector 向量雷射、Reranker 電漿護盾）。
* [ ] 在戰鬥介面加入「出牌」邏輯，玩家必須將行動卡拖曳或點擊打出，才能觸發對應的檢索或過濾行為。

### 任務三：PlayArea 容量限制與防呆
* [ ] 在 `PlayArea.gd` (或 `HandData.gd`) 的 `_can_drop_data` 或陣列操作中，加入容量上限檢測 (Max = 5)。
* [ ] 若超過容量，拒絕卡牌放入並在 UI 顯示「Context Window Full」的警告提示。

### 任務四：修復 Tween 記憶體洩漏
* [ ] 審查 `MainMenu.gd` 與其他 UI 控制器，將所有在 `tween.finished` 中觸發 `change_scene_to_...` 的回呼，改為使用 `target_signal.call_deferred()` 或利用 `get_tree().create_timer()` 安全交接。

### 任務五：幽靈文件淨化與公證
* [ ] 重構並更新 `player_journey_uml.md`，確保它在開發完成後，能 100% 精準對齊實體代碼的流程。
* [ ] 執行無頭自動化測試 (`make test-headless`)，確保所有的 UI 修改與依賴注入皆未引發 Regression。
