# Phase 5.5.0: 無網路極端環境下之系統自動擴充與離線硬化計畫

本計畫旨在針對 Archon 系統進行「離線化與自適應進化」硬化。當本系統部署於無網路（Air-gapped）的極端邊緣端環境（例如無人機、離線機器人大腦）時，使其仍能保有完整的自我診斷、代碼編寫、依賴下載、RAG 檢索與 UI 視覺公證之自動擴充能力。

---

## 研發分析與容量評估

### 1. macOS Host 實體磁碟容量限制
- **現狀掃描**：目前 macOS 主機剩餘空間僅 **`29 GB`**，是系統硬碟的物理瓶頸（Docker 雖然顯示有 83.4 GB，但底層映像檔大小仍受 Host 物理限制）。
- **策略**：系統大模型必須極致精簡，所有下載的模型、依賴與快取加總不能超過 15 GB。

### 2. 核心本地模型選擇 (100% Google Gemma 家族)
- **LLM/VLM (Agent 協作、代碼自癒與視覺評判官)**: **`gemma4:e4b`** (~4.7 GB)
  - Gemma 4 E4B 為原生多模態（text/image）模型。我們將其作為**一體化模型**，同時負責 Agent 的推理代碼編寫，以及 Twin-Scout 截圖的視覺版面 mismatch 評判，無須分開下載 `qwen` 與 `llava`，省下 5 GB 以上空間。
- **Embedding (本地 RAG)**: **`embeddinggemma`** (~540 MB)
  - Google 官方專為本地 RAG 與語義檢索設計的 300M 輕量嵌入模型，預設輸出 **`768` 維**，支持 Matryoshka 表示學習。
- **總計磁碟佔用**：約 **`5.2 GB`**，完美容納於 29 GB 內。

### 3. 「非強制性下載」拉取策略
- 為了避免自動化測試或開發時自動拉取數 GB 模型導致超時或頻寬浪費，系統**不實施強制下載**。
- 代碼會實現模型可用性檢查，如果本地 Ollama 未拉取模型，將優先使用 Mock 或提示下載，實際模型拉取（`ollama pull gemma4:e4b`）由部署人員在有網環境下一鍵手動完成。

---

## 建議變更

### 第一階段：離線模型適配器與 Prompt 自動降級 (Offline LLM/VLM Adapter)
1. **本地推論相容層**：
   - 整合本地 Ollama 服務，透過 `OLLAMA_HOST` 環境變數（本機部署設為 `http://host.docker.internal:11434`，Docker 部署設為 `http://ollama:11434`）對接。
2. **Prompt 自動降級與結構化約束**：
   - 針對 Gemma 4 (4B effective) 設計專屬簡化 Prompt，提供嚴格的 JSON Schema 約束防範幻覺，並使用 few-shot 約束本地模型決策。

### 第二階段：離線套件快照與動態依賴沙盒 (Offline Package Mirror & Sandbox)
1. **容器內離線套件庫 (Pre-cached Wheels)**：
   - 在 `Dockerfile.server` 中預編譯並快取常用科學計算與訊號處理庫（如 `scipy`、`sympy`、`pandas`）的 Python Wheels 至 `/app/offline_wheels`。
2. **無網安裝路由配置**：
   - 設定 `uv` 與 `pnpm` 的安裝指令。當檢測到斷網時，自動導向本地快取目錄（`--find-links=/app/offline_wheels` 或 `--offline` 模式），使 DevBot 能在無網環境下動態安裝並載入新模組。

### 第三階段：本地嵌入引擎與資料庫離線方案 (Local Embedding & Offline DB)
因 Supabase 是雲端服務，在無網環境下，我們設計**雙軌資料庫離線機制**：
1. **雙軌資料庫模式**：
   - **混合模式（本地 GPU + 雲端資料庫）**：保留極小外網流量存取 Supabase DB，本地執行 Gemma 4 AI 推理（成本低、對頻寬要求極低）。
   - **完全離線模式（本地 PostgreSQL）**：在 `docker-compose.yml` 中新增一個輕量化本地 PostgreSQL 容器服務，並在 `OFFLINE_MODE=true` 時，後端主動切換至直接 SQL Client 連線（如 SQLAlchemy），繞過繁重且無法連線的雲端 Supabase HTTP API。
2. **本地 Embedding 與 re-index**：
   - 在 `knowledge_service.py` 整合 `embeddinggemma` 本地模型。當切換為離線時，自動調整 `embedding` 欄位維度為 **`768`**，並執行 SQL `REINDEX` 重建 `HNSW` 向量索引。

### 第四階段：離線視覺評判官 (Local Visual Judge)
1. **多模態視覺對帳**：
   - 將 `scripts/vision_judge.py` 與 `llm_judge_content.py` 中對雲端 Gemini-Vision 的呼叫，替換為本地多模態大模型 **`gemma4:e4b`**。
   - 由 `gemma4:e4b` 解析 Twin-Scout 產出的畫面截圖，確認排版無崩潰、按鈕物理位置正確，完成離線狀態下的 E2E 品質門禁公證。

---

## 驗證計畫

### 自動化驗證
- **拔網線測試 (Air-gapped Simulation)**：
  - 啟動 Docker 並完全阻斷容器外網連線。
  - 執行 `make twin-simulator --limit 3`，驗證系統是否能自動調用本地 `embeddinggemma` 與 `gemma4:e4b`，且 RAG 搜尋與 Twin-Scout 的視覺對帳仍能全數通過。
  - 指派 DevBot 撰寫一個需要 `sympy` 庫的新功能，驗證系統能否在無網狀態下從本地快取成功安裝並動態載入執行。
