---
name: godot-4-audit
description: Strict code generation, architecture design, headless compilation checks, and visual proof guidelines for Godot 4.x (GDScript 2.0) projects.
---

# Godot 4.x GDScript 2.0 開發與自動化門禁規範

你是一個專門針對 Godot 4.x 的代碼生成、重構與自動化審計的開發 Skill。你必須嚴格遵守 Godot 官方文檔的 GDScript 2.0 語法規範，拒絕任何過時或幻想像的 API，並確保專案在本地與無頭（Headless）環境下皆能順利編譯與測試。

---

## 🔍 官方開發文件與調試查詢參考 (Official References)
在遇到任何語法、API 變動或調試瓶頸時，優先查閱以下官方文檔網址：
- **Godot 4.x 官方中文文檔**：`https://docs.godotengine.org/zh-cn/4.x/`
- **GDScript 2.0 語法基礎指引**：`https://docs.godotengine.org/zh-cn/4.x/tutorials/scripting/gdscript/gdscript_basics.html`
- **Godot 4.x 完整 API 類別索引**：`https://docs.godotengine.org/zh-cn/4.x/classes/index.html`
- **命令列 (CLI) 與無頭模式調用參數**：`https://docs.godotengine.org/zh-cn/4.x/tutorials/editor/command_line_primer.html`
- **Web (HTML5) 導出與部署規範**：`https://docs.godotengine.org/zh-cn/4.x/tutorials/export/exporting_for_web.html`

---

## 🛑 一、【強制語法與編譯對齊】

### 1.1 靜態型別 (Static Typing)
所有變量、函數參數及返回值必須帶有明確的型別宣告，嚴禁使用隱式動態型別。
- **錯誤**：`var speed = 200`
- **正確**：`var speed: float = 200.0`
- **正確型別函數**：`func _process(delta: float) -> void:`

### 1.2 註解與註冊 (Annotations)
一律使用 Godot 4.x 的 `@` 註解語法，拒絕 Godot 3 的舊式括號宣告。
- **錯誤**：`onready var p = $Sprite`
- **正確**：`@onready var p: Sprite2D = $Sprite`
- **錯誤**：`export(int) var health`
- **正確**：`@export var health: int = 100`

### 1.3 實例化與節點更名 (Instantiation & Rename)
- 實例化統一使用 `instantiate()`，禁止使用 `instance()`。
- 必須使用 Godot 4 更名後的節點：
  - `KinematicBody2D` ➡️ `CharacterBody2D`
  - `Position2D` ➡️ `Marker2D`
- 物理移動一律不帶參數：
  - **正確**：`velocity = direction * speed; move_and_slide()`

### 1.4 信號連接 (Signals)
使用可調用對象（Callable）連接信號，禁止傳遞字串函數名。
- **錯誤**：`button.connect("pressed", self, "_on_pressed")`
- **正確**：`button.pressed.connect(_on_pressed)`

### 1.5 狀態解耦 (Resource + Event Bus MVC)
嚴禁 UI 節點 (View) 直接呼叫底層模擬邏輯或持有 Manager 實體。狀態必須存在 `Resource` 或純邏輯節點中，並透過 `EventBus` 發送訊號，UI 只能監聽。

### 1.6 非同步與記憶體安全 (Async & Memory Safety)
- **非同步死鎖 (Tweens)**：使用 `await tween.finished` 時，若目標節點被釋放 (`queue_free()`) 或轉移父節點，會導致死鎖或崩潰。高風險非同步應改用 `await get_tree().create_timer(time).timeout`，或在 `_exit_tree` 時手動 `tween.kill()`。
- **懸空指標 (Lambdas)**：Lambda 閉包捕獲外部 Node 參考時，若該 Node 被釋放觸發 Lambda 會導致靜默崩潰。**強制**在內部使用 `if is_instance_valid(node):` 進行檢查。

### 1.7 UI 事件傳遞防禦 (mouse_filter)
透明遮罩或裝飾性卡牌子節點的預設 `mouse_filter = STOP` 容易意外攔截滑鼠點擊，導致拖曳系統 (Drag & Drop) 癱瘓。嚴格區分 `STOP` (攔截)、`PASS` (攔截並穿透給父節點) 與 `IGNORE` (完全忽略)。裝飾性 UI 一律設為 `IGNORE`。

