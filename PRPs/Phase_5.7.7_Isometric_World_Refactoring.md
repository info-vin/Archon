# Phase 5.7.7: Isometric World Refactoring (等距世界與視覺對齊重構)

## 📌 核心目標 (Objective)
徹底打破目前基於「UI 容器排版 (`GridContainer`)」的偽場景架構，將遊戲底層渲染架構全面升級為「等距/俯視角 (Isometric/Top-Down)」的 `Node2D` 實體世界。所有的程式重構與美術切割，皆須 100% 對齊視覺聖經中的概念圖 (`neon_tycoon_ui_mockup.jpg`)，實現真正的空間深度、遮擋關係與無障礙的遊戲操作體驗。

## 🔍 架構落差與痛點分析 (Architecture Gaps)
1. **空間維度的錯置 (The Container Trap)**：
   * 目前 `Main.tscn` 將房間塞在 UI `PanelContainer` 內，導致場景大小受限於視窗拉伸。
   * **解法**：全面解耦。建立一個無限延伸的 `Node2D` 作為真正的世界根節點，並引入 `Camera2D` 負責視野的平移與縮放。
2. **缺乏 Y 軸深度排序與對齊 (The Y-Sort & Alignment Crisis)**：
   * 目前的辦公桌與家具是「散落的 Sprite2D」硬塞在絕對座標上。小人無法精準走位，視覺上沒有透視吸附感，完全是「小學生作業」的拼貼畫。
   * **解法**：全面拋棄 `Sprite2D` 手動排版。導入 Godot 內建的 `TileMapLayer`，建立嚴格的 2:1 等距網格 (Isometric Grid)，強制所有地板與家具像素對齊，並依賴引擎層級的自動 Y-Sort。
3. **UI 喧賓奪主 (UI Obscuring the Ant Farm)**：
   * 目前的 UI 採用 `HBoxContainer` 與遊戲畫面瓜分螢幕空間，擠壓了真正的模擬經營畫面。
   * **解法**：引入 `CanvasLayer`。將 TopBar（資金/信譽）、RightPanel（事件日誌/雷達）與 BottomBar（指令按鈕）移至浮動的 UI 層，使世界地圖能 100% 鋪滿螢幕底層。

## 🏛️ 三大 Cyberpunk 等距視覺公定標準 (The 3 Pillars of Aesthetics)
為了 100% 物理對齊 `Art_Bible.md` 中的高標準概念圖，我們設立以下三條不可妥協的美術實作天條：
1. **幾何空間標準 (Geometric Isometric Standard)**：
   * 拒絕手動輸入絕對座標。所有房間必須封裝為 `Isometric TileMap`，網格鎖定 2:1 菱形比例 (如 128x64)。地磚與牆壁/家具必須精準吸附格線，不容許絲毫像素錯位。
2. **渲染與光影標準 (Rendering & Lighting Standard)**：
   * 拒絕在黑色背景貼去背圖。場景必須掛載 `CanvasModulate` 將全局環境光壓暗。
   * 家具必須掛載 `PointLight2D` (如開發部 `#39ff14`)，在黑暗房間中將光暈打在地板與角色身上。
3. **後期處理標準 (Post-Processing Standard)**：
   * 啟用 `WorldEnvironment` 的 `Glow/Bloom` 效果，並配置 `Additive` 混合與降低 `HDR Threshold`，讓霓虹像素產生真正的高科技溢光。

## 🎯 實作計畫 (Action Plan)

### Step 1: 基礎設施拆分 (World & UI Decoupling)
*   **任務**: 重構 `Main.tscn`，將場景一分為二。
*   **規格**:
    *   新增 `CanvasLayer` 命名為 `UILayer`，將所有的 UI 面板移入其中，並設定 Anchors 貼齊邊緣。
    *   新增 `Node2D` 命名為 `World`，作為所有辦公室房間與員工的實體容器。
    *   新增 `Camera2D`，綁定自訂的 Pan & Zoom 拖曳腳本，取代現有的 `ScrollContainer`。

### Step 2: 等距網格地圖重構 (Isometric TileMap Conversion)
*   **任務**: 將混亂的 `Sprite2D` 廢墟拆除，建立真正的 Isometric TileSet。
*   **規格**:
    *   建立 `Isometric_TileSet.tres` 資源，定義 128x64 等距網格。
    *   將切好的 `floor_tile.png` 加入 TileSet 作為底層繪製。
    *   將 `desk_SW.png`, `server_rack_SW.png` 等家具以 Y-Sort 原點偏移的方式匯入 TileSet，或以場景節點放置但鎖定 Grid Snap。
    *   在 `DevRoom` 啟用 `TileMapLayer`，刷出無縫的地板與對齊的家具陣列。

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
