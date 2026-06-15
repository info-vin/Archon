# Technical Design Document (TDD): Semantic Infiltration

```text
=============================================================================
                  Archon: Semantic Infiltration (Godot 4.3)
                  "Grid Logic + Arcade Visuals" Architecture
=============================================================================
```

## 1. 核心理念與 RAG 教育目標 (Core Vision & Educational Goals)
本作旨在透過**「完全資訊的網格戰術潛行 (Perfect Information Tactical Stealth)」**機制（靈感汲取自《Invisible, Inc.》與《Into the Breach》），讓玩家深刻體會 RAG 工程師在解決真實問題時的智力博弈：**如何在極度受限的算力資源 (Action Points) 下，操縱向量空間 (Spatial Manipulation)，避開語意假陽性的視線，精準提取目標資料。**

本作摒棄依賴反應速度的街機玩法，轉而強調「空間預判」、「資源管理」與「環境控制」。

### 1.1 RAG 機制映射表 (Tactical Metaphor Mapping)
| 戰術遊戲元素 (Tactical Element) | RAG 專業術語 (RAG Concept) | 遊戲內行為與隱喻 (Behavior) |
| :--- | :--- | :--- |
| **行動點數 (AP / Turn)** | **Compute Budget (算力/Token 預算)**| 每回合玩家有固定的 AP。移動或使用裝備皆消耗 AP，隱喻 API 的調用成本。 |
| **敵人的視野錐 (Vision Cone)** | **Semantic Radius (語意相似度範圍)** | 敵人 (雜訊) 有明確的黃/紅視野範圍。玩家可預先看見。若停留在視野內，即被「檢索 (Retrieved)」並產生警告值。 |
| **警報等級 (Alarm Level)** | **Context Pollution (上下文污染度)** | 被敵人發現不會立刻死亡，而是增加全域警報值。警報值過高會導致終點 LLM `Hallucination (幻覺)`。 |
| **誘餌/推擠操作 (Push/Manipulate)**| **Prompt Engineering & Reranking** | 玩家不能「殺死」資料，但可透過發射誘餌改變敵人面向 (Prompt Injection)，或使用技能將敵人推開 (Reranking 降權)。 |
| **發光綠豆** | **Target Chunk (目標資料)** | 玩家必須收集的核心情資，是解鎖 `LLM Portal` 的必要條件。 |

### 1.2 RAG 紙娃娃裝備系統 (Modular RAG Loadout)
玩家在進入關卡前，必須透過組裝飛船的「武器與外掛模組」來建構自己的 RAG Pipeline。不同的模組會改變玩家在網格中的戰鬥與移動策略。

*   **[引擎核心] (Query Transformation)**
    *   **HyDE 引擎**: 發射「虛影飛船」探路，自動吸引周圍的 Chunk (LLM 預生成假答案以提升檢索命中率)。
    *   **Query Expansion 散彈槍**: 飛船光環分裂為三個方向同步掃描 (多角度提問擴展)。
*   **[主武器] (Retrieval Strategy)**
    *   **Dense Vector 雷射**: 範圍廣但容易喚醒遠處的紅色 False Positive (語意相似度檢索的雙面刃)。
    *   **BM25 實彈**: 必須極度靠近才能吸附 Chunk，但絕對不會喚醒無關幽靈 (死板但精準的關鍵字比對)。
*   **[副武器/防禦] (Post-Retrieval)**
    *   **Reranker 護盾**: 可彈開紅色幽靈，防止雜訊進入尾巴 (Cross-Encoder 重新評分過濾)。
    *   **LLMLingua 壓縮彈**: 主動消耗品，瞬間縮短飛船尾巴長度，恢復移動速度 (Token 壓縮技術)。
    *   **GraphRAG 鉤爪**: 吃到綠豆後，可瞬間把地圖上相連的綠豆扯過來 (知識圖譜的實體關聯跳躍)。

### 1.3 現實數據錨定與裝備數值平衡 (Data-Driven Loadout Balancing)
為了確保遊戲的教育價值，飛船裝備的數值設定（範圍、精準度、速度代價）並非憑空捏造，而是嚴格錨定真實世界的 RAG 評測基準 (Benchmarks)。我們將 Ragas 的核心指標轉化為遊戲內的屬性面板：

