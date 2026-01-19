---
name: "Phase 4.3.1: Admin UI Regression & RBAC Completion (Admin UI 回歸修復與 RBAC 補完)"
description: "修復因 Phase 4.3 與 Phase 5 合併導致的 Admin UI 功能退化，並完成 Task Assignee ID 的最後一哩路。"
status: "Planned"
dependencies: ["Phase 4.3", "Phase 5.2"]
---

## 1. 背景與問題 (Context & Problem)

在 Phase 4.3 (Marketing Site) 與 Phase 5 (RBAC) 完成後，Admin UI (Port 3737) 出現了嚴重的回歸 (Regression)。雖然 End-User UI (Port 5173) 功能正常，但管理後台的核心功能癱瘓，且資料庫遷移 (Migration 007) 與程式碼實作脫鉤。

### 關鍵症狀 (Symptoms)
1.  **Ghost Upload**: Admin UI 上傳文件後無錯誤訊息，但文件未出現在列表中，RAG 處理流程未觸發。
2.  **RAG Status Red**: Admin UI 顯示 RAG 服務狀態為紅圈 (Disconnected)，但後端服務實際上是健康的。
3.  **Data Mismatch**: `migration/007` 雖然建立了 `assignee_id` 欄位，但後端 `TaskService` 與前端 `Task` 類型並未實作此欄位的讀寫，導致功能形同虛設。

## 2. 根因分析 (Root Cause Analysis)

### 2.1 Admin UI Auth 斷裂
*   **證據**: `knowledgeService.ts` (Commit `67a83e3`) 嘗試從 `localStorage.getItem('archon_token')` 獲取 Token。
*   **事實**: Supabase Auth 在 Admin UI 中使用的 Key 格式為 `sb-<project-ref>-auth-token`，而非 `archon_token`。
*   **後果**: 上傳請求未攜帶 Authorization Header -> 後端 `knowledge_api.py` 拒絕請求 (403/401) -> 前端因缺乏錯誤處理而靜默失敗。

### 2.2 RAG Health Check 權限誤殺
*   **證據**: 後端 API 引入了嚴格的 `Depends(get_current_user)`。
*   **事實**: Admin UI 的 Health Check 請求若未攜帶正確 Token，或使用了不被允許的角色 (如未正確傳遞 `system_admin`)，將被 Middleware 攔截。

### 2.3 Migration 007 孤兒化
*   **證據**: `task_service.py` 的 `create_task` 與 `update_task` 方法參數中完全沒有 `assignee_id`。
*   **事實**: 資料庫有欄位，但 API 層與 Service 層未對接。

## 3. 實作計畫 (Implementation Plan)

### Step 1: Admin UI Auth Client 修復 (Critical)
*   **目標**: 恢復 `knowledgeService.ts` 的 Token 獲取能力。
*   **行動**:
    *   重構 `knowledgeService.ts` 的 `uploadDocument` 方法。
    *   使用 `supabase.auth.session()?.access_token` 取代 `localStorage` 讀取，或引入 `useAuth` hook 的 Context。
    *   確保所有手動 Fetch 請求都正確注入 `Authorization: Bearer ...` Header。

### Step 2: Task Assignee ID 實作 (Backend & Frontend)
*   **目標**: 讓 Task 指派能真正寫入 `assignee_id`。
*   **行動**:
    *   **Backend**: 修改 `python/src/server/services/projects/task_service.py`，在 `create_task`, `update_task`, `list_tasks` 中加入 `assignee_id` 處理邏輯。
    *   **Frontend**: 更新 `archon-ui-main/src/features/projects/tasks/types/task.ts`，加入 `assignee_id` 欄位。

### Step 3: 文件同步
*   **目標**: 確保開發者手冊反映真實狀況。
*   **行動**: 更新 `CONTRIBUTING_tw.md`，加入 `migration/007` 說明。

## 4. 驗收標準 (Acceptance Criteria)

### 4.1 Admin UI (Port 3737)
- [ ] **RAG Status**: 進入 Knowledge 頁面，右上角 RAG 狀態顯示 **綠勾 (Connected)**。
- [ ] **Upload Success**: 上傳一個 `.md` 文件，進度條跑完後，列表 **立即顯示** 該文件。
- [ ] **API Header**: 在 Network Tab 檢查 `POST /api/documents/upload`，確認 Header 包含 `Authorization: Bearer eyJ...`。

### 4.2 Task Management
- [ ] **DB Write**: 在 Admin UI 建立一個指派給 "Alice" 的任務，查詢資料庫 `SELECT assignee_id FROM archon_tasks` 確認欄位非空。
- [ ] **Type Check**: 執行 `pnpm type-check` (或 build)，確認無 `assignee_id` 相關錯誤。

### 4.3 Documentation
- [ ] **Consistency**: `CONTRIBUTING_tw.md` 包含 `007` 的執行說明。
