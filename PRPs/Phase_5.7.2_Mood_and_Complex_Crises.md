# Phase 5.7.2: Tycoon Mood System, Complex Crises, Audio Jukebox, and Animation Overhaul

## 核心目標 (Goal)
根據 [TDD_Agency_Tycoon.md](file:///Users/vincenta/GoogleKwok022/Archon/docs/game_design/TDD_Agency_Tycoon.md) 中的「TDD 第九階段」，為本機的 Godot Tycoon 遊戲引入動態的**員工心情系統 (Happiness System)** 與 **深度隨機危機 2.0 (Complex Crises 2.0)**。

同時，重構**紙娃娃動畫系統（引進 AnimationPlayer 骨骼級位移）**，並建立一個**多軌復古 BGM 點播器 (Audio Jukebox)**。本階段的美術提示詞與動畫設計將 **100% 物理對齊 Archon 科技辦公室經營（Tech Office Tycoon）的主題與視覺風格**，拒絕無關的動作遊戲元素。最後，修復 `test_office_view.gd` 中的假性通過測試漏洞。

---

## 🛡️ godot-4-audit 合規性聲明
本階段開發將嚴格遵守 `godot-4-audit` 規範，具體實施以下三項核心標準：
1.  **1.1 靜態型別 (Static Typing) 門禁**：新撰寫的所有變數與函數特徵均強制實行靜態型別宣告（例如：`var happiness: float = 100.0`），絕不出現動態隱式宣告。
2.  **2.1 無頭編譯防禦 (Headless Class_Name Fallback)**：跨腳本引用與型別約束時，一律採用 base 類型搭配 `preload`，防止無頭測試編譯中斷。
3.  **1.4 信號Callable連接 (Callable Signals)**：所有點播器 UI 按鈕與狀態信號均使用 Callable 連接語法，拒絕傳遞 String 函數名。

---

## 🎨 辦公室經營專屬 AI 提示詞參考 (Office Tycoon Prompts)

為了產出與 `archon-agency-tycoon` 100% 契合的美術資產，必須使用以下調整後的辦公室專屬提示詞：

### 1. 辦公室員工骨骼拆件圖集 (Office Staff Texture Atlas)
*   **DEV/SALES/QA 辦公室員工拆件**：
    > **Positive Prompt**: `16-bit pixel art texture atlas of office staff characters, spritesheet with separated body parts, head with glasses, torso wearing hoodie, suit jacket, arm typing, arm holding coffee mug, smartphone, laptop accessory, flat colors, isolated on solid sharp white background`
    > **Negative Prompt**: `3d, realistic, blurry, shading, gradient, sword, weapon, knight, ninja, side-scroller action`

### 2. 科技辦公室家具圖塊集 (Tech Office Furniture Tileset)
*   **辦公室/伺服器房/休息室物件**：
    > **Positive Prompt**: `16-bit pixel art tech office room furniture tileset, cross-section flat view, server racks with blinking lights, programmer computer desks with dual screens, office chairs, whiteboard with charts, water cooler, vending machine, coffee maker, retro futuristic cyberpunk theme, isolated on solid white background`
    > **Negative Prompt**: `3d, perspective distortion, blurry, realistic, grass, tree, cave, landscape`

---

## 執行步驟 (Execution Plan)

### Step 1: 建立專屬開發分支 (Branching)
- **行動**: 建立並切換至新分支 `feature/phase5-7-2-mood-crises-audio`。

### Step 2: 修復測試假性通過漏洞 (Fix Test False-Pass)
- **行動**: 修改 [test_office_view.gd](file:///Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Tests/Unit/test_office_view.gd)，在對子節點進行 `set_script` 前，先將 `view` 加入樹中（`add_child(view)`）以初始化其 `@onready` 變數。

### Step 3: 辦公室紙娃娃骨骼與動畫重構 (Office AnimationPlayer Overhaul)
- **動畫設計 (Animation Library)**:
  - `idle`: 坐在椅子上輕微的呼吸起伏（身軀與頭部輕微 Y 軸位移）。
  - `walk`: 辦公室走動（腿部踏步貼圖交替與雙臂擺動）。
  - `work`: **程式打字/電話溝通**（雙手放在鍵盤位置快速拍打，或手持電話貼耳，螢幕發出微光）。
  - `rest`: 在沙發上休息（眼睛閉合，頭頂冒出 `Zzz` 氣泡）。
  - `strike` (罷工): 站在桌旁抱胸，頭頂冒出生氣氣泡，拒絕打字。

### Step 4: 多軌復古 BGM 點播器 (AudioManager Jukebox)
- **AudioManager 載入**: 新增全域 Autoload 節點 `AudioManager.gd`，加載 `bgm_neon_city.wav` 等辦公室賽博風背景樂。
- **HUD Jukebox 控制介面**: 在頂部戰情列右側整合極簡 Jukebox，提供歌曲切換與音量開關。

### Step 5: 心情系統與罷工機制 (Happiness & Strike System)
- 心情 < 20：工作速度降低 50%。心情歸 0 時強制鎖定為 `STRIKE`，進度條完全停滯。

### Step 6: 深度隨機危機 2.0 (Complex Crises 2.0)
- 實作連鎖反應擴散與地獄客戶（加倍體力/心情消耗，不可 Rush）。

### Step 7: TDD 測試驅動驗證
- 新增針對心情衰減、罷工停工及連鎖危機的單元測試斷言。

---

## 🟢 實作與驗證結果 (Implementation & Verification Results)

- **實作狀態**：已於分支 `feature/phase5-7-2-mood-crises-audio` 完成所有功能的開發。
- **自動化測試**：運行 `/Applications/Godot.app/Contents/MacOS/Godot --headless -s Tests/HeadlessRunner.gd` 順利通過全部 **139 項單元與整合測試斷言**。
- **視覺公證**：透過實體 GUI 模式執行 `Tests/capture_ui.gd` 成功生成渲染截圖 `proof_phase5_7_2.png`，並儲存至 `/Users/vincenta/.gemini/antigravity/brain/7c07631b-6e8f-46fa-bb56-61b419ecd84c/proof_phase5_7_2.png`。驗證顯示 Jukebox 按鈕、心情計量條與房間隨機危機 Label 均完全正常對齊渲染，無排版錯亂。

