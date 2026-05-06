# Phase 4.6.20: MCP 減肥與架構精煉 (MCP Slimming & Refactoring)

> **文件狀態**: ✅ 已結案 (Physical Parity Achieved) - 2026-03-26
> **目標**: 減少 MCP 服務的代碼冗餘，抽離核心基礎設施，並優化依賴項，達成系統輕量化與穩定性雙重提升。

---

## ✅ 已完成任務 (Physical Progress)

### 1. 核心基礎設施抽離 (Core Extraction)
- [x] **建立 `core.py`**: 成功將 `ArchonContext`、`perform_health_checks` 與 `lifespan` 邏輯從主入口抽離。
- [x] **物理隔離**: 解決了進程初始化順序問題，確保工具註冊與請求處理在同一個物理進程環境中。

### 2. HTTP 通訊去重 (HTTP Consolidation)
- [x] **實作 `call_api()`**: 在 `utils/http_client.py` 中建立統一的 API 助手，整合超時、報錯與 JSON 解析。
- [x] **模組重構**: `rag_tools.py` 與 `task_tools.py` 已物理遷移至 `call_api` 模式，消除了 120+ 行重複代碼。

### 3. 入口檔案瘦身 (Entry-Point Slimming)
- [x] **建立 `infra_tools.py`**: 將 `health_check` 與 `session_info` 等內部工具抽離。
- [x] **行數縮減**: `mcp_server.py` 從 759 行物理縮減至 **487 行** (縮減 36%)。

### 4. 依賴與基礎設施優化
- [x] **依賴剪枝**: 從 `pyproject.toml` 移除 `openai`、`supabase` 等 MCP 冗餘包。
- [x] **Volume 固化**: 在 `docker-compose.yml` 建立 `mcp-cache` 映射至 `/tmp`，物理保證工具清單跨進程共享。

---

## 📊 物理驗收結果 (Final DoD)
1.  **品質保證**: `make lint` 物理通過 (Zero-Error)，全端型別對齊。
2.  **測試主權**: `make test-be` 物理通過 (555 Passed)，包含所有重構後的 Mock 整合測試。
3.  **神經穩定**: 物理撥測證實 26 個工具依然動態發現且通訊正常 (200 OK)。

---

## 📅 下一步計畫
啟動 **Phase 4.8 Agent 覺醒**：移除 `AgentService` 中的模擬邏輯，讓 Agent 開始真實調用 MCP 工具。
