---
name: "Phase 4.3: Marketing Site Modernization (行銷網站現代化重構)"
description: "將舊有的靜態 HTML (public/ai) 重構為現代化 React 元件，建立獨立的解決方案入口，並修復登入後的導航體驗問題。"
status: "In Progress"
last_updated: "2026-01-14"
dependencies: ["Phase 4.2"]
---

## 1. 核心目標 (Core Goals)

**Feature Goal**: 將遺留在 `public/ai` 的舊版行銷素材 (智慧製造解決方案) 轉化為 `enduser-ui-fe` 的原生 React 頁面，提升品牌形象與維護性。同時解決使用者登入後「迷失」在 Dashboard，無法返回官網首頁的問題。

**Deliverables**:
1.  **Solutions Microsite**: 一個整合在主站中的解決方案專區 (`/solutions`)，取代舊的 `home.html`。
2.  **React Components**: 將 `summary.html`, `requirements.html` 等靜態內容轉化為可重用的 React 元件。
3.  **Navigation Fix**: 優化路由與導航，確保使用者登入後仍能自由往返 Dashboard 與 Public Site (Home/Blog)。
4.  **Blog Content**: 新增一篇關於「網站重構」的技術文章 (案例六)。
5.  **Strategic Assets**: 整合高價值的客戶提案手冊 (`153_testCase`) 至受保護的閱覽區。

## 2. 使用者故事 (User Stories)

*   **作為訪客 (Visitor)**: 我想在首頁點擊 "Solutions"，在一個現代、美觀的頁面中瀏覽智慧製造方案，而不是看到一個過時的 iframe 網頁。
*   **作為使用者 (User)**: 當我登入 Dashboard 後，我想隨時切換回官網首頁查看最新消息，而不必登出或手動輸入網址。
*   **作為行銷人員 (Bob)**: 我希望網頁內容是模組化的，未來修改文字或圖片時，不必擔心破壞整體版型。
*   **作為業務代表 (Alice)**: 我希望能在系統中直接展示針對特定客戶 (如 Fujitec) 的完整 POC 規劃手冊，而不需要另外找檔案。

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

為了管理大量且多層級的舊版內容，並整合 RBAC 權限，將建立 `src/features/marketing/solutionsConfig.tsx` 作為單一真理來源。

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

6.  **Strategic Client POCs (策略客戶案例)** (需登入)
    *   **Fujitec Handbook** (LegacyViewer): 來源 `aus/153_testCase/Fujitec_Intelligent_Scheduling_Project.html` (Protected)
    *   **POC Success Metrics** (LegacyViewer): 來源 `aus/153_testCase/v.0.1.2.html` (Protected)

7.  **Architecture Tools (架構規劃工具)**
    *   **Cloud Configurator** (LegacyViewer): 來源 `aus/152_SA/resource_locate.html` (Public)

#### 3.2.2 元件開發

*   **`solutionsConfig.tsx`**: 定義選單結構、圖示、內容類型 (`component` vs `legacy`) 以及權限標記 (`protected: true`)。
*   **`SolutionsPage.tsx`**: 重構為讀取 Config 並遞迴渲染左側選單 (支援兩層結構)。
*   **`ContentRenderer.tsx`**: 根據 Config 自動切換 `SmartManufacturing` (React) 或 `LegacyViewer` (iframe)。若內容標記為 `protected` 且使用者未登入，顯示 "Login to View" 遮罩。
*   **`LegacyViewer.tsx`**: 優化樣式，加入 "Open in New Tab" 按鈕以解決潛在的 RWD 問題。

### 3.3 案例六：重構之路 (Case Study 6)

*   **標題**: 從 iframe 到 React 元件：現代化企業網站的重構之路
*   **作者**: Bob (Content Lead)
*   **內容**: 記錄從 `public/ai` 的混亂現狀，到採用 Component-based 架構的思考過程。強調「策展」與「使用者體驗」的重要性。

### 3.4 知識庫增強 (Knowledge Base Enhancement)

