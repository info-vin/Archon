# Phase 5.7.7: Isometric World Refactoring (等距世界與視覺對齊重構)

## 📌 核心目標 (Objective)
徹底打破目前基於「UI 容器排版 (`GridContainer`)」的偽場景架構，將遊戲底層渲染架構全面升級為「等距/俯視角 (Isometric/Top-Down)」的 `Node2D` 實體世界。所有的程式重構與尋路邏輯，皆須 100% 建立在【可被完美編碼實作】的數學基礎上，實現真正的空間深度、遮擋關係與無障礙的遊戲操作體驗。

## 🔍 架構落差與痛點分析 (Architecture Gaps)
1. **素材管線的極限 (The Asset Pipeline Reality)**：
   * 痛點：目前的去背素材（牆角、辦公桌、伺服器）來自 AI 獨立生成，缺乏人工修圖邊緣對齊。強行用程式碼去拉伸、裁切或拼接「封閉式連續隔間牆」，必然產生裂縫與透視崩壞（小學生作業現象）。
   * **解法**：**放棄連續牆壁**。轉向「開放式浮島架構 (Open-Plan Islands)」，承認素材極限，只做程式碼 100% 算得準的事。
2. **缺乏 Y 軸深度排序與對齊 (The Y-Sort & Alignment Crisis)**：
   * 痛點：目前的辦公桌與家具是「散落的 Sprite2D」硬塞在絕對座標上。小人無法精準走位，視覺上沒有透視吸附感。
   * **解法**：全面拋棄 `Sprite2D` 手動排版。建立嚴格的 2:1 等距網格 (Isometric Grid, 128x64)，強制所有地板與家具像素對齊，並完全依賴 Godot 引擎的 `Y-Sort` 處理前後遮蔽。
3. **UI 喧賓奪主 (UI Obscuring the Ant Farm)**：
   * 痛點：目前的 UI 採用 `HBoxContainer` 與遊戲畫面瓜分螢幕空間。
   * **解法**：引入 `CanvasLayer`。將 UI 移至浮動層，使世界地圖能 100% 鋪滿螢幕底層，搭配 `Camera2D` 負責視野的平移與縮放。

## 🏛️ 三大實作可行之視覺標準 (The 3 Implementable Pillars)
為了在有限的素材下達到最高專業水準，我們確立以下三條不可妥協的實作天條（絕不通靈）：
1. **無牆開放式/角落錨點架構 (Open-Plan / Corner Anchor Architecture)**：
   * 拒絕手動拼接直牆。四大部門表現為相連或獨立的「等距地板區塊」。
   * 僅在每個部門的最北端（視覺最深處）放置唯一一張 `wall_corner.png` 作為視覺錨點，絕對不向兩側做物理延伸。
   * **物理邊界即地板**：`AStarGrid2D` 尋路網格嚴格對齊地板邊緣，沒有鋪設地板的網格即為實體牆壁/深淵，角色不可逾越。
2. **嚴格的數學網格對齊 (Strict Grid Alignment & Y-Sort)**：
   * 所有家具必須精準吸附於 128x64 的 Isometric 菱形格。
   * 家具的物理碰撞（障礙物）必須註冊在實際佔用的網格點上。
   * 角色走動與路徑計算 (Pathfinding) 完全交由 `AStarGrid2D` 處理，徹底拔除基於畫面像素的亂數座標移動。
3. **光影與 UI 融合 (Lighting & UI Integration)**：
   * 使用 `CanvasModulate` 壓暗場景，家具自帶的光源作為主照明。
   * UI 面板改為暗黑玻璃透視風格 (`Alpha 0.6` ~ `0.8`) 搭配霓虹字體，讓底層精心編排的等距像素世界能自然透出。

## 🎯 實作計畫 (Action Plan)

### Step 1: 基礎網格與地基重建 (Grid & Foundation)
*   **任務**: 清除所有舊的破爛牆壁腳本，重新建立乾淨的地基。
*   **規格**:
    *   在 `World` 節點下建立 `TileMapLayer`，設置為 Isometric 模式，Tile Size 為 128x64。
    *   使用 `floor_tile.png` 鋪設出四個部門的地板區塊，區塊間以地板顏色或走道區分。

### Step 2: 尋路與碰撞數學重構 (AStarGrid2D & Collision)
*   **任務**: 重寫 `AgentRouter.gd` 與角色移動邏輯。
*   **規格**:
    *   建立對齊 `TileMapLayer` 的 `AStarGrid2D` 實體。
    *   把帶有碰撞的家具 (桌子、伺服器) 所佔據的格點標記為 `is_solid = true`。
    *   角色移動時，嚴格沿著 AStar 計算出的網格路徑點 `map_to_local` 移動。

### Step 3: Y-Sort 與物件放置 (Y-Sort Registration)
*   **任務**: 讓角色能自然地繞過辦公桌與伺服器並被正確遮蔽。
*   **規格**:
    *   開啟 `YSortWorld` (Node2D) 的 `y_sort_enabled = true`。
    *   確保所有角色與家具都位於此節點下，並微調原點偏移量 (Offset Y)，確保底部基準線正確對齊。

### Step 4: 素材補完與比例校準 (Asset Completion & Scale Calibration) [進度更新]
*   **目前進度 (Status)**:
    *   已透過 Python 腳本完成舊有家具的鏡像翻轉 (產生 `_SE` 朝向)。
    *   已透過 Python 色相偏移完成四部門彩色地板 (`floor_tile_red/blue/orange.png`)。
    *   已結合 AI 生成與 Python 裁切去背，自動產出新的賽博龐克物件 (咖啡機、販賣機)。
    *   已成功用 `World2D` 與 `TileMapLayer` 拼圖並透過截圖確認程式拼接邏輯無誤。
*   **待辦任務 (Pending Actions)**:
    1.  **尺寸校準 (Scale Calibration)**: AI 產出的素材 (如咖啡機) 以及舊家具在網格上的比例與目標 Mock 圖存在落差，需要進一步統整 Sprite 的 Scale 或重新規範邏輯框架大小。
    2.  **背景底圖融合 (Background Integration)**: 將精細繪製的背景圖 (Background) 墊入 `CanvasLayer` 或底層 `ParallaxBackground`，以填補目前素材不足的空白區域，提升整體賽博龐克氛圍。
    3.  **大量素材擴充 (Asset Expansion)**: 目前素材庫品項仍遠小於 Mock 圖的豐富度，需要持續建立更多辦公道具與隔間細節。

## 🛡️ 防翻供公證 (Anti-Flip-Flop Clause)
本文件已確實記錄「無牆開放式架構」作為官方實作標準。禁止 Agent 以任何理由退回「程式碼拼接破牆」或「整圖流」等無法滿足 Tycoon 核心機制與現有素材極限的荒謬解法。所有重構必須奠基於嚴謹的網格數學之上。
