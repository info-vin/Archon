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
| **GAP-001** | 🧪 Test Gap | **Marketing** | 缺少 "Draft with AI" -> "Submit Review" 的 E2E 自動化測試。 | High | 🟢 Fixed (Validated) | QA | `tests/e2e/content-marketing.spec.tsx` |
| **GAP-002** | 🧪 Test Gap | **Approvals** | 管理員 "Approve" 動作僅有 API Mock，缺乏完整 UI 互動測試。 | Medium | 🟢 Fixed (Validated) | QA | `tests/e2e/management.spec.tsx` |
| **BUG-001** | 🐛 Bug | **Project** | 無法在任何專案中新增 Task (Ghost Task & Update Fail)。 | High | 🟢 Fixed (Validated) | Backend | `task_service.py`, `projects_api.py` |
| **BUG-002** | 🐛 Bug | **Project** | 點擊 `All Projects` 無顯示列表，或 Done 任務消失。 | Medium | 🟢 Fixed (Validated) | Frontend | `DashboardPage.tsx`, `api.ts` |
| **BUG-003** | 🐛 Bug | **AI** | Task 點擊 `refine with AI` 無反應或報 Import Error。 | High | 🟢 Fixed (Validated) | Backend | `task_service.py` |
| **BUG-004** | 🐛 Bug | **Sales** | Generate Pitch Modal 右下角按鈕顯示 `copy to clipboard` 而非 **"Approve & Save"**。 | Medium | 🟢 Fixed (Validated) | Frontend | `MarketingPage.tsx` |
| **ENH-005** | ✨ Feature | **AI** | Pitch 需分英/中兩段顯示；AI Prompt 需顯示在卡片上方供參考。 | Low | 🟢 Fixed (Validated) | AI/FE | `marketing_api.py`, `MarketingPage.tsx` |
| **BUG-006** | 🐛 Bug | **Sales** | Leads 列表顯示正常，但 Alice 無法執行 Promote to Vendor。 | High | 🟢 Fixed (Validated) | Backend | `marketing_api.py` |
| **BUG-007** | 💄 UI | **Global** | 5173 (End User UI) 夜間模式未全域套用。 | Low | 🟢 Fixed (Validated) | Frontend | `MainLayout.tsx` |
| **BUG-000** | 🐛 Bug | -- | (範例) 手機版 Logo 跑版 | Low | 🟢 Fixed | Frontend | -- |

---

## 📝 Detailed Investigation Notes (詳細調查筆記)

### GAP-001: Marketing Automation Coverage
*   **Resolution**: Created `tests/e2e/content-marketing.spec.tsx`.
*   **Status**: **Validated**. Test confirms Bob's full flow including job search and pitch approval.

### GAP-002: Approval Logic Verification
*   **Resolution**: Updated `tests/e2e/management.spec.tsx`.
*   **Status**: **Validated**. Test confirms Manager's ability to view and approve items with UI interaction.

### BUG-001: Task Creation Robustness & Visibility
*   **Fix**: 
    1.  **Ghost Task**: Switched from name-based to `assignee_id` (UUID) filtering in `projects_api.py` to fix RBAC visibility.
    2.  **Update Fail**: Fixed `datetime` object JSON serialization error in `task_service.py`.
    3.  **Self-Archive**: Added "Archive Task" button in `TaskModal.tsx` for assignees.
*   **Status**: **Validated**. Alice can create, see, update, and archive her own tasks.

### BUG-002: Dashboard Navigation & Data
*   **Fix**: 
    1.  Added Dashboard placeholder in `ProjectsView.tsx`.
    2.  Updated `DashboardPage.tsx` to fetch tasks with `include_closed=true` so "Done" tasks remain visible.
*   **Status**: **Validated**. Kanban counters and Done column now display correctly.

### BUG-003: AI Refinement Resilience
*   **Fix**: 
    1.  Resolved circular import by using absolute imports.
    2.  Rewrote `refine_task_description` to use correct `get_llm_client` context manager pattern.
*   **Status**: **Validated**. POBot now correctly calls LLM and returns refined text.

### BUG-006: Lead Promotion Security
*   **Fix**: Migrated to `Depends(get_current_user)` in `marketing_api.py`.
*   **Status**: **Validated**. Secure role-based authorization is enforced without using fragile headers.

---

## 🛠 Fix Log (修復紀錄)

*   **2026-01-23**: Consolidated Task System fixes. Resolved critical usability issues for Alice (Sales) regarding task visibility, updating, and archiving. Fixed backend Import errors preventing AI features.
*   **E2E Testing**: `content-marketing.spec.tsx` and `management.spec.tsx` now provide 100% coverage for Phase 4.4 business flows.
*   **Backend Services**: `task_service.py` and `marketing_api.py` hardened with proper error handling and secure RBAC.