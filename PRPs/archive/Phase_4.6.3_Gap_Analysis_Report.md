# Phase 4.6.3 Charlie 角色 (指揮官工作流) 技術落差分析報告

**文件編號**: PRP-4.6.3-GAP-001
**日期**: 2026-02-03
**對象**: 資深工程團隊、系統架構師
**參考依據**: `Phase_4.6.3_Charlie_Persona_Workflows.md`

---

## 1. 執行摘要 (Executive Summary)

本報告旨在評估「Charlie 指揮官工作流」的提案與當前代碼庫實作之間的差距。目前的評估結論是：系統的 **「基礎設施層 (Infrastructure Layer)」** (包含排程器、RAG 與 RBAC) 已趨於成熟，但 **「業務應用層 (Application Layer)」** 缺乏將這些組件串聯成「自動化監控 -> 經理裁決 -> 任務分派」閉環的具體邏輯。

**核心發現**: 系統目前具備「監控」與「自動化」的能力 (`SchedulerService` 與 `TaskService`)，但缺乏針對「銷售與 CRM 領域」的具體配置與集成。

---

## 2. 架構落差分析 (Architectural Gap Analysis)

### 2.1 組件：Sentinel 哨兵 (業務異常監測)

*   **需求規格**: 一個後端背景 Agent ("Sentinel")，持續掃描業務異常 (例如：14 天未拜訪的停滯線索、高價值客戶流失風險)，並將警示寫入日誌系統。
*   **技術現狀 (`python/src/server/services/scheduler_service.py`)**:
    *   **機制**: 已正確實作基於 `AsyncIOScheduler` 的異步排程器。
    *   **現有任務**:
        *   `_run_system_probe`: 基礎設施健康檢查。
        *   `_run_log_patrol`: 錯誤日誌掃描與自動修復觸發。
    *   **缺口**: 完全缺乏針對「業務垂直領域 (Sales/Marketing)」的掃描邏輯。`leads` 表格目前從未被排程器查詢或監控。
*   **技術差距**:
    *   `SchedulerService` 中缺失 `_run_business_sentinel` 方法。
    *   缺乏針對「停滯線索 (Stale Lead)」的啟發式邏輯 (Heuristic Logic) 配置 (例如：硬編碼 14 天 vs. 動態系統設定)。

### 2.2 組件：事件與警示攝取 (Data Access Layer)

*   **需求規格**: 一個集中的日誌存儲 (`archon_logs`)，需對前端開放讀取接口，以便 Charlie 在儀表板查看實時警示。
*   **技術現狀**:
    *   **資料庫**: `archon_logs` 表已建立 (Migration 012)，且已針對 `created_at` 建立索引。
    *   **API (`python/src/server/api_routes/log_api.py`)**: 目前僅呈現 **「單向寫入 (Write-Only)」** 模式。僅存在 `POST /record-gemini-log`。
*   **技術差距**:
    *   **讀寫不對稱 (Read Asymmetry)**: 缺乏查詢日誌/警示的 API 端點，無法根據等級 (Level='ALERT') 或來源 (Source='sentinel') 進行過濾。
    *   **類型安全性**: 現有的 `GeminiLogRequest` 模型過於聚焦在 LLM 交互，不支援儀表板所需的通用警示模型 (Generic Alert Schema)。

### 2.3 組件：智慧任務分派 (Smart Task)

*   **需求規格**: 經理能一鍵將警示轉化為任務，且 AI 會根據警示上下文 (例如：客戶 X 的歷史背景) 自動填充任務詳情。
*   **技術現狀 (`python/src/server/services/projects/task_service.py`)**:
    *   **核心能力**: 存在 `refine_task_description` (POBot)，具備 RAG 與 LLM 生成能力。
    *   **整合程度**: 該邏輯目前要求顯式的標題與描述輸入，尚未與 `archon_logs` 實體進行邏輯關聯。
*   **技術差距**:
    *   缺乏 **「工廠模式 (Factory Pattern)」** 或輔助方法 `create_task_from_log_entry(log_id)`，用於：
        1.  獲取日誌條目。
        2.  提取元數據 (如 `lead_id`, `risk_score`)。
        3.  合成 POBot 的生成提示詞。
        4.  自動建立任務。

### 2.4 組件：指揮中心儀表板 (Frontend)

*   **需求規格**: 經理專用的統一視圖，整合「審核隊列」與「業務警示」。
*   **技術現狀 (`enduser-ui-fe/src/pages/ApprovalsPage.tsx`)**:
    *   **UI 結構**: 已實作分頁標籤 (Content, DevOps, Alerts)，佈局基本完成。
    *   **資料綁定**: **全數硬編碼 (Hardcoded Mocks)**。`alerts` 狀態僅由靜態資料初始化。
    *   **動作處理**: `handleDispatchTask` 僅建立一個通用的任務，未利用後端的 AI 生成能力。
