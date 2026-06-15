# Technical Design Document (TDD): Semantic Infiltration

```text
=============================================================================
                  Archon: Semantic Infiltration (Godot 4.3)
                  "Grid Logic + Arcade Visuals" Architecture
=============================================================================
```

## 1. 核心理念與 RAG 教育目標 (Core Vision & Educational Goals)
本作旨在透過高速街機潛行玩法 (類似 Pac-Man CE DX 的霓虹飄移)，讓玩家直觀理解 RAG (檢索增強生成) 的核心挑戰：**如何在有限的上下文視窗 (Context Window) 中，最大化高價值資料 (Target Chunks)，並甩開語意假陽性 (False Positives) 的雜訊污染。**

### 1.1 RAG 機制映射表 (Metaphor Mapping)
| 遊戲內元素 (Game Element) | RAG 專業術語 (RAG Concept) | 遊戲內行為與隱喻 (Behavior) |
| :--- | :--- | :--- |
| **玩家飛船** | **Query (使用者提示詞)** | 在網格中移動。移動代表著在向量空間中進行相似度搜索。 |
| **網格迷宮** | **Vector Database (向量資料庫)**| 存放所有切片資料的多維空間。 |
| **發光綠豆** | **Target Chunk (目標資料)** | 玩家必須收集的正確上下文。收集後會連接在飛船尾巴上。 |
| **紅色幽靈** | **False Positive (語意假陽性)** | 平時休眠。一旦 Query 靠近(相似度高)即被「喚醒檢索」，變紅並死命追逐玩家。 |
| **飛船尾巴** | **Context Window (上下文視窗)** | 收集的綠豆與追逐的紅幽靈共同組成。長度代表 Token 消耗，越長飛船越重/越慢。 |
| **終點傳送門** | **LLM Generation (大模型生成)** | 帶著尾巴衝入結算。若尾巴中紅大於綠，觸發 `Hallucination (幻覺)` 失敗。 |

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
採用 **"邏輯網格瞬間結算 + 視覺補間延遲表現"** 的雙層架構。

### 2.1 [Model] 邏輯層 (瞬間發生，0 秒，100% 可單元測試)
純 GDScript 類別，不依賴 SceneTree 或 Node。

*   `GridState.gd`: 負責二維陣列 `Array[Array[int]]` 管理牆壁、路徑。提供自製 A* 尋路 (曼哈頓距離)。
*   `EntityLogic.gd`: 玩家與敵人的邏輯實體。只記錄 `grid_position (Vector2i)` 與狀態。
*   **回合解析器 (Turn Resolver)**: 當玩家輸入方向，邏輯層「瞬間」將玩家移至下一格，並「瞬間」計算所有被喚醒幽靈的下一步路徑。

### 2.2 [View] 視覺層 (有慣性與延遲，負責 Juice)
掛載於 Godot Node 上的控制器。負責「演戲」。

*   `ShipView.gd`: 監聽邏輯層的 `position_changed(new_grid_pos)` Signal。
*   **動畫鎖定 (Animation Lock)**: 收到信號後，使用 Godot `Tween` 以具有彈性 (Elastic) 的曲線，將 `Sprite2D` 的像素座標平滑移動至目標網格。移動期間鎖定輸入（或存入 Input Queue）。
*   **Cornering 飄移**: 如果 Input Queue 中有下一個方向，在轉角處會畫出弧線並產生粒子特效 (Sparks)。

---

## 3. 測試驅動開發策略 (TDD Strategy)
依賴團隊自製的 `MiniTest.gd` 進行 Headless 測試。因為邏輯層完全無延遲，測試可瞬間跑完。

### 3.1 核心測試案例 (Core Test Cases)
1.  **`test_grid_movement`**: 測試 `EntityLogic` 無法將 `grid_position` 移入標記為 `WALL` 的網格。
2.  **`test_knn_awakening`**: 測試當 Query 的 `grid_position` 與幽靈距離 <= `SIMILARITY_RADIUS` 時，幽靈狀態從 `SLEEP` 變為 `RETRIEVED`。
3.  **`test_hallucination_check`**: 模擬回合結算，手動注入 1 個綠豆與 2 個紅幽靈到 `ContextWindow` 陣列，驗證進入終點時是否正確觸發 `Hallucination` 錯誤代碼。

### 3.2 裝備模組測試 (Loadout Logic Tests)
為了確保紙娃娃系統的平衡性，必須針對各個 RAG 模組進行獨立測試：
1.  **`test_module_bm25`**: 裝備 BM25 實彈時，即使玩家 `grid_position` 與幽靈重疊，幽靈也絕對不可被喚醒 (`awake = false`)，除非完全命中。
2.  **`test_module_reranker`**: 裝備 Reranker 護盾時，當幽靈的 `grid_position` 嘗試進入玩家所在的網格，會被反彈至相鄰網格，且不會加入 `ContextWindow`。
3.  **`test_module_llmlingua`**: 當 `ContextWindow` 長度為 5 時，施放壓縮彈，長度必須瞬間減少至 `round(5 * 0.5)`，並觸發速度恢復 Signal。