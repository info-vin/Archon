# Phase 5.8.12: Art Asset Pipeline (Godot Native)

## 目標 (Goal)
廢除依賴外部 Python 與 `uv` 環境的一次性縮圖腳本，將「美術資源瘦身」與「卡牌動態合成」全面內建於 Godot 引擎中，確立零斷層的實體開發管線。

## 核心設計理念 (Core Principles)
1. **拒絕外部依賴 (Zero External Dependency)**：美術人員將原圖放入專案後，無需離開 Godot 編輯器，即可透過內建的 `@tool` 腳本自動降階並覆寫，保證全團隊環境統一。
2. **動態渲染取代靜態合成 (Dynamic Rendering over Static Mockups)**：不在硬碟中儲存任何合成後的卡牌圖片。底框與晶片作為獨立的 Sprite/Texture 載入，利用 Shader 在 GPU 端進行即時合成與遮罩。
3. **物理精準的遮罩 (Physically Accurate Masking)**：卡槽設計為**「八邊形倒角正方形 (Octagon / Chamfered Square)」**，必須透過 Shader 的數學算法精準裁切邊緣，嚴禁使用 Alpha Blend 導致的色彩失真。

## 實作模組 (Implementation Modules)

### 1. `AssetOptimizer.gd` (美術自動降階工具)
作為繼承 `EditorScript` 的開發工具，提供以下功能：
- **安全防禦**：使用 `FileAccess` 與 `DirAccess` 動態掃描目錄，嚴禁硬編碼絕對路徑。找不到檔案時必須噴出具體的 Error Log，禁止靜默失敗。
- **高品質縮放**：使用 `Image.INTERPOLATE_LANCZOS` 取代 Python 的 Pillow 演算法。
- **正方置中裁切**：使用 `Image.get_region(Rect2i)` 演算法，將非等比原圖進行安全裁切。

### 2. `OctagonMask.gdshader` (八角倒角遮罩)
一個標準的 Fragment Shader，擁有暴露的 `chamfer_ratio` 參數（預設 `0.18`），動態將方形晶片紋理的四個角落捨棄 (`discard`)，使之完美鑲嵌進入卡牌底框。

### 3. `CardChip.tscn` (實體 UI 組件)
卡牌合成的最終 Godot 場景，負責呈現動態合成的視覺結果，確保開發者能隨時預覽。依據 `TDD_Recontextualization.md` 規範，此檔案存放於 `src/views/CardChip.tscn`。

## 歷史教訓 (Historical Lessons)
- **【視覺認知修正】**：在之前的規劃中，曾誤將卡槽邊界稱為「六角形」，這會導致左右邊緣被切除產生黑邊。本階段嚴格糾正為「八角形倒角正方形 (Octagon)」，四邊平直，四角傾斜。
