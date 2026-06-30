# Technical Design Document (TDD): Recontextualization

```text
=============================================================================
                  Archon: Recontextualization (Godot 4.3)
                  "Hybrid RAG Deck-builder" Architecture
=============================================================================
```

## 核心理念 (Core Vision)
本作已拋棄原本的二維網格走位，全面轉向《進入矩陣（Into The Grid）》風格的**「RAG 混合檢索與卡牌構築 (Hybrid RAG Deck-builder)」**。

遊戲目標在於讓玩家深刻體會 RAG 工程師的智力博弈：如何在極度受限的記憶體與算力資源下，透過卡牌構築 (Deck-building) 與混合檢索 (Hybrid Search)，過濾假陽性雜訊並精準提取出目標資料，最終解鎖 LLM Portal。相關核心名詞定義請參閱 [附錄 A：核心名詞定義表](#附錄-a核心名詞定義表)。

---

## 1. 混合 RAG 矩陣與動態卡牌演算系統

### 1.1 系統核心架構與開發戰略：抽取 Maaack 核心 + RAG 模組化升級
經過架構評估，本專案嚴格採用 **Data-Driven MVC 架構** 進行完全解耦。為加速開發並確保底層穩定性，我們採用「抽取 Maaack 核心 (借殼上市)」戰略：

1.  **抽取 Maaack 核心 (MVC 基底)**：
    移植 [Maaack/Battle-Deck-Energy](https://github.com/Maaack/Battle-Deck-Energy) 開源專案中極度純粹的資料層模組（`DeckData.gd`, `CardData.gd` 等純陣列數學操作），以及其基礎的 `EventBus` 狀態分發機制。
2.  **RAG 模組化升級 (剔除本地耦合)**：
    *   **掛載 `BackendClient.gd`**：捨棄 Maaack 原有的 JSON 本地存檔讀取，讓遊戲在啟動與執行過程中直接向 FastAPI 與 Supabase 請求 RAG 向量檢索結果。
    *   **動態工廠模式 (`CardRegistry`)**：捨棄寫死的資源清單，自動掃描目錄註冊卡牌，實現真正的 OCP (開閉原則)。
3.  **零延遲結算與 Event Queue 視覺化**：
    `DeckData` 僅處理陣列移轉並瞬間結算 (0 毫秒延遲，完美支援無頭測試)；而 `EventQueue` 扮演動畫佇列，視覺層（`GameBoard` 與 `CardChip`）只負責消耗佇列播放動畫。

#### 【硬編碼優化方案 (Godot 4 官方規範最佳實踐)】
依據 Godot 4 官方最佳實踐，為避免路徑與設定硬編碼 (Hardcoding)，本專案實施以下優化：
*   **路徑常量化與全域設定資源**：所有的系統靜態路徑（如 `res://src/models/cards/resources/`）與網路 API 地址，強制封裝於 `GameState` 或專屬的 `.tres` 配置檔中。
*   **導航與資源動態載入**：放棄直寫字串路徑，利用 Godot 的 `preload` 機制或導出變數（`@export_file`）實現編輯器靜態安全校驗，防止執行期解析 404。

---

### 1.2 系統架構序列圖 (Sequence Diagram)
以下為客戶端與後端異步 RAG 資料檢索與發牌之 9 個步驟：

```mermaid
sequenceDiagram
    participant Godot as Godot 4.3 (Game Client)
    participant FastAPI as Python Backend (archon-server)
    participant HF as Hugging Face Inference API
    participant DB as Supabase PostgreSQL
    participant CDN as GitHub Raw CDN
 
    Godot->>FastAPI: 1. 發送 Query 請求與卡牌技能 (HTTP POST)
    FastAPI->>HF: 2. 呼叫 API 請求向量化 (all-mpnet-base-v2 等)
    Note over HF: 依賴伺服器設定的 HF_TOKEN 額度
    HF-->>FastAPI: 3. 回傳 768 維度向量
    FastAPI->>DB: 4. 呼叫 hybrid_match_chunks 預存程序
    Note over DB: SQL fts (關鍵字匹配)<br/>pgvector 相似度檢索 (向量匹配)
    DB-->>FastAPI: 5. 回傳 chunk_id, metadata, similarity 與 match_type
    FastAPI->>CDN: 6. 根據 metadata 請求完整實體 JSON
    CDN-->>FastAPI: 7. 回傳真實文本實體資料 (醫療/法規)
    FastAPI-->>Godot: 8. 異步回傳組合後的純 JSON 數據
    Godot->>Godot: 9. 將 JSON 解析並推入 EventQueue 驅動 UI
```

#### 【連線異常與效能優化說明】
*   **異常處理 (Error Handling)**：
    *   **超時限制 (SLA Timeout)**：網路請求設定為 5 秒超時。
    *   **指數型退避重試 (Exponential Backoff)**：客戶端 `BackendClient.gd` 內建 3 次重試機制，每次失敗間隔時間按數倍遞增。
    *   **無網 Fallback 自癒**：當檢索連線中斷或後端不可用時，遊戲將自動啟動本地隨機資料生成機制（Fallback Generator），確保遊戲仍 100% 可玩。
*   **快取優化 (Latency Reduction)**：後端對熱門 Query 與 GitHub CDN 回傳內容實施本地記憶體快取 (LRU Cache)，大幅減少 RAG 響應時間。

---

### 1.3 0元低耗能分離式 RAG 資料管線 (0-Cost Decoupled RAG Pipeline)
本系統實施「向量索引與文本存儲的物理分離」，並透過 FastAPI 後端達成高效能代理，避免載入龐大資料集拖垮遊戲客戶端：

| 步驟 | 項目 | 傳統結合式 RAG (Coupled) | 本專案分離式 RAG (Decoupled) | 優勢與重點 |
|---|---|---|---|---|
| 1 | 向量化 | 本地端運行 PyTorch / Transformers 巨型模型 | 呼叫 Hugging Face Serverless Inference API | **0 本地算力**，免去客戶端下載數 GB 模型空間 |
| 2 | 檢索 | Postgres 直接儲存與檢索龐大原文區塊 | Supabase `hybrid_match_chunks` 僅檢索 ID、相似度與 CDN URL | **極低記憶體占用**，資料庫讀寫效能提升 10 倍以上 |
| 3 | 文本讀取 | 從資料庫實體 Table 讀取大量 JSON | 依據 metadata 中的 URL 異步抓取 GitHub Raw CDN | **0 頻寬開銷**，利用 CDN 全球快取節省伺服器成本 |
| 4 | 遊戲解析 | 客戶端阻塞等待全文解析完畢 | 透過異步 `EventQueue` 進行晶片卡牌動態渲染 | 介面流暢無卡頓，實現 60 FPS 順暢體驗 |

---

## 2. 核心遊戲機制與模型層 (Core Mechanics & Model Layer)

### 2.1 牌組邏輯與狀態機
資料在庫中以 Chunk 形式存在，進入遊戲後完全轉化為「卡牌（Cards）」與「陣列移轉」。
*   **知識庫 (Knowledge Base)** = 主牌組陣列。
*   **上下文視窗 (Context Window / 手牌區)** = 核心手牌區陣列（上限 5 張，防溢出限制）。
*   **算力預算 (AP)** = 玩家每回合出牌的 Token 費用限制（預設最大值為 10 AP，每回合回復）。
*   **系統危機 (Crisis HP)** = 關卡的 Severity 分數。
*   **玩家生命 (Player HP)** = 預算與工程師精神力（上限 100.0）。

### 2.2 核心對決邏輯 (Signal vs Noise 訊噪比博弈)
*   **【BM25 關鍵字實彈卡 (Keyword Search)】**：消耗 1 AP。字面匹配，精準抓取對應字眼資料。若沒有配上高相似度，極易轉化為紅幽靈雜訊晶片。
*   **【Dense Laser 向量雷射卡 (Dense Search)】**：消耗 2 AP。召回率極高，解鎖跨領域語意推理，但易因語意模糊引入低相似度之紅幽靈雜訊晶片。
*   **【Reranker 電漿護盾卡 (Rerank/Filter)】**：消耗 3 AP。發動時，強制對手牌進行 Cross-Encoder 權重重排與硬性截斷，**物理抹除手牌區中 `similarity < 0.5` 的所有雜訊卡**。

---

### 2.3 核心戰鬥數學驗證公式 (Combat Math Validation Formulas)

1.  **上下文純淨度 (Context Purity, $P$)**:
    $$P = \frac{\text{有效訊號晶片 (similarity } \ge 0.5 \text{ 且為 DATA\_CHIP)}}{\text{手牌區 (Context Window) 總晶片數}}$$
2.  **LLM 交付傷害 (Delivery Damage, $D$)**:
    $$D = (\text{基礎火力 } 1000) \times P \times \text{連鎖乘數}$$
    *(註：若觸發 GraphRAG 連鎖卡，連鎖乘數為 $1.5$，否則為 $1.0$)*
3.  **幻覺反噬懲罰 (Hallucination Penalty)**:
    若交付時 $P < 1.0$ (手牌包含紅幽靈雜訊晶片)，該次交付傷害 $D$ 強制歸零，且玩家受到直接反噬傷害：
    $$\text{玩家受傷} = (\text{手牌中紅幽靈晶片數量}) \times 20.0 \text{ HP}$$

#### 【連貫性遊戲回合實例說明】
```
【初始狀態】玩家 10 AP，Player HP 100.0，Crisis HP 10000.0，手牌為空。
  ↓
【第一步】玩家輸入 Query "Antibiotics for kidney disease" 並檢索。
  ↓ (發牌) 抽出 3 張晶片：
    - Card A (similarity = 0.9, type = DATA_CHIP)
    - Card B (similarity = 0.4, type = NOISE_CHIP / [CORRUPTED])
    - Card C (similarity = 0.95, type = DATA_CHIP)
  ↓
【第二步】玩家花費 3 AP 打出行動卡【Reranker 電漿護盾卡】。
  ↓ (過濾) Reranker 發動，檢測到 Card B 相似度 0.4 < 0.5，物理抹除 Card B。手牌區僅剩 A 與 C (Purity 變為 100%)。
  ↓
【第三步】玩家花費 1 AP 打出【BM25 關鍵字實彈卡】交付。
  ↓ (計算) Purity = 2/2 = 1.0。傷害 D = 1000 * 1.0 * 1.0 = 1000.0。
  ↓
【結算】Crisis HP 降至 9000.0。Player HP 維持 100.0。回合結束，安全過關。
```

---

## 3. RPG Meta-Architecture & 產業主題劇本 (Campaigns)

### 3.1 過關條件與失敗懲罰 (Win/Loss Conditions)
*   **過關條件**：交付純淨卡牌使「系統危機 (Crisis HP)」降至 0。
*   **失敗條件**：玩家生命 (Player HP) 歸零，或運算超時 (SLA Timeout / `sla_timer` 歸零)。

### 3.2 玩家職涯與非線性複合危機 (Progression & Composite Threats)
*   **職等晉升 (Progression & Domain Specialization)**：
    *   **L3 助理工程師**：解鎖「BM25 關鍵字實彈卡」。雜訊晶片為「明牌顯示」（紅色警告外框）。
    *   **L4 中階工程師**：解鎖「Dense Laser 向量雷射卡」。解鎖**【關鍵字專長 (Keyword Purist)】**領域，雜訊卡轉為「暗牌隱藏」（需玩家自行 hover 閱讀 similarity）。
    *   **L5 資深工程師**：解鎖「Reranker 電漿護盾卡」。解鎖**【向量專家 (Vector Specialist)】**與**【圖譜架構師 (GraphRAG Architect)】**領域，解鎖對應專屬卡牌（技能樹解鎖機制）。

#### 【非線性關卡危機起源 (Scenario Crises Origin)】
遊戲中的「系統危機 (Crisis HP)」並非憑空產生，而是模擬真實 RAG 發生的工程故障：
*   **資料庫污染 (Data Poisoning)**：檢索池遭惡意注入大量雜訊，導致抽卡時 Data 轉換為 Noise 的機率隨時間攀升。
*   **高併發限流 (Rate Limit Attack)**：高併發存取導致 API 擁堵，浮動壓縮玩家的 AP 上限。

---

### 3.3 局外系統擴充性 (Meta-Game Scalability)
為實現「免改代碼即能擴充 (Modularity & Expansion Pack)」之概念，本專案將卡牌與關卡設定完全外部資料化：
*   **JSON 擴充包規格**：新增卡牌不需要修改 `CardData.gd`，只需在 `res://src/models/cards/resources/` 放入新的 `.tres` 檔案或載入外部 JSON 描述檔。
*   **關卡資源化 (CampaignResource)**：關卡的目標、真實資料集網址、SLA 時間、初始危機血量等皆寫在資源檔中，關卡管理器可動態解析並載入，代碼完全零耦合。

---

### 3.4 實作案例：產業主題劇本與現實反思機制

| 劇本名稱 | 真實資料源 (GitHub API) | 核心痛點 | 關卡危機成因 | 結算反思報告 |
|---|---|---|---|---|
| **醫療劇本：抗生素的致命防線** | `pubmedqa/master/data/ori_pqal.json` | 容錯率為 0，假陽性雜訊會導致醫療事故 | 檢索污染度極高，高相似度中混雜了語意相左的雜訊 | ❌ 失敗：「嚴重醫療事故發生！模型幻覺將 Metformin 推薦給腎病患者，導致患者乳酸中毒。」 |
| **能源劇本：黑點危機** | `owid/energy-data/master/owid-energy-data.json` | 算力與 AP 極度匱乏，海量法規檢索超時 | 連續發送大 query 導致高併發 API 限流 (AP 上限壓縮) | ✅ 成功：「成功利用 Matryoshka 壓縮與多跳圖譜推理，以最低 Token 完成調度。」 |
| **遊戲產業劇本：失控的熱修復與架構腐敗** | `local_repo/Archon/commits` | 開發者頭痛醫頭，導致架構物理限制被繞過 (例如：無上限的 Context Window 與消失的行動卡) | 為了快速解決 UI 阻斷問題，強行寫死 Enter 鍵熱修復，導致 TDD 核心卡牌構築體驗徹底崩壞 | ❌ 失敗：「嚴重技術債爆發！由於 PlayArea 未限制容量，玩家塞入無限資料導致 LLM Token 溢出，系統當機；且因 Action Cards 工廠缺失，遊戲降級為無聊的文字輸入框。」 |

---

## 4. 資料庫預存程序實作 (Database RPC Implementation)
本遊戲的資料庫端混合檢索完全基於已部署的 RPC 預存程序實作：

*   **實體部署路徑**：詳見 SQL 遷移檔 [26_rag_hybrid_match_chunks.sql](file:///Users/vincenta/GoogleKwok022/Archon/migration/0.2.2/26_rag_hybrid_match_chunks.sql)。
*   **核心功能摘要**：該預存程序實作了全文檢索 (Keyword) 與向量相似度 (Vector) 的外連接合併 (Full Outer Join)，並依照相似度分數進行降序排列與動態閥值過濾，對回傳的 Chunk 標記 `match_type` 傳回給遊戲客戶端。

---

## 5. 美術設計 AI 提示詞 (SDXL / Flux Prompts Database)
為方便快速複製與動態解析，本專案將所有美術資產提示詞整合為標準的 JSON 格式：

```json
{
  "backgrounds": {
    "vector_grid": {
      "purpose": "遊戲主畫面背景底圖，用以模擬 RAG 高維度向量資料庫的立體網絡空間並建立沉浸感",
      "prompt": "A mesmerizing, infinitely deep 3D wireframe grid, retro-futuristic synthwave style, glowing neon cyan and dark purple, representing a high-dimensional vector database space. Hacker aesthetic, floating glowing data points in the far distance, cinematic lighting, 8k resolution, Into the Grid style, clean lines, aspect ratio 16:9"
    }
  },
  "ui_elements": {
    "server_rack": {
      "purpose": "手牌區 (Context Window) 的伺服器插槽背景圖，物理上承載各個裝載的資料與行動晶片",
      "prompt": "A high-tech server rack interface, empty glowing motherboard RAM slots, cyberpunk aesthetic, dark metallic textures, neon green indicator lights, retro CRT monitor elements, UI design, flat front-facing perspective, highly detailed, transparent background layout, aspect ratio 16:9"
    }
  },
  "cards": {
    "data_chips": {
      "target_chunk": {
        "purpose": "出現在 Context Window (手牌區)，代表相似度高於安全閥值且能解鎖 Combo 的綠色黃金數據晶片",
        "prompt": "A futuristic rectangular data chip, glowing neon green circuit board lines, holographic text projecting 'MATCH', clean cyberpunk aesthetic, aspect ratio 2:3"
      },
      "noise_chip": {
        "purpose": "出現在 Context Window (手牌區)，代表已被投毒或相似度過低、會觸發幻覺懲罰的紅色雜訊晶片 ([CORRUPTED])",
        "prompt": "A corrupted dark rectangular data chip, rust red and crimson glowing edges, digital glitch effects, torn circuits, menacing virus aesthetic, aspect ratio 2:3"
      }
    },
    "action_cards": {
      "keyword_search": {
        "purpose": "BM25 關鍵字實彈卡 (Keyword Search) 技能圖標，用於展示精準字面匹配",
        "prompt": "A tactical cyberpunk ability card, metallic grey and orange aesthetic, showing a sniper crosshair locking onto data text, mechanical and precise, retro-arcade style, aspect ratio 2:3"
      },
      "dense_search": {
        "purpose": "Dense 向量雷射卡 (Dense Search) 技能圖標，用於展示高召回率語意穿透效果",
        "prompt": "A dynamic sci-fi ability card, shooting a massive glowing cyan laser beam through a matrix of numbers, high energy, neon vaporwave aesthetic, aspect ratio 2:3"
      },
      "reranker": {
        "purpose": "Reranker 電漿護盾卡 (Rerank/Filter) 技能圖標，展示抹除假陽性雜訊的物理屏障效果",
        "prompt": "A defensive cyberpunk ability card, showing a glowing hexagonal energy shield repelling red corrupted data bugs, glowing blue forcefield, high tech, aspect ratio 2:3"
      },
      "matryoshka": {
        "purpose": "Matryoshka 降維壓縮卡 (Dimension Shrink) 技能圖標，展示將肥大維度高能物理壓縮的折疊效果",
        "prompt": "A futuristic ability card, showing a glowing holographic cube folding and compressing into a smaller hypercube, neon purple and green, physics manipulation aesthetic, aspect ratio 2:3"
      },
      "graph_rag": {
        "purpose": "知識圖譜連鎖卡 (GraphRAG Navigation) 技能圖標，展示數據節點多跳關聯的纖維星座結構",
        "prompt": "A network-themed ability card, showing glowing nodes and laser fiber-optic connections forming a constellation, data networking, neon blue and gold, cybernetic web, aspect ratio 2:3"
      }
    }
  }
}
```

---

## 6. 測試驅動開發與自動化公證 (TDD & Automation)
*   **原生無頭測試框架**：為了極致的效能與 CI/CD 整合，捨棄了 Gut 框架，改以原生無頭模式自製微型測試框架 [HeadlessRunner.gd](file:///Users/vincenta/GoogleKwok022/Archon/recontextualization/tests/HeadlessRunner.gd)，徹底實現 0 依賴公證。
*   **存檔淨化與自癒**：所有自動化腳本在測試前必須強制刪除 `user://savegame.save`，確保測試的絕對無狀態性 (Stateless)。
*   **ClassDB 預載解析**：為了在 `--headless` 下防範型別快取解析錯誤，所有動態加載腳本**強制使用 `preload` 取代直寫 `class_name`**。

---

## 7. Web 輸出與跨裝置適配 (Web Export & Cross-Device Optimization)
*   **iPad 與行動裝置拖曳優化**：本專案直接使用 Godot 的原生 `Control` 節點拖曳系統 (`_get_drag_data`, `_can_drop_data`, `_drop_data`)。該系統在 Godot 4.3 內部會**自動將觸控手勢 (Touch Gestures) 映射為滑鼠事件**。因此，iPad 的拖控與滑鼠操作在底層由同一套 Control API 處理，無需額外編寫平台判斷程式碼，極致簡化架構。
*   **響應式視角 (Responsive Camera)**：Window 設定 `stretch/mode = canvas_items` 且 `aspect = expand`，確保在各種螢幕解析度下 UI 卡牌自動適配。

---

## 8. 專案檔案架構樹狀圖 (File Architecture)
專案目錄結構擴展至第三階，以便快速進行目錄比對：

```text
archon/
├── recontextualization/                # Godot 4.3 卡牌遊戲客戶端
│   ├── project.godot
│   ├── assets/                         # 視覺與音效資源目錄
│   │   └── maaack/                     # 移植之開源 UI/音效資源
│   ├── src/
│   │   ├── autoloads/                  # 全域單例
│   │   │   ├── EventBus.gd             # 事件分發總線
│   │   │   └── GameState.gd            # 核心遊戲狀態機與危機結算
│   │   ├── managers/                   # 管理工廠
│   │   │   └── CardRegistry.gd         # 動態卡牌資源掃描器
│   │   ├── models/                     # 純數據層
│   │   │   ├── cards/
│   │   │   │   ├── CardData.gd         # 卡牌 Resource 定義
│   │   │   │   └── resources/          # 實體行動卡資源 (.tres)
│   │   │   └── DeckData.gd             # 手牌 context 陣列與 RAG 數學公式
│   │   ├── views/                      # 視覺 UI 特效層
│   │   │   ├── GameBoard.tscn          # 主遊戲場景 UI
│   │   │   ├── GameBoard.gd            # 綁定狀態機信號與播放視覺動畫
│   │   │   ├── CardChip.tscn           # 卡牌 UI 實體
│   │   │   └── PlayArea.gd             # 拖曳投放判定區
│   │   └── network/                    # 網路通訊層
│   │       └── BackendClient.gd        # FastAPI 異步 RAG 請求
│   └── tests/                          # 自動化無頭測試
│       ├── HeadlessRunner.gd           # 測試執行入口
│       ├── test_deck_math.gd           # 測試 RAG 數學公式
│       ├── test_state_machine.gd       # 測試出牌狀態扣除與傷害
│       └── test_composite_threats.gd   # 測試高壓複合危機機制
```

---

## 附錄 A：核心名詞定義表

| 核心名詞 | 遊戲內術語 | 對應真實 RAG 概念 | 遊戲內行為與懲罰 |
|---|---|---|---|
| **SLA Timer** | 運算倒數 / SLA 條 | RAG 系統的服務等級協議 (SLA) 響應時間 | 每秒自動遞減。若打出高耗能行動卡會追加「運算僵直」時間懲罰，歸零時直接遊戲失敗。 |
| **Crisis HP** | 危機血量 | 待解決之系統故障嚴重程度 | 透過交付純淨手牌來削減 Crisis HP，歸零時獲得勝利。 |
| **Context Window** | 手牌區 (最多 5 張) | 語言模型輸入的脈絡長度限制 | 存放玩家從資料庫撈出的 Chunk。上限為 5 張，多出的晶片無法進入手牌。 |
| **Data Chip** | 資料晶片 (綠色) | 相似度高於 0.5 的有效資料區塊 | 提升 Context Window 的純淨度，保證輸出傷害。 |
| **Noise Chip / [CORRUPTED]** | 雜訊晶片 (紅色) | 相似度低於 0.5 的假陽性/髒資料 | 會污染 Context Window。一旦交付含有雜訊的 Prompt，傷害強制歸零且引發幻覺反噬。 |
| **Hallucination** | 模型幻覺 | LLM 產生自信但錯誤的回答 | 當 Context Window 含有雜訊時交付會觸發，對玩家造成直接扣血傷害。 |
| **Rate Limit** | 限流警告 / AP 壓縮 | API 因請求頻繁被服務商強制節流 | 交付次數越多，攻擊限流度越高。會自動壓縮玩家在當次交付造成的最終傷害輸出。 |
| **Data Poisoning** | 資料庫投毒 | 惡意攻擊者向檢索池中寫入大量垃圾數據 | 隨著 SLA 條降低，抽牌時原本合法的 Data Chip 機率轉變為 Noise Chip 的污染機率攀セン。 |