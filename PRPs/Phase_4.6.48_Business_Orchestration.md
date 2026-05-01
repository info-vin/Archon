# Phase 4.6.48: 全角色業務流顯式串接與前置作業調查 (Business Orchestration & Preliminary Investigation)

> **核心目標**: 解除 Phase 4.6.6+ 遺留的「幽靈邏輯」，透過**顯式服務協調 (Service Orchestration)**，將 Alice (Sales)、Bob (Marketing) 與 Charlie (Manager) 的業務副作用與系統底層 (Librarian, POBot, Sentinel) 實體掛鉤。
> **修復箝制原則 (Constraints)**: 
> 1. **零循環依賴**: 所有跨 Service 呼叫必須在 `async def` 函數內部執行 (Lazy Import)。
> 2. **零隱含事件**: 拒絕 Event Bus 造輪子，所有邏輯必須在 API 或主 Service 方法內清晰可見。
> 3. **物理隔離驗證**: 各角色的修復必須附帶獨立的實體驗證步驟，避免改 A 壞 B。

---

## 1. 業務邏輯顯式化實作 (Explicit Orchestration Plan)

### 1.1 Alice (Sales): 潛客失敗分析閉環
* **標的檔案**: `python/src/server/services/marketing/lead_handler.py`
* **修復動作**:
    * 在 `update_lead` 中攔截 `status == "LOST"` 的狀態變更。
    * 引入 `LibrarianService` (Lazy Import) 並呼叫 `archive_failure_case`。
    * 提供完整的 `reason`, `company_name`, `job_title` 等元數據。
* **箝制點**: 確保 `LibrarianService` 的失敗不會導致 `update_lead` 的 SQL Transaction Rollback (Exception 應被 Catch 並轉為 Error Log)。

### 1.2 Bob (Marketing): 品牌風格學習閉環
* **標的檔案**: `python/src/server/services/marketing/content_handler.py`
* **修復動作**:
    * 在 `process_approval` 函數內攔截 `action == "REJECT"` 且附帶 `notes` 的操作。
    * 引入 `LibrarianService` 並呼叫 `archive_style_critique`。
    * 確保將拒絕原因提取並標記為 `brand_voice` 或 `style_critique`。
* **箝制點**: 必須確保 `notes` 內容非空且具備知識價值才進行向量化，減少浪費。

### 1.3 Charlie (Manager): 異常監控與自動分派閉環
* **標的檔案**: `python/src/server/services/scheduler_service.py` 與 `python/src/server/services/projects/task_service.py`
* **修復動作**:
    * **Scheduler**: 擴充 `_run_business_sentinel` 方法，掃描 `leads` 表中停滯過久的資料，寫入 `archon_logs` (Level=ALERT)。
    * **TaskService**: 建立 `generate_task_from_alert` 工廠方法，接收 Alert ID，呼叫 POBot 生成對應的「跟進」任務，並指派給原 Lead Owner。
* **箝制點**: Sentinel 需具備狀態標記，避免對同一筆停滯 Lead 重複觸發 Alert (Idempotency)。

---

## 2. 前置作業調查與物理驗證 (Preliminary Investigation & Verification)

### 2.1 驗證步驟 A: Alice 狀態連動 (Lead Status -> Librarian)
1. **環境重置**: 執行 `make db-init` 確保資料庫有預設的 Leads。
2. **觸發操作**: 呼叫 `PATCH /api/marketing/leads/{lead_id}`，Payload 為 `{"status": "LOST", "lost_reason": "Price too high"}`。
3. **物理斷言 (Assertions)**:
    * 查詢 `leads` 表，確認該筆 Lead 狀態已轉為 `LOST`。
    * 查詢 `archon_crawled_pages` 表，確認新增了一筆 `metadata->>'outcome' = 'failure'` 且 URL 包含 `analysis://failure/` 的知識項目。
    * 查詢伺服器日誌，確認無循環依賴報錯。

### 2.2 驗證步驟 B: Bob 審核回饋 (Blog Approval -> Librarian)
1. **環境重置**: 使用 `make db-init` 初始化一篇狀態為 `review` 的草稿。
2. **觸發操作**: Charlie 呼叫 `POST /api/marketing/blog/{post_id}/approve`，Payload 為 `{"action": "REJECT", "notes": "Tone is too casual, needs more professional vocabulary."}`。
3. **物理斷言 (Assertions)**:
    * 查詢 `blog_posts` 表，確認狀態退回 `draft` 或 `rejected`。
    * 查詢 `archon_document_versions` 或 `archon_crawled_pages`，確認 `archive_style_critique` 已執行並寫入帶有 `review_notes` 的風格約束知識點。

### 2.3 驗證步驟 C: Charlie 監控分派 (Sentinel -> Task)
1. **數據準備**: 手動在資料庫將一筆 `leads` 的 `updated_at` 修改為 30 天前。
2. **觸發操作**: 在後端手動或透過 API 觸發 `SchedulerService()._run_business_sentinel()`。
3. **物理斷言 (Assertions)**:
    * 查詢 `archon_logs`，確認新增一筆 `level = 'ALERT'` 的紀錄，內容提及該停滯的 Lead。
    * 查詢 `archon_tasks`，確認新增了一筆 `status = 'todo'` 的任務，且標題或描述中包含了 AI 生成的跟進建議，被指派給 Alice。

---

## 3. 潛在架構影響評估
- **耦合度**: 使用 Lazy Import 可完美避開 Startup Phase 的 Circular Import 錯誤。
- **維護性**: 邏輯集中在 `update_lead`, `process_approval` 等核心業務方法內，易於透過 `grep` 追蹤。
- **測試隔離**: `test_marketing_api.py` 可能需要 mock `LibrarianService` 以免執行耗時的向量化操作。
