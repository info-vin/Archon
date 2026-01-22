# Phase 4.4 Bug & Gap Tracking Report (P4.4 缺陷與缺口追蹤表)

> **文件目的**: 集中管理 Phase 4.4 系統校正過程中的已知問題、測試缺口 (Coverage Gaps) 與回歸錯誤 (Regressions)。
> **更新頻率**: 每日站會 (Daily Standup) 後更新。

---

## 📊 Summary Dashboard (摘要儀表板)

| Metric | Count | Details |
| :--- | :--- | :--- |
| **Total Issues** | 9 | Sum of all active items (Gaps + Bugs + UI + Feature). |
| **Critical Gaps** | 2 | Missing E2E Coverage for core business flows (Type=Test Gap). |
| **Functional Bugs**| 5 | Functional bugs (Type=Bug) excluding UI issues. |

*Calculation Logic:*
*   **Total Issues (9)**: 2 Gaps + 5 Functional Bugs + 1 UI Bug + 1 Feature.
*   **Critical Gaps (2)**: GAP-001, GAP-002.
*   **Functional Bugs (5)**: BUG-001, BUG-002, BUG-003, BUG-004, BUG-006.

---

## 🔍 Defect & Gap Tracking Table (缺陷追蹤詳表)

| ID | Type (類型) | Function (功能模組) | Description (問題描述) | Severity (嚴重度) | Status (狀態) | Assignee (負責人) | Trace (相關檔案) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GAP-001** | 🧪 Test Gap | **Marketing** | 缺少 "Draft with AI" -> "Submit Review" 的 E2E 自動化測試。 | High | 🔴 Open | QA | `tests/e2e/content-marketing.spec.tsx` (Missing) |
| **GAP-002** | 🧪 Test Gap | **Approvals** | 管理員 "Approve" 動作僅有 API Mock，缺乏完整 UI 互動測試。 | Medium | 🔴 Open | QA | `tests/e2e/management.spec.tsx` |
| **BUG-001** | 🐛 Bug | **Project** | 無法在任何專案中新增 Task。 | High | 🟢 Fixed | Backend | `src/server/services/projects/task_service.py` |
| **BUG-002** | 🐛 Bug | **Project** | 點擊 `All Projects` 無顯示列表，需選單一專案才顯示 Dashboard。 | Medium | 🟢 Fixed | Frontend | `src/features/projects/views/ProjectsView.tsx` |
| **BUG-003** | 🐛 Bug | **AI** | Task 點擊 `refine with AI` 無反應或未觸發 Agent 修正。 | High | 🟢 Fixed | Backend | `src/server/services/projects/task_service.py` |
| **BUG-004** | 🐛 Bug | **Sales** | Generate Pitch Modal 右下角按鈕顯示 `copy to clipboard` 而非 **"Approve & Save"**。 | Medium | 🟢 Fixed | Frontend | `enduser-ui-fe/src/pages/MarketingPage.tsx` |
| **ENH-005** | ✨ Feature | **AI** | Pitch 需分英/中兩段顯示；AI Prompt 需顯示在卡片上方供參考。 | Low | 🟢 Fixed | AI/FE | `src/server/api_routes/marketing_api.py`, `MarketingPage.tsx` |
| **BUG-006** | 🐛 Bug | **Sales** | Leads 列表顯示正常，但 Alice 無法執行 Promote to Vendor。 | High | 🟢 Fixed | Backend | `src/server/api_routes/marketing_api.py` |
| **BUG-007** | 💄 UI | **Global** | 5173 (End User UI) 夜間模式未全域套用。 | Low | 🟢 Fixed | Frontend | `src/components/layout/MainLayout.tsx` |
| **BUG-000** | 🐛 Bug | -- | (範例) 手機版 Logo 跑版 | Low | 🟢 Fixed | Frontend | -- |

---

## 📝 Detailed Investigation Notes (詳細調查筆記)

### GAP-001: Marketing Automation Coverage
*   **現狀**: 目前 `sales-intelligence.spec.tsx` 只測到了「情蒐」。
*   **缺口**: Bob (Marketing) 的工作流完全沒有 E2E 保護。若後端 `ContentService` 改動，可能導致前台 "Draft with AI" 靜默失敗。
*   **建議行動**: 建立新測試檔 `content-marketing.spec.tsx`，模擬 Bob 登入 -> 生成 -> 提交的完整路徑。

### GAP-002: Approval Logic Verification
*   **現狀**: `management.spec.tsx` 側重於 "Refine Task"，對於 "Approve Blog/Lead" 的邏輯依賴 Mock 回傳。
*   **風險**: 若前端 `ApprovalsWidget` 的 API 呼叫路徑錯誤 (e.g., 拼錯 URL)，目前的測試無法抓出（因為它是 Mock Response）。
*   **建議行動**: 在 E2E 中加入真實的點擊互動，並驗證畫面上的項目是否正確消失 (Optimistic UI Update)。

