# Technical Design Document (TDD): Archon Token Tower Defense

## 1. 架構總覽 (Architecture Overview)
本專案採用 Godot 4.x 開發。基於 Lean (精實) 開發原則，架構設計嚴格遵循「邏輯與視圖分離 (Separation of Concerns)」與「事件驅動 (Event-Driven)」模式，避免節點間的強耦合。

### 1.1 核心單例模式 (Autoloads / Singletons)
為了避免層層傳遞變數（造成義大利麵條代碼），系統將註冊以下兩個 Autoloads：
*   **`GameManager.gd`**: 全局狀態機。負責管理核心數值：`current_tokens` (當前 Token 預算)、`current_wave` (波數)、`lives` (伺服器健康度)。
*   **`SignalBus.gd`**: 全局事件匯流排。所有跨節點的通訊皆透過此腳本廣播。
    *   *定義信號例*：`signal enemy_destroyed(reward_amount)`
    *   *定義信號例*：`signal token_spent(cost_amount)`
    *   *定義信號例*：`signal base_damaged(damage_amount)`

---

## 2. 實體節點結構 (Node Hierarchy Specification)
絕不盲猜節點用法，以下為基於 Godot 4.x 官方最佳實踐的精確節點組合：

### 2.1 主場景 (`Main.tscn`)
```text
Node2D (Root)
 ├── TileMap (地圖繪製，無導航網格)
 ├── Path2D (定義敵人行走路徑的貝茲曲線)
 │    └── PathFollow2D_Spawner (負責動態實例化敵人)
 ├── Node2D (Towers_Container，用於存放玩家佈署的 Agent 塔)
 ├── Node2D (Projectiles_Container，用於存放發射的 Prompt 子彈)
 └── CanvasLayer (UI_Layer，確保 UI 永遠渲染在最上層)
      ├── Panel (頂部資訊列：Tokens, 波數, 血量)
      └── HBoxContainer (底部建塔選單)
```

### 2.2 敵人場景 (`Enemy.tscn` / `BugTicket`)
*捨棄高開銷的 `CharacterBody2D`，改用 `PathFollow2D` 綁定 `Area2D`。*
```text
PathFollow2D (透過腳本調整 progress 屬性來移動)
 └── Area2D (碰撞接收器)
      ├── Sprite2D (視覺圖形)
      ├── CollisionShape2D (碰撞範圍)
      └── ProgressBar (血條)
```
*   **移動邏輯**: 在 `_process(delta)` 中執行 `progress += speed * delta`。

### 2.3 代理人塔場景 (`Tower.tscn` / `AgentTower`)
```text
Node2D (Root)
 ├── Sprite2D (Agent 視覺，例如小機器人)
 ├── Area2D (攻擊範圍偵測器)
 │    └── CollisionShape2D (圓形範圍，CircleShape2D)
 └── Timer (攻擊冷卻計時器)
```
*   **索敵邏輯**: 
    *   當敵人的 Area2D 觸發 `area_entered` 時，將其加入 `enemies_in_range` 陣列。
    *   觸發 `area_exited` 時，將其移出陣列。
    *   `Timer` Timeout 時，若陣列不為空，則實例化子彈，目標設為陣列中的第一個元素 (或計算 `progress` 最大的敵人)。

### 2.4 提示詞子彈場景 (`Projectile.tscn` / `PromptBullet`)
```text
Area2D (本體與碰撞偵測)
 ├── Sprite2D (子彈視覺，如封裝的信封或對話氣泡)
 └── CollisionShape2D (微小碰撞盒)
```
*   **命中邏輯**: 觸發 `area_entered` 時，檢查目標是否擁有 `take_damage()` 方法。呼叫該方法後，呼叫 `queue_free()` 銷毀自身。

---

## 3. 數值與資料驅動設計 (Data-Driven Design)
為了避免在程式碼中硬編碼 (Hardcoding) 塔的攻擊力或敵人的血量，系統將使用 Godot 的 `Resource` 類別來定義數據結構。

### 3.1 資源腳本: `TowerStats.gd`
繼承自 `Resource`，定義 Agent 的基礎屬性：
*   `@export var agent_name: String` (如 "MarketBot")
*   `@export var deploy_cost: int` (消耗 Token)
*   `@export var damage: float` (Prompt 解決問題的能力)
*   `@export var fire_rate: float` (冷卻時間秒數)
*   `@export var attack_range: float` (索敵半徑)

*實作效益：設計師可以在 Godot 編輯器的 Inspector 中直接右鍵新增不同的 `TowerStats` 資源檔（例如 `devbot_stats.tres`, `marketbot_stats.tres`），而不需要修改任何一行程式碼。*

---

## 4. 物理與碰撞遮罩規劃 (Collision Layers & Masks)
為了效能極佳化，絕不讓子彈去偵測其他子彈或防禦塔，嚴格定義 Collision Layer：
*   **Layer 1 (Towers)**: 防禦塔佔用。
*   **Layer 2 (Enemies)**: 敵人佔用。
*   **Layer 3 (Projectiles)**: 子彈佔用。
*   **設定**: 
    *   防禦塔的索敵 `Area2D`：Layer 1, Mask 2 (只偵測敵人)。
    *   子彈的 `Area2D`：Layer 3, Mask 2 (只偵測敵人)。
    *   敵人的 `Area2D`：Layer 2, Mask 0 (不主動偵測，被動接收)。

---

## 5. 後端 API 擴展預留 (Backend Integration Hook)
雖然 MVP 是本地單機遊戲，但架構需預留與 Archon FastAPI 後端溝通的介面。
*   **實作位置**: `GameManager.gd` 中掛載一個 `HTTPRequest` 節點。
*   **觸發時機**: 當遊戲結束 (`game_over`) 或通關 (`victory`) 時，發送 POST 請求至 `/api/stats/game_record`，將消耗的 Token 與成功防禦的波數寫入真實的資料庫進行排行。