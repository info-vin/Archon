# Phase 5.5.3: 核心代碼審查與系統硬化範疇 (Code Review & Hardening Scopes)

## 目標 (Objective)
針對 2026-04-29 至 2026-05-31 期間完成的 Phase 4.6.47 到 Phase 5.5.1 開發成果進行深度代碼審查 (Code Review) 與系統硬化，確保系統架構在動態演進、離線運行與多 Agent 異步協同下的穩定性、效能與安全性。

---

## 審查範疇 (Review Scopes)

### 1. 離線雙軌架構與向量維度動態適應 (Offline Mode & Dynamic Vector Adaptation)
* **背景與修改內容**：
  * 當系統切換至 `OFFLINE_MODE=true` 時，向量資料庫維度會動態適應（如將維度自雲端的高維度降階至本地的 384 維），並且在降階前清空原有 embeddings，改由本地 `all-MiniLM-L6-v2` 嵌入模型（384維）與本地 Ollama 運行的 `gemma4:e4b` 驅動推理。
* **審查重點 (Review Focus)**：
  * **維度一致性**：確保向量查詢（如 Cosine Similarity 函數或 pgvector 索引）在維度動態調整時不會發生維度不匹配 (Dimension Mismatch) 的 SQL 錯誤。
  * **降階清空安全性**：確認執行清空與重新向量化時的 SQL 事務 (Transaction) 控制，防範資料寫入中斷。
* **涉及檔案**：
  * [migration_service.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/migration_service.py) -> `adapt_vector_dimensions_for_offline_mode`
  * [batch_processor.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/embeddings/batch_processor.py)
  * [lifespan.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/core/lifespan.py)

---

### 2. Pydantic Graph 異步工作流與 Fan-out Map-Reduce 引擎 (Async Graph & Fan-out Engine)
* **背景與修改內容**：
  * 系統引進了 `pydantic_graph.beta` 實現多 Agent（Alice、Bob、System 等）的並行 Fan-out 運算與 Map-Reduce 彙總。
  * 引入了 `asyncio.Semaphore(2)` 控制最大併發限制，並配合 `_run_agent_with_retry` 進行 429 限流退避保護。
* **審查重點 (Review Focus)**：
  * **併發控制與資源洩漏**：驗證 Semaphore 控制是否徹底防止了 Supabase 的連線耗盡。
  * **錯誤傳播 (Error Propagation)**：確保在 Fan-out 分支執行失敗時，Map-Reduce 節點能優雅捕獲異常並進行 Fallback，而不是卡死主執行緒或陷入死鎖。
  * **異步 Telemetry**：審查 Token telemetry 異步背景執行 (Fire-and-forget) 對資料庫寫入的壓力。
* **涉及檔案**：
  * [engine.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/engine.py)
  * [nodes.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/nodes.py)
  * [engine_beta_graph.py](file:///Users/vincenta/GoogleKwok022/Archon/python/src/agents/workflow/engine_beta_graph.py)

---

### 3. 資料庫 Schema 整合與 UUID 重組 (DB Schema Consolidation)
* **背景與修改內容**：
  * 進行了資料庫架構大收網，刪除 `customers`、`subscriptions`、`market_insights` 等冗餘表，並將所有 SQL 整合至 `migration/0.2.2/`。
  * 對齊 AI 代理人 UUID (AI_AGENT_ROLES)，並在前端與後端 Auth Sync 同步流程中手動排除此類系統級特殊帳號。
* **審查重點 (Review Focus)**：
  * **孤立參考與外鍵關聯**：審查移除冗餘表後是否仍有任何 API、背景任務或測試代碼存在未清理的 CRUD 參照。
  * **UUID 型別安全性**：檢查資料庫 UUID 轉換邏輯，特別是 `sync_persona_parity` 遷移指令。
* **涉及檔案**：
  * [0.2.2 遷移目錄](file:///Users/vincenta/GoogleKwok022/Archon/migration/0.2.2/)
  * [03_tables_business.sql](file:///Users/vincenta/GoogleKwok022/Archon/migration/0.2.2/03_tables_business.sql)
  * [RESET_DB.sql](file:///Users/vincenta/GoogleKwok022/Archon/migration/0.2.2/RESET_DB.sql)

---

### 4. 核心 God Objects 模組化拆分 (God Object Refactoring)
* **背景與修改內容**：
  * 依照單一職責原則 (SRP)，將多個超過 400 行的巨型類別進行 L2 模組化拆分，例如 `LibrarianService`、`TaskService`、`MarketingService` 與 `CredentialsManager`。
* **審查重點 (Review Focus)**：
  * **導入循環 (Circular Import)**：審查拆分後的模組引用鏈，確保無循環調用。
  * **Facade 相容性**：確認分拆出來的子領域模組（例如 `sales_pitch`、`blog_generator` 等）對外的 Facade 接口與原模組 100% 相容。
* **涉及檔案**：
  * [LibrarianService 相關](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/knowledge/)
  * [MarketingService 相關](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/marketing/)
  * [CredentialsManager 相關](file:///Users/vincenta/GoogleKwok022/Archon/python/src/server/services/credentials/)

---

## 5.5.3 已實現之硬化優化 (Implemented Hardening Optimizations)
* **優化 1：生產環境雲端資料庫防誤刪保護**
  * **修改內容**：在 `MigrationService.adapt_vector_dimensions_for_offline_mode` 中加入 URL 特徵校驗。若 `SUPABASE_DB_URL` 包含 `supabase.co` 且目標維度為 `384`（離線低維度），系統會自動攔截 DDL 清空與 Alter Table 指令，防止線上正式資料損毀。
  * **涉及代碼**：`migration_service.py` -> `adapt_vector_dimensions_for_offline_mode` 的首段保護邏輯。
* **優化 2：CLI 終端模式下 Token 遙測完整性保障**
  * **修改內容**：將原先 `WorkflowEngine` 中 Fire-and-forget 的 `asyncio.create_task` 改為使用 `asyncio.wait_for(..., timeout=2.0)` 進行同步等待防護。確保在 CLI 短期任務執行完畢時，Token 遙測能有足夠的時間完成網絡傳輸，而不被主程序退出打斷。
  * **涉及代碼**：`engine.py` -> `run_workflow` 中對 `log_telemetry` 的調用邏輯。

---

## 驗證與硬化指令 (Verification Commands)

在進行 Code Review 的同時，建議執行以下指令以確保代碼的靜態品質與測試健康度：

```bash
# 1. 執行後端全體靜態類型檢查
make lint-be

# 2. 執行後端單元測試與集成測試，確認無迴歸錯誤
make test-be

# 3. 執行全系統品質網關審計
make audit-qa
```
