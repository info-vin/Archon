# Phase 5.8.5: 卡牌合成拆解工坊與美術遷移 (Workshop Synthesis & Art Migration)

> **核心原則：非線性牌組建構 (Non-linear Deck-building) 與 拒絕虛假開發**
> 為了維持 Archon 數位雙生 (Digital Twin) 的真實性，遊戲內的所有 RAG 卡牌機制必須 100% 映射到實際可用的後端 Python RAG 服務參數。且卡牌的取得並非線性解鎖，而是引入類似寶可夢卡牌的「合成與拆解 (Synthesize & Dismantle)」Meta-Game 機制。

## 1. 參數驅動與非線性卡牌擴充 (Parameter-Driven Synthesis Expansion)

在後端尚未實裝 GraphRAG 與 Matryoshka 等演算法前，我們將利用既有的 RAG 服務參數 (Vector, Hybrid, Reranker, Threshold) 來劃分卡牌階級 (L1~L5)。玩家脫離新手村後，將解鎖「卡牌工坊 (Workshop)」，體驗機率性的卡牌合成系統。

### 1.1 實體參數映射卡牌階級 (Parameter Mapping)
*   **L1 基礎級 (Base Vector)**：`match_count=5, min_score=0.0`。極易產生雜訊。
*   **L2 標準級 (Hybrid Scatter)**：啟用 `hybrid_search`，召回率高。
*   **L3 進階級 (Precision Vector)**：`min_score=0.75`。嚴格過濾，只給高純度晶片。
*   **L4 專家級 (Reranker Shield)**：啟用 `use_reranking=True`。物理抹除假陽性。
*   **L5 傳說級 (Overclocked RAG)**：Hybrid + Reranking + 極端參數。

### 1.2 核心新機制：合成與拆解 (Synthesize & Dismantle)
不再是「升級送卡」，而是真正的牌組經營 (Deck Management)：
*   **合成 (Synthesize)**：玩家可將 3 張同階級的卡牌放進合成爐，有一定機率 (如 60%) 合成出高一階的卡牌。如果失敗，卡牌將碎裂成「算力廢鐵 (Scraps)」。
*   **拆解 (Dismantle)**：將不需要的高階卡或雜訊卡拆解，換取基礎 L1 卡牌或合成素材。
*   **實作目標**：建立 `CardWorkshop.tscn` 場景，並將 `CardData.gd` 模組化，加入 `rag_parameters` 與 `card_level` 屬性。

---

## 2. L5 終極卡牌底層實作計畫 (MRL & GraphRAG API Blueprint)

基於「探針先行 (Probe-First)」原則，我們已於 2026/07 成功完成 `probe_mrl_pipeline.py` 與 `probe_graphrag_pipeline.py` 的物理驗證。證明了在不引入沉重外部依賴 (如 Neo4j) 的情況下，目前的 Supabase/PostgreSQL 架構完全具備支援 L5 終極卡牌的運算能力。

### 2.1 探針實體驗證結果 (Probe Results)
*   **MRL 維度裁切 (Matryoshka Representation Learning)**：
    *   **結果**：✅ 通過。成功使用 `pgvector` 的陣列切片語法 `(((embedding::real[])[1:256])::vector(256))`，將 768 維度裁切為 256 維度進行餘弦相似度比對。
    *   **效能**：在 1000 筆小量測試中獲得約 1.70 倍的檢索提速。預期在巨量資料下能更大幅度降低向量檢索的 AP (算力) 與延遲消耗。
*   **GraphRAG 圖譜推理 (Pure Postgres Recursive CTE)**：
    *   **結果**：✅ 通過。成功使用純 SQL 的遞迴查詢 (Recursive CTE)，以極低延遲 (0.04s) 完成從實體節點到衍生風險的 2-hop 多跳推理。這在架構上證明了不需部署 Neo4j 也能達成關聯性檢索，貫徹了單一事實來源 (SSOT) 原則。

### 2.2 後端 API 實作藍圖 (Backend API Implementation) - ✅ 已完成 (Completed)
為了讓 Godot 遊戲端能真正實作並打出這兩張 L5 卡牌（而非只是用 Hybrid 參數充數），我們已於 FastAPI 後端完成以下擴充與自動化測試：

1.  **✅ MRL 裁切 API 擴充 (`rag_api.py`)**：
    *   **通訊協定**：在 `HybridSearchRequest` 中新增可選參數 `truncate_dim: int | None = None`。
    *   **資料庫層**：修改 `hybrid_match_chunks` Supabase RPC，使其能根據傳入的 `truncate_dim` 動態組合 SQL 切片語法，只比對向量的前 N 個維度。
    *   **遊戲對接**：玩家打出「🗜️ Matryoshka 降維壓縮卡」時，前端請求將帶上 `truncate_dim=256`，不僅提升檢索速度，還能解鎖特殊的卡牌連鎖效果。

2.  **✅ GraphRAG 圖譜連鎖 API (`graph_api.py` 整合於 `rag_api.py`)**：
    *   **通訊協定**：新增 `/api/rag/graph-search` 端點。
    *   **資料庫層**：建立實體的 `knowledge_entities` 與 `knowledge_relationships` 表格，並將 Probe 中驗證通過的 Recursive CTE 邏輯封裝為預存程序 `graph_reasoning_n_hop`。
    *   **遊戲對接**：玩家打出「🕸️ 知識圖譜連鎖卡」時，向此端點發送請求。後端回傳多跳的關聯路徑 (如 `Godot -> GDScript -> MemoryLeak`)，並在遊戲中依據跳數 (Hop count) 結算爆擊傷害乘數。
