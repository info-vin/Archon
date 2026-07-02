# Phase 5.8.7: 玩家角色管理 UI 與全域美術遷移 (Art Migration & Character UI)

> **前置相依：本階段承接 Phase 5.8.6 的 RPG 系統實作。**
> 本階段旨在將前期使用的佔位素材 (Placeholder) 全面升級為 SDXL/Flux 生成的高保真 AI 美術，並為新增的 RPG 系統實裝對應的玩家角色管理 UI 與動畫特效。

## 1. 玩家角色管理 UI (Player Character Management UI)

配合 Phase 5.8.6 的 A+B+C RPG 系統，我們需要一個全新的全螢幕 UI 場景，讓玩家能夠檢視與管理自己的駭客角色狀態。

*   **實作目標：`CharacterDashboard.tscn` (角色面板)**
    *   **視覺風格**：Cyberpunk 駭客終端機風格，帶有 CRT 掃描線特效。
    *   **權限區塊 (Sector Clearance - B系統)**：顯示目前的 `Clearance Rating (CR)` 積分條與當前的 Sector 圖示（例如：Sector 1 為青銅資料庫、Sector 3 為黃金防火牆）。
    *   **認知等級與天賦區塊 (Cognitive Level & Topology - A+C系統)**：
        *   顯示目前的 `Account XP` 進度條與 `Cognitive Level`。
        *   建立一個以網狀節點呈現的「天賦星盤 (Topology Talent Web)」子視窗。點擊節點會發出脈衝光動畫，並消耗 `TP` 點數解鎖能力。
    *   **動畫要求**：當玩家升級或成功晉升 Sector 時，需有專屬的粒子特效與音效（如資料庫解鎖的聲響）。

---

## 2. SDXL / Flux 美術資產遷移 (Global Art Migration)

將《進入矩陣》與 Cyberpunk 駭客主題的高質感 AI 美術資產，實裝至目前的戰鬥與工坊場景中。

### 2.1 主視覺背景 (Backgrounds)
*   **戰鬥場景**：替換 `GameBoard.tscn` 的空白背景。產出 `vector_grid.png`，呈現高維度向量資料庫的深邃感。
*   **卡牌工坊**：產出 `synthesizer_furnace.png`，作為 `CardWorkshop.tscn` 的實體承載視覺，呈現充滿高溫與電火花的量子融合爐。

### 2.2 高保真晶片替換 (Data Chips)
*   **黃金命中晶片 (Target Chunk)**：將 `data_green.png` 替換為帶有螢光綠電路紋理的高科技晶片圖示。
*   **紅幽靈雜訊晶片 (Noise/Corrupted)**：將 `data_red_corrupted.png` 替換為帶有破圖與病毒干擾特效的赤紅晶片圖示。

### 2.3 L1~L5 行動卡圖示翻新 (Action Cards)
*   為不同參數階級套用對應的 AI 生成視覺：
    *   **Keyword (BM25)**：套用精準的狙擊鎖定視覺。
    *   **Dense (Vector)**：套用高能雷射穿透視覺。
    *   **Reranker**：套用藍色六角形電漿護盾防禦視覺。

### 2.4 動畫特效微調 (VFX Integration)
*   **合成特效**：在 `CardWorkshop.tscn` 中，製作「合成成功」的粒子大爆發特效，以及「合成失敗 (碎裂)」的震動與破片特效。
*   **UI 佈局相容性**：匯入新的資源後，確認所有 `TextureRect` 縮放比例正常，確保戰鬥拖曳判定 (Drag & Drop) 範圍不受影響。
