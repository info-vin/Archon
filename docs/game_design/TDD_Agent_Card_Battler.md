# Technical Design Document (TDD): Agent Card Battler

```text
=============================================================================
                  Archon: Agent Card Battler (Godot 4.x)
                         Core Event & Node Architecture
=============================================================================

 [ AUTOLOADS (Global) ]
 -----------------------------------------------------------
 | GameManager.gd       |        SignalBus.gd              |
 | - current_mana       |<------ [card_played]             |
 | - player_hp          |<------ [enemy_turn_ended]        |
 | - enemy_hp           |<------ [player_turn_ended]       |
 -----------------------------------------------------------
        ^                            ^
        | (Listen)                   | (Emit)
        v                            |
 [ UI LAYER (CanvasLayer) ]          |
 ------------------------            |
 | TopBar               |            |
 | - Health Bar         |            |
 | - Enemy Intent       |            |
 ------------------------            |
 | HandContainer        |            |
 | - CardUI (Node)      |---(Drag)---+
 | - CardUI (Node)      |            |
 ------------------------            |
                                     |
 [ LOGIC LAYER (Nodes) ]             |
 -----------------------------------------------------------
 | DeckManager.gd (Array[CardRes])   |                     |
 | - draw_cards(amount)              |                     |
 | - shuffle_discard()               |                     |
 |                                   |                     |
 | TurnManager.gd                    |                     |
 | - start_player_turn()             |                     |
 | - execute_enemy_action()          |                     |
 -----------------------------------------------------------
```

### 🧠 架構設計亮點 (符合 MVC 與 TDD 原則)

1. **極致解耦 (Extreme Decoupling)**：
   *   **Model**: `DeckManager` 和 `GameManager` 只處理純資料陣列與數值運算。這使得我們可以在沒有任何 UI 的情況下，撰寫 100% 覆蓋率的單元測試（例如測試「抽 3 張牌後，牌庫數量是否減少 3」）。
   *   **View**: `CardUI` 只負責顯示圖片和滑鼠懸停動畫。
   *   **Controller**: 玩家將卡牌拖曳到敵人身上時，只會觸發一個信號 `card_played(card_id)`，然後視覺卡牌立刻被銷毀，由 `GameManager` 接手計算扣血與扣除 Token。

2. **資料驅動 (Data-Driven Design)**：
   每張卡牌都是一個繼承自 `Resource` 的自訂資源檔 (`CardStats.tres`)，包含 `cost` (消耗 Token), `damage` (傷害), `block` (護盾) 等屬性。企劃可以直接在 Godot 編輯器中新增卡牌，完全不需要動到程式碼。

3. **回合制狀態機 (Turn-Based State Machine)**：
   拋棄了複雜的 `_process(delta)` 即時物理碰撞。遊戲狀態嚴格受控於 `PlayerTurn` 與 `EnemyTurn` 兩個狀態，徹底消除了時間軸上的 Race Condition 與非同步 Bug。

---

## 🚀 混血 UI/UX 實作指南 (Slay the Spire 資訊密度 + 爐石打擊感)

為了打造沉浸式的 Agent 卡牌體驗，我們的 View 層與 Model 層必須融合頂尖業界標準，並通過 LEAN 的嚴謹驗證。

### 第一層：真實數據抽取與 LEAN 驗證 (Git Log -> Model)
卡牌的數值將由真實開發環境的 Git Log 動態生成，實作「開發即遊戲」的元遊戲體驗。

