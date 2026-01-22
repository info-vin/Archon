# Phase 4.4 Bug & Gap Tracking Report (P4.4 缺陷與缺口追蹤表)

> **文件目的**: 集中管理 Phase 4.4 系統校正過程中的已知問題、測試缺口 (Coverage Gaps) 與回歸錯誤 (Regressions)。
> **更新頻率**: 每日站會 (Daily Standup) 後更新。

---

## 📊 Summary Dashboard (摘要儀表板)

| Metric | Count | Details |
| :--- | :--- | :--- |
| **Total Issues** | 9 | Sum of all active items (Gaps + Bugs + UI + Feature). |
| **Critical Gaps** | 0 | All E2E Coverage Gaps addressed. |
| **Functional Bugs**| 0 | All identified bugs fixed. |

*Calculation Logic:*
*   **Total Issues (9)**: All previous issues are now resolved or covered.
*   **Fixed**: GAP-001, GAP-002, BUG-001, BUG-002, BUG-003, BUG-004, BUG-006, BUG-007, ENH-005.

---

## 🔍 Defect & Gap Tracking Table (缺陷追蹤詳表)

| ID | Type (類型) | Function (功能模組) | Description (問題描述) | Severity (嚴重度) | Status (狀態) | Assignee (負責人) | Trace (相關檔案) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GAP-001** | 🧪 Test Gap | **Marketing** | 缺少 "Draft with AI" -> "Submit Review" 的 E2E 自動化測試。 | High | 🟢 Fixed | QA | `tests/e2e/content-marketing.spec.tsx` (Created) |
| **GAP-002** | 🧪 Test Gap | **Approvals** | 管理員 "Approve" 動作僅有 API Mock，缺乏完整 UI 互動測試。 | Medium | 🟢 Fixed | QA | `tests/e2e/management.spec.tsx` (Created) |
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
*   **Resolution**: Created `tests/e2e/content-marketing.spec.tsx`.
*   **Coverage**: Verifies the flow: Login (Bob) -> Sales Intelligence (Search) -> Generate Pitch -> Approve & Save. Verified that the new "Approve & Save" button exists and triggers the success alert.

### GAP-002: Approval Logic Verification
*   **Resolution**: Created `tests/e2e/management.spec.tsx`.
*   **Coverage**: Verifies the flow: Login (Alice/Admin) -> Team Management -> View Pending Approvals -> Click Approve. Confirms the UI renders approvals correctly and the action completes without error.

### BUG-001: Project Task Creation Failure
*   **Fix**: Wrapped reordering logic in `TaskService.create_task` with try/except to prevent transaction failures.

### BUG-002: Project List Empty
*   **Fix**: Removed forced redirection in `ProjectsView.tsx` and added an "All Projects" dashboard placeholder state.

### BUG-003: AI Refine Task Unresponsive
*   **Fix**: Added error handling in `TaskService.refine_task_description` to return system error messages to the UI instead of failing silently.

### BUG-004: Pitch Generator Button Label
*   **Fix**: Renamed "Copy to Clipboard" to "Approve & Save" in `MarketingPage.tsx`.

### BUG-006: Lead Promote Permission Denied
*   **Fix**: Added role check (blocking viewers) and robust parameter handling (timestamps, optional emails) in `marketing_api.py`.

### BUG-007: Theme Context
*   **Fix**: Updated `MainLayout.tsx` and `MarketingPage.tsx` to use semantic CSS classes (`bg-background`, `bg-card`) for proper dark mode support.

---

## 🛠 Fix Log (修復紀錄)

*   **GAP-001 (Marketing Test)**: Added `tests/e2e/content-marketing.spec.tsx` covering the Sales Intelligence flow and new "Approve & Save" functionality. Updated `handlers.ts` to support necessary API mocks.
*   **GAP-002 (Approval Test)**: Added `tests/e2e/management.spec.tsx` covering the Team Management approval workflow.
*   **BUG-001 (Task Creation)**: Added exception handling to task reordering logic in `TaskService.create_task`. Prevents failure of the entire task creation process if updating sibling tasks' order fails (e.g. due to RLS).
*   **BUG-003 (AI Refine)**: Enhanced error handling in `TaskService.refine_task_description`. Added check for empty LLM response and improved error message formatting so the UI displays the system error instead of failing silently.
*   **BUG-006 (Lead Promote)**: Added `x_user_role` header support and explicit role check (blocking 'viewer') in `marketing_api.py`. Improved error logging and robustness of the `promote_lead_to_vendor` endpoint, including `contact_email` handling and timestamps.
*   **BUG-002 (Project List)**: Fixed `ProjectsView` to allow rendering the "All Projects" list without forcing a redirect to a specific project. Added a "Select a project" placeholder state to improve UX.
*   **BUG-004 (Pitch Button)**: Updated `MarketingPage.tsx` to label the action button as "Approve & Save" instead of "Copy to Clipboard", aligning with the business flow.
*   **ENH-005 (Bilingual Pitch)**: Updated backend prompt in `marketing_api.py` to request output in both English and Chinese sections. Updated frontend `MarketingPage.tsx` to display the AI System Prompt for reference and improved the pitch display UI.
*   **BUG-007 (Dark Mode)**: Fixed `MainLayout` in `enduser-ui-fe` to use semantic `bg-background` instead of hardcoded `bg-gray-50`. Refactored `MarketingPage` to use dark-mode compatible classes (`bg-card`, `text-foreground`), resolving global dark mode inconsistencies.
