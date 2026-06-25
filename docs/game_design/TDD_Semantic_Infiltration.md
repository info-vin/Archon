# Technical Design Document (TDD): Semantic Infiltration

```text
=============================================================================
                  Archon: Semantic Infiltration (Godot 4.3)
                  "Hybrid RAG Deck-builder" Architecture
=============================================================================
```

## 核心理念 (Core Vision)
本作已拋棄原本的《Into the Breach》二維網格走位，全面轉向《進入矩陣（Into The Grid）》風格的**「RAG 混合檢索與卡牌構築 (Hybrid RAG Deck-builder)」**。

遊戲目標在於讓玩家深刻體會 RAG 工程師的智力博弈：如何在極度受限的記憶體與算力資源下，透過卡牌構築 (Deck-building) 與混合檢索 (Hybrid Search)，過濾假陽性雜訊並精準提取出目標資料，最終解鎖 LLM Portal。

---

## 1. 混合 RAG 矩陣與動態卡牌演算系統

### 1.1 系統核心架構與資料流 (Architecture & Data Flow)
本系統嚴格採用 **Data-Driven MVC 架構 (借鑒 Maaack/Battle-Deck-Energy 模式)** 進行完全解耦：
*   **Model**：所有卡牌屬性繼承 `Resource`。`DeckManager` 僅處理陣列移轉，並發射狀態快照 (Snapshot)。
*   **Event Queue**：扮演動畫佇列 (Animation Queue)。確保邏輯層瞬間結算 (0 毫秒延遲)，而視覺層只負責消耗佇列播放動畫。
這確保了在自動化測試時，完全無需等待 Godot 物理與動畫，達到純數學的精準度與極速 TDD 迴圈。

### 1.2 系統架構序列圖 (Sequence Diagram)
```mermaid
sequenceDiagram
    participant Godot as Godot 4.3 (Game Client)
    participant FastAPI as Python Backend (archon-server)
    participant HF as Hugging Face Inference API
    participant DB as Supabase PostgreSQL
    participant CDN as GitHub Raw CDN

    Godot->>FastAPI: 1. 發送 Query 請求與卡牌技能 (HTTP POST)
    FastAPI->>HF: 2. 呼叫 API 請求向量化 (Xenova/bge-small)
    Note over HF: 依賴伺服器設定的 HF_TOKEN 額度
    HF-->>FastAPI: 3. 回傳 384 維度向量
    FastAPI->>DB: 4. 呼叫 hybrid_match_chunks 預存程序
    Note over DB: SQL fts (關鍵字匹配)<br/>pgvector 相似度檢索 (向量匹配)<br/>雜訊過濾 (相似度 < 0.82)
    DB-->>FastAPI: 5. 回傳 chunk_id, metadata(含 GitHub 網址) 與相似度
    FastAPI->>CDN: 6. 根據 metadata 請求完整實體 JSON
    CDN-->>FastAPI: 7. 回傳真實文本實體資料 (醫療/法規)
    FastAPI-->>Godot: 8. 異步回傳組合後的純 JSON 數據
    Godot->>Godot: 9. 將 JSON 解析並推入 EventQueue 驅動 UI
```

### 1.3 0元低耗能分離式 RAG 資料管線 (0-Cost Decoupled RAG Pipeline)
為捍衛系統效能與儲存極限，系統實施「向量索引與文本存儲的物理分離」，並透過 FastAPI 後端達成高效能代理：

*   **步驟一（向量化與重排）**：
    Python 後端 (`archon-server`) 接收到請求後，直接呼叫 Hugging Face Serverless Inference API (例如 768 維的開源模型) 取得向量。重排則可利用 HF 額度或後端資源執行，完全不佔用遊戲客戶端算力。
*   **步驟二（輕量向量索引）**：
    Supabase Postgres 內部**不存完整 JSON 原文**，僅儲存用於搜尋的輕量摘要 (`content`)、指向 GitHub CDN 的 `metadata`，以及降維後的 768 維向量。透過預存程序快速選出 Top-K。
