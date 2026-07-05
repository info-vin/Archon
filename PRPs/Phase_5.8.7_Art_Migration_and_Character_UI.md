# Phase 5.8.7: 玩家角色管理 UI 與全域美術遷移 (Art Migration & Character UI)

> **前置相依：本階段承接 Phase 5.8.6 的 RPG 系統實作。**
> 本階段旨在將前期使用的佔位素材 (Placeholder) 全面升級為 SDXL/Flux 生成的高保真 AI 美術，並為新增的 RPG 系統實裝對應的玩家角色管理 UI 與動畫特效。

## 目前實體進度 (Strict Reality Check)
* [x] **美術提示詞庫建立**：`Art_Asset_Prompts.md` 已全面更新，包含背景、晶片、行動卡、轉場動畫、玩家階級徽章 (Rank C~S) 的提示詞。
* [x] **轉場影片轉檔自動化**：實作 `scripts/convert_videos.py`，支援自動偵測影片長度並等比例加速 (Time-compression)，無縫轉檔為 Godot 原生 `.ogv` 格式。
* [x] **轉場影片全域串接**：
  * [x] **OS Boot**：將 `IntroVideo.tscn` 設為初始場景，播放 `transition_os_boot.ogv` 後跳轉主選單。
  * [x] **Battle Intro**：實作 `TransitionVideo.tscn`，主選單點擊 New Career/Continue 時播放衝刺特效並跳轉 `GameBoard.tscn`。
  * [x] **Victory/Defeat**：於 `GameBoard.tscn` 直接疊加全螢幕影片播放，實作無縫的勝利與破圖斷電串聯動畫。
* [x] **背景美術套用**：`bg_vector_grid.png` 與 `bg_synthesizer.png` 已產出，但尚未綁定至 `GameBoard.tscn` 與 `CardWorkshop.tscn`。
* [x] **高保真晶片與卡牌圖示替換**：尚未產出與套用。
* [x] **玩家角色管理 UI (`CharacterDashboard.tscn`)**：尚未實作。
* [x] **CGF 視覺工藝 (扇形手牌、貝茲曲線、雷射拖曳)**：尚未實作。

---

## 1. 玩家角色管理 UI (Player Character Management UI) [已完成]

配合 Phase 5.8.6 的 A+B+C RPG 系統，我們需要一個全新的全螢幕 UI 場景，讓玩家能夠檢視與管理自己的駭客角色狀態。

*   **實作目標：`CharacterDashboard.tscn` (角色面板)**
    *   **視覺風格**：Cyberpunk 駭客終端機風格，帶有 CRT 掃描線特效。
    *   **權限區塊 (Sector Clearance - B系統)**：顯示目前的 `Clearance Rating (CR)` 積分條與當前的 Sector 徽章（由 Rank C 到 Rank S）。
    *   **認知等級與天賦區塊 (Cognitive Level & Topology - A+C系統)**：
        *   顯示目前的 `Account XP` 進度條與 `Cognitive Level`。
        *   建立一個以網狀節點呈現的「天賦星盤 (Topology Talent Web)」子視窗。點擊節點會發出脈衝光動畫，並消耗 `TP` 點數解鎖能力。
    *   **動畫要求**：當玩家升級或成功晉升 Sector 時，需有專屬的粒子特效與音效（如資料庫解鎖的聲響）。

---

## 2. SDXL / Flux 美術資產遷移 (Global Art Migration) [已完成]

將《進入矩陣》與 Cyberpunk 駭客主題的高質感 AI 美術資產，實裝至目前的戰鬥與工坊場景中。

### 2.1 主視覺背景 (Backgrounds)
*   **戰鬥場景**：替換 `GameBoard.tscn` 的空白背景為 `bg_vector_grid.png`。
*   **卡牌工坊**：替換 `CardWorkshop.tscn` 的背景為 `bg_synthesizer.png`。

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

---

## 3. CGF 視覺工藝借鑑 (CGF-inspired Visual Interactions) [已完成]

借鑑 CGF (db0) 在 Godot 中的頂級視覺回饋，將其用 MIT 授權規範乾淨地實作於我們的戰鬥場景 (`GameBoard.tscn`)：

*   **3.1 扇形手牌自動排列 (Fan Layout Container)**：
    *   實作一個客製化的 `HandContainer`，當卡牌加入時，能依據手牌數量自動計算弧度，呈現扇形 (Fan) 排列。
    *   Hover 卡牌時，自動放大並置頂 (Z-index 提升)，解決卡牌遮擋問題。
*   **3.2 貝茲曲線拖曳軌跡 (Bezier Curve Dragging)**：
    *   當玩家抽牌或將卡牌打出時，使用 `Tween` 與 `Path2D` 運算，讓卡牌不只是線性平移，而是帶有立體拋物線感的平滑移動。
*   **3.3 攻擊與指定目標箭頭 (Targeting Arrow)**：
    *   當玩家拖曳某張需要指定目標的指令卡時，從卡牌中心畫出一條動態連接到滑鼠鼠標的雷射箭頭 (使用 `Line2D` 與自定義 Shader 實作光流動感)。

---

## 4. 殘留斷層與防禦性自癒計畫 (Gaps & Self-Healing Action Plan) [未開始]

經過 2026/07 的 Headless 測試與實體程式碼稽核，我們揪出了 CGF 美術遷移後引發的型別與單例註冊死鎖，現制定修復計畫如下：

*   **4.1 解決型別聲明死鎖 (Type Mismatch Fix)**：
    *   將 [GameBoard.gd](file:///Users/vincenta/GoogleKwok022/Archon/recontextualization/src/views/GameBoard.gd) 中對 `hand_container` 的定義從 `HBoxContainer` 改為 `Container`，以物理適配 `.tscn` 中已轉換為 `Container` (掛載 `HandLayout`) 的實體節點。
*   **4.2 解決 Headless 測試下的單例定位崩潰 (Safe Singleton Lookup)**：
    *   重構 [GameState.gd](file:///Users/vincenta/GoogleKwok022/Archon/recontextualization/src/autoloads/GameState.gd) 與 [CardRegistry.gd](file:///Users/vincenta/GoogleKwok022/Archon/recontextualization/src/managers/CardRegistry.gd)，將 `get_node("/root/...")` 的絕對路徑獲取，改為「Engine 單例池與場景樹雙軌尋訪機制」，確保測試在 `.new()` 實體化且不在活躍場景樹時，能自癒定位：
      `var event_bus = Engine.get_singleton("EventBus") if Engine.has_singleton("EventBus") else (get_node_or_null("/root/EventBus") if is_inside_tree() else null)`
*   **4.3 解決單例註冊衝突 (Duplicate Registration Fix)**：
    *   在 [test_tutorial_fsm.gd](file:///Users/vincenta/GoogleKwok022/Archon/recontextualization/tests/test_tutorial_fsm.gd) 等測試腳本的 `run_tests()` 開頭與結尾，補強 `Engine.has_singleton(...)` 檢查與 `Engine.unregister_singleton(...)` 銷毀邏輯，徹底阻斷測試執行序中的單例註冊死鎖。
