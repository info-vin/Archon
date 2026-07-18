# Phase 5.8.21: Premium Player Status HUD (SDF Implementation)

## 🎯 核心目標 (Core Objective)
基於 TDD_Recontextualization 規範與最新的高質感科幻視覺參考圖，全面重構玩家狀態列 (Player Status HUD)。徹底捨棄傳統粗糙的進度條 (ProgressBar)，導入基於有向距離場 (SDF, Signed Distance Fields) 的頂級 Shader 技術，以抗鋸齒、高亮度發光、完美折角的外觀，精準對應玩家的「4 大核心本錢」。

---

## 📐 資源對應架構 (Resource Mapping Architecture)
新的 HUD 視覺將嚴格對應以下四大玩家資源：

1.  **純淨度 (Purity)**：對應左側**大圓環與中央百分比數字**。
2.  **職級 (Rank)**：對應右上角斜切邊緣頂部的 **標籤文字 (原圖中的 LOADING...)**。
3.  **特務血量 (Player HP)**：對應右側面板的 **水平發光長條**。
4.  **行動點數 (AP)**：對應右下角的 **連續正三角形分段能量格**。

---

## 🛠️ 實作計畫細節 (Implementation Details)

### 1. 頂級著色器開發 (Shader Layer)
*   **檔案位置**：`src/views/shaders/PlayerStatusHUD.gdshader` (與 `.tres` 材質檔)
*   **技術規格 (SDF)**：
    *   使用 `sdCircle` 繪製左側環形。
    *   使用 `sdSegment` 計算精準的折角多邊形外框。
    *   使用 `sdEqTriangle` 陣列迴圈渲染 AP 點數格。
    *   導入 `smoothstep` 進行邊緣極致抗鋸齒 (Anti-aliasing)。
    *   疊加 `exp(-dist)` 指數函數實現動態光暈 (Bloom)，呈現高級雷射質感。
*   **導出參數 (Uniforms)**：
    *   `purity_pct` (float, 0.0~1.0)
    *   `hp_pct` (float, 0.0~1.0)
    *   `ap_current` (int), `ap_max` (int)

### 2. UI 節點掛載與無損文字疊加 (UI Component Layer)
*   **檔案位置**：`src/views/components/PlayerStatusHUD.tscn` (與 `.gd` 腳本)
*   **節點結構**：
    *   建立一個根節點 `Control` 負責排版佔位。
    *   加入 `ColorRect` 並套用 `PlayerStatusHUD.tres`，負責算繪底層所有絢麗光影與邊框。
    *   **無損文字疊加技術**：在 `ColorRect` 上方，利用 Godot 原生 `Label` 節點精準對齊放置 `PurityLabel` (顯示 50%) 與 `RankLabel` (顯示 [RANK] L4)，確保字體在任何解析度下保持絕對銳利，且完美支援多國語系 `translations.csv`。

### 3. 主場景整合與訊號對接 (Integration)
*   **檔案位置**：`src/views/components/GameHUD.tscn` / `GameHUD.gd`
*   **執行步驟**：
    1.  從舊版的 `GameHUD` 中移除原有的普通 `PlayerHPBar`、`PurityBar` 以及單純文字的 `CareerLabel` 與 `APLabel`。
    2.  將全新的 `PlayerStatusHUD.tscn` 實體化並崁入 `GameHUD.tscn` 的左半部。
    3.  在 `GameHUD.gd` 中串接對應的狀態更新函式 (例如接收玩家扣血、扣除 AP 的事件)，並將數值轉換後同步寫入 `PlayerStatusHUD` 的 Shader 參數與文字節點中。

---

## 🛡️ 品質保證與門禁 (Quality Gates)
*   **視覺門禁**：不可使用會產生嚴重鋸齒的 `if/else` 硬切像素，必須保證所有斜切線條平滑。
*   **架構門禁**：文字絕對不可硬編碼在 Shader 內，必須分離為原生 UI Label 節點。
*   **相容性**：確保此 HUD 在 `GameBoard.tscn` 的無頭測試環境 (Headless Mode) 下不會引發空指標錯誤 (Null Pointer Exception)。