*   **步驟三（GitHub Raw CDN 取回）**：
    算出 ID 後，FastAPI 解析 `metadata` 中的 GitHub Raw 網址 (例如 `raw.githubusercontent.com/.../medical.json`)，精準抓取對應的龐大 JSON 實體區塊。
*   **步驟四（Godot 異步結算）**：
    將輕量且富含真實資料的 JSON 回傳給 Godot 的 Event Queue 進行卡牌實體化。

---

## 2. 核心遊戲機制與模型層 (Core Mechanics & Model Layer)

### 2.1 牌組邏輯與狀態機 (DeckManager.gd)
資料在庫中以 Chunk 形式存在，進入遊戲後完全轉化為「卡牌（Cards）」與「陣列移轉」。
*   **知識庫 (Knowledge Base)** = 主牌組陣列 `Array[Dictionary]`。
*   **上下文視窗 (Context Window)** = 核心手牌區陣列（上限 5 張）。
*   **算力預算 (AP / 水晶)** = 玩家每回合出牌的 Token 費用限制。

### 2.2 核心對決邏輯 (Recall vs Precision)
*   **【BM25 關鍵字實彈卡】**：字面匹配（類似 SQL）。出牌時精準度 100%，但毫無推理能力，無法觸發語意跨界連鎖（Combo）。
*   **【Dense Laser 向量雷射卡】**：召回率極高（Recall）。能一口氣大量抽牌並解鎖跨領域語意推理，但代價是會引發「假陽性（False Positive）」，強制將帶有 Glitch 污染效果的紅色【雜訊卡/紅幽靈】塞進玩家手牌。
*   **【Reranker 電漿護盾卡】**：執行 Cross-Encoder 權重重排。發動時，強制將手牌中 `is_noise: true` 的紅色雜訊卡直接丟棄 (Discard) 至回收桶，淨化 Context Window。

**最終結算（LLM 交付）**：手牌純度越高（綠色 Target 卡多，紅色雜訊卡為 0），觸發的 LLM 生成 Combo 傷害越高。若混入紅色雜訊卡，直接扣除玩家血量並判定【模型幻覺崩潰 (Hallucination)】。

### 2.3 核心戰鬥數學驗證公式 (Combat Math Validation Formulas)
為了確保 TDD 腳本能進行精確的斷言 (Assert)，以下是 Godot Model 層必須實作的嚴格數學公式：

1.  **上下文純淨度 (Context Purity, $P$)**:
    $$P = \frac{\text{黃金命中晶片數量}}{\text{手牌區 (Context Window) 總晶片數}}$$
2.  **LLM 交付傷害 (Delivery Damage, $D$)**:
    當按下「交付」時，對目標危機造成的解決分數 (傷害)：
    $$D = (\text{基礎火力 } 1000) \times P \times \text{連鎖乘數}$$
    *(註：若觸發 GraphRAG 連鎖卡，連鎖乘數為 $1.5$，否則為 $1.0$)*
3.  **幻覺反噬懲罰 (Hallucination Penalty)**:
    若交付時 $P < 1.0$ (即手牌中包含「紅幽靈雜訊晶片」)，交付傷害 $D$ 強制歸零，且玩家直接受到反噬：
    $$\text{玩家受傷} = (\text{紅幽靈晶片數量}) \times 500 \text{ HP}$$
4.  **算力消耗 (AP Cost)**:
    玩家每回合初始 AP = 5。
    *   BM25 實彈卡：消耗 1 AP
    *   Dense 向量雷射卡：消耗 2 AP
    *   Reranker 電漿護盾卡：消耗 3 AP (極度耗能，需謹慎使用)

---

## 3. 產業主題劇本與現實反思機制 (Scenario Campaigns & Post-Mortem Feedback)

為了達到「RAG 系統工程師模擬器」的教育目的，遊戲設計了兩大極端流派的劇本關卡，並在通關/失敗後提供「現實反思結算報告 (Post-Mortem Report)」。

