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
    3. **LEAN TDD 驗證規格**：
        *   必須撰寫單元測試來驗證：即便 Git 回傳了一次超巨型的提交，我們的 Normalizer 是否能準確地將其壓縮在規定的天花板 (Ceiling) 之內。

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