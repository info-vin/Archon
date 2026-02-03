# Phase 4.6.3 實作現狀與差距分析報告 (Implementation Gap Analysis: Revised)

> **報告日期**: 2026-02-03
> **分析對象**: Codebase vs. `Phase_4.6.3_Charlie_Persona_Workflows.md`
> **執行者**: Gemini (Codebase Investigator)

---

## 1. 執行摘要 (Executive Summary)

經過第二輪深度代碼審查，我們發現後端基礎設施 (`SchedulerService`, `TaskService`) 比預期完善，但在 **「業務邏輯串接」** 上存在關鍵斷層。

**結論**: 我們**不需要**從頭打造所有元件。現有架構已具備 Cron Job 與 Task Creation 能力，Gap 主要在於 **「如何讓這些組件為 Charlie 的工作流服務」**。

---

## 2. 深度差距矩陣 (The Detailed Gap Matrix)

| 功能模組 | 需求規格 (Requirement) | 實作現狀 (Current Reality) | 差距分析 (Gap Analysis) | 風險等級 |
| :--- | :--- | :--- | :--- | :--- |
| **🛡️ Sentinel (哨兵)** | 定期掃描業務異常 (如 Stale Leads) 並發出警示。 | **Partial Implementation**<br>`SchedulerService` 已存在 (`scheduler_service.py`)，目前有 `_run_log_patrol` (錯誤監控) 與 `_analyze_token_usage`。 | **Missing Business Logic**: 缺乏 `_run_business_sentinel` 方法來檢查 `leads` 表的 `updated_at`。<br>**Missing Alerts API**: 前端無法讀取 Sentinel 產生的 `archon_logs`。 | 🔴 High |
| **🔔 Alerts API** | 前端顯示真實警示。 | **Missing**<br>`log_api.py` 只有 `record-gemini-log` (寫入)。<br>`ApprovalsPage.tsx` 使用寫死的 Mock Data。 | **Endpoint Gap**: 需要新增 `GET /api/logs/alerts` 端點，查詢 `archon_logs` 表 (Level='ALERT')。 | 🔴 High |
| **⚡ Smart Task** | AI 自動生成任務草稿。 | **Partial Capability**<br>`TaskService.refine_task_description` (POBot) 已存在！使用了 RAG 與 LLM。 | **Integration Gap**: 目前 POBot 是為 "Refine" 設計的 (輸入現有文字)，尚未與 Sentinel Alert 整合 (從 Alert 生成任務)。 | 🟡 Medium |
| **🔐 RBAC** | 只有 Manager 可發布。 | **Partial**<br>`marketing_api.process_approval` 檢查了 `user_role`。 | **API Gap**: 前端 `/api/blog/{id}/publish` 端點可能與 `process_approval` 重疊或混用，需統一入口並確保權限。 | 🟢 Low |

---

## 3. 實作計畫 (Revised Implementation Plan)

基於「不重造輪子」的原則，我們將採取以下行動：

### A. 後端增強 (Backend Enhancement)

1.  **擴充 `SchedulerService` (`python/src/server/services/scheduler_service.py`)**:
    *   新增 `_run_business_sentinel()` 方法。
    *   邏輯：查詢 `leads` 表 (`status != 'won' AND updated_at < NOW-14d`)。
    *   行動：將發現的 Stale Leads 寫入 `archon_logs` (Source='sentinel', Level='ALERT')。
    *   排程：設定為每 12 小時執行一次。

2.  **擴充 `LogAPI` (`python/src/server/api_routes/log_api.py`)**:
    *   新增 `GET /api/logs/alerts` 端點。
    *   邏輯：回傳 `SELECT * FROM archon_logs WHERE level = 'ALERT' ORDER BY created_at DESC`。

3.  **擴充 `TaskService` (Optional but Good)**:
    *   考慮新增 `create_task_from_alert(alert_id)`，復用 `refine_task_description` 的邏輯來生成高質量的任務描述。

### B. 前端接合 (Frontend Integration)

1.  **更新 `api.ts`**:
    *   新增 `getAlerts()` 方法，呼叫 `/api/logs/alerts`。

2.  **更新 `ApprovalsPage.tsx`**:
    *   移除 `setAlerts` 中的 Mock Data。
    *   使用 `api.getAlerts()` 獲取真實資料。
    *   (UI 優化) 調整 Alert 卡片樣式，使其顯示 Alert 的詳細資訊 (如 `details` JSON 欄位)。

---

## 4. 數據與決策支援 (Data & Decision Support)

目前的 `StatsAPI` (`tasks-by-status`, `member-performance`) 已經能提供基本的儀表板數據。Charlie 的 Dashboard (`ApprovalsPage.tsx`) 已經整合了這些數據的入口。

**建議**: 為了讓 Charlie 的決策更數據化，我們可以在 Alert 卡片上顯示該 Lead 的 `enrichment_score` (目前 Sentinel 邏輯中已有此計畫)。

---

**請問您是否批准這個基於現有架構 ("Scheduler + LogAPI") 的修正計畫？**
如果批准，我將依序執行：
1.  修改 `scheduler_service.py` 加入 Sentinel 邏輯。
2.  修改 `log_api.py` 開放 Alerts 查詢。
3.  修改前端 `ApprovalsPage.tsx` 對接真實 API。