*   **TDD 更新要點 (實作規格)**:
    1. **數據抓取機制**：
        *   明確使用 Godot 的 `OS.execute()` 指令來呼叫 `git log`。
        *   設定預設讀取 最近 20 筆 非合併 Commit。
    2. **數值歸一化邏輯 (Normalization) — 維持遊戲平衡的關鍵**：
        為了避免一張 Commit 因為改了 1000 行而變成「毀滅世界」的神卡，我制定了數學過濾規則：
        *   **Cost (費用)**：根據 Files Changed 計算。最小值 1 費，最大值 3 費。
        *   **Attack (傷害)**：`Insertions / 10`。保底 5 點，天花板 50 點。
        *   **Defense (護盾)**：`Deletions / 5`。最大值 30 點。（重構刪除代碼的防禦價值較高）。
    3. **10 大卡牌屬性、顏色與特殊效果規劃**：
        卡牌生成時會根據 Git Commit 訊息的前綴進行分類，並擁有各自的霓虹樣式與特殊戰術效果：
        
        | 類別屬性 (Category) | 前綴 / 符號 | 邊框與背景底色 | 抽牌率 | 🎮 特殊卡牌效果 (Special Effect When Played) |
        | :--- | :--- | :--- | :---: | :--- |
        | **功能 (Feature)** | `feat:`, `✨` | 🟢 翠綠色邊框 / 深綠背景 | **22.95%** | **主力輸出**：無額外效果，純依行數造成大量傷害。 |
        | **說明文件 (Docs)** | `docs:`, `doc:` | 🌐 青綠色邊框 / 深青背景 | **16.94%** | **資料檢索**：打出時**額外抽 1 張牌**。 |
        | **分支合併 (Merge)** | `merge`, `Merge` | 👑 黃金色邊框 / 暗金背景 | **16.03%** | **程式碼合併**：打出時**為玩家治癒 10 點 HP**。 |
        | **修復 (Fix)** | `fix:`, `bug:` | 🔴 鮮紅色邊框 / 深紅背景 | **14.21%** | **即時除錯**：無額外效果，費用低且穩定。 |
        | **重構 (Refactor)** | `refactor:` | 🔵 寶藍色邊框 / 深藍背景 | **8.01%** | **重構自癒**：防守兼備，造成傷害時獲得 Block。 |
        | **效能 (Performance)**| `perf:`, `⚡` | 🟡 閃電黃邊框 / 暗黃背景 | **6.19%** | **效能加速**：打出時**為玩家恢復 2 點 Token (費用)**。 |
        | **雜務 (Chore)** | `chore:`, `ci:` | 🔘 鋼鐵灰邊框 / 深灰背景 | **5.46%** | **專案清理**：打出時**棄置手牌並補抽 2 張牌**。 |
        | **測試 (Test)** | `test:`, `🧪` | 🟣 薰衣草紫邊 / 深紫背景 | **4.55%** | **測試防禦**：打出時**額外獲得卡牌防禦值一倍的 Block**。 |
        | **樣式 (Style)** | `style:`, `🎨` | 🌸 粉紅色邊框 / 深粉背景 | **3.64%** | **降費美化**：打出時**額外獲得 10 點 Block**。 |
        | **自動化 (Agent)** | `🤖`, `agent:` | 🔮 幻境紫邊框 / 深紫背景 | **2.00%** | **Agent直擊**：召喚 AI 助理，**對敵人造成 20 點無視護盾的直接傷害**。 |

    4. **LEAN TDD 驗證規格**：
        *   必須撰寫單元測試來驗證：即便 Git 回傳了一次超巨型的提交，我們的 Normalizer 是否能準確地將其壓縮在規定的天花板 (Ceiling) 之內。
        *   新增 TDD 測試，驗證 10 種卡牌類別在打出時觸發的特殊機制與數值變化。

*   **LEAN TDD 斷言**: 
    *   所有字串解析與數據轉換必須在沒有 UI 的環境下，透過 `MiniTest` 進行 100% 的純數學與邏輯斷言。不依賴外部環境的 Flaky Tests。
    *   測試解析器是否能處理各種 Git 異常輸出（如：只有標題無數據、只有刪除無新增）。
    *   驗證歸一化函數是否精準將 1000 行 Insertion 壓縮至 50 點傷害的天花板。

### 第二層：Slay the Spire 的極致資訊密度 (View - Data)
遵循「一眼看穿戰局 (Information First)」的原則，特別針對無頭自動化戰鬥做視覺化處理：
*   **富文本卡牌資訊 (RichTextLabel)**：使用 BBCode 渲染來自 Git 的數據：`"[b]{commit_msg}[/b]\n[color=#4ade80]+{insertions} Additions[/color]\n[color=#f87171]-{deletions} Deletions[/color]"`。
*   **敵人意圖 (Intents)**：在敵人頂部掛載 `HBoxContainer`。當底層邏輯設定傷害時，立即在 UI 反映（例如一把劍圖示加上 "30"），並且支援滑鼠懸停顯示 Tooltip 解釋詳細計算。

### 第三層：爐石戰記的物理實體感 (View - Juice)
View 層的作用是「聆聽」Model 變化，並利用 `create_tween()` 創造「實體物件 (Physical Object)」的操作回饋，絕不干涉狀態機邏輯。
*   **非靜默彈出 (Material & Tactility)**：選單與對話框透過 Tween 實作彈出與翻轉，配合厚重音效。
*   **卡牌實體感 (Hover Weight)**：滑鼠懸停時，使用 Cubic Easing 將卡牌微微放大、向 Z 軸提升，並附帶紙張摩擦音效，創造實體桌遊感。
*   **全息對話框 (Piano Glass)**：融合科幻風格，對話框使用半透明 `StyleBoxFlat` 毛玻璃材質，並利用 `visible_characters` 實作 AI Agent 的打字機特效 (Typewriter Effect)。

---

## 🛠️ Web Assembly (WASM) 導出與前台整合指南 (Vite / React Integration)

為了在前端 `enduser-ui-fe` (Port 5173) 順利執行 Godot 編譯的網頁遊戲，我們在此紀錄標準的部署與除錯工作流：

### 1. 正確的 Web 導出路徑
在 Godot 的 **Project > Export** 視窗中，**Export Path** 必須設定為：
`../enduser-ui-fe/public/games/card-battler/index.html`
*   導出時，Godot 將會自動建立 `/games/card-battler/` 資料夾，並寫入 `index.html`、`index.js`、`index.wasm`、`index.pck`。
*   React 的 [GamePage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/GamePage.tsx) 內部 `iframe` 容器已配置直接讀取此路徑，且路徑與 `ROUTES.GAME_CARD_BATTLER` 完全對齊。

