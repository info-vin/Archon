# Phase 5.7.4: Zero-Cost ONNX Reranker Integration (Cloud-Native Hardening)

## 核心目標 (Goal)
解決 Hugging Face 雲端部署時因模型下載造成的 0-Tools 啟動死鎖，以及原本 `sentence-transformers` 夾帶巨型 PyTorch 依賴導致的 Docker ENOSPC (空間耗盡) 危機。
本階段將實作並導入極輕量級的 **ONNX Runtime Reranker**，以 **0 API 成本**、**極低記憶體與容量佔用**、**不依賴 PyTorch** 的前提，無痛恢復 Archon RAG 系統原本強大的語意重排 (Semantic Reranking) 能力。

## 執行方案 (Implementation Plan)
1. **依賴隔離與輕量化 (Dependency Diet)**：
   - 確保 `pyproject.toml` 或 `requirements.txt` 中不包含厚重的 `sentence-transformers` 與 `torch`。
   - 引入輕量級的 `onnxruntime` (或 `onnxruntime-node/cpu`) 以及只負責斷詞的輕量 Tokenizer。
2. **ONNX 模型獲取策略**：
   - 不手動將巨大的模型推入 Git LFS (會再次觸發 HF 限制)。
   - 撰寫輕量下載器，在啟動時直接抓取官方預轉換好的 `.onnx` 權重檔 (如 `ms-marco-MiniLM-L-6-v2.onnx`，約 80MB)，並放入 `.cache` 或掛載卷中。
3. **Reranking 引擎重構**：
   - 重構 `python/src/server/services/search/reranking_strategy.py`。
   - 實作基於 `onnxruntime.InferenceSession` 的算分邏輯：將 Query 與 Chunk 打包為 Token 傳入，獲取 Logits 並轉為 0-1 相關性分數。
4. **極端環境驗證 (Edge Testing)**：
   - 確認 Docker 構建體積不會異常膨脹。
   - 確保在 CPU 環境下 (如 Docker / HF Serverless) 能在合理時間 (數十毫秒) 內完成排序。

## 品質門禁與防禦 (Quality Gates)
- **架構鐵律**：絕對禁止在生產環境 Docker Image 中安裝任何 PyTorch 相關模組。 (✅ 已移除)
- **介面相容**：維持原有的 `reranking_strategy` 介面合約，前端與 PydanticAI Agent 不需修改任何邏輯。 (✅ 已維持)
- **Fall-Fast 防禦**：若 ONNX 模型載入失敗，必須優雅降級 (Graceful Degradation) 回傳原始順序，不得讓系統崩潰。 (✅ 已實作 `try/except` 防禦)

## 執行報告 (Execution Report - 2026-06-22)
- **依賴替換**：成功將 `pyproject.toml` 中的 `sentence-transformers` 與 `torch` 替換為 `onnxruntime` (<1.20.0，以兼容 macOS x86) 與 `huggingface-hub`。
- **Docker 瘦身**：移除 `Dockerfile` 與 `Dockerfile.server` 中強制安裝 PyTorch 的步驟，解決了潛在的 ENOSPC 空間爆炸危機。
- **ONNX 引擎上線**：改寫 `reranking_strategy.py`，改為使用 `onnxruntime.InferenceSession` 即時載入 `Xenova/ms-marco-MiniLM-L-6-v2` 的 22MB 量化權重。
- **測試公證**：
  - `make lint`: 修正了 Mypy 的 `None` callable 檢查 (100% 通過)。
  - `make test-be`: 607 passed (100% 通過，確保無破壞性變更)。
  - `make phase-audit`: 物理掃描通過。
本階段目標圓滿達成，正式從 PyTorch 解放，實現了 0 Token 成本且極低記憶體的強大語意重排。
