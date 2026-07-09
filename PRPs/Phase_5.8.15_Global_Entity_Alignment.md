# Phase 5.8.15: Global Entity Alignment (全域實體對齊與幽靈淨化)

## 目標 (Objective)
解決遊戲紀錄機制 (`SaveManager.gd`) 與核心/測試模組中，卡牌 ID 硬編碼與 SSOT (`Art_Asset_Prompts.md` / `resources/`) 嚴重脫鉤的斷層問題。消滅「幽靈卡牌」並將所有卡牌 ID 統一對齊至最新的 `action_*` 命名空間。

## 證據與現狀分析 (Evidence & Current State)
依據實體檢索 (`grep_search`)，發現以下嚴重斷層：

1. **幽靈卡牌 (Phantom Cards)**
   - `SaveManager.gd` 預設載入了 3 張未定義於 SSOT、無美術圖、無實體資源的卡牌：`filter_by_date`, `author_query`, `web_crawler`。
   - `CardManagementMenuController.gd` 為了這些幽靈卡寫死了假字典資料。

2. **命名空間錯位 (Namespace Mismatch)**
   - 全域代碼與測試檔廣泛使用舊版 ID：`keyword_search`, `dense_search`, `reranker`。
   - 最新 SSOT 與 `GenerateCardResources.gd` 產出的 `.tres` 資源使用新版 ID：`action_keyword`, `action_dense`, `action_reranker`。

3. **受污染的檔案清單 (Polluted Files List)**
   - **核心單例與配置**: `SaveManager.gd`, `GameBalanceConfig.gd`
   - **MVC 控制器**: `MatchBuilder.gd`, `CardEffectResolver.gd`, `CardManagementMenuController.gd`, `CardWorkshop.gd`, `CardWorkshopController.gd`
   - **UI 元件**: `CardSlot.gd`
   - **測試公證檔**: `Screenshotter.gd`, `test_meta_progression.gd`, `test_save_manager.gd`, `test_talent_modifiers.gd`, `test_visual_integration.gd`

## 實作計畫 (Implementation Plan)

### Step 1: 淨化 SaveManager 與全域常數
- **目標檔案**: `src/autoloads/SaveManager.gd`, `src/models/GameBalanceConfig.gd`
- **操作**: 
  - 徹底刪除 `filter_by_date`, `author_query`, `web_crawler`。
  - 將預設陣列中的舊 ID 替換為 `action_keyword`, `action_dense`, `action_reranker`。
  - 將 `GameBalanceConfig.gd` 中的 `CARD_KEYWORD` 常數值修改為 `action_keyword`。

### Step 2: MVC 控制器與 UI 解耦修復
- **目標檔案**: `src/views/CardManagementMenuController.gd`, `src/models/cards/CardEffectResolver.gd` 等
- **操作**:
  - 將 `CardEffectResolver.gd` 中解析邏輯 `elif card_id == "keyword_search":` 等分支，更新為 `action_keyword`。
  - 清理 `CardManagementMenuController.gd` 中寫死的假字典，並確保起始解鎖陣列對齊新 ID。
  - 將 `CardWorkshopController.gd` 與 `CardSlot.gd` 中的 `KEYWORD_SEARCH` 大寫硬編碼，統一替換為對應的新 ID。

### Step 3: 測試框架與公證檔對齊
- **目標檔案**: 包含 `test_save_manager.gd`, `Screenshotter.gd` 在內的所有測試檔案。
- **操作**: 
  - 全面將測試斷言中的舊 ID 替換為 `action_*`。
  - 確保 `test_visual_integration.gd` 在加載時指向正確的 `action_keyword.tres` 而非舊檔名。

### Step 4: 物理無頭公證 (Headless Testing)
- **操作**: 執行 `godot --headless -s tests/HeadlessRunner.gd`，確保沒有因為 ID 修改而產生任何紅字錯誤，並保證所有的測試依舊 100% 通過。

---
**※ 備註 (Notes):** 
本計畫嚴格遵守「絕不盲猜」與「物理公證」原則，所有修改目標皆為透過 `grep` 搜索獲得的實體行數。未提及的擴充卡 (L1-L5) 將在未來功能解鎖實作時再行加入預設列表。

## 執行結果 (Execution Result)
- [x] **Step 1 ~ Step 3 完成**: 成功淨化 13 支實體腳本，幽靈資料全面移除，ID 命名空間統一為 `action_*`。
- [x] **技術債修復**: 發現並修復了 7 月 7 日的開發技術債 (意外刪除 `GameBoard.tscn` 外部資源造成的毀損)。
- [x] **Step 4 物理公證**: `Passed: 15 / Failed: 0`，全域無頭測試通過。
- **狀態**: 🟢 **已結案 (Closed)**
