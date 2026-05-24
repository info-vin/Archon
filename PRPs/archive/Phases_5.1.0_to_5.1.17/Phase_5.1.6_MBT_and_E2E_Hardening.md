# Phase 5.1.6: MBT & E2E Testing Hardening (測試防護網物理硬化)

## Goal Description
為了解決在 Phase 5.1.5 查帳中發現的「測試斷層 (Locator Gap)」與「極端樂觀路徑偏差 (Optimistic Path Bias)」，本階段的目標是全面硬化 E2E 與 Model-Based Testing (MBT) 的防禦力。我們將確保測試套件不僅能驗證快樂路徑，還能物理抵抗網路中斷 (503/429)、確保空資料 (Empty States) 渲染不崩潰，並徹底清除剩餘 4 個 MBT 的脆弱選擇器債務。

## Proposed Changes (實體對帳版)

### 1. [Frontend Testing] 負面路徑與 503 防禦
*   **[MODIFY] [AdminPanelExhaustive.spec.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/tests/playwright/AdminPanelExhaustive.spec.ts)**:
    - 新增專屬的負面測試區塊：模擬 `/api/stats/system-overview` 等端點回傳 `503 Service Unavailable` 或發生 `Timeout`。
    - 斷言驗證：確保 UI 畫面會顯示紅色的 "System Offline" 或 "Probe Failed" 錯誤 Fallback 卡片，而非 React 白畫面崩潰。
    - 新增空資料 (Empty State) 測試：當 API 回傳 `active_agents: []` 或無 `daily_costs` 時，驗證 Recharts 圖表不會因為 `NaN` 座標引發 `TickItem Error` 崩潰。

### 2. [Frontend UI & Testing] MBT 定位器物理硬化 (`data-testid`)
*   **[MODIFY] [ApprovalsPage.tsx](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/src/pages/ApprovalsPage.tsx)**:
    - 補齊 `data-testid="approval-inbox-list"` 與 `data-testid="approve-action-button"`。
*   **[MODIFY] [ApprovalsPage.mbt.spec.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/tests/playwright/ApprovalsPage.mbt.spec.ts)**:
    - 全面改用 `page.getByTestId()` 替換脆弱的 CSS 文字與位置定位器。
*   **[MODIFY] 剩餘 3 個 MBT 腳本與對應元件**:
    - **ImagePicker**: 補齊 `data-testid="image-grid"` 與相應定位器。
    - **CorrectionAnalytics**: 硬化 Token 視覺對齊定位器。
    - **CitationTransparency**: 確保 Librarian 引用序號與 Hover 視窗具備專屬的 `data-testid`。

### 3. [Frontend Testing] Spinner 彈性防禦
*   **[MODIFY] [systemFixtures.ts](file:///Users/vincenta/GoogleKwok022/Archon/enduser-ui-fe/tests/playwright/fixtures/systemFixtures.ts)**:
    - 實體落地 `waitForSpinner(page)` 輔助工具，強制防禦 Subagent 或自動化測試在 SSE 非同步處理期間所遇到的「旋轉圈圈」死鎖超時。

## Verification Plan

### Automated Tests
1. **負面測試綠燈驗收**:
   - 執行 `npx playwright test AdminPanelExhaustive.spec.ts`，確認新增的 503 斷線處理與空資料測試一次性通過。
2. **硬化後 MBT 驗收**:
   - 執行 `npx playwright test ApprovalsPage.mbt.spec.ts`，確認在多次運行中定位器 100% 穩定，消除 Flaky 抖動。

### Manual Verification
- 使用 Chrome 觀察控制台，確保當 API Mock 斷開時，控制台捕獲的 Error 被 Playwright 的監聽器正確印出，且無 React 渲染的 Trace 溢出。
