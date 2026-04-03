# Phase 4.6.28: 神經橋接實體化 (Neural Bridge Realization)

> **目標 (Goal)**: 
> 1. **解耦 ML 運算**：將 Reranking 邏輯從 `archon-server` 物理轉移至 `archon-agents`。
> 2. **實作跨容器調用**：透過 `AGENTS_SERVICE_URL` 建立兩者之間的通訊橋樑。
> 3. **為瘦身奠基**：確保 Server 不再依賴本地的 `torch` 與 `transformers`。

## 1. 物理修改清單 (Action Items)

### Task A: Agents 接收端實體化
- [ ] **修改 `python/src/agents/server.py`**:
    - 新增 `POST /rerank` 接口。
    - 導入並呼叫 `reranking_strategy.py` 執行運算。
    - 返回標準化的 JSON 結果。

### Task B: Server 請求端實體化
- [ ] **修改 `python/src/server/services/search/rag_service.py`**:
    - 檢查 `AGENTS_ENABLED` 與 `AGENTS_SERVICE_URL`。
    - 若啟用，則使用 `httpx` 將請求發送至 Agents 容器。
    - 實作優雅降級：若遠端調用失敗，且本地模型不存在，則返回原始搜尋結果（不崩潰）。

### Task C: 聯動驗證 (The Integration)
- [ ] **物理探針測試**:
    - 啟動 `archon-agents` 與 `archon-server`。
    - 物理刪除 Server 容器內的模型檔案，驗證搜尋是否仍能透過 Agents 容器成功返回。

## 2. 安全與風險評估
- **改 A 壞 B 風險**: 搬遷模型前，必須先確保遠端調用代碼已 100% 覆蓋所有 RAG 入口。
- **性能開銷**: 跨容器 HTTP 呼叫會增加約 10ms-50ms 的網路延遲，但能換取 5GB 的 Server 空間釋放。

## 3. 預期結果
- `archon-server` 代碼中不再出現 `from ...reranking_strategy import reranking_strategy`。
- 系統維持 2.3s 搜尋效能，但服務職責明確分離。
