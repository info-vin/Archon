# Phase 5.1.2: MBT Hardening (深度加固 MBT 測試 - 實戰修復版)

## Goal Description
延續 Phase 5.1.1 的 SSE 被動化重構，本階段目標是解決 MBT 在真實 Docker 環境下遇到的「語意落差」與「物理不穩定性」。我們將透過 TestID 硬化定位器、引入 Spinner 彈性等待機制，並補齊對 SSE 斷線與網路錯誤 (503/429) 的日誌驗證邏輯。

## User Review Required

> [!IMPORTANT]
> **定位器策略變更**: 為了避免 Subagent 或 Playwright 在 UI 更新時失去目標，我們將在生產代碼中引入 `data-testid`。這會增加少量的代碼體積，但能保證 MBT 的絕對穩定。
> **日誌對帳 (Log Audit)**: 測試將不僅檢查 UI，還會檢查瀏覽器 Console 是否出現 `VITE PROXY ERROR`，這將作為 MBT 失敗的硬性指標。

## 4.6.54 技術債對帳與 Bug 分析 (Physical Audit)

### 🚨 關鍵發現：條件渲染導致的「幽靈元素」 (Conditional Unmounting Bug)
在 2026-05-16 的 Alice 流程驗證中發現，原本預期的 `await expect(magicDraftBtn).toBeEnabled()` 會因超時失敗。
*   **根源**: `SalesCartPage.tsx` 將 Batch Action Bar 包裹在 `{selectedIds.size > 0}` 中。當 Magic Draft 任務完成（SSE `done`），狀態機自動清空選擇，導致 UI 立即卸載 (Unmount) 了按鈕。
*   **對策**: MBT 斷言必須對齊產品生命週期。對於「動作完成即隱藏」的 UI，應改用 `expect(btn).not.toBeVisible()`。

### 📊 全量 MBT 盤點 (Global MBT Audit)
目前系統共有 7 個核心 MBT，除已完成加固的 3 個外，剩餘 4 個均存在「定位器脆弱」與「缺乏 Spinner 防禦」的問題：
1.  **[x] PersonaWorkflow** (Alice -> Bob -> Charlie)
2.  **[x] TaskAssignment** (Crawler/Agent Dispatch)
3.  **[x] PromptManagement** (Visual/Diff View) - Hardened in Phase 5.1.1
4.  **[x] ApprovalsPage** (Manager Inbox)
5.  **[x] ImagePicker** (Asset Selection)
6.  **[x] CorrectionAnalytics** (Token Usage)
7.  **[x] CitationTransparency** (RAG Refs)

### 🧱 實體環境與 Schema 技術債 (Environment & Schema Debt)
在 5.1.3 啟動前夕偵得的底層阻塞：
*   **[CRITICAL] 容器環境殘缺**: `archon-server` 容器未安裝 `git`，導致 L2 `CodeModifier` 呼叫失敗。必須更新 `Dockerfile`。
*   **[BLOCKER] 混合 ID 陷阱**: `auth.users` 與 `proposed_changes` 外鍵強綁定 UUID，但 `profiles` 卻使用簡化 ID ('1', '2', '3')。需統一物理 ID 策略。

## Proposed Changes

### [Frontend UI] enduser-ui-fe/src/
#### [MODIFY] [SalesCartPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/SalesCartPage.tsx)
- 為「Magic Draft」按鈕新增 `data-testid="magic-draft-button"`。
- 為購物車列表新增 `data-testid="sales-cart-list"`。

### [Frontend Testing] enduser-ui-fe/tests/playwright/
#### [MODIFY] [systemFixtures.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/tests/playwright/fixtures/systemFixtures.ts)
- 新增 `waitForSpinner(page)` helper，解決 Subagent 遇到的「旋轉迴圈」導致的測試中斷。
- 強化 `simulateSSEUpdate` 支援隨機延遲，模擬真實網路抖動。

#### [MODIFY] [PersonaWorkflow.mbt.spec.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/tests/playwright/PersonaWorkflow.mbt.spec.ts)
- **導航硬化**: 修正 Alice 流程，加入從 `Sales Intel` 導航至 `Sales Cart` 的顯式等待。
- **定位器更新**: 全面改用 `page.getByTestId()`。
- **日誌檢查**: 在 `afterEach` 加入對控制台錯誤日誌的掃描，確保沒有隱藏的 Proxy 錯誤。

## Verification Plan

### Automated Tests
- 執行 `npx playwright test PersonaWorkflow.mbt.spec.ts`。
- **負面測試**: 故意關閉後端服務，驗證 MBT 是否能正確回報 `ERR_CONNECTION_REFUSED` 並在日誌中體現。

### Manual Verification (Antigravity)
- 使用 Browser Subagent 執行 `final_sse_verify` 任務，驗證在引入 TestID 後，AI 是否能更精準地操作 UI。
