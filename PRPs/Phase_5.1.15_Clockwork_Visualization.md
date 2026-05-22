# Phase 5.1.15: Clockwork 排程器狀態可視化與 Admin UI 整合 (Clockwork Visualization)

## 背景 (Background)
在 Phase 5.1.14 中，我們已經將系統的 13 項任務重構為可靠的生命週期觸發架構。然而，目前這些任務的執行狀態仍隱藏在伺服器日誌中，David (Admin) 無法從 UI 直接得知單一排程（如 `alice_auto_fetch`）的下次預定時間或執行結果。

**防重複造輪子聲明**：在現有的 `SystemHealthDashboard.tsx` 中，已經有顯示 `Clockwork` 作為一個 Agent 的狀態列。我們不需要建立全新的儀表板，而是應該在該頁面進行無縫擴充。

## 本階段目標 (Goals)
在 David 的 Admin UI 中擴充既有的系統健康看板，提供「Clockwork 任務級別」的排程透明度。

### 1. 後端 API 擴充 (Admin API Exposure)
* 修改 `python/src/server/services/stats/__init__.py` 中的 `get_system_health_overview`。
* 從 `scheduler_service` 的記憶體狀態（APScheduler Job List）與資料庫的 `archon_settings` (LAST_RUN_*) 中聚合這 13 項任務的狀態。
* 將其作為 `jobs_snapshot` 屬性，附加到回傳的 `active_agents` 陣列中的 `clockwork` 實體上。

### 2. 前端 UI 元件擴充 (SystemHealthDashboard Integration)
* **組件名稱**: `ClockworkJobsTable.tsx` (作為子元件)。
* **整合位置**: 將其無縫嵌入於 `enduser-ui-fe/src/features/admin/components/SystemHealthDashboard.tsx` 中 `Agent Status & XP` 區塊的下方。
* **視覺風格**: 簡潔的資料表，列出：任務名稱、類型 (Stateful/Stateless)、上次執行時間 (相對時間，如 "5 mins ago")、下次預定時間。

### 3. 即時手動干預 (Operational Control)
* 在前端實作 API 呼叫，允許對特定 Job 點擊「立即執行 (Run Now)」。
* 後端在 `internal_api.py` 的 `/cron/trigger` 擴充支援 `?job_id=xxx` 的單點觸發參數。

## 驗收標準 (Acceptance Criteria)
1. [x] David 登入 Admin UI 後，能在「System Health」分頁看見 Clockwork 專屬的任務擴展列表。
2. [x] 列表正確顯示 13 項任務的 `LAST_RUN` 與預計下一次的 `NEXT_RUN` 時間。
3. [x] 點擊「立即執行」能成功觸發單一任務而不影響其他任務。
4. [x] 通過 `make audit-qa` (前端 Unit Tests 物理驗證)。
