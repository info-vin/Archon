# Phase 5.9.18: 背景巡邏任務最佳化 (Stateless Patrols Optimization)

## 背景 (Background)
根據 `archon_logs` 的真實數據分析，系統目前在全天候常駐背景任務 (Stateless Patrols) 產生了頻繁的資料庫讀寫：
* `system_probe` 每 15 分鐘運行一次，且無論健康與否都會將狀態寫入 Supabase，導致每天約 96 筆 Spam 日誌，消耗資料庫空間。
* `meta_twin_audit` (每 10 分鐘) 與 `model_verification` (每 120 分鐘) 在無修復動作時也會消耗 API/DB 讀取資源。
* `task_dispatcher` 負責回收殭屍任務 (每 30 分鐘)，但回收時僅寫入 `archon_logs`，缺乏即時的維運通知。

## 決策與變更 (Decisions & Changes)

### 1. Scheduler 排程頻率最佳化
在 `scheduler_service.py` 調整無狀態任務的觸發頻率：
- `system_probe`: 15m -> **60m** (保留成功與失敗的紀錄，作為系統心跳)
- `meta_twin_audit`: 10m -> **20m**
- `task_dispatcher`: 30m -> **15m**
- `model_verification`: 120m -> **150m**

### 2. 殭屍任務即時警報
修改 `task_dispatcher.py` 的殭屍回收邏輯：
- 只要偵測到 `len(reclaim_data) > 0`，立刻透過 `TelegramService` 發送推播警告，讓指揮官能第一時間得知有 Agent 卡死。

## 驗證 (Verification)
- [x] 靜態代碼檢查與排版 (`make lint`)
- [x] 單元測試 (`make test-be`) 確保 Scheduler 與 Dispatcher 行為符合預期。
