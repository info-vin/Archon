# Phase 5.6.7 - 基於約束的任務動態分發 (Dynamic Dispatch based on Constraints)

## 🎯 核心目標 (Goal)
在 `UsageTrackingCompletions` 中建立路由邏輯，當 RAG 查詢被評估為簡單且允許離線時，動態將任務分發至本地 Ollama 實例 (Tier 3)，以節省雲端 Token 預算。

## 📋 建議變更與詳細實作計畫 (Proposed Changes)

### 1. 讀取基準與狀態加載 (Matrix Loading)
- 讓 `base.py` (或新的 Router 模組) 在啟動時讀取 Phase 5.6.1 產出的 `.twin/diagnostics/hardware_capability_matrix.json`。
- 如果本地 Ollama 狀態在矩陣中為 `available: true`，則允許本地路由；否則強制 fallback 至 Tier 1 Cloud。

### 2. 實作路由邏輯與複雜度評估 (Routing & Complexity Heuristics)
- **修改檔案**：
  - [修改] [hybrid_router.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/hybrid_router.py)
  - [修改] [base.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/llm/base.py)
- **詳細步驟**：
  1. 於 `hybrid_router.py` 中實作 `is_query_simple_and_offline(messages: list) -> bool`。
  2. 提取對話中最後一條用戶訊息 (User message)，評估其複雜度：
     - **簡單 (Simple)**：提示詞字數低於 50 字。
     - **允許離線 (Offline-Compatible)**：提示詞中不包含需要外部即時網頁資料或複雜任務的關鍵字（如 `search`、`crawl`、`fetch`、`live`、`latest`、`realtime`、`google`、`news`、`code`、`寫程式`）。
  3. 於 `base.py` 中的 `UsageTrackingCompletions.create()`，在進入 Cloud (Tier 1) 呼叫前插入判斷，符合條件時強制導流至本地 Ollama (Tier 3)。

---

## ✅ 驗證計畫 (Verification Plan)

### 1. 自動化測試 (Automated Tests)
- **新增測試檔案**：[test_hybrid_routing.py](file:///Users/vincenta/GoogleKwok022/Archon/python/tests/test_hybrid_routing.py)
- **驗證場景**：
  - 當 Ollama 可用時，簡單提示詞（如 "Hello"）成功分發至 Tier 3，且 `active_tier` 為 3。
  - 線上搜尋查詢或大於 50 字的複雜查詢成功分發至 Tier 1，且 `active_tier` 為 1。
  - 當 Ollama 不可用時，簡單提示詞自動降階至 Tier 1。
- **執行指令**：`make test-be ARGS="tests/test_hybrid_routing.py"`

### 2. 手動驗證 (Manual Verification)
- 運行 `python scripts/benchmark_hardware.py` 產生算力矩陣。
- 透過 Web UI 發送簡單對話，觀察後端日誌輸出 `Hybrid Router: Routing simple query to Tier 3 Ollama (Local)`。