### 3.1 醫療劇本：【抗生素的致命防線】 (防禦流)
*   **真實資料源 (GitHub API)**：`https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json` (PubMedQA 專家標記集)
*   **核心痛點**：容錯率為 0，單靠向量相似度搜尋極易引發配伍禁忌（Contraindication）致死。
*   **卡牌策略**：玩家必須發動**【知識圖譜護盾卡 (GraphRAG)】**，強制過濾並炸毀手牌中因語意相近而混入的「假陽性紅幽靈卡（危險雜訊）」，僅留下 100% 安全的黃金指南卡餵給 LLM Boss。
*   **結算反思**：
    *   ❌ *失敗報告*：「嚴重醫療事故發生！您未啟動 GraphRAG 護盾，模型因幻覺將 Metformin 推薦給腎病患者，導致患者乳酸中毒。」

### 3.2 能源劇本：【黑點危機】 (極限流)
*   **真實資料源 (GitHub API)**：`https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.json` (Our World in Data 全球能源時序資料)
*   **核心痛點**：算力（AP / Token 預算）極度匱乏，直接搜尋數萬頁法規與電網時序數據會瞬間耗光能量 (Latency 極高)。
*   **卡牌策略**：玩家必須先打出**【Matryoshka 降維壓縮卡】**將肥大的數據卡物理壓縮 60%，再利用**【圖譜導航連鎖卡 (KG Navigation)】**打出 Combo，用最低能耗一次拉出相連的法規與數據晶片找出過熱網格。
*   **結算反思**：
    *   ✅ *成功報告*：「完美節能！您成功利用 Matryoshka 壓縮與多跳圖譜推理，以最低 Token 消耗完成了 2026 歐盟節能指令的電廠調度。」

---

## 4. 資料庫預存程序實作 (Database RPC Implementation)
在 Supabase SQL 編輯器中部署的低能耗混合檢索函數，結合全文檢索與輕量向量檢索：

```sql
create or replace function hybrid_match_chunks (
  query_text text,
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  title text,
  similarity float,
  is_noise boolean
)
language plpgsql
as $$
begin
  return query
  with keyword_matches as (
    -- 1. 第一階段：死板但免費的 SQL 全文檢索
    select t.id, t.content, t.metadata, t.title, 1.0 as similarity
    from archon_crawled_pages t
    where to_tsvector('english', t.content) @@ to_tsquery('english', query_text)
    limit 3
  ),
  vector_matches as (
    -- 2. 第二階段：具備推理能力的向量相似度檢索
    select v.id, v.content, v.metadata, v.title, 1 - (v.embedding <=> query_embedding) as similarity
    from archon_crawled_pages v
    where 1 - (v.embedding <=> query_embedding) > match_threshold
    order by v.embedding <=> query_embedding asc
    limit match_count
  )
  
  -- 3. 混合去重合併，並動態判定是否為「語意假陽性（紅幽靈卡）」
  select 
    m.id, 
    m.content,
    m.metadata,
    m.title,
    m.similarity,
    case when m.similarity < 0.82 then true else false end as is_noise
  from (
    select * from keyword_matches
    union
    select * from vector_matches
  ) m
  order by m.similarity desc;
end;
$$;
```

---

## 5. 美術設計 AI 提示詞 (SDXL / Flux Prompts)
有鑑於手刻著色器 (Shader) 可能無法達到商業級的視覺震撼，本專案的美術資產將全面採用**免費且強大的開源 AI 生成圖像模型** (如 Stable Diffusion XL 或 Flux.1，無需任何付費帳號) 處理，以高品質的 2D 貼圖取代程式碼運算。以下為給定設計師與 AI 的核心 Prompt：

