# Phase 5.9.21: API Leakage Fix & Architecture Purification

## 背景與問題陳述 (Background)
在執行 600 多項後端測試 (`make test-be`) 時，系統向 Google Gemini API 發出了實體 HTTP 請求，導致瞬間突破免費額度並引發了嚴重的 `429 Too Many Requests`。
經過物理追查 (`git log -S "httpx.AsyncClient(timeout=20.0)" --oneline python/src/server/services/embeddings/batch_processor.py`)，確認問題根源來自於 commit `b71dba5b`。
當時為了解決 Group B 的技術債，`batch_processor.py` 捨棄了官方 SDK，改為直接使用 `httpx.AsyncClient` 對 `https://generativelanguage.googleapis.com` 發起 REST 呼叫。由於 `python/tests/conftest.py` 的全局 Mock 僅防護了 `google.genai.Client` 與 `openai.AsyncOpenAI`，導致 `httpx` 請求成功穿透了測試沙盒，形成了嚴重的 **API Leakage**。

## 核心原則 (Core Principles)
1. **絕不幻想**: 基於已公證的程式碼行為，針對確診的 `httpx` 穿透點進行手術。
2. **符合 SSOT**: 必須從 `rag_settings` 動態獲取 `EMBEDDING_DIMENSIONS`，並依賴 `config.get("embedding_model")` 取代任何硬編碼的模型字串。
3. **零副作用公證**: 確保修改後，本機執行 `uv run pytest python/tests/test_async_embedding_service.py` 完全不向外發送網路封包。

## 實作目標 (Implementation Goals)

### 1. 升級全域測試防禦網 (Hardening `conftest.py`)
在 `python/tests/conftest.py` 中擴充對 `google.genai` 的 Mock，將 `embed_content` 納入防護傘下：
- **動態長度配適**: `mock_genai_client_instance.aio.models.embed_content` 必須能根據傳入的 `contents` (Batch Size) 動態回傳對應數量的 `ContentEmbedding` Mock 物件，其 `values` 為 `[0.1] * 768`。

### 2. 架構淨化 (`python/src/server/services/embeddings/batch_processor.py`)
- **移除 httpx**: 徹底刪除直接以 `httpx.AsyncClient` 對 `https://generativelanguage.googleapis.com` 發起的 REST API 請求。
- **官方 SDK 對齊**: 改採官方的 `genai.Client(api_key=api_key_to_use)` 來執行 `embed_content`。
- **嚴格遵守 SSOT**: 強制從 `rag_settings` 提取 `EMBEDDING_DIMENSIONS`，消滅硬編碼並依據模型版本動態切換降維參數。
- **消除字串硬編碼**: 在判斷模型是否支援降維時，不再硬編碼 `stable_model != "models/embedding-001"`，而是採用更具彈性的 `if "embedding-001" not in stable_model.lower():` 進行比對，相容資料庫中 `gemini-embedding-001` 的 SSOT 命名規範，根除幻覺漏洞。
- **批量處理 (Batching)**: 將整理好的 `batch` (List of string) 送入 `client.aio.models.embed_content`，並將回傳的 `resp.embeddings` 安全地映射至 `result.add_success`。

## SSOT Review (Single Source of Truth)
確認所有 Embedding 設定均已從 `rag_settings` 取代 `constants.py` 的殘留硬編碼，並確保模型切換邏輯符合 `config.get("embedding_model")` 的唯一性原則。

## 驗證計畫 (Validation Plan)
1. **單元防護驗證**: 執行 `uv run pytest python/tests/test_async_embedding_service.py -v`，確保完全不發生 `httpx.ConnectError` 或 `429`。
2. **全域迴歸公證**: 執行 `make test-be`，並監控 `[Google Cloud Console -> API APIs & Services]`，確保 `generativelanguage.googleapis.com` 的流量為 **零 (0)**。

## ✅ 執行狀態 (Execution Status)
- **完成日期**：2026-07-25
- **狀態**：✅ 已完成 (Completed)
- **備註**：已完成全部實作，通過全部後端測試公證，並成功根除所有 API Leakage 漏洞。