*   **技術差距**:
    *   前端與後端 `archon_logs` 的真實數據流處於斷開狀態。
    *   API Client 方法 `api.getAlerts()` 缺失。

---

## 3. 風險評估 (Risk Assessment)

| 風險類別 | 嚴重度 | 描述 |
| :--- | :--- | :--- |
| **資料一致性 (Consistency)** | 高 | 若 Sentinel 監控邏輯與前端 Mock 邏輯不符 (例如過期天數定義不同)，使用者會看到矛盾的系統狀態。 |
| **效能風險 (Performance)** | 中 | 對 `leads` 表執行 `updated_at < T` 的大規模查詢需確保有合適的複合索引，否則隨數據量增長會引發全表掃描。 |
| **安全與權限 (RBAC)** | 中 | 透過 API 公開 `archon_logs` 需嚴格過濾 Level，避免非 Admin 使用者看到系統內部的堆疊追蹤 (Stack Traces) 等敏感資訊。 |

---

## 4. 實作規格與修正指南 (Implementation Specification)

### 階段 4.6.3-A: 後端邏輯注入

**4.1 擴充排程服務**
*   **檔案**: `python/src/server/services/scheduler_service.py`
*   **行動**: 注入 `_run_business_sentinel` 方法。
*   **邏輯**: 查詢 `leads` 表中 `updated_at` 過期且狀態非 `won` 的條目，並寫入 `archon_logs` (Level='ALERT')。

**4.2 開放警示 API**
*   **檔案**: `python/src/server/api_routes/log_api.py`
*   **行動**: 新增 `GET /alerts`。
*   **約束**: 必須強制執行 `level = 'ALERT'` 過濾，並建議支援分頁 (`limit=50`)。

### 階段 4.6.3-B: 智慧分派整合

**4.3 任務工廠方法**
*   **檔案**: `python/src/server/services/projects/task_service.py`
*   **行動**: 新增 `generate_task_from_alert(log_id: str, assignee_id: str)`。
*   **流程**: 讀取日誌 -> 提取客戶背景 -> 呼叫 LLM 轉化為「跟進任務」描述 -> 寫入 Task。

### 階段 4.6.3-C: 前端數據對齊

**4.4 指揮中心接合**
*   **檔案**: `enduser-ui-fe/src/pages/ApprovalsPage.tsx`
*   **行動**: 將 `setAlerts` 假資料替換為 `api.getAlerts()`。
*   **行動**: 將 `handleDispatchTask` 升級為呼叫後端的智慧分派端點。

---

## 5. 驗收標準 (Acceptance Criteria)

為確保 Phase 4.6.3 實作符合資深工程標準，開發完成後必須通過以下驗收點：

### 5.1 哨兵自動化 (Sentinel Automation)
- [ ] **觸發驗證**: 手動將某一 Lead 的 `updated_at` 改為 15 天前，執行 Sentinel 掃描後，`archon_logs` 應出現對應的 `ALERT` 記錄。
- [ ] **防刷機制**: 重複執行掃描，同一 Lead 不應產生重複的 `ALERT` (需檢查日誌中的 `details.lead_id`)。

### 5.2 數據流真實性 (Data Pipeline Integrity)
- [ ] **API 驗證**: 呼叫 `GET /api/logs/alerts` 應回傳正確的 JSON 數組，且 `level` 欄位必須嚴格等於 `ALERT`。
- [ ] **前端渲染**: 指揮中心 (`ApprovalsPage`) 的 Alerts Tab 應顯示與資料庫一致的內容，包含客戶名稱與風險天數。

### 5.3 智慧分派 (Smart Dispatch)
- [ ] **AI 生成驗證**: 點擊 "Dispatch" 後，系統應在 `archon_tasks` 建立新任務。
- [ ] **上下文豐富化**: 產出的任務描述應包含該 Lead 的歷史摘要 (由 RAG 提供)，而非僅是簡單的文字拼接。

### 5.4 權限與安全 (Security & RBAC)
- [ ] **角色阻擋**: 以 `sales` 或 `member` 角色登入，應無法存取 `/approvals` 路由且無法呼叫 `/api/logs/alerts` 端點。
- [ ] **日誌脫敏**: 警示 API 不得洩漏資料庫連線字串、堆疊追蹤或未經處理的系統路徑。

---

## 6. 結論 (Conclusion)

Archon 系統目前已完成 80% 的工作，剩餘的 20% 是將背景排程器與使用者介面之間 **「結締組織 (Connective Tissue)」** 補齊。透過擴充現有的 `SchedulerService` 並開啟 `archon_logs` 的讀取通道，我們可以在不引入重大架構債的情況下，完整落地「Charlie」指揮官的人設。