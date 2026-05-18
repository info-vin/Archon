# Phase 5.1.1: Reactive Frontend & Advanced Agentic Orchestration

> **Document Status**: 📝 Proposed Plan (2026-05-15)
> **Goal**: 延續 Phase 5.1.0 的架構基礎，將前端狀態機由「主動輪詢/等待」重構為「被動反應 (Reactive)」，並實作進階的多智能體協作場景，確保全系統在 SSE 驅動下的高響應性與資料一致性。

## 1. 核心目標

1. **前端 SSE 整合**: 建立全域 SSE 監聽機制，接收後端廣播的任務狀態更新。
2. **狀態機被動化 (Passive Machines)**: 重構 `salesCartMachine.ts` 等核心狀態機，使其不再阻塞式等待 API 回傳，而是根據 SSE 事件切換狀態。
3. **進階協作場景實體化**: 實作「市場洞察與線索補全 (Market Intelligence Loop)」的多智能體工作流。
4. **性能與穩定性加固**: 優化 Worker 輪詢間隔與 SSE 斷線重連機制。

---

## 2. 實作里程碑與工作清單 (Execution Milestones)

### Milestone 1: 前端 SSE 基礎設施 (Frontend SSE Infrastructure)
- [x] **1.1 建立 `useSSE` Hook**: 在 `src/hooks/useSSE.ts` 中實作一個具備斷線重連、事件分發功能的 SSE Hook。
- [x] **1.2 全域注入**: 在 `App.tsx` 或 `Layout.tsx` 中啟動 SSE 連線，並將更新事件透過事件總線或 Context 傳遞給 XState Machines。
- [x] **1.3 斷線自癒機制**: 實作 `Last-Event-ID` 支援，確保手機端在切換網路或螢幕關閉後重新連線時能補抓遺失的狀態變更。

### Milestone 2: 狀態機反應式重構 (Reactive State Machine Refactoring)
- [x] **2.1 `salesCartMachine` 被動化**: 
    - 移除 `processBatchAction` 的 `fromPromise` 阻塞等待。
    - 點擊按鈕後立即進入 `dispatched` 狀態（樂觀 UI）。
    - 監聽 `SSE_TASK_UPDATED` 事件，當任務狀態變為 `done` 時自動觸發資料重新整理或顯示結果。
- [x] **2.2 任務詳情同步**: 確保 `TaskModal` 能夠即時顯示 Agent 在背景產出的 `agent_output` (打字機效果或流式顯示)。

### Milestone 3: 進階多智能體工作流 (Advanced Orchestration)
- [x] **3.1 實作「獵人模式」自動補全管線**: 
    - 當 Alice 右滑 Lead 時，觸發一個複雜的 `Supervisor` 任務。
    - 流程：`Supervisor` -> `Librarian` (104 爬蟲) -> `MarketBot` (需求預測) -> `Supervisor` -> `Update DB`。
- [x] **3.2 強化 Worker 並發防護**: 在 `WorkerService` 中引入 `semaphore` 或併發限制，避免同時執行過多耗費 Token 的大型任務。

### Milestone 4: 測試與驗證 (Verification & Hardening)
- [x] **4.1 SSE 斷線模擬測試**: 使用 Playwright 模擬網路中斷，驗證 UI 是否能正確恢復狀態。
- [x] **4.2 負載壓力測試**: 同時觸發 10 個以上的 Agent 任務，觀察 `WorkerService` 的調度邏輯與 SSE 的傳遞延遲。

---

## 3. 變更詳情 (Proposed Changes)

### [Frontend] enduser-ui-fe/src/hooks/useSSE.ts [NEW]
實作全域 SSE 監聽邏輯。

### [Frontend] enduser-ui-fe/src/features/manager/machines/salesCartMachine.ts [MODIFY]
重構狀態流轉邏輯，由 Promise-based 改為 Event-based。

### [Backend] python/src/server/services/system/worker_service.py [MODIFY]
優化任務選取邏輯，支援按優先級或角色分配並發額度。

---

## 4. 驗收標準 (Acceptance Criteria)
1. **零輪詢 (Zero Polling)**: 前端不再使用 `setInterval` 檢查任務狀態。
2. **即時響應 (Real-time Feedback)**: 任務從「指派」到「開始執行」再到「完成」，UI 在 100ms 內反應 SSE 事件。
3. **物理一致性**: 所有的 UI 狀態切換必須對齊 `archon_tasks.status` 資料庫實體。

---

## 5. 下一步 (Next Steps)
- 取得架構審查核准。
- 由 **Milestone 1 (SSE Hook)** 開始動工。
