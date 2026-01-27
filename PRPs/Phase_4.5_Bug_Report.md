# Phase 4.5 Bug & Gap Tracking Report (P4.5 缺陷與缺口追蹤表)

> **文件目的**: 集中管理 Phase 4.5 (System Institutionalization) 系統轉型過程中的已知問題、測試缺口 (Coverage Gaps) 與回歸錯誤 (Regressions)。
> **更新頻率**: 每日站會 (Daily Standup) 後更新。

---

## 📊 Summary Dashboard (摘要儀表板)

| Metric | Count | Details |
| :--- | :--- | :--- |
| **Total Issues** | 2 | Navbar RBAC & Test Data Persistence. |
| **Critical Gaps** | 1 | RBAC Visual Feedback (Navbar). |
| **Functional Bugs**| 1 | Test Data Leakage. |

---

## 🔍 Defect & Gap Tracking Table (缺陷追蹤詳表)

| ID | Type (類型) | Function (功能模組) | Description (問題描述) | Severity (嚴重度) | Status (狀態) | Assignee (負責人) | Trace (相關檔案) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-013** | 🐛 Bug | **UX/RBAC** | 所有角色 (Alice, Bob, Charlie) 在 5173 登入後看到的導覽列都完全相同 (Sidebar Role Filter Fail)。 | High | 🟢 Fixed (Implemented) | Frontend | `MainLayout.tsx`, `Sidebar.tsx` |
| **BUG-014** | 🐛 Bug | **Knowledge** | Knowledge Base (Supabase Studio Tests?) 充滿測試資料，需釐清資料來源與清理機制。 | Medium | 🟢 Fixed (Implemented) | Backend/QA | `tests/backend`, `test_supabase_interaction.py` |

---

## 📝 Detailed Investigation Notes (詳細調查筆記)

### BUG-013: Navbar RBAC Consistency (導覽列權限失效)
*   **Symptom**: 使用者回報 5173 (Frontend) 的每個角色看到的導覽列都一樣。
*   **Root Cause**: 
    1.  `usePermission.ts` 定義的 `leads:view:all` 權限被 Sales 和 Marketing 角色同時擁有。
    2.  `MainLayout.tsx` 的導覽連結 (Sales Intel / Brand Hub) 都只檢查這個通用權限，導致顯示重疊。
*   **Requirement**: 
    *   **Alice (Sales)**: 只能看到 **Sales Intel**。
    *   **Bob (Marketing)**: 只能看到 **Brand Hub**。
    *   **Charlie (Manager/PM)**: **必須能同時看到** Sales Intel 與 Brand Hub（跨部門管理權限）。
*   **Fix**: 
    1.  **Frontend**: 在 `usePermission.ts` 將權限拆解為 `leads:view:sales` 與 `leads:view:marketing`。
    2.  **Mapping**: 為 `manager` 與 `PM` 角色同時分配上述兩項權限。
    3.  **Layout**: 更新 `MainLayout.tsx`，讓連結對應到精準權限。

### BUG-014: Knowledge Base Test Data Leakage (測試資料殘留)
*   **Symptom**: Knowledge Base 充滿測試資料 (3737 knowledge base)。
*   **Root Cause**: 後端整合測試 (Integration Tests) 在執行資料庫寫入操作後，缺乏強制的清理機制 (Teardown)。如果測試失敗 (Assertion Error)，清理程式碼往往被跳過。
*   **Fix**: 
    1.  **Backend**: 在 `test_supabase_interaction.py` 中引入 `try...finally` 區塊，確保無論測試結果如何，`delete()` 清理指令都會執行。
    2.  **ID Strategy**: 使用固定的 UUID (`00000000-0000-0000-0000-000000000000`) 以便精確鎖定並刪除測試資料。

---

## 🛠 Fix Log (修復紀錄)

*   **2026-01-27**:
    *   **BUG-013 (RBAC)**: 完成前端權限拆分。驗證 Alice (Sales) 僅能看見 Sales Intel，Bob (Marketing) 僅能看見 Brand Hub。
    *   **BUG-013 (Systemic Fix)**: 發現 `init_db.py` 將 `seed_mock_data.sql` 視為一次性 Migration，導致後續修改或資料偏移無法被自動校正。已重構 `init_db.py` 使其實現「每次初始化皆強制執行 Seed」，確保所有開發者的角色 (Admin, Bob, Charlie) 永遠與種子資料對齊。
    *   **BUG-014 (Quality)**: 重構後端測試，加入 Robust Teardown 機制。經 `make test-be` 驗證，測試後資料庫無殘留污染。