### 1.8 全域單例與 API 存取 (Singleton & API Misuse)
- **單例認知錯誤**：`Engine.has_singleton("GameState")` 是檢查 C++ 單例。自定義的 Autoload 必須使用 `get_tree().root.has_node("GameState")` 或 `get_node_or_null("/root/GameState")` 檢查。
- **Object.get 誤用**：將 Godot 的 `Object.get(property)` 誤用為 Python 的 `dict.get(key, default)`（傳入兩個參數）會導致靜默崩潰。存取 Object 時只能傳遞單一屬性名稱。

---

## 🛡️ 二、【無頭模式防禦與相容性門禁】

### 2.1 避開全域 ClassDB 快取缺失 (Headless Class_Name Fallback)
在 `--headless` 命令列或 CI/CD 環境下，Godot 未經編輯器 GUI 掃描前，全域 Class 註冊表是空的。**在跨腳本實體化或型別約束時，禁止直接寫 ClassName**。
- **致命錯誤**：
  ```gdscript
  var resolver: CardEffectResolver = CardEffectResolver.new() # Headless 會報 Identifier not declared 錯誤
  ```
- **硬化正確寫法**：
  ```gdscript
  var resolver: RefCounted = preload("res://Scripts/Logic/CardEffectResolver.gd").new()
  ```

### 2.2 唯一名稱與數據分離 (Architecture)
- **場景唯一節點**：獲取高頻率變動的子節點時，優先使用唯一名稱 `%`（如 `get_node("%PlayerSprite")`），防止場景樹結構調整導致路徑失效。
- **數據與邏輯分離**：道具、卡牌與怪物屬性禁止硬編碼。必須提供繼承自 `Resource` 的 GDScript 定義（如 `class_name CardStats extends Resource`）並指導生成對應的 `.tres` 檔案。
- **動態節點清理**：生成 any 動態實例化（如特效、掉落物）時，必須包含 `Timer` 或 `VisibleOnScreenNotifier2D`，並在超時/出鏡時調用 `queue_free()`，杜絕內存洩漏。

---

## 🧪 三、【自動化測試與視覺公證規範】

### 3.1 輕量 MiniTest 測試框架
所有單元/整合測試必須繼承自自製反射基底 `MiniTest`，禁止依賴外部測試插件。
- 測試方法命名必須以 `test_` 開頭。
- 執行斷言時使用 `assert_eq(actual, expected, msg)` 或 `assert_not_null(actual, msg)`.
- **無頭測試執行命令**：
  ```bash
  GODOT_DISABLE_LEAK_CHECKS=1 godot --headless -s Tests/HeadlessRunner.gd
  ```

### 3.2 繞過 Headless 進行視覺公證 (Visual Proof)
- **問題**：`--headless` 下 dummy 渲染器不渲染視區，截圖會返回 `null`。
- **解決方案**：必須透過 Python 橋接腳本（`capture_proof.py`）拉起帶 GUI 的實體 Godot進程執行 `capture_ui.gd`，在場景載入後使用 `await create_timer(1.0).timeout` 緩衝幀，再儲存為 `proof_refactor_success.png` 物理圖檔。

### 3.3 WASM 匯出發布
修改遊戲後，必須呼叫以下命令將 WASM 包體導出至前端靜態目錄以供託管：
```bash
godot --headless --export-release "Web" ../enduser-ui-fe/public/games/card-battler/index.html
```

---

## 📏 四、【L2 模組化與 400 行門禁】

- **400 行絕對限制**：任何 GDScript 主檔案（包括 `MainUI.gd`、`GameState.gd`）行數上限為 **400 行**。
- **核心職責拆分**：
  - 音效、震動與受擊文字等視覺回饋抽出至 `CombatJuice.gd`。
  - 卡牌特技效果抽出至 `CardEffectResolver.gd`。
  - 翻譯與字串處理抽出至 `GitTranslator.gd`。

---

## 🎯 五、【經典架構範例】

### 5.1 狀態機基底 (State.gd)
```gdscript
class_name State extends Node

var actor: CharacterBody2D

func enter() -> void: pass
func exit() -> void: pass
func handle_input(_event: InputEvent) -> void: pass
func update(_delta: float) -> void: pass
func physics_update(_delta: float) -> void: pass
```

### 5.2 反射式測試基底 (MiniTest.gd)
```gdscript
extends RefCounted
class_name MiniTest

var tests_passed: int = 0
var tests_failed: int = 0

func assert_eq(actual, expected, message: String = "") -> void:
	if actual == expected:
		tests_passed += 1
		print("  🟢 [PASS] ", message)
	else:
		tests_failed += 1
		push_error("  🔴 [FAIL] ", message, " | Expected: ", expected, " | Got: ", actual)

func run_test_suite() -> void:
	for method in get_method_list():
		if method.name.begins_with("test_"):
			call(method.name)
```
