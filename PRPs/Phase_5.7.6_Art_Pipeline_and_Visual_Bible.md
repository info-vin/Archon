# Phase 5.7.6: Art Pipeline & Visual Bible (美術管線與視覺聖經)

## 📌 核心目標 (Objective)
解決前期開發中「美術管線缺乏細節思考」與「視覺風格缺乏基準」的嚴重問題。將硬編碼的美術數值抽離，並確立符合「Cyberpunk 霓虹 + 復古像素」的高品質視覺規範，徹底解決紙娃娃圖層疊加與裁切偏移的災難。

## 🔍 痛點分析與歷史盲點 (Pain Points)
1. **連通域裁切災難 (Bounding Box Trimming Loss)**：
   * 過去的 Python 腳本 (`process_sprites.py`) 在去除透明背景時，採用了緊湊的 Bounding Box 裁切。這破壞了每個部位（頭髮、衣服、眼睛）相對身體的原始空間座標。
   * **骨牌效應**：導致程式端 (`ModularAgent.gd`) 必須填寫 `Vector2(0, -27)` 這種不合理的魔法偏移量才能將五官對齊。
2. **AI 生成穿模 (Prompt Overlap Issue)**：
   * 先前的生成提示詞缺乏物理隔離約束，導致圖層融合，無法透過腳本完美剝離。
3. **無視覺聖經 (Lack of Art Bible)**：
   * 缺乏具象化的 UI Mockup，僅靠文字描述難以對齊團隊認知。

## 🎯 實作計畫 (Action Plan)

### 1. 建立《視覺聖經》與視覺錨點
*   **任務**: 生成並確立最高品質的 UI 概念圖，並總結成《Art Bible》。
*   **狀態**: 🟢 **已完成 (Completed)**
*   **產出物**:
    *   主遊戲視角概念圖：`PRPs/neon_tycoon_ui_mockup.jpg`
    *   創角面板概念圖：`PRPs/character_creator_mockup.jpg`
    *   視覺規範文件：`docs/game_design/Art_Bible.md`

### 2. 嚴格網格制 AI 提示詞 (Strict Grid Prompts)
*   **任務**: 制定新的 AI 生成規範，強制 AI 在 3x3 或 4x4 的網格內作圖，確保各部位完全物理隔離，不可有任何穿模交疊。
*   **規格**:
    *   要求 `solid white background`。
    *   各部位（Base Body, Outfit, Hair, Eyes, Tools）必須分列/分行排列。

### 3. 重構 Python 切圖腳本 (Refactor Extraction Pipeline)
*   **任務**: 廢除過去自動裁切空白的作法。
*   **規格**: 新的 `process_sprites.py` 必須依照固定的網格尺寸（如 64x64）進行切割，**100% 保留所有的透明像素與邊距**。
*   **目的**: 讓所有的圖層 PNG 在進入 Godot 後，中心點皆能完美對齊 `Vector2(0, 0)`，徹底消滅程式碼中的魔法數字。

### 4. Godot 動畫狀態機升級 (AnimationTree Implementation)
*   **任務**: 放棄單純的 `Tween` 縮放（紙片平移），導入真正的幀動畫 (`Sprite Frames`) 配合 `AnimationPlayer` 與 `AnimationTree`，呈現工作敲擊、走路等生動態勢。

## 📁 相關檔案與路徑
*   `docs/game_design/Art_Bible.md` (美術聖經文件)
*   `PRPs/neon_tycoon_ui_mockup.jpg` (UI 概念圖)
*   `PRPs/character_creator_mockup.jpg` (創角概念圖)
*   `archon-agency-tycoon/Scripts/Main.gd` (修正任務同步邏輯)
*   `archon-agency-tycoon/Scripts/Logic/SimulationEngine.gd` (修正 MVC 架構)
