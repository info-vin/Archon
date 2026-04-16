# Phase 4.6.34: Workflow Self-Healing (工作流自癒與 UI 斷層修復)

## 1. 專案背景
根據 Phase 4.6.33 (Twin Scout v36) 的物理巡檢報告 (`report_20260409_082959.md`)，系統偵測到兩個關鍵的邏輯斷層。本階段旨在根據診斷結果進行精準修復。

## 2. 修復目標 (Corrective Actions)

### 34.1 [BUG] Bob (Marketing) RBAC 權限過嚴修復
- **現象**: Bob 登入 `/marketing` 頁面顯示 `Access Denied: leads:view:sales`。
- **原因**: `/marketing` 頁面的 `PermissionGuard` 誤用了 Alice 的專屬權限 `leads:view:sales`，而非 Bob 的 `leads:view:all` 或 `brand:manage`。
- **物理對齊**: 🟢 已修正 `MarketingPage.tsx` 與 `MainLayout.tsx` 中的權限掛載為 `leads:view:all`。

### 34.2 [BUG] Alice (Sales) 任務列表加載死鎖
- **現象**: DB 顯示 Alice 有 0 筆任務，但 UI 呈現無限 `Loading tasks...`。
- **原因**: 前端 `TaskContainer` (DashboardPage) 在處理 API 空響應時未正確切換至 `EmptyState`。
- **物理對齊**: 🟢 已修正 `DashboardPage.tsx` 邏輯，引入並顯示 `EmptyState`。

## 3. 驗證基準
1. **複檢**: 執行 `make twin-scout`，預期結論變更為 `WORKFLOW_SUCCESS`。
2. **代謝**: 確認修復後的綠色報告能正常被代謝機制覆蓋。
