# Phase 5.5.0: 無網路極端環境下之系統自動擴充與離線硬化計畫

本計畫旨在針對 Archon 系統進行「離線化與自適應進化」硬化。當本系統部署於無網路（Air-gapped）的極端邊緣端環境（例如無人機、離線機器人大腦）時，使其仍能保有完整的自我診斷、代碼編寫、依賴下載、RAG 檢索與 UI 視覺公證之自動擴充能力。

---

## 建議變更

### 第一階段：離線模型適配器與 Prompt 自動降級 (Offline LLM/VLM Adapter)

目前系統的多 Agent 協作（星環架構）與規劃器高度依賴雲端大模型。在無網路狀態下，必須切換至本地推論引擎。

1. **本地推論相容層**：
   - 擴充 `python/src/server/config/config.py`，完整接入本地 Ollama/Llama.cpp 服務。
2. **Prompt 自動降級與結構化約束**：
   - 針對本地小模型（如 Llama-3-8B、Mistral-7B），設計專屬的 Prompt 降級範本（Simplification Templates），以更嚴格的 JSON Schema 與少樣本提示 (Few-shot)，引導本地模型輸出穩定、不產生幻覺的 Agent 協作決策。

### 第二階段：離線套件快照與動態依賴沙盒 (Offline Package Mirror & Sandbox)

當 DevBot 自動生成新代碼來擴充無人機控制功能時，如果引入了未安裝的套件，系統必須能在無網狀態下完成安裝。

1. **容器內離線套件庫 (Pre-cached Wheels/Modules)**：
   - 在 `Dockerfile.server` 中，預先打包常用科學計算與訊號處理庫（如 `scipy`、`sympy`、`pandas`）的 Python Wheels，並在 `enduser-ui-fe` 容器中快取常用的 Node modules。
2. **無網安裝路由配置**：
   - 設定 `uv` 與 `pnpm` 的安裝指令，當檢測到斷網時，自動導向本地快取目錄（`--find-links=/app/offline_wheels` 或 `--offline` 模式），使 DevBot 能在不中斷的情況下動態安裝並載入新模組。

### 第三階段：本地嵌入引擎與向量索引動態重建 (Local Embedding & Re-indexing)

移除對雲端 OpenAI/Gemini Embedding API 的依賴，實現完全本地化的 RAG 知識庫寫入與检索。

1. **本地 Embedding 模組**：
   - 在 `knowledge_service.py` 中，整合輕量化本地嵌入模型（如使用 `sentence-transformers` 的 `all-MiniLM-L6-v2`，維度為 384）。
2. **動態維度適配與索引重建**：
   - 當系統從「在線模式」切換為「離線模式」時，自動調整資料庫 `documents` 資料表的 `embedding` 向量維度。
   - 撰寫動態 SQL 觸發器，自動執行 `REINDEX` 並重建 Postgres 上的 `HNSW` 索引，確保離線語義檢索的精準度與效能。

### 第四階段：離線視覺評判官 (Local Visual Judge)

解決 Twin-Scout 截圖後，無法在無網環境下進行 UI 對帳與版面異常分析的問題。

1. **本地多模態裁判整合**：
   - 將 `scripts/vision_judge.py` 與 `llm_judge_content.py` 中對雲端 Gemini-Vision 的呼叫，替換為本地多模態模型（如執行於邊緣端的 `LLaVA-minicp` 或 `Qwen-VL`）。
   - 由本地視覺模型解析 Twin-Scout 產出的畫面截圖，確認排版無崩潰、按鈕物理位置正確，完成離線狀態下的 E2E 品質門禁公證。

---

## 驗證計畫

### 自動化驗證
- **拔網線測試 (Air-gapped Simulation)**：
  - 啟動 Docker 並完全阻斷容器外網連線。
  - 執行 `make audit-qa` 與 `make twin-simulator`，驗證系統是否能自動切換至本地 Ollama，且 RAG 搜尋與 Twin-Scout 的視覺對帳仍能全數通過。
  - 指派 DevBot 撰寫一個需要 `sympy` 庫的新功能，驗證系統能否在無網狀態下從本地快取成功安裝並動態載入執行。
