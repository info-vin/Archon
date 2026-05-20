# Phase 5.1.11: Fan-out Engine 自動化測試與 Clockwork 排程整合

Status: Completed

本計畫延續 Phase 5.1.10 的實體 LLM Map-Reduce 驗證，旨在將實驗性的 `engine_beta_graph.py` 轉化為生產級 (Production-ready) 模組，並透過嚴格的自動化測試防護網，將其掛載至 Archon 的 Clockwork 定期排程系統中。

## 核心原則：拒絕樂觀路徑 (No Optimistic Paths)

在將高消耗的 Fan-out 引擎掛載至背景自動執行前，必須透過以下三個階段的物理驗證與自動化測試，確保系統在遭遇網路異常、API 限制或併發競爭時，能維持絕對的強健性 (Resilience)。

---

## 階段一：建立 Fan-out 引擎的自動化防護網 (Pytest)

目標位置：`python/tests/workflow/test_engine_beta_graph.py`

為了確保 CI/CD 環境穩定且不產生額外 API 費用，測試必須使用 `unittest.mock.patch` 隔離真實的 LLM 呼叫 (`_run_agent_with_retry`)。

### 1. 正向斷言 (Happy Path - Map-Reduce 完整性)
*   **測試目標**: 驗證圖的發散與聚合邏輯正確。
*   **斷言要求**:
    *   [x] `beta_graph.run()` 能成功觸發。
    *   [x] Mock 被呼叫的次數必須為 4 次 (3 個 Worker + 1 個 Supervisor)。
    *   [x] 最終 `BetaState.map_results` 字典確實包含 `sales`, `marketing`, `system` 三把 Key。
    *   [x] `SharedState.final_result` 確實有產出非空的最終摘要字串。

### 2. 負向斷言 (Negative Path - 局部節點崩潰)
*   **測試目標**: 驗證系統容錯能力，確保單一情報源失敗不會摧毀整個排程。
*   **模擬情境**: 設定 Mock 條件，當目標為 `system` 且呼叫 `system_agent` 時，強迫拋出 `Exception("Simulated API Crash")`。
*   **斷言要求**:
    *   [x] 執行過程不能拋出 Unhandled Exception 導致整個 Test Case 崩潰。
    *   [x] 最終的 `map_results['system']` 必須優雅降級為包含錯誤訊息的字串 (e.g., `"Failed due to error..."`)。
    *   [x] `sales` 與 `marketing` 的正常資料必須保留不受影響。

### 3. 防禦性斷言 (Token ROI 併發累加驗證)
*   **測試目標**: 確保在多協程 (async) 並發寫入下，Token 計算不會因 Race Condition 被互相覆蓋。
*   **模擬情境**: 讓每個 Mock 的 Worker 呼叫都回傳 `RunResult` 並固定消耗 10 個 Input Tokens 與 5 個 Output Tokens。
*   **斷言要求**: 
    *   [x] 執行結束後，`SharedState.input_tokens` 必須精確等於 `40` (3 Worker * 10 + 1 Supervisor * 10)。
    *   [x] 證明全域狀態具備併發寫入的安全性。

---

## 階段二：實作 `business.py` 排程任務與測試

在引擎本身有測試保護後，將其包裝為符合專案標準的商業任務。

### 1. 商業邏輯實作
*   **位置**: `python/src/server/services/scheduler/jobs/business.py`
*   **函式**: `run_daily_executive_summary()`
*   **行為**: 
    1. [x] 實體化 `SharedState`，並呼叫 `beta_graph.run()`。
    2. [x] 將產出的 `final_result` (Executive Summary) 寫入資料庫的 `tasks` 表。
    3. [x] 將該 Task 指派給 Supervisor/Manager 角色 (Charlie)，標題設定為 `[Daily Report] Executive Summary`。

### 2. 排程器自動化測試
*   **位置**: `python/tests/services/test_business_scheduler.py`
*   **測試目標**: 確保業務邏輯確實能將 Graph 的記憶體輸出，轉換為資料庫中的持久化實體。
*   **斷言要求**: 
    *   [x] Mock `beta_graph.run()` 以及 `supabase.table("tasks").insert()`。
    *   [x] 驗證 `insert` 方法有被正確呼叫，且 Payload 中包含正確的標題與 Graph 輸出的內容。

---

## 階段三：Clockwork 掛載與物理公證

### 1. 排程掛載 (Scheduler Mounting)
*   **位置**: `python/src/server/services/scheduler_service.py`
*   **行為**: [x] 在 `SchedulerService._schedule_jobs()` 中，使用 `_schedule_stateful_job` 將 `run_daily_executive_summary` 加入排程。
*   **頻率設定**: [x] 週期設定為 **24 小時 (Daily)**，並確保具備重啟狀態記憶 (Stateful)，防止伺服器重啟導致漏發或重複派發。

### 2. 終極物理驗證 (Twin Scout - Playwright)
*   **行動**: [x] 修改或新增一個 Playwright E2E 測試腳本 (例如透過 `make twin-scout` 機制)。
*   **斷言**: [x] 由 Playwright 啟動無頭瀏覽器，登入為 Manager (Charlie)。導航至 Task 列表，**物理斷言 (Physical Assertion)** DOM 中確實能渲染出這張 `[Daily Report]` 的卡片，達成從後端引擎到前端 React 渲染的 100% 物理對齊。