### 5.1 遊戲背景：立體向量網格 (Background Image)
*   **Prompt**: `A mesmerizing, infinitely deep 3D wireframe grid, retro-futuristic synthwave style, glowing neon cyan and dark purple, representing a high-dimensional vector database space. Hacker aesthetic, floating glowing data points in the far distance, cinematic lighting, 8k resolution, Into the Grid style, clean lines, aspect ratio 16:9`
*   **實作方式**: 將生成的圖像匯入 Godot 作為 `TextureRect` 背景，可配合簡單的 Tween 進行緩慢的 Z 軸放大縮放，即可達成極強的沉浸感。

### 5.2 伺服器插槽與 UI (Server Rack UI)
*   **Prompt**: `A high-tech server rack interface, empty glowing motherboard RAM slots, cyberpunk aesthetic, dark metallic textures, neon green indicator lights, retro CRT monitor elements, UI design, flat front-facing perspective, highly detailed, transparent background layout, aspect ratio 16:9`
*   **實作方式**: 裁切圖像後，作為玩家的 Context Window（手牌區）插槽背景底圖。

### 5.3 數據晶片與行動卡牌 (Data Chips & Action Cards)
為了與第 2、3 節的核心機制完全對齊，卡牌視覺分為「檢索回來的數據晶片」與「玩家打出的行動卡」兩大類：

#### 5.3.1 檢索數據晶片 (Retrieved Data Chips)
出現在 Context Window (手牌區)，代表從資料庫撈出的 Chunk。
*   **🟢 黃金命中晶片 (Target Chunk)**
    *   **Prompt**: `A futuristic rectangular data chip, glowing neon green circuit board lines, holographic text projecting "MATCH", clean cyberpunk aesthetic, aspect ratio 2:3`
*   **🔴 紅幽靈雜訊晶片 (False Positive)**
    *   **Prompt**: `A corrupted dark rectangular data chip, rust red and crimson glowing edges, digital glitch effects, torn circuits, menacing virus aesthetic, aspect ratio 2:3`

#### 5.3.2 玩家行動卡 (Player Action Cards)
玩家用於操作檢索策略的技能卡。
*   **🔫 BM25 關鍵字實彈卡 (Keyword Search)**
    *   **Prompt**: `A tactical cyberpunk ability card, metallic grey and orange aesthetic, showing a sniper crosshair locking onto data text, mechanical and precise, retro-arcade style, aspect ratio 2:3`
*   **☄️ Dense 向量雷射卡 (Dense Search)**
    *   **Prompt**: `A dynamic sci-fi ability card, shooting a massive glowing cyan laser beam through a matrix of numbers, high energy, neon vaporwave aesthetic, aspect ratio 2:3`
*   **🛡️ Reranker 電漿護盾卡 (Rerank/Filter)**
    *   **Prompt**: `A defensive cyberpunk ability card, showing a glowing hexagonal energy shield repelling red corrupted data bugs, glowing blue forcefield, high tech, aspect ratio 2:3`
*   **🗜️ Matryoshka 降維壓縮卡 (Dimension Shrink)**
    *   **Prompt**: `A futuristic ability card, showing a glowing holographic cube folding and compressing into a smaller hypercube, neon purple and green, physics manipulation aesthetic, aspect ratio 2:3`
*   **🕸️ 知識圖譜連鎖卡 (GraphRAG Navigation)**
    *   **Prompt**: `A network-themed ability card, showing glowing nodes and laser fiber-optic connections forming a constellation, data networking, neon blue and gold, cybernetic web, aspect ratio 2:3`

---

## 6. 測試驅動開發與自動化公證 (TDD & Automation)

在完全解耦的 MVC 架構下，遊戲的邏輯層 (Model) 是一組純粹的陣列操作與狀態機轉移。這保證了在進行單元測試與整合測試時，可以在無 Godot 視覺介面的 Headless 環境中瞬間完成結算，確保「0 毫秒延遲」的物理精準度。

