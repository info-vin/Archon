# Phase 5.7.5: Tycoon Architecture Remediation (三大痛點全面除鏽)

## 核心目標 (Goal)
為了解決「公司模擬器 (Agency Tycoon)」因架構缺陷導致無法順利收尾的問題，本階段將針對 Godot 4 開發中最致命的「三大痛點」進行外科手術式重構。我們將建立純粹的 MVC 邊界，解耦渲染限制，並淨化測試環境。

---

## 痛點一：UI 與核心邏輯的深度耦合 (Main.gd 上帝類別)
**現狀**：`Main.gd` (原 MainUI.gd) 身兼多職，同時握有所有商業邏輯管理器 (`AgentManager`, `TaskManager`, `TycoonManager`)、驅動主迴圈 (`GameTickTimer`)，甚至直接操控角色尋路與位置，導致改動 UI 就會牽一髮動全身。
**實作計畫 (L2 解耦與 Event Bus)**：
1. **建立 `EventBus.gd` (Autoload)**：
   - 負責所有跨階層通訊的 Signal 定義（如 `tick_updated`, `task_generated`, `agent_moved`）。
2. **抽離 `SimulationEngine.gd` (核心邏輯層)**：
   - 將所有 `Manager` 實體與儲存/讀取功能、`Timer` 主迴圈，從 `Main.gd` 中物理剝離至此節點。
   - 此引擎不操作任何 UI 節點，純計算數據，然後透過 `EventBus` 廣播狀態改變。
3. **降級 `Main.gd` (純視圖層)**：
   - 移除 `Main.gd` 內的所有邏輯計算代碼。
   - 在 `_ready()` 中註冊監聽 `EventBus`，只負責接收訊號並更新底下的 `HUDController` 與 `ModularAgentView`。

## 痛點二：Headless 模式視覺公證的限制 (Viewport 截圖崩潰)
**現狀**：為了 CI/CD 執行自動化公證，我們會使用 `--headless` 模式。但 Godot 4 在此模式下會徹底關閉渲染管線 (RenderingServer)，導致所有與 `Viewport.get_texture()` 或畫面截圖相關的測試會拿到 null 或直接報錯，造成視覺驗證受阻。
**實作計畫 (視覺與邏輯雙軌測試驗證)**：
1. **環境嗅探與優雅降級**：
   - 在 `capture_ui.gd` 或 `Minimap.gd` 中加入防禦機制：若 `DisplayServer.get_name() == "headless"`，則跳過 Texture 擷取或渲染更新，以防腳本崩潰。
2. **分離公證職責**：
   - **邏輯層**：由 `MiniTest.gd` 搭配 `--headless` 負責所有不帶 UI 渲染的核心單元測試（速度極快）。
   - **視覺層**：將 `capture_interactive_ui.gd` (視覺公證截圖) 隔離出 `--headless` CI 流程，改為在部署前由手動/非無頭模式啟動，保證視覺證據的有效性。

## 痛點三：單元測試狀態污染與框架臃腫
**現狀**：Godot 的節點如果過度依賴生命週期 (`_ready`, `_process`) 且邏輯全寫在裡面，單元測試必須頻繁實例化場景 (`.instantiate()`) 並掛載到樹上才能跑。這導致測試極度脆弱，加上全域變數未清空會引發「幽靈報錯 (State Pollution)」。
**實作計畫 (狀態隔離與 RefCounted 轉型)**：
1. **純粹的資料模型 (Model Layer)**：
   - 確保 `AgentResource`, `TaskResource`, `GameState` 皆繼承自 `Resource` 或 `RefCounted`，完全不依賴 Scene Tree 就能被測試。
2. **測試前淨化協議 (Clean Room Protocol)**：
   - 強化自製 `HeadlessRunner.gd` 測試框架：在每個 `test_*.gd` 執行前與結束後，強制重設 `EventBus` 狀態並刪除暫存檔 (`user://savegame.save`)。
   - 禁止在測試中使用全域殘留數據，所有 Mock Data 必須深拷貝或重新實例化。

---

## 預期產出與驗收標準 (Deliverables)
1. **[架構]** `Main.gd` 的行數大幅縮減，不再包含任何直接的數值計算與尋路邏輯。 (✅ 完成)
2. **[架構]** 新增 `EventBus.gd` 並成功註冊為 Autoload。 (✅ 完成)
3. **[架構]** 核心邏輯安全封裝於 `SimulationEngine.gd` 中。 (✅ 完成)
4. **[測試]** 所有 `--headless` 測試不會因為 UI 或 Viewport 的渲染缺失而產生 Error 或 Warning 污染日誌。 (✅ 完成)
5. **[測試]** 測試腳本具備自動清除 `user://savegame.save` 的防污染機制。 (✅ 完成)

## 狀態總結
三大痛點已經全面除鏽並進行物理驗證。公司模擬器成功實現了 MVC 解耦、解決了 Headless 視覺截圖崩潰問題，並完善了測試淨化協議！
