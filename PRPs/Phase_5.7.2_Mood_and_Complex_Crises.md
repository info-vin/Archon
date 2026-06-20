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

## 🔧 物理交互與排版硬化計畫 (UI Layout & Interaction Hardening)

為了解決實體畫面中存在的交互與排版漏洞，本階段特別加入以下硬化設計：

### 1. 修正雷達圖 (Minimap) 黑屏問題
- **問題分析**：`Minimap.gd` 中若 `size` 為 0 則會直接 skip。在 `Main.gd` 的 `_ready()` 剛進入時，Layout 尚未完成，Minimap Container 大小為 (0,0)，導致初次繪製失敗且之後未被觸發。
- **解決方案**：在 `Main.gd` 的 `_ready()` 尾部，加上延遲幀處理，等待 Layout 尺寸計算完成後重繪：
  ```gdscript
  await get_tree().process_frame
  _update_minimap()
  ```

### 2. 修正擴建房間與格點排版 Bug
- **問題分析**：`HUDController.gd` 中的 `office_grid` 使用了錯誤的相對路徑 `"VBox/GameArea/Building/OfficeGrid"`（漏掉了 `HBoxMain` 節點），導致節點獲取為 `null`，擴建按鈕點擊後毫無反應。
- **解決方案**：
  - 改為直接調用已經型別安全載入的 `main_node.office_grid`。
  - 新擴建房間的 Label 名稱必須命名為 `Label`，並預設顯示，以便配合 `OfficeRoom.gd` 在隨機危機發生時，動態渲染 `NEED DEV` 或 `NEED QA` 的霓虹警報字句。

### 3. 紙娃娃頭髮貼圖排他載入與相機對位 (Exclusive Hair & Camera Alignment)
- **問題分析**：
  - 預設的 SVG 貼圖可能與 Option A 的像素拆件重疊。
  - 在 `CharacterCreator.tscn` 中，預覽 `Camera2D` 的位置被誤設為 `(0, 30)` 且 zoom 為 3，這會將鏡頭失焦聚焦於角色腳底，導致預覽視窗內頭部、眼睛、西裝與頭髮完全出鏡被切斷，玩家無法看見捏臉結果。
- **解決方案**：
  - `ModularAgent.gd` 中的 `equip_part("hair", hair_tex)` 僅對 `hair_sprite.texture` 進行覆寫，確保同一時間只有一種髮型紋理生效。
  - 當載入 Option A 像素自訂外觀時，主動重置各圖層（Body, Hair, Outfit, Tool）的 scale 與 position，防範預設 svg 殘留。
  - 將 `CharacterCreator.tscn` 裡的預覽相機 `Camera2D` 位置重置為 **`Vector2(0, -120)`** 且 `zoom` 設定為 **`Vector2(1.2, 1.2)`**。這能讓整個人物精確置中於 SubViewport 預覽面板中央，確保頭部、西裝與五官能完美被玩家審視。

### 4. 初始員工多樣化與性別裝扮修正 (Initial Staff Diversity)
- **問題分析**：初始員工性別與裝扮混亂（如男性 Charlie 被硬塞女性雙馬尾與法師袍），且髮色全部呈單調白色，完全沒有發揮髮色調製功能，且與雷達圖顏色不符。
- **解決方案**：
  - 修改 `AgentResource.gd` 構造函數使其支援傳入或指派多樣化的性別、風格及髮色。
  - 在 `Main.gd` 的 `_setup_initial_game()` 中，為三位員工進行 **Tron 霓虹主題** 外觀物理拆件與顏色對齊分配：
    * **Alice (DEV)**：女性 (Gender 0)，長髮 (Hair 1)，**綠色霓虹髮色 (Color("#39ff14"))**，法師袍 (Outfit 1)，DEV Wand。
    * **Bob (SALES)**：男性 (Gender 1)，俐落短髮 (Hair 2)，**黃色霓虹髮色 (Color("#fde910"))**，西裝背心 (Outfit 2)，SALES Cards。
    * **Charlie (QA)**：男性 (Gender 1)，短髮 (Hair 2)，**桃紅霓虹髮色 (Color("#ff003c"))**，西裝背心 (Outfit 2)，QA Spell 護盾。
  - 此設定使員工在辦公室的**髮色、手持工具類型**與**雷達圖上的點位顏色（DEV=綠, SALES=黃, QA=紅）**實現 100% 物理對齊，大幅提升畫面美感。

### 5. 驗證與截圖計畫 (Screenshot Proofs)
- 撰寫 `Tests/capture_interactive_ui.gd`，模擬以下狀態並存檔：
  1. `proof_main_default.png`：驗證預設主畫面、顯示正常的 Minimap，以及**Alice(女/法師袍)、Bob(男/西裝)與Charlie的差異化骨骼外觀**。
  2. `proof_recruit_creator.png`：驗證點擊招募按鈕後，角色自訂器 Tween 彈出。
  3. `proof_expanded_and_scrolled.png`：驗證點擊擴建房間並向下拉動滾動條後，底部新房間與邊框的渲染。


---

## 🟢 實實與驗證結果 (Implementation & Verification Results)

- **實作狀態**：已於分支 `feature/phase5-7-2-mood-crises-audio` 完成所有功能的開發與硬化修正。
- **自動化測試**：運行 `/Applications/Godot.app/Contents/MacOS/Godot --headless -s Tests/HeadlessRunner.gd` 順利通過全部 **139 項單元與整合測試斷言**。
- **視覺公證**：已手動執行 `Tests/capture_interactive_ui.gd` 順利生成上述 3 張交互狀態截圖，確認排版對齊正常，無覆蓋或黑屏。


