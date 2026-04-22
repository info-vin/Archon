# Phase 4.6.44: 測試物理隔離與 Baseline 全量恢復

> **目標 (Goal)**: 徹底根除 E2E 測試中的「狀態污染 (Test Pollution)」，確保全量測試 (100% Pass) 的穩定性與 Baseline 的物理完整性。

## 1. 現狀診斷 (Physical Audit: 2026-04-21)

經過物理穿透掃描，確認導致測試失敗的數據斷層如下：

1.  **物件引用洩漏 (Reference Leak)**:
    - **檔案**: `e2e.setup.tsx`
    - **數據證明**: `MOCK_ADMIN_USER` 為共享對象，測試修改其屬性後未 Teardown，導致級聯污染。
2.  **環境初始化競爭 (Race Condition)**:
    - **檔案**: `App.tsx` (L39), `ThemeToggle.tsx` (L13)
    - **數據證明**: `window.matchMedia` 在模組解析階段被呼叫時為 `undefined`，引發 React 渲染樹根部崩潰。
3.  **數據鏈路斷裂 (Data Chain Breach)**:
    - **檔案**: `useDashboardLogic.ts`
    - **數據證明**: API 返回 `undefined` 導致 `forEach` 與 `map` 崩潰，主因是 Mock 數據與實體代碼欄位不對位（`full_name` vs `name`）。
4.  **標籤與選取器歧義 (Selector Collision)**:
    - **檔案**: `admin-workflows.spec.tsx`
    - **數據證明**: 測試腳本 `/Add User/i` 與實體代碼 `NEW USER` 標籤不符。

## 2. 實施路徑 (Execution Plan)

### [Phase 1] 環境與物件隔離 (Isolation)
- [ ] **Task 1: 物件深拷貝 (Deep Clone)**
    - 修改 `e2e.setup.tsx`，每次 `renderApp` 時物理執行 `structuredClone(MOCK_ADMIN_USER)`。
- [ ] **Task 2: 環境硬化 (Environment Hardening)**
    - 將 `matchMedia` Polyfill 固定在 `e2e.setup.tsx` 所有匯入後的第一行，確保全域對象就緒。

### [Phase 2] 數據歸一與防禦 (Data Consistency)
- [ ] **Task 3: Mock 歸一化**
    - 徹底對位 `e2e.setup.tsx` 與後端模型，將所有姓名欄位統一為 `name`。
    - 為核心 API (`getTasks`, `getProjects`) 提供不准為空的回傳保證。
- [ ] **Task 4: 組件防禦性落地**
    - 物理保留對 `ThemeToggle` 與 `DashboardPage` 的 Null-check，對抗 JSDOM 的不穩定性。

### [Phase 3] 測試對位 (Alignment)
- [ ] **Task 5: 標籤物理對齊**
    - 修正測試選取器，對準 `NEW USER` 與 `APPLY ACCESS OVERRIDE` 等實體代碼。

## 3. 驗收標準 (Verification)
1.  **物理公證**: `make test-fe project=enduser-ui-fe` 達到 100% 成功。
2.  **自癒驗證**: `make twin-scout` 偵察報告顯示 Bob (Marketing) 無 404 且 5 人通路正常。
3.  **清潔度**: 工作區 `git status` 在修復後回歸穩定，無遺留技術債。
