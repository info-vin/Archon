# Phase 5.7.7: HD-2D Orthogonal World Refactoring (降維打擊：3D正交等距重構)

## 📌 核心目標 (Objective)
徹底打破目前基於「UI 容器排版 (`GridContainer`)」或「2D 偽等距 (`Node2D` + `Y-Sort`)」的架構，將遊戲底層渲染架構全面升級為 **「HD-2D」風格的 3D 空間 + 2.5D 正交視覺 (Node3D + Orthogonal Camera3D + Sprite3D)**。
藉由 Godot 原生的 3D Z-buffer 深度渲染，徹底消滅 2D 排序噩夢與錯位的「小學生作業現象」，實現完美的空間深度、真實光影與物理遮擋。

## 🔍 架構痛點與降維打擊 (Architecture Paradigm Shift)
過去使用 2D 引擎強做等距遊戲的三大痛點：
1. **Y-Sort 遮擋地獄**：角色走到桌子後面，還要手動調整 Sprite 的 Y 軸偏移點，稍有不慎就會出現頭穿破桌子的慘況。
2. **等距座標轉換噩夢**：滑鼠點擊與角色移動要在菱形網格與直角座標系之間來回轉換，充滿 Bug。
3. **破爛的牆壁與空間感**：缺乏真正透視，2D 素材拉伸後邊緣破裂。

**🚀 降維打擊解法 (The HD-2D Solution)**：
**把世界做成真正的 3D，但把它「拍」成 2.5D。**
* 所有的牆壁、地板與家具都放置在絕對精準的 3D `GridMap` 空間中。
* 角色是貼著 2D 動畫的 `Sprite3D` (Billboard 永遠面向鏡頭)。
* 攝影機採用 `PROJECTION_ORTHOGONAL` (正交投影)，斜 45 度角鎖定俯視。在正交投影下，3D 空間在螢幕上看起來就是完美的 Isometric 像素風。
* **物理遮擋交給 Z-buffer**，再也不用寫任何 Y-Sort 程式碼！

## 🏛️ 三大實作可行之視覺標準 (The 3 Implementable Pillars)
1. **3D 實體網格背景 (GridMap Foundation)**：
   * 遊戲世界由 `GridMap` 搭建。地板為 `y=0` 的網格，家具和牆壁佔據 `y=1` 的網格。
   * 地圖不再是 2D 的手動拼接圖，而是透過 `set_cell_item` 從 `MeshLibrary` 取出具備長寬高的 3D 方塊。
2. **正交攝影機與移動修正 (Orthogonal Camera Rig)**：
   * `Camera3D` 放置於相對於玩家的 `Vector3(15, 20, 15)`，啟用 `PROJECTION_ORTHOGONAL` 並 `look_at` 玩家。
   * 玩家的移動向量將根據攝影機的 `basis` 進行相對修正。按 W 鍵永遠是往螢幕的「上方」走，而非世界座標的絕對北邊，保證操作直覺。
3. **動態 3D 光影與賽博龐克渲染 (3D Lighting & Shadows)**：
   * 引入 `DirectionalLight3D` 與 `OmniLight3D`，讓 2D 的 `Sprite3D` 也能投射出真實的 3D 陰影在 3D 地板上。
   * UI 面板改為暗黑玻璃透視風格 (`Alpha 0.6` ~ `0.8`) 搭配霓虹字體，讓底層精心編排的 HD-2D 世界能自然透出。

## 🎯 實作計畫 (Action Plan)

### Step 1: 3D 世界地基重建 (Node3D & GridMap)
*   **任務**: 清除所有 2D `TileMapLayer` 與 UI 偽場景，建立 `Node3D` 的世界根節點。
*   **規格**:
    *   在 `World` 節點下建立 `GridMap`，設定 Cell Size (例如 `2x2x2`)。
    *   製作基礎的 `MeshLibrary` (包含地板與基礎牆體)。
    *   透過 GDScript 腳本動態生成或鋪設 3D 辦公室格局。

### Step 2: HD-2D 角色與正交運鏡 (Sprite3D & Orthogonal Camera)
*   **任務**: 將 2D 小人升級為 3D 空間實體，並掛載正交攝影機。
*   **規格**:
    *   將角色節點改為 `CharacterBody3D`。
    *   外觀使用 `Sprite3D`，並設定 `billboard = BaseMaterial3D.BILLBOARD_FIXED_Y`，確保紙片人永遠面朝鏡頭但不會前後傾倒。
    *   掛載 `Camera3D`，設定為 Orthogonal 投影，定位於斜上方並追蹤角色。

### Step 3: 移動邏輯與 3D 尋路對齊 (3D Navigation)
*   **任務**: 讓角色能在 3D 空間中順暢走動，且操作符合 2.5D 視覺直覺。
*   **規格**:
    *   重寫輸入控制，將 WASD 方向依據 Camera 的 `basis` 轉換為 X-Z 平面移動。
    *   （可選）導入 `AStar3D` 或 `NavigationRegion3D` 讓 Agent 角色能自動避障導航。

## 🛡️ 防翻供公證 (Anti-Flip-Flop Clause)
本文件已確實記錄「HD-2D 3D正交架構」作為官方實作標準。禁止 Agent 退回任何基於「2D Node + Y-Sort 手動排版」或「Sprite2D 偽場景」的過時方案。所有空間遮擋必須 100% 交由 Godot 3D 引擎的 Z-buffer 物理處理，徹底根除小學生作業現象。