為了讓 Archon 不僅是「內容展示者」，更是「內容解讀者」，我們將導入歷史累積的高價值非結構化數據。

*   **目標**: 將 `enduser-ui-fe/public/aus/156_resource/` 下的舊合約、市場研究報告與技術白皮書，轉化為可被語義檢索的知識向量。
*   **執行策略**:
    1.  **資料盤點**: 來源包含 `.docx` (合約、研究報告) 與 `.pdf` (技術文件)。
    2.  **Agent 協作**: 使用 `POBot` (負責合約需求分析) 或 `Librarian` (負責技術研究歸檔) 透過 `knowledge_api` 進行批量上傳與解析。
    3.  **RAG 整合**: 驗證這些文件能被「行銷情資 (Sales Intel)」或「合約分析」場景所引用。
*   **預期效益**: 業務人員 (Alice) 可直接詢問「南非鋰電池市場的關鍵數據為何？」，系統將引用 `160_south_africa_lithium_battery_market_bp.docx` 回答。

### 3.5 銷售情資驗證 (Sales Intelligence E2E)

為了確保業務流程的穩定性，我們將建立嚴格的端對端測試。

*   **測試檔案**: `enduser-ui-fe/tests/e2e/sales-intelligence.spec.tsx`
*   **實作細節 (Implementation Details)**:
    1.  **Mock 策略 (MSW)**:
        *   攔截 `GET /api/marketing/jobs`。
        *   回傳 Fixture Data: 包含 `description_full: "Requires specific BI tool knowledge (Tableau)..."` 的特徵字串。
    2.  **角色模擬**:
        *   使用 `e2e.setup.ts` 中的 `mockUser` 模擬 Alice 登入狀態。
    3.  **關鍵斷言 (Assertions)**:
        *   **列表渲染**: 確認 `Retail Corp` 卡片出現。
        *   **詳情展開**: 模擬點擊 `View Full JD` (或類似觸發點)，驗證 DOM 中出現 "Requires specific BI tool knowledge"。
        *   **Pitch 生成**: 點擊 `Generate Pitch`，驗證生成的文字框中包含公司名稱與 Mock 的職缺關鍵字。

### 3.6 知識庫導入驗證 (Knowledge Ingestion E2E)

*   **測試檔案**: `enduser-ui-fe/tests/e2e/rag-ingestion.spec.tsx` (New)
*   **劇本**: "Admin Ingests Legacy Documents"
    1.  **Login**: 以 `Admin` 身份登入 (因為 Alice 無權上傳)。
    2.  **Upload**: 模擬檔案上傳 `test-contract.pdf`。
    3.  **Verify**: 確認上傳成功 toast 出現，且列表新增一筆資料。
    4.  **RAG Check**: (Optional) 透過 `Mock Service Worker` 模擬 RAG 檢索 API 回傳該文件的片段，驗證前端顯示。

- [ ] **自動化測試覆蓋**:
    - `sales-intelligence.spec.tsx` 通過，且明確驗證了 `description_full` 欄位的顯示。
    - `rag-ingestion.spec.tsx` 通過，驗證檔案上傳 UI 流程。

### 3.7 前端技術對齊 (Frontend Technical Alignment)

為了支撐後端升級後的職缺爬蟲功能，前端需執行以下精確變更：

1.  **類型系統定義 (Type Definition)**:
    *   **檔案**: `enduser-ui-fe/src/types.ts`
    *   **變更**: 在 `JobData` 介面新增 `description_full?: string` 欄位。
2.  **UI 渲染邏輯 (UI Component)**:
    *   **檔案**: `enduser-ui-fe/src/pages/MarketingPage.tsx`
    *   **實作細節**: 
        *   新增 React State: `expandedJobIdx` 用於追蹤展開的職缺索引。
        *   在 `lead-card` 中新增切換按鈕 `[View Full JD]`。
        *   條件渲染: 顯示 `job.description_full` (若無則顯示摘要)。
