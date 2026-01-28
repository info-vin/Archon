# Phase 4.5 Bug & Gap Tracking Report (P4.5 缺陷與缺口追蹤表)

> **文件目的**: 集中管理 Phase 4.5 (System Institutionalization) 系統轉型過程中的已知問題、測試缺口 (Coverage Gaps) 與回歸錯誤 (Regressions)。
> **更新頻率**: 每日站會 (Daily Standup) 後更新。

---

## 📊 Summary Dashboard (摘要儀表板)

| Metric | Count | Details |
| :--- | :--- | :--- |
| **Total Issues** | 7 | Navbar RBAC, Test Data, E2E Stability. |
| **Critical Gaps** | 0 | All critical regressions resolved. |
| **Functional Bugs**| 0 | All known functional bugs fixed. |

---

## 🔍 Defect & Gap Tracking Table (缺陷追蹤詳表)

| ID | Type (類型) | Function (功能模組) | Description (問題描述) | Severity (嚴重度) | Status (狀態) | Assignee (負責人) | Trace (相關檔案) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-013** | 🐛 Bug | **UX/RBAC** | 所有角色 (Alice, Bob, Charlie) 在 5173 登入後看到的導覽列都完全相同 (Sidebar Role Filter Fail)。 | High | 🟢 Fixed (Implemented) | Frontend | `MainLayout.tsx`, `Sidebar.tsx` |
| **BUG-014** | 🐛 Bug | **Knowledge** | Knowledge Base (Supabase Studio Tests?) 充滿測試資料，需釐清資料來源與清理機制。 | Medium | 🟢 Fixed (Implemented) | Backend/QA | `tests/backend`, `test_supabase_interaction.py` |
| **BUG-015** | 🐛 Regression | **QA/RBAC** | E2E 測試 Mock Data 過時，導致所有涉及 Sales/Marketing 頁面的測試判定為 Access Denied。 | Critical | 🟢 Fixed (Refactored) | QA | `tests/e2e/*.spec.tsx` |
| **BUG-016** | 🐛 Bug | **QA/Timing** | `task-persistence.spec.tsx` 頻繁出現 Loading 超時，需優化測試等待邏輯。 | Medium | 🟢 Fixed (Implemented) | QA | `task-persistence.spec.tsx` |
| **BUG-017** | 🐛 Regression | **QA/Setup** | `e2e.setup.tsx` 引用外部 Factory 導致 Vitest 提升錯誤 (ReferenceError)。 | Critical | 🟢 Fixed (Hoisted) | QA | `e2e.setup.tsx` |
| **BUG-018** | 🐛 Bug | **QA/Syntax** | `sales-intelligence.spec.tsx` 存在語法錯誤 (殘留字符 'n')。 | High | 🟢 Fixed (Corrected) | QA | `sales-intelligence.spec.tsx` |
| **BUG-019** | 🐛 Regression | **QA/Env** | JSDOM 不支援 `scrollIntoView`，導致測試執行中崩潰。 | Medium | 🟢 Fixed (Polyfilled) | QA | `e2e.setup.tsx` |

---

## 📝 Detailed Investigation Notes (詳細調查筆記)

### BUG-015 ~ 019: The Great E2E Refactoring
*   **Root Cause**: 測試資料與實作脫鉤 (Decoupled Truth) + 環境配置不足 + 語法/時序問題。
*   **Solution**: 
    1.  **Permission Factory**: 建立 `userFactory.ts` 並導出 `PERMISSION_SETS`，實現 SSOT。
    2.  **Hoisting Fix**: 使用 `vi.hoisted` 解決 `e2e.setup.tsx` 的引用順序問題。
    3.  **Environment**: 補齊 `scrollIntoView` Polyfill。
    4.  **Timing**: 優化 `waitFor` 邏輯。
*   **Outcome**: 測試套件現在具備「自動適應權限變更」的能力。

---

## ⚠️ Testing Strategy Constraints (測試策略限制)

*   **One-Shot Testing (只能測試一次)**: 
    *   由於測試環境或資源的限制（如 API Rate Limit, DB State Complexity），每個測試回合應被視為「單次機會」。
    *   **Action**: 在執行測試前，必須進行詳盡的靜態分析 (Static Analysis) 與代碼審查。測試失敗應被視為嚴重事件，需立即記錄並暫停，而非反覆重試。
    *   **Protocol**: Fail -> Log to Report -> Fix -> Verify Static -> Retry.

---

## 🛠 Fix Log (修復紀錄)

*   **2026-01-27**:
    *   **BUG-013 (RBAC)**: 完成前端權限拆分。
    *   **BUG-014 (Quality)**: 重構後端測試清理機制。
*   **2026-01-28**:
    *   **BUG-015~019 (QA Institutionalization)**: 完成 E2E 測試的全面重構，引入 `userFactory` 與 `vi.hoisted`，解決了魔術字串與提升錯誤，並修復了 JSDOM 環境缺口。