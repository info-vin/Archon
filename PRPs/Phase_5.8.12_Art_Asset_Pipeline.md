# Phase 5.8.12: Art Asset Pipeline (Godot Native)

## 目標 (Goal)
廢除依賴外部 Python 與 `uv` 環境的一次性縮圖腳本，將「美術資源瘦身」與「卡牌動態合成」全面內建於 Godot 引擎中，確立零斷層的實體開發管線。

## 核心名詞與功能定義 (Core Definitions)
為避免「合成」一詞造成的語意混淆，本專案嚴格區分以下三個層次的功能，絕不可混為一談：

1. **開發期降階工具 (Asset Downscaling Tool)**
   - **定位**：開發階段的自動化腳本 (`AssetOptimizer.gd`)。
   - **職責**：開發者 (TA) 在放入大尺寸原圖後，於編輯器內**手動觸發**。它會立刻掃描並將原圖物理覆寫為遊戲可用的小尺寸（例如 256x256）。
   - **禁忌**：絕對禁止在玩家執行遊戲 (Runtime/Loading) 時才進行降階。

2. **動態組合樣卡 (Visual UI Assembly)**
   - **定位**：純粹的視覺呈現層 (View)，即 `CardChip.tscn` 搭配 `OctagonMask.gdshader`。
   - **職責**：利用 Shader 在 GPU 端，將「空白底框」與「八角形晶片」圖層疊加，負責畫面的「排版」。
   - **禁忌**：它只是純 UI 骨架，**不包含**任何遊戲機制。且必須落實「零硬編碼 (Zero Hardcoding)」，開放介面接收動態資料，嚴禁寫死圖片路徑。

3. **卡牌升階機制 (Gameplay Crafting/Synthesis)**
   - **定位**：遊戲核心玩法 (Controller/Model)。
   - **職責**：玩家在工作坊消耗低階素材，經由機率判定與特效播完後，獲得高階卡牌。
   - **禁忌**：這不是單一 UI 場景能負責的邏輯，由獨立的系統（如 `GameState`）負責更新資料庫與庫存狀態。

## 執行進度與技術細節 (Execution Progress & Technical Details)
**狀態: 🟢 已完成 (Completed)**

本次實作徹底移除了所有不穩定的一次性 Python/Shell 腳本，完全改用語意正確的 Godot 引擎原生工具與 UI 系統完成。
- **動態樣卡生成與 UI 生命週期修復**：實作了 `CardChip.tscn` 作為動態卡牌骨架。在除錯過程中，我們解決了 Godot 4 中 `MarginContainer` 動態修改錨點 (Anchors) 時因為沒有強制重置 Offset (`PRESET_FULL_RECT`) 而導致子物件被壓縮成 `0x0` 的黑洞陷阱；並解決了 `@onready` 生命週期在實例化 (`instantiate`) 與節點掛載 (`add_child`) 時的時序問題，透過將文字變數 (`stats_text`) 匯出並在 `_ready()` 中綁定，確保資料 100% 渲染。
- **Shader 與美術融合**：捨棄了單純的裁切，最終實作了 `HexagonMask.gdshader`。考量到原圖 `card_frame_blank.png` 中央並非透明，我們採用了 `render_mode blend_add` 的全像投影 (Holographic) 發光混合技術，並將原畫作進行 `0.75x` 縮放，完美套入金屬框內部。
- **動態多國語系字典**：全面廢除硬編碼字串，透過 `translations.csv` 實現標準的 Godot 語系管理 (TranslationServer)，並修復了實體檔名 (`chip_red_noise.png`) 與字典 Key 不匹配的歷史錯誤。
- **一次性除錯腳本清理**：依照開發紀律，所有作為過渡測試用的 `build_card_chip.gd` 與 `capture_gallery.gd` 等一次性腳本皆已被徹底刪除，確保程式碼庫保持純淨。

## 實作模組 (Implementation Modules)

### 1. `AssetOptimizer.gd` (開發期自動降階工具)
作為繼承 `EditorScript` 的開發工具，提供以下功能：
- **開發者手動觸發**：美術人員將原圖放入後，於編輯器內執行此腳本即可完成物理替換，確保全團隊環境統一。
- **安全防禦**：使用 `FileAccess` 與 `DirAccess` 動態掃描目錄，嚴禁硬編碼絕對路徑。找不到檔案時必須噴出具體的 Error Log，禁止靜默失敗。
- **高品質縮放**：使用 `Image.INTERPOLATE_LANCZOS`。
- **正方置中裁切**：使用 `Image.get_region(Rect2i)` 演算法。

### 2. `HexagonMask.gdshader` (六角形全像投影遮罩)
一個標準的 CanvasItem Shader，考量到底框並非透明，採用了 `render_mode blend_add` 將影像以發光疊加的方式鑲嵌。動態透過縮放與裁切將方形晶片紋理鑲嵌進入卡牌底框。

### 3. `CardChip.tscn` (動態組合樣卡 UI 骨架)
單一卡牌的 UI 骨架。負責將材質與文字動態組合。依據 `TDD_Recontextualization.md` 規範，此檔案存放於 `src/views/CardChip.tscn`。
- **圖鑑預覽**：實作了 `CardGalleryPreview.gd`，透過 `DirAccess` 動態掃描素材目錄，並透過程式化 `Instantiate()` 實例化卡牌骨架並注入動態生成的 BBCode (`RichTextLabel`) 參數。

## 歷史教訓 (Historical Lessons)
- **【視覺認知修正與 Shader 對策】**：在之前的規劃中，曾誤以為可以使用八角形遮罩直接挖空，但由於 `card_frame_blank.png` 的中央是實體的深色背景，傳統 `mix` 會覆蓋陰影。改用 `blend_add` 後獲得了極佳的駭客風格發光效果。
- **【Godot UI 排版防呆】**：嚴格禁止在沒有先呼叫 `set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)` 的情況下，透過腳本修改 Container 的錨點，否則會導致 UI 元件在生成時坍縮至 0x0 而完全消失。
- **【翻譯檔嚴謹度】**：翻譯字典 (CSV) 的 Key 必須與實體資源檔名（如 `chip_red_noise.png`）嚴格 100% 物理對齊，拒絕任何主觀的名稱縮寫或幻覺，否則會導致線上漏翻。
