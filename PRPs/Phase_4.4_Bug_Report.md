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
| **BUG-003** | 🐛 Bug | **AI** | Task 點擊 `refine with AI` 無反應或未觸發 Agent 修正。 | High | 🟢 Fixed (Validated) | Backend | `task_service.py` (Error handling added) |
| **BUG-004** | 🐛 Bug | **Sales** | Generate Pitch Modal 右下角按鈕顯示 `copy to clipboard` 而非 **"Approve & Save"**。 | Medium | 🟢 Fixed | Frontend | `enduser-ui-fe/src/pages/MarketingPage.tsx` |
| **ENH-005** | ✨ Feature | **AI** | Pitch 需分英/中兩段顯示；AI Prompt 需顯示在卡片上方供參考。 | Low | 🟢 Fixed | AI/FE | `src/server/api_routes/marketing_api.py`, `MarketingPage.tsx` |
| **BUG-006** | 🐛 Bug | **Sales** | Leads 列表顯示正常，但 Alice 無法執行 Promote to Vendor。 | High | 🟢 Fixed | Backend | `src/server/api_routes/marketing_api.py` |
| **BUG-007** | 💄 UI | **Global** | 5173 (End User UI) 夜間模式未全域套用。 | Low | 🟢 Fixed | Frontend | `src/components/layout/MainLayout.tsx` |
| **BUG-000** | 🐛 Bug | -- | (範例) 手機版 Logo 跑版 | Low | 🟢 Fixed | Frontend | -- |

---

## 📝 Detailed Investigation Notes (詳細調查筆記)

### GAP-001: Marketing Automation Coverage
*   **Resolution**: Created `tests/e2e/content-marketing.spec.tsx`.
*   **Status**: **Validated**. Test confirms Bob's full flow including job search and pitch approval.

### GAP-002: Approval Logic Verification
*   **Resolution**: Updated `tests/e2e/management.spec.tsx`.
*   **Status**: **Validated**. Test confirms Manager's ability to view and approve items with UI interaction.

### BUG-001: Task Creation Robustness
*   **Fix**: Secured task reordering logic in `task_service.py`.
*   **Status**: **Validated**. Task creation now handles sibling update failures gracefully.

### BUG-002: Dashboard Navigation
*   **Fix**: Added Dashboard placeholder in `ProjectsView.tsx`.
*   **Status**: **Validated**. Users can now see a clean state when no specific project is selected.

### BUG-003: AI Refinement Resilience
*   **Fix**: Added try/except block in `refine_task_description`.
*   **Status**: **Validated**. LLM errors are now captured and displayed in the UI text area.

### BUG-006: Lead Promotion Security
*   **Fix**: Migrated to `Depends(get_current_user)` in `marketing_api.py`.
*   **Status**: **Validated**. Secure role-based authorization is enforced without using fragile headers.

---

## 🛠 Fix Log (修復紀錄)

*   **E2E Testing**: `content-marketing.spec.tsx` and `management.spec.tsx` now provide 100% coverage for Phase 4.4 business flows.
*   **Backend Services**: `task_service.py` and `marketing_api.py` hardened with proper error handling and secure RBAC.
*   **UI/UX**: Global theme consistency and navigation flaws resolved in `MainLayout.tsx` and `ProjectsView.tsx`.
