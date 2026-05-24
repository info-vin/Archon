# Phase 5.1.12: Async I/O Refactoring & Bulk Insert Optimization

## 目標 (Objective)
1. 清除系統中潛藏的 I/O 阻塞技術債。將散落於各 `async def` 函式內的同步 `open()` 替換為 `aiofiles.open()`，以避免在高併發場景下阻塞 asyncio 事件迴圈。
2. 清除隱藏在排程器與服務層中的「迴圈內單筆 Insert」反模式 (Anti-pattern)，將其升級為批次新增 (Bulk Insert)，減少資料庫連線往返與 I/O 阻塞。

## 階段一: Async I/O Refactoring
在先前的「全系統 Async 化重構」中，雖然大部分核心服務已轉換，但仍有部分底層服務與 API 路由殘留了同步的檔案讀寫操作 (`open()`)。透過 AST 腳本實體掃描，確認有 9 個檔案受到影響。這違反了 ASGI/FastAPI 非同步設計原則。

### 影響範圍 (Scope)
共計 9 個檔案：
- `python/src/server/api_routes/internal_api.py`
- `python/src/server/api_routes/admin_api.py`
- `python/src/server/services/migration_service.py`
- `python/src/server/services/dev_ops_agent_service.py`
- `python/src/server/services/scout_ingestion_service.py`
- `python/src/server/services/system/seeding_service.py`
- `python/src/server/services/marketing/analytics_handler.py`
- `python/src/mcp_server/router.py`
- `python/src/mcp_server/features/developer/file_operation_tools.py`

### 執行計畫 (Execution Plan)
1. **[DONE]** **注入依賴**: 確保上述檔案皆有 `import aiofiles`。
2. **[DONE]** **替換為非同步 Context**: 將 `with open(...)` 轉換為 `async with aiofiles.open(...)`。
3. **[DONE]** **替換讀寫操作**: 
   - `f.read()` -> `await f.read()`
   - `f.write(...)` -> `await f.write(...)`
   - `json.load(f)` -> `json.loads(await f.read())`

## 階段二: Database Bulk Insert Optimization
將迴圈內逐筆寫入資料庫的低效做法，重構為透過 Python list 收集 payloads 後，在迴圈外一次性使用 `.insert(payloads)`，大幅優化效能。

### 影響範圍 (Scope)
共計 4 個檔案：
- `python/src/server/services/marketing/content_handler.py`
- `python/src/server/services/job_board_service.py`
- `python/src/server/services/scheduler/jobs/business.py`
- `python/src/server/services/scheduler/jobs/task_dispatcher.py`

### 執行計畫 (Execution Plan)
1. **[DONE]** **重構 `content_handler.py`**: 將 `generate_draft_from_leads` 中的單筆新增改為收集 `new_posts` 列表後一次性寫入 `blog_posts`。
2. **[DONE]** **重構 `job_board_service.py`**: 在爬取 Leads 儲存邏輯中實作批量新增，並同時維護後續 Agent Logs 更新的資料映射。
3. **[DONE]** **重構 `business.py`**: 將 `stale_leads` 與 `content_bottlenecks` 的 log 寫入改為批量，並遍歷回傳的 `.data` 以觸發正確的 `asyncio.create_task`。
4. **[DONE]** **重構 `task_dispatcher.py`**: 將任務派發的 log 紀錄改為批量寫入。
5. **[DONE]** **測試斷言修復**: 修正 `test_job_board_service.py` 中的 `test_identify_leads_and_save`，將預期的單筆 Dict payload 斷言更新為 List payload 斷言以匹配 Bulk Insert 行為。

## 執行結果 (Results)
- **程式碼品質**: 透過腳本實體驗證並重構，執行 `make lint-be` 獲得 `100% Passed` (All checks passed! no issues found in 337 source files)。
- **單元測試**: 執行 `make test-be` 總計 572 項核心測試全數通過 (扣除外部 API Key 驗證異常)。
- **狀態**: **已完成 (Completed)**。兩大隱性效能瓶頸 (Event Loop 阻塞與 Database I/O 阻塞) 皆已徹底根除。