### BUG-001: Project Task Creation Failure
*   **Investigation**:
    *   Trace: `python/src/server/services/projects/task_service.py`
    *   Logic: `create_task` method performs several validations (title, project_id, assignee) before inserting into `archon_tasks`.
    *   Potential Cause: The issue "Unable to add task in any project" suggests a critical failure in the validation logic or database schema. The code relies on `get_supabase_client()` which typically uses the service key. If the table schema has changed (e.g., new required columns without defaults) or if the `validate_assignee` check is too strict (expecting "User" but receiving "Alice"), it fails.
    *   Action: Verify schema match and relax validation or fix frontend payload.

### BUG-002: Project List Empty
*   **Investigation**:
    *   Trace: `archon-ui-main/src/features/projects/components/ProjectList.tsx`
    *   Logic: The component likely fetches projects but might be failing to render them if the API response format changed or if the `useProjects` hook is broken.
    *   Action: Check API response vs Component expectation.

### BUG-003: AI Refine Task Unresponsive
*   **Investigation**:
    *   Trace: `python/src/server/services/projects/task_service.py` (Method: `refine_task_description`)
    *   Logic: The method calls `RAGService` and `llm_provider_service`.
    *   Potential Cause: The `refine_task_description` method imports `llm_provider_service` *inside* the function. If there's an import error or if the LLM provider configuration is missing/invalid, it catches the exception and returns the original description with an error note, which might look like "no reaction" to the user if the UI doesn't display the error note prominently.
    *   Action: Ensure LLM service is correctly configured and error propagation is clear.

### BUG-004: Pitch Generator Button Label
*   **Investigation**:
    *   Trace: Frontend Modal Component (likely `PitchGeneratorModal` or `TaskModal` variant).
    *   Logic: The UI shows "Copy to Clipboard" instead of "Approve & Save". This is a state/logic error in the React component where it stays in "Generated" mode instead of offering the "Save" action.
    *   Action: Update UI logic to show the correct primary action button.

### BUG-006: Lead Promote Permission Denied
*   **Investigation**:
    *   Trace: `python/src/server/api_routes/marketing_api.py` (Endpoint: `/leads/{lead_id}/promote`)
    *   Logic: The endpoint `promote_lead_to_vendor` calls `supabase.table("vendors").insert(...)`.
    *   Potential Cause: The code uses `get_supabase_client()`, which usually returns the admin client. However, if RLS is enforced and the client is somehow context-aware (or if the `vendors` table has strict policies), the operation fails. The endpoint does *not* explicitly check `RBACService` permissions for the user. It implicitly relies on the ability to hit the endpoint. If Alice gets a 403, it might be an API Gateway/Middleware issue or simply that the UI disables the button based on a frontend permission check that is out of sync with backend capabilities.
    *   Action: Add explicit RBAC check or fix RLS policies.

### BUG-007: Theme Context
*   **Investigation**:
    *   Trace: `src/contexts/ThemeContext.tsx`
    *   Logic: `useEffect` might not be persisting the theme preference to `localStorage` or `document.documentElement` correctly across all routes (especially hash routes).
    *   Action: Fix Context Provider.

---

## 🛠 Fix Log (修復紀錄)

*   **BUG-001 (Task Creation)**: Added exception handling to task reordering logic in `TaskService.create_task`. Prevents failure of the entire task creation process if updating sibling tasks' order fails (e.g. due to RLS).
*   **BUG-003 (AI Refine)**: Enhanced error handling in `TaskService.refine_task_description`. Added check for empty LLM response and improved error message formatting so the UI displays the system error instead of failing silently.
*   **BUG-006 (Lead Promote)**: Added `x_user_role` header support and explicit role check (blocking 'viewer') in `marketing_api.py`. Improved error logging and robustness of the `promote_lead_to_vendor` endpoint, including `contact_email` handling and timestamps.
*   **BUG-002 (Project List)**: Fixed `ProjectsView` to allow rendering the "All Projects" list without forcing a redirect to a specific project. Added a "Select a project" placeholder state to improve UX.
*   **BUG-004 (Pitch Button)**: Updated `MarketingPage.tsx` to label the action button as "Approve & Save" instead of "Copy to Clipboard", aligning with the business flow.
*   **ENH-005 (Bilingual Pitch)**: Updated backend prompt in `marketing_api.py` to request output in both English and Chinese sections. Updated frontend `MarketingPage.tsx` to display the AI System Prompt for reference and improved the pitch display UI.
*   **BUG-007 (Dark Mode)**: Fixed `MainLayout` in `enduser-ui-fe` to use semantic `bg-background` instead of hardcoded `bg-gray-50`. Refactored `MarketingPage` to use dark-mode compatible classes (`bg-card`, `text-foreground`), resolving global dark mode inconsistencies.
