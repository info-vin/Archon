# Phase 4.4 Bug & Gap Tracking Report (P4.4 缺陷與缺口追蹤表)

> **文件目的**: 集中管理 Phase 4.4 系統校正過程中的已知問題、測試缺口 (Coverage Gaps) 與回歸錯誤 (Regressions)。
> **更新頻率**: 每日站會 (Daily Standup) 後更新。

---

## 📊 Summary Dashboard (摘要儀表板)

| Metric | Count | Details |
| :--- | :--- | :--- |
| **Total Issues** | 9 | Current active tracked items |
| **Critical Gaps** | 2 | Missing E2E Coverage for core business flows |
| **Functional Bugs**| 5 | Blocking functional bugs reported by Alice/Team |

---

## 🔍 Defect & Gap Tracking Table (缺陷追蹤詳表)

| ID | Type (類型) | Function (功能模組) | Description (問題描述) | Severity (嚴重度) | Status (狀態) | Assignee (負責人) | Trace (相關檔案) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GAP-001** | 🧪 Test Gap | **Marketing** | 缺少 "Draft with AI" -> "Submit Review" 的 E2E 自動化測試。 | High | 🔴 Open | QA | `tests/e2e/content-marketing.spec.tsx` (Missing) |
| **GAP-002** | 🧪 Test Gap | **Approvals** | 管理員 "Approve" 動作僅有 API Mock，缺乏完整 UI 互動測試。 | Medium | 🔴 Open | QA | `tests/e2e/management.spec.tsx` |
| **BUG-001** | 🐛 Bug | **Project** | 無法在任何專案中新增 Task。 | High | 🔴 Open | Backend | `TaskService` / `Permission` |
| **BUG-002** | 🐛 Bug | **Project** | 點擊 `All Projects` 無顯示列表，需選單一專案才顯示 Dashboard。 | Medium | 🔴 Open | Frontend | `ProjectList` / `Route` |
| **BUG-003** | 🐛 Bug | **AI** | Task 點擊 `refine with AI` 無反應或未觸發 Agent 修正。 | High | 🔴 Open | Backend | `POBotService` / `TaskModal` |
| **BUG-004** | 🐛 Bug | **Sales** | Generate Pitch Modal 右下角按鈕顯示 `copy to clipboard` 而非 **"Approve & Save"**。 | Medium | 🔴 Open | Frontend | `PitchGeneratorModal` |
| **ENH-005** | ✨ Feature | **AI** | Pitch 需分英/中兩段顯示；AI Prompt 需顯示在卡片上方供參考。 | Low | 🔴 Open | AI/FE | `MarketBot` / `PitchCard` |
| **BUG-006** | 🐛 Bug | **Sales** | Leads 列表顯示正常，但 Alice 無法執行 Promote to Vendor。 | High | 🔴 Open | Backend | `LeadService` / `RBAC` |
| **BUG-007** | 💄 UI | **Global** | 5173 (End User UI) 夜間模式未全域套用。 | Low | 🔴 Open | Frontend | `ThemeContext` |
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

---

## 🛠 Fix Log (修復紀錄)

*   *(暫無修復紀錄)*
