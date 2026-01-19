---
name: "Phase 4.3.1: Admin UI Regression & RBAC Completion (Admin UI 回歸修復與 RBAC 補完)"
description: "修復因 Phase 4.3 與 Phase 5 合併導致的 Admin UI 功能退化，並完成 Task Assignee ID 的最後一哩路。"
status: "Completed"
dependencies: ["Phase 4.3", "Phase 5.2"]
---

## 1. 背景與問題 (Context & Problem)

在 Phase 4.3 (Marketing Site) 與 Phase 5 (RBAC) 完成後，Admin UI (Port 3737) 出現了嚴重的回歸 (Regression)。雖然 End-User UI (Port 5173) 功能正常，但管理後台的核心功能癱瘓，且資料庫遷移 (Migration 007) 與程式碼實作脫鉤。

### 關鍵症狀 (Symptoms)
1.  **Ghost Upload**: Admin UI 上傳文件後無錯誤訊息，但文件未出現在列表中，RAG 處理流程未觸發。
2.  **RAG Status Red**: Admin UI 顯示 RAG 服務狀態為紅圈 (Disconnected)，但後端服務實際上是健康的。
3.  **Data Mismatch**: `migration/007` 雖然建立了 `assignee_id` 欄位，但後端 `TaskService` 與前端 `Task` 類型並未實作此欄位的讀寫，導致功能形同虛設。
4.  **Google Provider Error**: 設定 Google API Key 後，Provider 狀態顯示紅圈。
5.  **Large File Upload Failure**: 上傳 50MB 檔案失敗，即使後端已放寬限制。

## 2. 根因分析 (Root Cause Analysis)

### 2.1 Admin UI Auth 斷裂 (Identity Crisis)
*   **Dev-Token Domain Mismatch**: 後端 `auth_api.py` 嘗試登入 `admin@archon.ai`，但資料庫種子 (`init_db.py`) 建立的是 `admin@archon.com`。這導致後端在每次啟動時都會重複建立一個無關聯的新使用者，其 ID 與 `profiles` 表中的 `system_admin` 不匹配。
*   **API Client Failure**: Admin UI 的 `apiClient.ts` 與 `knowledgeService.ts` 寫死了從 `localStorage` 讀取 `archon_token`。但若自動登入失敗 (因 500 Error)，此 Token 為空。
*   **後果**: 上傳請求未攜帶 Authorization Header -> 後端 `knowledge_api.py` 拒絕請求 (403/401) -> 前端因缺乏錯誤處理而靜默失敗。

### 2.2 RAG Health Check 權限誤殺
*   **證據**: 後端 API 引入了嚴格的 `Depends(get_current_user)`。
*   **事實**: Admin UI 的 Health Check 請求若未攜帶正確 Token，或使用了不被允許的角色 (如未正確傳遞 `system_admin`)，將被 Middleware 攔截。

### 2.3 Migration 007 孤兒化
*   **證據**: `task_service.py` 的 `create_task` 與 `update_task` 方法參數中完全沒有 `assignee_id`。
*   **事實**: 資料庫有欄位，但 API 層與 Service 層未對接。

### 2.4 Google Provider API Version Error
*   **證據**: `providers_api.py` 使用了舊版 `v1` 端點 (`https://generativelanguage.googleapis.com/v1/models`)。
*   **事實**: Google 已強制要求使用 `v1beta` 或更新的 API 版本。這導致連線測試直接失敗。

### 2.5 Upload Timeout Bottleneck
*   **證據**: `knowledgeService.ts` 寫死了 `AbortSignal.timeout(30000)` (30秒)。
*   **事實**: 50MB 檔案上傳在本地 Docker 網路環境下極易超過 30 秒。前端主動切斷連線導致上傳失敗，與後端限制無關。

## 3. 實作計畫 (Implementation Plan)

### Step 1: Admin UI Auth Client 修復 (Critical)
*   **目標**: 恢復 `knowledgeService.ts` 的 Token 獲取能力。
*   **行動**:
    *   [x] **Fix Backend Domain**: 將 `auth_api.py` 中的 `admin@archon.ai` 修正為 `admin@archon.com`。
    *   [x] **Fix Frontend Client**: 重構 `knowledgeService.ts` 與 `apiClient.ts`，加入對 Supabase 標準 Token (`sb-*-auth-token`) 的搜尋邏輯作為備援。
    *   [x] **Update Tests**: 更新 `dev-login.test.tsx` 以匹配正確的 `.com` 網域。

### Step 2: Task Assignee ID 實作 (Backend & Frontend)
*   **目標**: 讓 Task 指派能真正寫入 `assignee_id`。
*   **行動**:
    *   [x] **Backend**: 修改 `python/src/server/services/projects/task_service.py`，在 `create_task`, `update_task`, `list_tasks` 中加入 `assignee_id` 處理邏輯。
    *   [x] **Frontend**: 更新 `archon-ui-main/src/features/projects/tasks/types/task.ts`，加入 `assignee_id` 欄位。

### Step 3: Provider & Upload Fixes (Stability)
*   **目標**: 修復 Google 連線與大檔案上傳。
*   **行動**:
    *   [x] **Google API**: 將 `providers_api.py` 端點更新為 `v1beta`。
    *   [x] **Upload Timeout**: 將 `knowledgeService.ts` 上傳超時放寬至 300秒 (5分鐘)。

### Step 4: 文件同步
*   **目標**: 確保開發者手冊反映真實狀況。
*   **行動**:
    *   [x] 更新 `CONTRIBUTING_tw.md`，加入 `migration/007` 說明。

## 4. 驗收標準與結果 (Acceptance Criteria & Results)

### 4.1 Admin UI (Port 3737) Auth & RAG
- [x] **Auto-Login**: 開啟 Admin UI，自動登入成功 (無 500 Error)。
- [x] **RAG Status**: 右上角 RAG 狀態顯示 **綠勾 (Connected)**。
- [x] **Provider Re-verification**: 若之前狀態為紅圈，需**手動刪除**舊設定並重新輸入 API Key 進行驗證，驗證後顯示 **綠勾**。

### 4.2 Knowledge Upload
- [x] **Large File Upload**: 上傳 50MB 檔案成功，進度條正常，無 Timeout 錯誤。
- [x] **API Header**: Network Tab 顯示 `Authorization` Header 注入成功。
- [!] **Filename Limitation**: 僅支援英文檔名，中文檔名會導致上傳失敗（已列入 Phase 4.3.2）。

### 4.3 Task Management
- [x] **Assignee Persistence**: 在 Dashboard 建立任務並指派給 "Alice"，DB 驗證 `assignee_id` 正確寫入。

## 5. Deferred Items (Phase 4.3.2: UX Polish)

以下項目在手動驗收中被識別為 UX/功能限制，將移至下一階段處理：

1.  **Unicode Filename Support**: 目前後端 URL 編碼邏輯對中文檔名支援不佳，需實作 `unidecode` 或更強健的檔名處理。
2.  **Document Preview**: 目前上傳的 DOCX/PDF 僅能下載，無法在瀏覽器直接預覽。需引入 PDF.js 或類似的 Viewer 元件。
3.  **Provider Auto-Retry**: 優化 Provider Settings 介面，在後端狀態變更時自動重試驗證，無需使用者手動刪除重設。