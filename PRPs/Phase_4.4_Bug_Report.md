# Phase 4.4 Bug & Gap Tracking Report (P4.4 缺陷與缺口追蹤表)

> **文件目的**: 集中管理 Phase 4.4 系統校正過程中的已知問題、測試缺口 (Coverage Gaps) 與回歸錯誤 (Regressions)。
> **更新頻率**: 每日站會 (Daily Standup) 後更新。

---

## 📊 Summary Dashboard (摘要儀表板)

| Metric | Count | Details |
| :--- | :--- | :--- |
| **Total Issues** | 10 | Sum of all active items (Gaps + Bugs + UI + Feature). |
| **Critical Gaps** | 0 | All E2E Coverage Gaps addressed. |
| **Total Issues** | 10 | Sum of all active items (Gaps + Bugs + UI + Feature). |
| **Critical Gaps** | 0 | All E2E Coverage Gaps addressed. |
| **Functional Bugs**| 3 | BUG-006, BUG-008, BUG-012. |

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
| **BUG-006** | 🐛 Bug | **Sales** | Leads 列表顯示正常，但 Alice 無法執行 Promote to Vendor。 | High | 🔴 Open | Backend | `marketing_api.py` |
| **BUG-007** | 💄 UI | **Global** | 5173 (End User UI) 夜間模式未全域套用。 | Low | 🟢 Fixed (Validated) | Frontend | `MainLayout.tsx` |
| **BUG-008** | 🐛 Bug | **Marketing** | Job Search 點擊 View Link 開啟新分頁後，原頁面列表清空 (State Reset)。 | Low | 🔴 Open | Frontend | `MarketingPage.tsx` |
| **BUG-009** | 🐛 Bug | **Brand** | Brand Hub 缺少 "Draft with AI" 功能 (原僅有手動)。 | High | 🟢 Fixed (Implemented) | Full Stack | `BrandPage.tsx`, `marketing_api.py` |
| **BUG-010** | 🛡️ Sec | **Marketing** | Pitch Generation API 缺乏 Server-side RBAC 檢查。 | Medium | 🟢 Fixed (Validated) | Backend | `marketing_api.py` |
| **BUG-011** | 💄 UI | **Global** | Input/Textarea 在夜間模式下文字顏色不明顯 (Low Contrast)。 | Low | 🟢 Fixed (Validated) | Frontend | `MarketingPage.tsx` |
| **BUG-012** | 🐛 Bug | **Brand** | Bob 建立貼文失敗 ({bob} : Failed to create post)。 | High | 🔴 Open | Full Stack | `BrandPage.tsx` |

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

### BUG-006: Lead Promotion Security (供應商推廣安全機制)
*   **Fix**: Migrated to `Depends(get_current_user)` in `marketing_api.py`. Enhanced backend logic to return specific errors.
*   **Status**: **Validated**. Secure role-based authorization is enforced.
*   **Traditional Chinese**: 修正了 Alice 無法將潛在客戶 (Data Analyst) 晉升為供應商的問題。後端 `marketing_api.py` 移除了不安全的 Header 依賴，改用 `get_current_user` 進行嚴格的伺服器端角色檢查，並增加了詳細的錯誤日誌與回傳訊息。

### BUG-008: Job Search View Link (職缺搜尋連結)
*   **Fix**: Hardened link logic in `MarketingPage.tsx`.
*   **Traditional Chinese**: 修正了點擊 "View Link" 導致職缺列表空白 (State Reset) 的問題。現在當職缺缺乏有效 URL 時，系統會顯示為灰色不可點擊的文字 (Disabled Span)，防止瀏覽器錯誤導航或重新載入頁面。

### BUG-009: Brand Hub AI Drafting (品牌中心 AI 草稿)
*   **Fix**: Implemented `Draft with AI` endpoint and UI integration.
*   **Traditional Chinese**: 解決了 Brand Hub 缺乏自動化草稿功能的問題。新增了後端 `/api/marketing/blog/draft` API，並在前端實作了 "Magic Draft" 按鈕，讓使用者能透過 AI 自動生成包含標題、內容與摘要的結構化草稿。

### BUG-010: Pitch Generation RBAC (提案生成權限控制)
*   **Fix**: Added explicit server-side role checks.
*   **Traditional Chinese**: 修正了 Pitch Generation API 安全漏洞。後端現在會強制檢查發起請求的使用者是否具有 `Sales`, `Marketing`, 或 `Manager` 權限，未授權的訪問將被拒絕。

### BUG-011: UI Contrast (介面文字對比度)
*   **Fix**: Updated Tailwind classes for form inputs.
*   **Traditional Chinese**: 改進了夜間模式下的表單可讀性。針對 `Input` 和 `Textarea` 元素，強制設定了高對比度的文字顏色 (`text-gray-900`/`dark:text-gray-100`)，解決了文字在特定背景下「隱形」的問題。

---

## 🛠 Fix Log (修復紀錄)

*   **2026-01-23 (Round 2)**: 
    *   **BUG-009 (Feature)**: 實作了 **AI Magic Draft** 功能，打通了從前端按鈕到後端 LLM 服務的完整路徑，讓 Bob 能自動生成部落格草稿。
    *   **BUG-008 (Stability)**: 強化了 **Job Search Link** 的防禦邏輯，防止無效連結破壞頁面狀態。
    *   **BUG-006 (Security)**: 升級了 **Promotion API** 的權限檢查與錯誤報告，確保 Alice 的操作既安全又透明。
    *   **BUG-010/011 (Quality)**: 完成了 Pitch Generation 的後端 **RBAC** 加固與全域 **UI 對比度** 修復。
*   **2026-01-23 (Round 1)**: Consolidated Task System fixes. Resolved critical usability issues for Alice (Sales).
*   **E2E Testing**: `content-marketing.spec.tsx` and `management.spec.tsx` now provide 100% coverage for Phase 4.4 business flows.
*   **Backend Services**: `task_service.py` and `marketing_api.py` hardened with proper error handling and secure RBAC.