### 6.1 核心測試案例 (Core Test Cases)
1.  **卡牌檢索測試**：驗證 Godot 發送 Query 後，正確地從 Event Queue 接收解析 JSON，並依照 `is_noise` 等屬性實體化卡牌 Model。
2.  **狀態移轉測試**：驗證當玩家打出卡牌時，Model 層正確扣除費用，並對陣列中的目標施加效果（例如提升 Context 質量，或丟棄雜訊卡）。
3.  **零物理依賴測試**：確認所有戰鬥與卡牌結算，完全不依賴 Godot 的 `Node2D` 物理屬性或 `CharacterBody2D`。

### 6.2 LEAN 驗證與 Headless 公證踩坑紀實 (LEAN Validation History)
在先前的架構驗證中，我們經歷了多次慘痛的血淚教訓，確立了以下不可動搖的 Godot 開發鐵律：
1.  **捨棄臃腫的 GUT 框架 (Lean 原則)**：為了極致的效能與 CI/CD 整合，我們捨棄了會污染專案的第三方 GUT 測試框架，改以原生 Headless 模式自製微型測試框架 (`HeadlessRunner.gd`)，徹底實現 0 依賴公證。
2.  **存檔淨化與幽靈失敗防禦 (State Purification)**：過去曾發生測試通過但實際執行報錯的「幽靈失敗」，主因是測試環境吃到殘留的存檔。因此，所有自動化腳本在測試前**必須強制刪除** `user://savegame.save`，確保測試的絕對無狀態性 (Stateless)。
3.  **ClassDB Registry 自癒防護**：Godot 在 `--headless` 模式下，有時會發生類別快取解析錯誤 (Class Name Resolution Error)。為了徹底根除此問題，所有動態載入的類別與腳本，**強制使用 `preload` 取代直寫 `class_name`**，以確保編譯期的強型別安全與依賴載入。
---

## 7. Web 輸出與跨裝置適配 (Web Export & Cross-Device Optimization)
本遊戲維持無縫嵌入網頁版與行動裝置瀏覽器 (Mobile Safari/Chrome) 的目標。

*   **觸控手勢驅動**：手機端著重於直覺的拖曳出牌 (Drag & Drop)。
*   **響應式視角 (Responsive Camera)**：Godot 視窗設定 `stretch/mode = canvas_items`，確保在手機版直式螢幕下 UI 卡牌佈局能自動適配，不被裁切。

---

## 8. 專案檔案架構樹狀圖 (File Architecture)
為了徹底貫徹 0 元邊緣計算與 Godot MVC 解耦，專案目錄結構設計如下：

archon/
├── archon-semantic-infiltration/       # Godot 4.3 卡牌遊戲客戶端
│   ├── project.godot
│   ├── assets/                         # 16-bit Cyber-Matrix 美術與音效資源
│   ├── src/
│   │   ├── models/                     # 純數據層 (不碰 UI)
│   │   │   ├── CardModel.gd            # 繼承 Resource 的卡牌資料結構
│   │   │   └── DeckManager.gd          # 負責陣列操作與洗牌機率的狀態機
│   │   ├── views/                      # 視覺特效層
│   │   │   ├── GameBoard.tscn          # 承載 AI 背景貼圖與 UI 的主場景
│   │   │   └── CardChip.tscn           # 匯入 AI 生成貼圖的卡牌介面
│   │   └── network/                    # 網路通訊層
│   │       └── BackendClient.gd        # 專職負責打 FastAPI (archon-server) 遊戲路由
│   └── tests/                          # GUT / Headless 測試劇本
│
├── python/                             # Phase 5 後端生態系
│   ├── src/
│   │   └── server/
│   │       ├── api_routes/
│   │       │   └── rag_game_api.py     # 處理 Godot 檢索與發牌的核心 FastAPI 路由
│   │       └── services/
│   │           └── rag_game_service.py # 負責打 HF API、Supabase DB 與 GitHub CDN
│   └── start_all.sh                    # 啟動整個 Phase 5 Docker 生態系的入口
│
└── migration/                          # 全域資料庫變更紀錄
    └── 0.2.2/
        └── 26_rag_hybrid_search_rpc.sql# pgvector 與 hybrid_match_chunks 預存程序
```