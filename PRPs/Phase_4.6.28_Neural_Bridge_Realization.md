# Phase 4.6.28: 神經橋接實體化 (Neural Bridge Realization)

> **目標 (Goal)**: 
> 1. **解耦 ML 運算**：將 Reranking 邏輯從 `archon-server` 物理轉移至 `archon-agents`。
> 2. **實作跨容器調用**：透過 `AGENTS_SERVICE_URL` 建立兩者之間的通訊橋樑。
> 3. **為瘦身奠基**：確保 Server 不再依賴本地的 `torch` 與 `transformers`。

## 1. 物理修改清單 (Action Items)

### Task A: Agents 接收端實體化
- [x] **修改 `python/src/agents/server.py`**:
    - 已實作：新增 `/ml/rerank` 接口並掛載。
    - 已實作：導入並呼叫 `reranking_strategy.py` 執行運算。
    - 已實作：返回標準化的 JSON 結果。

### Task B: Server 請求端實體化
- [x] **修改 `python/src/server/services/search/rag_service.py`**:
    - 已實作：檢查 `AGENTS_ENABLED` 與 `AGENTS_SERVICE_URL`。
    - 已實作：使用 `httpx` 將請求發送至 Agents 容器。
    - 已實作：實作優雅降級邏輯（L122）。

### Task C: 聯動驗證 (The Integration)
- [x] **物理探針測試**:
    - 已驗證：啟動聯動並成功通過 Embedding 維度與 Reranking 測試。

## 2. 安全與風險評估
- **改 A 壞 B 風險**: 搬遷模型前，必須先確保遠端調用代碼已 100% 覆蓋所有 RAG 入口。
- **性能開銷**: 跨容器 HTTP 呼叫會增加約 10ms-50ms 的網路延遲，但能換取 5GB 的 Server 空間釋放。

## 3. 預期結果
- `archon-server` 代碼中不再出現 `from ...reranking_strategy import reranking_strategy`。
- 系統維持 2.3s 搜尋效能，但服務職責明確分離。