3.  **E2E 數據模擬 (Mocking)**:
    *   **檔案**: `enduser-ui-fe/tests/e2e/e2e.setup.tsx`
    *   **變更**: 升級 `searchJobs` 的 mock 回傳值，加入包含關鍵字（如 "BI tools", "Spark"）的 `description_full` 欄位。

### 3.8 環境與依賴檢查 (Infrastructure Verification)

1.  **後端依賴**: 確保 `beautifulsoup4` 與 `lxml` 已加入 `python/pyproject.toml` 的 `server` group。
2.  **環境變數**: 爬蟲服務使用 AJAX 模擬，無需額外外部 API Key。
3.  **建置清理**: 
    *   `Makefile` 的 `install` target 必須清空 `dist/`。
    *   `enduser-ui-fe/vite.config.ts` 必須啟用 `build.emptyOutDir: true`。

## 4. 驗收標準 (Acceptance Criteria)

- [x] **Solutions 入口**: 首頁 Header 出現 "Solutions" 連結，點擊後進入新的解決方案頁面。
- [x] **完整導航覆蓋**: 左側選單必須包含上述 7 大類別 (新增 Architecture Tools)、共 17 個子項目，且點擊後皆能正確載入內容。
- [x] **權限控管 (RBAC Integration)**:
    *   訪客點擊 "Reports & Proposals" 或 "Strategic Client POCs" 下的項目時，應看到「請登入以查看完整方案細節」的提示，且無法看到內容。
    *   登入後 (Member/Admin)，該遮罩消失，內容正常顯示。
- [x] **Legacy 內容顯示**: 所有 HTML 檔案 (含 High-Tech, Reports, Fujitec POC 與 Cloud Configurator) 皆能透過 LegacyViewer 正常顯示，並提供 "Open in New Tab" 按鈕。
- [x] **導航自由**: 登入狀態下，可以從 Dashboard 點擊連結返回 Home，也能從 Home 點擊按鈕回到 Dashboard。
- [ ] **RAG 資料導入**: `public/aus/156_resource/` 下至少 3 份關鍵文件 (如鋰電池市場報告、整合策略) 已成功存入向量資料庫。
- [ ] **語義檢索驗證**: 在 RAG 測試介面輸入 "South Africa Lithium Market"，能準確召回相關文件片段。
- [ ] **格式支援**: 確認 `.docx` 與 `.pdf` 格式皆能被正確解析文字內容。

## 5. 技術注意事項 (Technical Notes)

*   **圖片資源**: 將 `public/ai/hightech` 等目錄下的圖片移至 `src/assets/images/solutions/` 並透過 `import` 引用，確保 Build 時期能被優化。
*   **樣式隔離**: 確保新頁面的 CSS 不會汙染 Dashboard，反之亦然 (Tailwind 的 `prose` plugin 可用於處理大量文字內容)。
*   **RAG 解析器依賴**: 確保後端環境已正確安裝並配置 `python-docx`, `pdfplumber`, `beautifulsoup4` 以支援多格式解析。
*   **靜態資源路徑**: 需注意 Docker 環境下 `public/` 目錄的掛載路徑，確保後端 API 能讀取到這些靜態檔案，或透過 Agent 模擬上傳流程。

## 6. 最終執行計畫 (Final Execution Plan)

### Action Items
- [ ] **Action A**: 修改 `enduser-ui-fe/src/types.ts`，加入 `description_full`。
- [ ] **Action B**: 修改 `enduser-ui-fe/src/pages/MarketingPage.tsx`，加入 `expandedJobIdx` state 與 `[View Full JD]` 按鈕。
- [ ] **Action C**: 修改 `enduser-ui-fe/tests/e2e/e2e.setup.tsx`，更新 Mock 資料。
- [ ] **Action D**: 修改 `enduser-ui-fe/tests/e2e/sales-intelligence.spec.tsx`，加入對應斷言。
- [ ] **Action E**: 修改 `job_board_service.py`，實作 `BeautifulSoup` 邏輯。
- [ ] **Action F**: 修改 `vite.config.ts` (`emptyOutDir`)。
- [ ] **Action G**: 修改 `Makefile` (`rm -rf dist`)。