*   **Recall (召回率/吸引範圍)**：代表飛船吸附 `Target Chunk` (綠豆) 的範圍。
*   **Precision (精準度/抗雜訊)**：代表飛船「不喚醒」或「彈開」 `False Positive` (紅幽靈) 的能力。
*   **Token Cost (運算成本)**：裝備越重，飛船基礎移動速度越慢。

#### 權威評比框架參考 (Reference Benchmarks)
1.  **[MTEB (Massive Text Embedding Benchmark)](https://huggingface.co/spaces/mteb/leaderboard)**：
    *   **遊戲映射**：定義「Dense Vector 雷射」的基礎 `Precision`。MTEB 榜單排名越高的模型（例如 OpenAI v3 vs MiniLM），在遊戲中解鎖的雷射判定錐角越精準，越不易誤觸邊緣雜訊。
2.  **[Ragas (RAG Assessment)](https://docs.ragas.io/en/stable/)**：
    *   **遊戲映射**：Ragas 的 `Context Precision` 與 `Faithfulness` 指標，直接成為終點 `LLM Portal` 判定「幻覺 (Hallucination)」與「過關」的數學結算公式基礎。
3.  **[ARES (Automated RAG Evaluation System)](https://arxiv.org/abs/2311.09476)**：
    *   **遊戲映射**：定義「Reranker 護盾」的效能。參考 ARES 論文中微調模型對提昇準確度的貢獻，高等級護盾將擁有 95% 以上彈開紅幽靈的機率。

| 飛船裝備 (RAG 模組) | Recall (範圍/吸引力) | Precision (抗雜訊/防喚醒) | Token Cost (飛船減速) |
| :--- | :--- | :--- | :--- |
| **BM25 實彈 (基礎)** | ⬛⬛⬜⬜⬜ (極短) | ⬛⬛⬛⬛⬛ (絕對精準) | ⬛⬜⬜⬜⬜ (極輕) |
| **Dense Vector 雷射** | ⬛⬛⬛⬛⬜ (超遠) | ⬛⬛⬜⬜⬜ (易引怪) | ⬛⬛⬜⬜⬜ (中等) |
| **HyDE 探路引擎** | ⬛⬛⬛⬛⬛ (全圖吸) | ⬛⬜⬜⬜⬜ (極易引怪) | ⬛⬛⬛⬛⬜ (極重) |
| **Reranker 護盾** | 無影響 | 提升 Precision +50% | ⬛⬛⬛⬜⬜ (消耗能量) |

這套基於 Benchmark 的數值設計，強制玩家在遊玩過程中體驗真實 AI 工程師每天面對的 **"Recall vs Precision Trade-off (召回率與精準度的拉扯)"**。

---

## 2. 混合架構設計: 徹底的神經分離 (Decoupled Sync Architecture)
為確保能夠實施 TDD 測試驅動開發，我們完全放棄依賴 Godot 物理引擎 (`CharacterBody2D`) 進行邏輯運算。
採用 **"邏輯網格瞬間結算 + 視覺事件佇列 (Event Queue)"** 的雙層架構。

### 2.1 嚴格資料結構與 Enum 定義 (Data Structures)
所有邏輯運算必須依賴以下強型別定義，嚴禁使用 Magic Numbers。

```gdscript
# Enums.gd (Global)
enum Cell { EMPTY = 0, WALL = 1, PORTAL = 2 }
enum EntityType { PLAYER, TARGET_CHUNK, FALSE_POSITIVE }
enum EntityState { IDLE, AWAKE, ABSORBED }

# EntityData.gd (Model 實體)
class_name EntityData extends RefCounted
var id: String               # 唯一識別碼 (ex: "chunk_1", "enemy_2")
var type: Enums.EntityType
var grid_pos: Vector2i
var state: Enums.EntityState = Enums.EntityState.IDLE
```

### 2.2 [Model] 邏輯層 (純 GDScript, 0 毫秒結算)
`GridState.gd` 負責管理所有 `EntityData` 與二維陣列 `Array[Array[int]]`。
當玩家輸入方向時，呼叫 `process_turn(direction: Vector2i) -> Array[Dictionary]`。

**回合精確執行順序 (Strict Turn Resolution Flow)：**
1. **玩家移動判定**：檢查 `player.grid_pos + direction` 是否為 `Cell.WALL`。若阻擋則中斷回合，回傳空陣列。
2. **玩家位置更新**：更新玩家 `grid_pos`，產生 `{"event": "move", "id": "player", "to": new_pos}`。
3. **物品拾取判定**：若玩家位置與 `TARGET_CHUNK` 重疊，將其加入 `ContextWindow`，標記為 `ABSORBED`，產生 `{"event": "absorb", "id": chunk_id, "type": "T"}`。
4. **裝備邏輯介入 (RAG Loadout)**：根據玩家裝備（如 BM25 或 HyDE）修正下一步的搜尋半徑。
5. **敵人 (KNN) 喚醒與追蹤判定**：
   - 遍歷所有 `FALSE_POSITIVE`。若距離 $\le$ 裝備定義的半徑，狀態改為 `AWAKE`，產生 `{"event": "awake", "id": enemy_id}`。
   - 對已 `AWAKE` 的敵人，使用 A* 尋路朝玩家移動 1 格，產生 `{"event": "move", "id": enemy_id, "to": next_pos}`。
6. **敵人碰撞判定**：若敵人移動後與玩家重疊，將其加入 `ContextWindow`，標記為 `ABSORBED`，產生 `{"event": "absorb", "id": enemy_id, "type": "F"}`。
7. **結算判定**：若玩家抵達 `Cell.PORTAL`，計算 ContextWindow 內的 T/F 比例，產生 `{"event": "game_over", "result": "hallucination" | "success"}`。

---

## 3. Godot 節點與信號架構 (Node Hierarchy & Signal Contracts)
採用「事件佇列 (Event Queue) 模式」解決動畫與邏輯的時間差。

```text
 [ AUTOLOADS (Global) ]
 -----------------------------------------------------------------
 | GameManager.gd                                                |
 | - var logic_model: GridState = GridState.new()                |
 | - var input_locked: bool = false                              |
 | - func execute_player_input(dir: Vector2i):                   |
 |     if input_locked: return                                   |
 |     input_locked = true                                       |
 |     var events = logic_model.process_turn(dir)                |
 |     SignalBus.turn_events_generated.emit(events)              |
 -----------------------------------------------------------------
        | (Emit: Array[Dictionary])
        v (Listen)
 [ VIEW LAYER (CanvasLayer / Node2D) ]
 -----------------------------------------------------------------
 | MazeView.gd (繼承 Node2D)                                     |
 | - func _on_turn_events_generated(events: Array):              |
 |     for event in events:                                      |
 |         await play_animation_for_event(event) # 依序或並行播放 |
 |     GameManager.input_locked = false # 動畫播完才解鎖輸入      |
 -----------------------------------------------------------------
 | - TileMapLayer (Grid visuals)                                 |
 | - EntityRenderer (負責執行 Tween，將 Sprite2D 移至目標座標)       |
 -----------------------------------------------------------------
```

**架構細節優勢**：
透過 `process_turn` 回傳事件陣列，並由 `MazeView` 使用 `await` 逐一解析播放。這保證了：
1. **Model** 可以瞬間跑完，100% 支援極速的單元測試 (TDD)。
2. **View** 可以從容地播放 0.3 秒的飄移 Tween 動畫，且動畫播放期間 `input_locked = true`，徹底根絕玩家狂按鍵盤導致的畫面與邏輯狀態脫軌 (Race Condition)。

## 4. Web 輸出與跨裝置適配 (Web Export & Cross-Device Optimization)
本遊戲必須支援無縫嵌入網頁版與行動裝置瀏覽器 (Mobile Safari/Chrome)。

*   **觸控手勢驅動 (Swipe to Dash)**：
    *   在手機版，隱藏螢幕虛擬搖桿 (D-Pad)。
    *   實作 `SwipeDetector`，玩家在螢幕任何地方「滑動 (Swipe)」即可決定飛船下一次「飄移過彎」的方向。
*   **響應式視角 (Responsive Camera)**：
    *   Godot 視窗設定：`stretch/mode` = `canvas_items`, `stretch/aspect` = `expand`。
    *   在手機版直式螢幕下，`Camera2D` 的 `zoom` 自動縮小，確保迷宮全貌不被嚴重裁切。
*   **主動技觸發 (Active Skills)**：
    *   在 Desktop 綁定 `Spacebar`。在 Mobile，於 HUD 右下角提供一個面積 `64x64` 以上的大按鈕，用於釋放壓縮彈或衝刺。

## 5. 素材管線與視覺紙娃娃 (Asset Pipeline & Visual Loadout)
為了反映 `Modular RAG Loadout` 的差異，玩家的飛船在視覺上必須呈現出其裝備的武器。

*   **Shader 驅動的外觀 (Shader-Based Variants)**：
    *   有別於 Tycoon 的 Sprite 重疊，本遊戲採用 Tron-like 科技風格。
    *   裝備的武器透過 **Shader 參數** 來表現。例如：裝備 BM25 時，飛船尾焰變成冷藍色短光束；裝備 HyDE 時，飛船會週期性發出波紋特效 (Ripple Effect)。
*   **粒子系統 (GPUParticles2D)**：
    *   飄移過彎、彈開紅色幽靈、吃掉 Target Chunk 等，全部依賴 Godot 原生的 GPU 粒子系統，確保在 Web 端也能維持 60FPS 的 Juice 回饋。

---

## 6. 測試驅動開發策略 (TDD Strategy)
依賴團隊自製的 `MiniTest.gd` 進行 Headless 測試。因為邏輯層完全無延遲，測試可瞬間跑完。

### 6.1 核心測試案例 (Core Test Cases)
1.  **`test_grid_movement`**: 測試 `EntityLogic` 無法將 `grid_position` 移入標記為 `WALL` 的網格。
2.  **`test_knn_awakening`**: 測試當 Query 的 `grid_position` 與幽靈距離 <= `SIMILARITY_RADIUS` 時，幽靈狀態從 `SLEEP` 變為 `RETRIEVED`。
3.  **`test_hallucination_check`**: 模擬回合結算，手動注入 1 個綠豆與 2 個紅幽靈到 `ContextWindow` 陣列，驗證進入終點時是否正確觸發 `Hallucination` 錯誤代碼。

### 6.2 裝備模組測試 (Loadout Logic Tests)
為了確保紙娃娃系統的平衡性，必須針對各個 RAG 模組進行獨立測試：
1.  **`test_module_bm25`**: 裝備 BM25 實彈時，即使玩家 `grid_position` 與幽靈重疊，幽靈也絕對不可被喚醒 (`awake = false`)，除非完全命中。
2.  **`test_module_reranker`**: 裝備 Reranker 護盾時，當幽靈的 `grid_position` 嘗試進入玩家所在的網格，會被反彈至相鄰網格，且不會加入 `ContextWindow`。
3.  **`test_module_llmlingua`**: 當 `ContextWindow` 長度為 5 時，施放壓縮彈，長度必須瞬間減少至 `round(5 * 0.5)`，並觸發速度恢復 Signal。

---

## 7. 開發進度追蹤 (Progress Checklist)
- [x] **Phase 0**: 數學模型與 ASCII 終端原型驗證 (`ascii_poc.py`)。
- [ ] **Phase 1**: Godot 專案初始化與 TDD 基礎框架 (`MiniTest.gd` 導入)。
- [ ] **Phase 2**: 核心邏輯層 (Model) 實作與 100% 測試覆蓋 (GridState, EntityLogic)。
- [ ] **Phase 3**: 視覺層 (View) 綁定與補間動畫 (Tween) 飄移手感打磨。
- [ ] **Phase 4**: RAG 武器紙娃娃系統 (Loadout UI) 與對應的 Shader 特效實作。
- [ ] **Phase 5**: Web 輸出、觸控滑動適配 (SwipeDetector) 與 RWD 響應式優化。