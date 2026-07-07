# Phase 5.8.13: 虛假驗證修復與場景美術精緻化 (Art Refinement & Validation Fix)

## 1. 核心原因與背景 (Background & Reason)
經過 Phase 5.8.7 與 5.8.9 等階段的開發，團隊發現了嚴重的「文件承諾 vs 程式碼現實」斷層（虛假驗證）。為了確保數位雙生與 Godot 客戶端能真實運作，本階段的唯一目標是將過去遺漏的實體美術資源確實綁定，並修復歷史技術債。

---

## 2. 斷層修復優先順序與重要性評估 (Priority & Severity Assessment)
經過物理審查，這四項虛假驗證對遊戲穩定性與體驗的破壞程度不同，因此我們確立了以下的修復優先級別：

### 🔴 【P0 - 阻斷性致命錯誤】通關畫面與轉場 (GameBoard Video Transitions)
* **重要性：極高 (Critical)**
* **影響**：在 `GameBoard.gd` 中，通關與失敗的過場影片變數全為 `null`。這意味著當玩家成功擊敗病毒或 SLA 歸零時，遊戲呼叫播放影片會引發 Null Reference 崩潰或陷入永久黑畫面死鎖（Soft-lock）。這直接破壞了核心遊戲迴圈的完整性，必須**第一優先修復**。

### 🟠 【P1 - 核心體驗缺失】玩家面板階級徽章 (CharacterDashboard)
* **重要性：高 (High)**
* **影響**：這是 Phase 5.8.6 RPG 系統的視覺核心。玩家辛苦升級獲得的 Rank B, A, S，若因為 UI 未綁定實體資源而無法顯示，將徹底摧毀玩家的「進度成就感 (Sense of Progression)」，且存取 `null` 的資源引用容易在底層引發靜默錯誤 (Silent errors)。

### 🟡 【P2 - 沉浸感與視覺降級】隊友面板頭像 (TeammateDashboard)
* **重要性：中 (Medium)**
* **影響**：目前 UI 雖然能運作（以純文字顯示清單），但完全抹殺了「與 Alice/Bob 協作」的 Cyberpunk 沉浸感。加上缺少「LLM 晶片裝備槽」的視覺引導，會讓新玩家對模型切換機制的理解度降低，屬於嚴重損害產品完成度的 UX 缺失。

### 🟡 【P2 - 沉浸感與視覺降級】卡片合成爐 (CardWorkshop)
* **重要性：中 (Medium)**
* **影響**：與隊友面板類似，功能運作正常，但使用簡陋的灰色 `ColorRect` 作為卡牌放置槽位，讓遊戲體驗瞬間退回原型（Prototype）階段，違背了本專案向高保真美術邁進的核心承諾。

---

## 3. 實作計畫 (Implementation Plan)
*依照上述優先順序 (P0 -> P2) 依序執行修復。*

### 3.1 (P0) 通關畫面與轉場 (Victory/Defeat Transitions)
* **目標檔案**：`recontextualization/src/views/GameBoard.tscn`
* **動作**：在 `.tscn` 根節點中補齊 `[ext_resource]`，將 `transition_victory.ogv`, `transition_defeat_glitch.ogv`, `transition_defeat_shutdown.ogv` 實體綁定至 `video_victory`, `video_defeat_glitch`, `video_defeat_shutdown` 變數。

### 3.2 (P1) 玩家面板 (Player Dashboard)
* **目標檔案**：`recontextualization/src/views/CharacterDashboard.tscn`
* **動作**：物理寫入 `[ext_resource]`，將 `badge_rank_b.png`, `badge_rank_a.png`, `badge_rank_s.png` 引入，並在根節點配置 `badge_rank_c`, `b`, `a`, `s` 的資源路徑，確保 `CharacterDashboard.gd` 能夠動態提取並渲染徽章。

### 3.3 (P2) 隊友面板 (TeammateDashboard)
* **目標檔案**：`recontextualization/src/views/TeammateDashboard.tscn` 與 `recontextualization/src/views/TeammateDashboard.gd`
* **動作**：
    1. 在腳本的 `populate_teammates` 中，預載 `avatar_alice.png`, `avatar_bob.png`, `avatar_charlie.png`，並使用 `teammate_list.add_item(name, icon)` 將高質感的動漫頭像注入 UI。
    2. 在 `.tscn` 中，於 `ModelHBox` (LLM 模型選項區) 旁邊，新增一個 `TextureRect` 節點並掛載 `icon_equipment_slot.png`。

### 3.4 (P2) 卡片合成爐 (CardWorkshop)
* **目標檔案**：`recontextualization/src/views/CardWorkshop.tscn`
* **動作**：將 `Slot1`, `Slot2`, `Slot3` 從簡陋的 `ColorRect` 轉換為 `TextureRect`，並掛載 `res://assets/images/card_frame_blank.png`，設定適當的 `expand_mode` 與 `stretch_mode`。

---

## 4. 驗證計畫 (Verification Plan)
* 執行 `make build-headless` 或以 Godot Headless 模式啟動編譯，確保沒有 `.tscn` 依賴錯誤或 Null Reference 崩潰。
* 手動檢查所有涉及修改的檔案，確保邏輯與 UI 掛載正確無誤。


### 3.5 (P0) 遊戲迴圈崩潰修復與 L2 架構對齊 (Lifecycle Architecture Hardening)
* **目標檔案**：`recontextualization/src/views/MainMenu.gd`, `MainMenu.tscn`, `CharacterDashboard.gd`, `CharacterDashboard.tscn`
* **動作**：
    1. 根除 `@onready` 在場景切換時導致的 `Invalid assignment on Nil` 崩潰。
    2. 將 UI 控制節點全面轉換為 `@export var` 並透過 `.tscn` 的 `node_paths` 屬性陣列進行物理綁定，落實真正的 MVC 架構單向資料流，打通導航迴圈。

### 3.6 (P2) 玩家面板 UX 檢討與互動性補強 (Dashboard UX & Interactivity)
* **目標檔案**：`recontextualization/src/views/CharacterDashboard.gd`, `CharacterDashboard.tscn`
* **動作**：
    1. **隱藏干擾性背景**：因目前的 `bg_texture` 缺乏明確的 UX 意義，導致介面混亂且「無聊」，暫時設定 `visible = false`，將介面還原至乾淨狀態，等待後續專業 UX 設計。
    2. **拓樸網實體化**：將原本隱形的假節點賦予實體圖示 (`chip_green_target.png`)，並實裝滑鼠懸停 (Hover) 的放大微光特效與點擊引爆 (Click Pulse) 的 HDR 閃光，讓介面脫離死氣沉沉的切版狀態。

