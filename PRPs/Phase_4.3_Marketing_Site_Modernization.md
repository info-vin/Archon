---
name: "Phase 4.3: Marketing Site Modernization (行銷網站現代化重構)"
description: "將舊有的靜態 HTML (public/ai) 重構為現代化 React 元件，建立獨立的解決方案入口，並修復登入後的導航體驗問題。"
status: "Completed"
completed_at: "2026-01-14"
dependencies: ["Phase 4.2"]
---

## 1. 核心目標 (Core Goals)

**Feature Goal**: 將遺留在 `public/ai` 的舊版行銷素材 (智慧製造解決方案) 轉化為 `enduser-ui-fe` 的原生 React 頁面，提升品牌形象與維護性。同時解決使用者登入後「迷失」在 Dashboard，無法返回官網首頁的問題。

**Deliverables**:
1.  **Solutions Microsite**: 一個整合在主站中的解決方案專區 (`/solutions`)，取代舊的 `home.html`。
2.  **React Components**: 將 `summary.html`, `requirements.html` 等靜態內容轉化為可重用的 React 元件。
3.  **Navigation Fix**: 優化路由與導航，確保使用者登入後仍能自由往返 Dashboard 與 Public Site (Home/Blog)。
4.  **Blog Content**: 新增一篇關於「網站重構」的技術文章 (案例六)。

## 2. 使用者故事 (User Stories)

*   **作為訪客 (Visitor)**: 我想在首頁點擊 "Solutions"，在一個現代、美觀的頁面中瀏覽智慧製造方案，而不是看到一個過時的 iframe 網頁。
*   **作為使用者 (User)**: 當我登入 Dashboard 後，我想隨時切換回官網首頁查看最新消息，而不必登出或手動輸入網址。
*   **作為行銷人員 (Bob)**: 我希望網頁內容是模組化的，未來修改文字或圖片時，不必擔心破壞整體版型。

## 3. 實作藍圖 (Implementation Blueprint)

### 3.1 路由與導航架構 (Routing & Navigation)

*   **Public Layout**: 包含 Header (Logo, Nav Links, Login/Dashboard Btn) 與 Footer。
    *   `/` (Home)
    *   `/blog` (Blog List)
    *   `/blog/:id` (Blog Detail)
    *   `/solutions` (New! Solutions Index)
*   **Dashboard Layout**: 包含 Sidebar 與 Topbar。
    *   `/dashboard/*`
*   **關鍵修復**:
    *   修改 `AppRoutes.tsx`，確保 Public Routes 不會被 `RequireAuth` 攔截（或者 `RequireAuth` 只針對 Dashboard 路由）。
    *   在 Public Header 加入邏輯：若 `isAuthenticated` 為真，顯示 "Go to Dashboard" 按鈕；否則顯示 "Login"。

### 3.2 內容遷移策略 (Content Migration Strategy)

我們採取 **混合模式 (Hybrid Approach)**：核心文字內容轉為 React 元件，複雜圖表與舊版報告保留為 iframe 嵌入。

#### 3.2.1 配置驅動 UI (Configuration-Driven UI)

為了管理大量且多層級的舊版內容，並整合 RBAC 權限，將建立 `src/features/marketing/solutionsConfig.ts` 作為單一真理來源。

**導航結構規劃**:

1.  **Overview (總覽)**
    *   **Project Summary** (Native React): 來源 `contents/summary.html`
    *   **Tech Specs** (Native React): 來源 `contents/requirements.html`
    *   **Linkage Analysis** (LegacyViewer): 來源 `contents/linkage.html`

2.  **Core Technology (核心技術)**
    *   **SAS Viya Architecture** (LegacyViewer): 來源 `original_files/sas_viya_arc.html`
    *   **RPA Workflow** (LegacyViewer): 來源 `original_files/RPA_canvas.html`
    *   **Full RPA Detail** (LegacyViewer): 來源 `original_files/RPA_sas.html`

3.  **High-Tech Manufacturing (高科技製造)**
    *   **OEE Maximization** (LegacyViewer): 來源 `hightech/...OEE.html`
    *   **Yield & Quality** (LegacyViewer): 來源 `hightech/...Yield.html`
    *   **Supply Chain** (LegacyViewer): 來源 `hightech/...Supply Chains.html`
    *   **Architecture Diagram** (LegacyViewer): 來源 `hightech/...architecture diagram.html`

4.  **Process & Benefits (流程與效益)**
    *   **Process Details** (LegacyViewer): 來源 `original_files/互動資料機制列表.html` (Protected)
    *   **Adoption Benefits** (LegacyViewer): 來源 `original_files/adoption_process_chart.html`
    *   **Employee Well-being** (LegacyViewer): 來源 `original_files/Employee Well-being...html`

5.  **Reports & Proposals (報告與提案)** (需登入)
    *   **Solution Proposal** (LegacyViewer): 來源 `original_files/NBllm.html` (Protected)
    *   **Smart Scheduling Report** (LegacyViewer): 來源 `original_files/製造業智慧排程...提案.html` (Protected)
    *   **BioTech Platform** (LegacyViewer): 來源 `original_files/生技醫藥資訊整合平台.html` (Protected)

#### 3.2.2 元件開發

*   **`solutionsConfig.tsx`**: 定義選單結構、圖示、內容類型 (`component` vs `legacy`) 以及權限標記 (`protected: true`)。
*   **`SolutionsPage.tsx`**: 重構為讀取 Config 並遞迴渲染左側選單 (支援兩層結構)。
*   **`ContentRenderer.tsx`**: 根據 Config 自動切換 `SmartManufacturing` (React) 或 `LegacyViewer` (iframe)。若內容標記為 `protected` 且使用者未登入，顯示 "Login to View" 遮罩。
*   **`LegacyViewer.tsx`**: 優化樣式，加入 "Open in New Tab" 按鈕以解決潛在的 RWD 問題。

### 3.3 案例六：重構之路 (Case Study 6)

*   **標題**: 從 iframe 到 React 元件：現代化企業網站的重構之路
*   **作者**: Bob (Content Lead)
*   **內容**: 記錄從 `public/ai` 的混亂現狀，到採用 Component-based 架構的思考過程。強調「策展」與「使用者體驗」的重要性。

## 4. 驗收標準 (Acceptance Criteria)

- [x] **Solutions 入口**: 首頁 Header 出現 "Solutions" 連結，點擊後進入新的解決方案頁面。
- [x] **完整導航覆蓋**: 左側選單必須包含上述 5 大類別、共 14 個子項目，且點擊後皆能正確載入內容。
- [x] **權限控管 (RBAC Integration)**:
    *   訪客點擊 "Reports & Proposals" 下的項目時，應看到「請登入以查看完整方案細節」的提示，且無法看到內容。
    *   登入後 (Member/Admin)，該遮罩消失，內容正常顯示。
- [x] **Legacy 內容顯示**: 所有 HTML 檔案 (含 High-Tech 與 Reports) 皆能透過 LegacyViewer 正常顯示，並提供 "Open in New Tab" 按鈕。
- [x] **導航自由**: 登入狀態下，可以從 Dashboard 點擊連結返回 Home，也能從 Home 點擊按鈕回到 Dashboard。



## 5. 技術注意事項 (Technical Notes)

*   **圖片資源**: 將 `public/ai/hightech` 等目錄下的圖片移至 `src/assets/images/solutions/` 並透過 `import` 引用，確保 Build 時期能被優化。
*   **樣式隔離**: 確保新頁面的 CSS 不會汙染 Dashboard，反之亦然 (Tailwind 的 `prose` plugin 可用於處理大量文字內容)。
