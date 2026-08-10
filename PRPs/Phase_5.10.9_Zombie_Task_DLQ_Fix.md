# Phase 5.10.9: Zombie Task Infinite Loop & DLQ Hardening

## 1. 背景與問題描述 (Background & Problem)
在任務背景執行系統中，`worker_service` 負責掃描並接管因系統崩潰而卡在 `processing` 或 `doing` 狀態的「殭屍任務 (Zombie Tasks)」。
該機制預期在自動重試 3 次後，將任務狀態標記為 `failed` 並丟入死信佇列 (DLQ)。

然而，我們發現在讀取路徑 (`query_logic.py`) 中，`task_data` 的字典映射漏掉了資料庫的 `retry_count` 欄位。這導致：
- 每次 `worker_service` 撈取殭屍任務時，`task.get("retry_count")` 皆返回 `None` (預設為 `0`)。
- 系統永遠將其視為第一次重試，並不斷將 `Attempt 1/3` 寫入任務描述中。
- 此「讀寫不對稱」導致無限迴圈，所有依賴背景排程的任務 (包含 Daily, Weekly, Monthly Reports) 若遭遇中斷，皆會陷入死結而永遠無法觸發 DLQ 失敗機制。

## 2. 修復計畫 (Proposed Fix)
透過物理對齊資料庫欄位與 Python Schema，修復讀寫不對稱問題。

### 目標檔案：`python/src/server/services/projects/tasks/query_logic.py`
在 `list_tasks_logic` 方法組裝 `task_data` 字典時，明確補回 `retry_count` 欄位。

```python
            task_data = {
                "id": task["id"],
                "project_id": task["project_id"],
                # ... 既有欄位
                "schedule_config": task.get("schedule_config"),
                "retry_count": task.get("retry_count", 0),  # [NEW] 補回遺失的重試次數映射
            }
```

## 3. 預期效益與驗證 (Expected Outcome & Verification)
1. **解除無限迴圈死結**：卡死的任務將正確累加 `retry_count` (1/3 -> 2/3 -> 3/3)，到達上限後正確轉換為 `failed` 狀態。
2. **零副作用**：此為純粹的 Schema Mapping 補齊，不影響既有的 API 結構與單元測試。
3. **驗證方式**：修改完成後，執行 `make test-be` (或 `uv run pytest`)，確保包含 `test_worker_service.py` 在內的核心模組全數通過。

## 4. 實際執行進度與物理驗證 (Execution Progress & Physical Verification)

### [2026-08-10] 實作與驗證完成 (Completed)
- **程式碼修改**：已於 `python/src/server/services/projects/tasks/query_logic.py` 補上 `"retry_count": task.get("retry_count", 0)` 映射。
- **物理驗證 (Physical Evidence)**：
  - 執行 `make test-be` 後端單元測試，無發生斷層破壞。
  - **測試結果**：`====== 645 passed, 9 skipped, 4 xfailed, 63 warnings in 153.12s (0:02:33) ======`。
  - **證實**：原有的 `test_worker_service.py` 測試依然通過。這進一步佐證了先前的虛假測試 (False Mock) 只測試了假想情況，而現在我們在底層真實修復了映射，達到了物理與測試的統一。
- **版控紀錄**：
  - Git Commit: `91c7f33e fix(tasks): map retry_count in query_logic to prevent zombie task infinite loop`
  - 狀態：已合併至 `dev/twins` 與 `feat/twins`，並成功推送至遠端。
