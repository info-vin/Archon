---
name: "Phase 4.3: Marketing Site Modernization (行銷網站現代化重構)"
description: "將舊有的靜態 HTML (public/ai) 重構為現代化 React 元件，建立獨立的解決方案入口，並修復登入後的導航體驗問題。"
status: "Completed"
last_updated: "2026-01-15"
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

為了讓 Archon 不僅是「內容展示者」，更是「內容解讀者」，我們將實施「前台使用、後台建置」的協作架構。

*   **分工邏輯**:
    1.  **後台建置 (Backstage - Admin UI)**: 由 Bob (Marketing) 或 Admin 負責。入口：`http://localhost:3737/knowledge`。
        *   **任務**: 上傳 `156_resource` 中的 Word/PDF，觸發向量化。
    2.  **前台使用 (Frontstage - End-User UI)**: 由 Alice (Sales) 負責。入口：`http://localhost:5173/marketing`。
        *   **任務**: 在搜尋情資後點擊 "Generate Pitch"，系統自動檢索後台導入的知識。
*   **技術數據**: 
    *   後端 `knowledge_api.py` 的 `/documents/upload` 具備 RBAC 保護，僅授權 `can_manage_content` 角色存取。
    *   RAG 檢索邏輯整合於 `Sales Intelligence` 流程中。

### 3.5 銷售情資驗證 (Sales Intelligence E2E)

為了確保業務流程的穩定性，我們將建立嚴格的端對端測試。

*   **測試檔案**: `enduser-ui-fe/tests/e2e/sales-intelligence.spec.tsx`
*   **實作細節**:
    1.  **Mock 策略**: 
        *   攔截 `/api/marketing/jobs` (Job Search)。
        *   攔截 `/api/marketing/generate-pitch` (RAG Generation) - **新增**。
    2.  **關鍵斷言**: 
        *   驗證卡片渲染及「View Full JD」展開功能。
        *   驗證 Pitch 生成框中包含 RAG 檢索特徵字串。

### 3.6 知識庫導入驗證 (Knowledge Ingestion Verification)

*   **驗證方式**: 手動/自動驗收 Admin UI。
*   **劇本**: 
    1.  Admin 登入 `Port 3737`。
    2.  上傳 `150_integration_study.docx`。
    3.  確認後端回傳 `progress_id` 且狀態轉為 `completed`。

### 3.9 真實 RAG 實作規格 (Real RAG Implementation Specs)

為了讓系統具備真正的生成能力，我們需打通「後端生成 API」至「前端調用」的最後一哩路。

1.  **後端端點**: `POST /api/marketing/generate-pitch`
    *   **Input**: `{ job_title: string, company: string, description: string }`
    *   **Logic**: `RAGService.query` -> LLM Prompt -> Pitch Text
2.  **前端整合**: 
    *   `api.ts`: 新增 `generatePitch` 方法。
    *   `MarketingPage.tsx`: 移除 Hardcoded Template，改為 `await api.generatePitch(...)`。

## 4. 驗收標準 (Acceptance Criteria)

- [x] **Solutions 入口**: 首頁 Header 出現 "Solutions" 連結。
- [x] **完整導航覆蓋**: 左側選單包含 7 大類別、共 17 個子項目。
- [x] **權限控管 (RBAC Integration)**: 訪客無法查看 Protected 內容，登入後可見。
- [x] **Legacy 內容顯示**: 舊 HTML 皆能透過 LegacyViewer 正常顯示。
- [x] **導航自由**: 登入狀態下可自由往返 Dashboard 與 Home。
- [ ] **RAG 資料導入**: `public/aus/156_resource/` 關鍵文件已成功透過 **Admin UI** 存入向量庫。
- [ ] **語義檢索驗證**: 在 RAG 測試介面輸入 "South Africa Lithium Market"，能準確召回相關文件片段。
- [x] **格式支援**: 確認 `.docx` 與 `.pdf` 解析正常。
- [x] **自動化測試覆蓋**: `sales-intelligence.spec.tsx` 已過綠燈。
- [ ] **RAG 真實生成**: 確認前端生成的 Pitch 是由後端 LLM 動態產生，而非寫死的樣板。

## 5. 技術注意事項 (Technical Notes)

*   **圖片資源**: 將 `public/ai/hightech` 等目錄下的圖片移至 `src/assets/images/solutions/` 並透過 `import` 引用，確保 Build 時期能被優化。
*   **樣式隔離**: 確保新頁面的 CSS 不會汙染 Dashboard，反之亦然 (Tailwind 的 `prose` plugin 可用於處理大量文字內容)。
*   **RAG 解析器依賴**: 確保後端環境已正確安裝並配置 `python-docx`, `pdfplumber`, `beautifulsoup4` 以支援多格式解析。
*   **靜態資源路徑**: 需注意 Docker 環境下 `public/` 目錄的掛載路徑，確保後端 API 能讀取到這些靜態檔案，或透過 Agent 模擬上傳流程。

## 6. 最終執行計畫 (Final Execution Plan)

### Phase 1: 基礎建設 (已完成)
- [x] **Action A**: 修改 `enduser-ui-fe/src/types.ts`，加入 `description_full`。
- [x] **Action B**: 修改 `enduser-ui-fe/src/pages/MarketingPage.tsx`，加入 `expandedJobIdx` 與按鈕。
- [x] **Action C**: 修改 `enduser-ui-fe/tests/e2e/e2e.setup.tsx`，更新 Mock 資料。
- [x] **Action D**: 修改 `enduser-ui-fe/tests/e2e/sales-intelligence.spec.tsx`，加入斷言。
- [x] **Action E**: 修改 `job_board_service.py`，強化爬蟲穩定性。
- [x] **Action F**: 修改 `vite.config.ts` (`emptyOutDir`)。
- [x] **Action G**: 修改 `Makefile` (`rm -rf dist`)。
- [x] **Action H**: **手冊移植與 Case 5 強化**：將操作指引完整移入 `seed_blog_posts.sql` 的 Case 5 內容中，並刪除暫存手冊。
- [x] **Action I**: **跨專案導航一致性檢查**：確保 Admin UI 與 End-User UI 的連結正確無誤。

### Phase 2: 真實 RAG 整合 (待執行)
- [ ] **Action K**: **後端 API 實作**：在 `marketing_api.py` 新增 `POST /generate-pitch` 端點，串接 `RAGService`。
- [ ] **Action L**: **前端 Client 擴充**：在 `api.ts` 新增 `generatePitch` 方法。
- [ ] **Action M**: **前端 UI 串接**：修改 `MarketingPage.tsx` 以呼叫真實 API。
- [ ] **Action N**: **E2E 測試升級**：更新 `sales-intelligence.spec.tsx` 以攔截新的 API 呼叫。
