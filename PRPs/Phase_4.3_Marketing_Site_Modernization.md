---
name: "Phase 4.3: Marketing Site Modernization (行銷網站現代化重構)"
description: "將舊有的靜態 HTML (public/ai) 重構為現代化 React 元件，建立獨立的解決方案入口，並修復登入後的導航體驗問題。"
status: "Planned"
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

### 3.2 內容遷移 (Content Migration: `public/ai` -> `src/features/marketing`)

*   **建立模組**: `src/features/marketing/`
*   **元件開發**:
    *   `SolutionsPage.tsx`: 新的入口頁，對應原 `home.html` 的導航功能，但使用 React Router `Link`。
    *   `SmartManufacturing.tsx`: 整合原 `summary.html`, `linkage.html` 的內容。
    *   `TechSpecs.tsx`: 將原 `requirements.html` 的表格轉為 Tailwind 樣式。
    *   `LegacyViewer.tsx`: 用於嵌入那些實在難以重構的舊 HTML (作為 iframe 降級方案)，但需加上 "Legacy Content" 標示。

### 3.3 案例六：重構之路 (Case Study 6)

*   **標題**: 從 iframe 到 React 元件：現代化企業網站的重構之路
*   **作者**: Bob (Content Lead)
*   **內容**: 記錄從 `public/ai` 的混亂現狀，到採用 Component-based 架構的思考過程。強調「策展」與「使用者體驗」的重要性。

## 4. 驗收標準 (Acceptance Criteria)

- [ ] **Solutions 入口**: 首頁 Header 出現 "Solutions" 連結，點擊後進入新的解決方案頁面。
- [ ] **內容呈現**: 至少將 `summary` 和 `requirements` 成功轉化為 React 頁面，無跑版。
- [ ] **導航自由**: 登入狀態下，可以從 Dashboard 點擊連結返回 Home，也能從 Home 點擊按鈕回到 Dashboard，無窮迴圈重導向消失。
- [ ] **Legacy 支援**: 舊的複雜圖表 (如 SAS 架構圖) 能透過 Legacy Viewer 正常顯示。
- [ ] **Blog 更新**: 資料庫中出現第六篇 Blog 文章。

## 5. 技術注意事項 (Technical Notes)

*   **圖片資源**: 將 `public/ai/hightech` 等目錄下的圖片移至 `src/assets/images/solutions/` 並透過 `import` 引用，確保 Build 時期能被優化。
*   **樣式隔離**: 確保新頁面的 CSS 不會汙染 Dashboard，反之亦然 (Tailwind 的 `prose` plugin 可用於處理大量文字內容)。
