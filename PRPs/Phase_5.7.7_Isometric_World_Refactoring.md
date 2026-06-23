# Phase 5.7.7: Isometric World Refactoring (等距世界與視覺對齊重構)

## 📌 核心目標 (Objective)
徹底打破目前基於「UI 容器排版 (`GridContainer`)」的偽場景架構，將遊戲底層渲染架構全面升級為「等距/俯視角 (Isometric/Top-Down)」的 `Node2D` 實體世界。所有的程式重構與美術切割，皆須 100% 對齊視覺聖經中的概念圖 (`neon_tycoon_ui_mockup.jpg`)，實現真正的空間深度、遮擋關係與無障礙的遊戲操作體驗。

## 🔍 架構落差與痛點分析 (Architecture Gaps)
1. **空間維度的錯置 (The Container Trap)**：
   * 目前 `Main.tscn` 將房間塞在 UI `PanelContainer` 內，導致場景大小受限於視窗拉伸。
   * **解法**：全面解耦。建立一個無限延伸的 `Node2D` 作為真正的世界根節點，並引入 `Camera2D` 負責視野的平移與縮放。
2. **缺乏 Y 軸深度排序 (The Y-Sort Crisis)**：
   * 目前的辦公桌與家具是「畫死 (Baked)」在房間背景圖上的。小人無法走到桌子後方，視覺上會產生在背景「飄移」的假象。
   * **解法**：必須將房間底圖拆解。地板與牆壁作為底圖（Layer 0），所有的桌子、伺服器、飲水機必須拆成獨立的 `Sprite2D`（Layer 1），並將整個房間的 `y_sort_enabled` 設為 `true`。
3. **UI 喧賓奪主 (UI Obscuring the Ant Farm)**：
   * 目前的 UI 採用 `HBoxContainer` 與遊戲畫面瓜分螢幕空間，擠壓了真正的模擬經營畫面。
   * **解法**：引入 `CanvasLayer`。將 TopBar（資金/信譽）、RightPanel（事件日誌/雷達）與 BottomBar（指令按鈕）移至浮動的 UI 層，使世界地圖能 100% 鋪滿螢幕底層。

## 🎯 實作計畫 (Action Plan)

### Step 1: 基礎設施拆分 (World & UI Decoupling)
*   **任務**: 重構 `Main.tscn`，將場景一分為二。
*   **規格**:
    *   新增 `CanvasLayer` 命名為 `UILayer`，將所有的 UI 面板移入其中，並設定 Anchors 貼齊邊緣。
    *   新增 `Node2D` 命名為 `World`，作為所有辦公室房間與員工的實體容器。
    *   新增 `Camera2D`，綁定自訂的 Pan & Zoom 拖曳腳本，取代現有的 `ScrollContainer`。

### Step 2: 家具與背景的物理剝離 (Asset Slicing for Depth)
*   **任務**: 將原本死板的 `dev_room_bg.png` 等房間背景進行拆解。
*   **規格**:
    *   將「地板」抽出作為基底貼圖。
    *   將「辦公桌」、「白板」等家具切成獨立的 PNG，並在場景中以獨立的 `Sprite2D` 重建。
    *   開啟房間節點的 `Y-Sort`，確保 `ModularAgent` 在 Y 軸高於桌子時，會被桌子正確遮擋。

### Step 3: 空間座標系重構 (Coordinate System Migration)
*   **任務**: 修正所有基於 UI 的假座標。
*   **規格**:
    *   將現有的 `Marker2D` (`DeskPoint`, `StandPoint`) 從 UI 的相對像素座標，轉換為 `World` 中的絕對全域座標。
    *   修改 `SimulationEngine` 與 `AgentRouter` 的尋路邏輯，讓角色能正確在 2D 世界中移動，不受 UI 縮放影響。

### Step 4: 霓虹風格對齊 (Neon Style Alignment)
*   **任務**: 將目前的灰色調/高亮 UI，全面替換為 Mockup 圖中的暗色系玻璃擬物化風格。
*   **規格**:
    *   UI 背景全面改為 `Color(0.1, 0.1, 0.1, 0.8)` 帶透明度的暗黑風格。
    *   數值與文字套用發光的 `#39ff14` (綠)、`#fde910` (黃)、`#ff003c` (紅)。
    *   導入像素字體 (VT323 或相似字型) 替換系統預設字體。

## 🛡️ 單一事實管理 (SSOT & Quality Gates)
*   本階段的所有修改，必須以 `neon_tycoon_ui_mockup.jpg` 為最終視覺驗收標準 (Visual Quality Gate)。
*   完成 Step 1~3 後，必須再次執行 `capture_interactive_ui.gd` 產生實體驗證圖，確認房間的 Y-Sort 深度關係正確生效。