### 2. macOS 本地除錯與 VS Code 整合 (godot-tools)
為了在 VS Code (或 Antigravity IDE) 中直接下中斷點偵錯與語法補全，請設定以下配置：
*   **LSP 連線埠設定**：在 Godot 的 **Editor Settings > Network > Language Server** 中，將 **Remote Host** 強制設為 `127.0.0.1` (避免 macOS 將 localhost 解析為 IPv6 導致斷線)，**Remote Port** 設為 `6005`。
*   **VS Code godot-tools**：若在 Antigravity IDE 中找不到擴充套件，請從官方 Marketplace 下載 `.vsix` 並使用 "Install from VSIX..." 手動載入。
*   **VS Code launch.json 設定**：配置 TCP port `6005`，即可按 `F5` 啟動偵錯。

### 3. 無頭 (Headless) TDD 測試自動化
我們重構了 `MiniTest` 繼承自 `RefCounted`，使其脫離編輯器 GUI。現在可以在 CI/CD 或命令列中一鍵運行 100% 的無頭邏輯測試：
```bash
# 在 archon-card-battler 目錄下執行：
"/Applications/Godot.app/Contents/MacOS/Godot" --headless -s Tests/HeadlessRunner.gd
```
*   **EditorRunner.gd**：繼承自 `EditorScript`，方便在 Godot 編輯器內直接執行全部測試。
*   **HeadlessRunner.gd**：繼承自 `SceneTree`，在無頭模式下回傳 exit code (0 代表 Pass，1 代表 Fail)，適合自動化門禁攔截。

## 📈 L2 解耦與模組化重構計畫 (L2 Decoupling & Refactoring Plan)

為避免主畫面單體腳本 `MainUI.gd` 淪為「上帝類別 (God Class)」而導致遊戲維護性崩潰，我們在此規劃 L2 解耦架構，並完全以 TDD (測試驅動開發) 流程實作：

### 1. 單一職責拆分 (SRP)
*   **Model (數據與狀態機)**:
    *   將血量、Token、Combo計數、手牌陣列等狀態抽取至獨立的資源檔 `GameState.gd` 中。
    *   `GameState.gd` 負責管理數值變更與發射相對應的 Godot 信號 (例如 `signal hp_changed(new_val)`)。
*   **View (視覺元件解耦)**:
    *   將倒數計時器 (Turn Timer)、血量進度條 (HP Bars)、遊戲結束結算 (GameOverOverlay) 拆分為獨立的子場景，掛載專屬小腳本。
    *   這些小腳本只負責動畫更新與自身的排版渲染，例如 `TimerUI.gd` 專門負責倒數計時大字型渲染與紅色警告。
*   **Controller (協調與接線)**:
    *   `MainUI.gd` 將大幅簡化至 100 行內，唯一的職責是在 `_ready()` 內將 `GameState` 的狀態信號連接到對應的 `View` 子節點更新函數上。

### 2. TDD 測試驅動重構流程 (L2 TDD Workflow)
在實作解耦重構時，必須嚴格遵守以下三部曲，確保 100% 邏輯覆蓋率與零 UI 耦合：

```text
  [步驟 1: 紅燈階段] ──> [步驟 2: 綠燈階段] ──> [步驟 3: 重構階段]
  撰寫無頭單元測試       實作 GameState         抽取輔助函式與最佳化
  定義信號與數值邊界     使測試 100% 通過       確保介面 Mocking 物理隔離
```

*   **紅燈階段 (Red - 測試先行)**：
    1. 在 `Tests/` 目錄下建立新單元測試檔案 `test_game_state.gd`。
    2. 在無 UI 實體下，針對未完成的 `GameState` 設計測試斷言：
       *   **狀態更新測試**：當 `damage` 施加時，`enemy_hp` 必須相應減少，且扣血信號 `signal enemy_hp_changed` 必須成功發射。
       *   **智慧回合結束測試**：當手牌費用皆高於剩餘 mana 時，測試 `GameState.check_smart_end_turn()` 是否應回傳 `true`。
       *   **Combo 倍率計算測試**：連續打出同類別卡牌時，測試數值乘積是否符合預期倍率。
    3. 執行測試並確認其因為未實作功能而亮紅燈（Fail）。
    
*   **綠燈階段 (Green - 快速實作)**：
    1. 實作最小限度的 `GameState.gd` 邏輯，僅滿足測試案例的要求。
    2. 執行無頭測試 `HeadlessRunner.gd`，使所有測試案例全數通過，指示燈轉為綠色（Pass）。
    
*   **重構階段 (Refactor - 模組解耦)**：
    1. 優化 `GameState.gd` 的程式碼結構，將複雜運算拆分成輔助函式。
    2. 確保 `GameState.gd` 中沒有任何 `Node` 視圖元件或 `TextureRect` 等渲染邏輯的引進。
    3. 再次執行單元測試，確保重構後功能未遭破壞（Regression Testing）。
    
*   **介面 Mocking 與 UI 連動**：
    *   針對 `View` 元件（例如 `TimerUI.gd`），建立一個 Mock 的 GameState 介面，在不啟動真實回合時序的情況下，模擬 mana/時間變更的信號，藉此單獨測試 UI 的警告閃爍與霓虹特效更新。
