# Phase 5.8.1: Recontextualization - 核心架構移植與模組化升級 (Core Porting & Modular Upgrades)

> **核心戰略：抽取 Maaack MVC 骨架，注入 RAG 裝甲 (No Happy Path)**
> 本階段承接自 Phase 5.8.0 的基礎設施驗證，目標是正式建立 Godot 的純淨邏輯層。我們拒絕從零手刻可能帶有緊耦合缺陷的架構，而是精確移植 [Maaack/Battle-Deck-Energy](https://github.com/Maaack/Battle-Deck-Energy) 開源專案的 `Model` 與 `EventBus`，並施加針對 RAG RPG 擴充性的外科手術升級。

## 階段一：純資料層物理抽取 (Data Layer Extraction)
**門禁**：移植的腳本內部**嚴禁**出現任何 `extends Node2D`, `extends Control` 或依賴 `Tween` 的視覺化程式碼，必須保證 100% 能夠在 Headless 模式下以 0 毫秒延遲執行。

*   ✅ **任務 1.1：`CardData.gd` (卡牌資源定義)**
    *   ✅ 從 Maaack 移植並擴充。繼承自 `Resource`。
    *   ✅ 新增 RAG 專屬屬性：`match_type` ('hybrid', 'vector', 'keyword'), `similarity` (float), `ap_cost` (int)。
*   ✅ **任務 1.2：`DeckData.gd` (陣列操作狀態機)**
    *   ✅ 從 Maaack 移植。負責卡牌陣列的 `shuffle`, `pop_front`, `append`。
    *   ✅ 新增核心 TDD 算式：`calculate_context_purity()` (計算安全閥值以上的純淨度)，`calculate_delivery_damage()` (計算最終交付傷害)。

## 階段二：RPG Meta-Architecture 模組化升級
**門禁**：嚴禁使用本地寫死的 `.tres` 清單進行註冊。

*   ✅ **任務 2.1：`CardRegistry.gd` (動態工廠)**
    *   ✅ 在遊戲啟動時 (`_ready`)，利用 `DirAccess` 動態掃描 `res://src/models/cards/` 目錄。
    *   ✅ 自動解析並將所有合法的 `ActionCard` 資源加載進全域 Dictionary 中，實現未來的 OCP 開閉原則。
*   ✅ **任務 2.2：`PlayerProfile.gd` (狀態管理) -> 實作為 `GameState.gd`**
    *   ✅ 汲取 Maaack `PersistentData.gd` 精神，建立 `GameState.gd` Autoload。
    *   ✅ 重構為支援 RPG 屬性：管理玩家 `AP` 以及對 Boss 的 `HP`，並且監聽 `EventBus`，實作單向資料流狀態機。
*   ✅ **任務 2.3：`EventBus.gd` (事件總線)**
    *   ✅ 除了基礎的 `card_drawn`, `card_played` 外，建立全域單例模式供後續擴充 RAG 危機信號。

## 階段三：零依賴物理公證 (Headless Validation)
*   ✅ **任務 3.1：Headless TDD 測試**
    *   ✅ 撰寫 `tests/test_deck_math.gd` 與 `tests/test_state_machine.gd`，在 `--headless` 模式下執行。
    *   ✅ **斷言 (Assert)**：注入卡牌驗證 `DeckData.calculate_context_purity()` 與 `calculate_delivery_damage()` 的數學期望值完全正確。
    *   ✅ **斷言 (Assert)**：`CardRegistry` 啟動後，動態註冊表內涵蓋各種類型卡牌，且數量與實體檔案一致。

## 階段四：網頁遊戲自適應物理約束 (Web Game RWD Constraints)
**門禁**：嚴格禁止在 UI 中使用絕對座標 (Absolute Positioning) 定位，以相容 iPad 等多解析度裝置。

*   [x] **任務 4.1：專案全局設定約束**
    *   `project.godot` 中 `display/window/stretch/mode` 必須為 `canvas_items`。
    *   `project.godot` 中 `display/window/stretch/aspect` 必須為 `expand`。
*   [x] **任務 4.2：UI 根節點與容器約束**
    *   主畫面 (`GameBoard` 等) 的根 `Control` 節點必須使用 `set_anchors_and_offsets_preset(PRESET_FULL_RECT)`，鎖死於螢幕四角。
    *   卡牌排列必須依賴 `HBoxContainer` / `VBoxContainer` / `GridContainer`。
    *   版面留白必須使用 `MarginContainer`，嚴禁使用 `position = Vector2(x, y)` 手動排版。
