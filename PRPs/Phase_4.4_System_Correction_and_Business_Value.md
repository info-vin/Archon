---
name: "Phase 4.4: System Correction & Business Value Realization (系統校正與商業價值變現)"
description: |
  A corrective roadmap addressing critical user feedback regarding workflow gaps, data integrity, and management features.
  This phase focuses on "Finishing the Job" — ensuring features like Sales Intelligence and Task Management are not just "coded" but "business-ready".
  (這是一個修正性的路線圖，旨在解決使用者回饋中關於工作流程斷點、資料完整性和管理功能的關鍵問題。此階段專注於「完成最後一哩路」——確保銷售情資與任務管理等功能不僅是「寫好程式碼」，而是「商業就緒」。)

---

## Goal (目標)

**Feature Goal (功能目標)**: To transform the "technical prototype" into a "business-ready solution" by filling the gaps in Sales Workflow, Management Tools, and AI Collaboration Architecture. (將「技術原型」轉化為「商業就緒解決方案」，透過填補銷售流程、管理工具與 AI 協作架構的缺口。)

**Deliverable (交付成果)**:
1.  **Project ECITON (遊蟻計畫)**: A complete rebranding execution plan involving dynamic SVG generation by **DevBot**, full UI replacement (3737 & 5173), and a handover workflow to Marketing. (一個完整的品牌重塑執行計畫，包含由 Agent 動態生成 SVG、雙端 UI 替換，以及移交給行銷部門的工作流。)
2.  **Sales Nexus (銷售連結)**: A seamless workflow connecting 104 Leads to existing Vendors and Projects, backed by **MarketBot** email generation and **Librarian** auto-archiving. (一個連接 104 線索、既有廠商與專案的無縫工作流，由 MarketBot 信件生成與 Librarian 自動歸檔支援。)
3.  **Real RBAC Management (真實權限管理)**: Empowering Managers (Charlie) to manage teams, AI budgets, and Marketers (Bob) to manage brand assets. (賦予經理管理團隊與 AI 預算的權限，以及行銷人員管理品牌資產的權限。)
4.  **AI Factory Architecture (AI 工廠架構)**: A structured integration of Jules and AutoGen via specialized adapters, plus **POBot** for task refinement. (Jules 與 AutoGen 的結構化整合，並加入 POBot 進行任務優化。)

**Success Definition (成功定義)**:
- **Charlie** can use **POBot** to refine a one-line task into a full spec, and assign it to **DevBot** for execution.
- **Alice** can click "Generate Intro Email" (**MarketBot**), and the result is automatically indexed by **Librarian**.
- **Bob** can log in and see a "Branding" settings page to tweak the logo later.
- **Verification**: All integration tests pass using **Vitest + MSW**.

## All Needed Context (所有需要的上下文)

### Documentation & References (文件與參考資料)

```yaml
- file: PRPs/Phase_4.2_Business_Feature_Expansion_Plan.md
  why: Reference for the initial Sales Intel design.
- file: python/src/server/auth/permissions.py
  why: Source of truth for current role permissions.
- file: enduser-ui-fe/src/components/layout/MainLayout.tsx
  why: Target for 5173 logo refactoring.
- file: migration/000_unified_schema.sql
  why: Confirmed existence of 'vendors' table (Lines 627-633).
- file: PRPs/ai_docs/RBAC_Collaboration_Matrix.md
  why: DEFINITIVE SOURCE for Role-Machine collaboration logic.
```

### AI Architecture Analysis: Current vs. New (AI 架構差異分析)

| Feature | Current Archon Agents (Phase 4.0) | New AI Factory (Phase 4.4 - Jules/AutoGen) | Difference (差異點) |
| :--- | :--- | :--- | :--- |
| **Role (角色)** | **Executor (執行者)** | **Specialist (專家)** | 現有 Agent 像是通才，Jules/AutoGen 是專才。 |
| **Framework (框架)** | PydanticAI (Single Agent) | Google Vertex AI / MS AutoGen (Multi-Agent) | 從單一代理人轉向多代理人協作系統。 |
| **Trigger (觸發)** | User Manual Click (使用者點擊) | Event-Driven (CI/Webhook/API) | Jules 由程式碼提交觸發；AutoGen 由複雜規劃請求觸發。 |
| **Integration** | MCP Tools (Internal) | **Adapter & CLI Wrapper** | Jules 透過 CLI 工具整合；AutoGen 需要 Docker 沙盒執行。 |

---

## 2. Q&A and Proposed Solutions (詳細 Q&A 與解決方案)

> 此章節記錄了針對用戶回饋的深度分析與解決方案，確保所有決策皆有跡可循。

### Q1: 管理與權限 (Management & RBAC)
**Question**: 只有開單沒有結案日，如何評估效率？Charlie 也要管理 User Management 吧？
**Solution**:
1.  **Time Tracking**: 在 `tasks` 表中新增 `estimated_hours` 與 `actual_hours`，並在 Dashboard 實作燃盡圖。
2.  **Team Management Panel**: 打造專屬的 `TeamManagementPage`，開放給 `manager` 角色使用。允許管理同一部門 (`department`) 的員工帳號，但隔離 System Admin 的敏感設定。
**Status**: ✅ 已解決 (實作 `TeamManagementPage`，Charlie 現可查看團隊與 AI Fleet)。

### Q2: 銷售與爬蟲 (Sales & Crawler)
**Question**: Alice 如何收集資料？資料庫缺欄位，如何跟進？104 爬蟲重複資料怎麼辦？
**Solution**:
1.  **Schema Expansion**: 擴充 `leads` 表，新增 `contact_name`, `contact_email`, `contact_phone`, `next_followup_date`。
2.  **Crawler Uniqueness**: 在 `leads.source_job_url` 建立 UNIQUE 索引。
3.  **Human-in-the-loop**: 定義流程：MarketBot 廣撒網 -> 系統存入 `leads` -> Alice 人工補全聯絡人資料 -> 系統排程跟進。
**Status**: ✅ 已解決 (證實程式具備實體抓取能力，並已修復 `limit` 與重複請求問題，前端加入 Source Badge)。

### Q3: 測試與品質 (Testing & Quality)
**Question**: Phase 4.3 還在 debug，測試不完全。
**Solution**:
1.  **Stop & Fix**: 暫停新功能開發，優先修復 E2E 測試。
2.  **Automated Scenarios**: 將「建立任務 -> 指派給 Alice -> Alice 完成任務」的完整路徑寫入 `tests/e2e`，確保核心業務邏輯不再回歸。
**Status**: 📋 已規劃 (已建立 E2E 測試保護網)。

### Q4: 任務指派 (Task Assignment)
**Question**: Task 可以指定的 Agent 只有兩個？可以指定的人員名單呢？
**Solution**:
1.  **UI Fix**: 修正 `TaskModal.tsx`，使其呼叫正確的 API 端點 (`/api/assignable-users` + `/api/agents/assignable`) 並合併顯示。
2.  **UX Improvement**: 在下拉選單中加入圖示區分 🤖 (Bot) 與 👤 (Human)。
3.  **Assignee Logic**: 採用單一分組選單，但內容根據角色動態過濾 (Manager 看團隊 + Agents，Member 看自己 + 相關 Agent)。
**Status**: ✅ 已解決 (UI 與 API 皆已整合)。

### Q5: 內容更新 (Content Updates)
**Question**: Blog 內容改了種子檔，但網頁還是舊的？
**Solution**:
1.  **UPSERT Logic**: 修改 `seed_blog_posts.sql`，將 `ON CONFLICT DO NOTHING` 改為 `ON CONFLICT (id) DO UPDATE SET ...`。這確保了每次 `make db-init` 後，資料庫內容絕對與檔案同步。
**Status**: ✅ 已解決 (遷移腳本已包含 UPSERT)。

### Q6: AI 協作 (AI Collaboration)
**Question**: 如何利用 Jules (100 credits) + AutoGen？
**Solution**:
1.  **Jules (The Janitor)**: 負責高頻低腦力的 Lint fix 與 Unit Test 補全。透過 CLI Wrapper 整合。
2.  **AutoGen (The Architect)**: 負責複雜 Schema 設計與 refactoring。透過 Docker-in-Docker 執行。
3.  **Metrics**: 建立「AI 貢獻儀表板」追蹤 Jules 的產出量與通過率。
**Status**: 🔄 待對接 (基礎架構已規劃)。

---

## Implementation Blueprint (實作藍圖)

### Phase 4.4.1: Project ECITON - The Living Brand (遊蟻計畫 - 活體品牌)
*Focus: End-to-End rebranding with DevBot integration and RBAC handover.*

**Core Concept**: Logo is a data-driven SVG asset generated by **DevBot**.

**Sequence Diagram (時序圖)**:

```mermaid
sequenceDiagram
    participant Charlie as Manager (Charlie)
    participant UI_5173 as EndUser UI (5173)
    participant UI_3737 as Admin UI (3737)
    participant Backend as Archon Server
    participant DevBot as DevBot (Agent)

    Note over Charlie, DevBot: Step 1: 任務啟動 (Task Injection)
    Charlie->>UI_5173: 查看 "Rebrand: Project Eciton" 任務卡
    Charlie->>Backend: 點擊 "Trigger DevBot" (Assign & Run)

    Note over Backend, DevBot: Step 2: 動態生成 (Agent Execution)
    Backend->>DevBot: 請求生成 "Geometric Ant Node-Link Style"
    DevBot->>DevBot: 運算 SVG 路徑 (Nodes + Links)
    DevBot-->>Backend: 回傳 SVG Code (Payload)

    Note over Backend, UI_3737: Step 3: 資產部署 (Deployment)
    Backend->>Backend: 寫入 public/logo-eciton.svg (Shared Asset)
    Backend-->>UI_5173: 通知 "Asset Ready"
    
    Note over UI_5173, UI_3737: Step 4: 全面替換 (Refactor & Replace)
    UI_5173->>UI_5173: <BrandLogo /> 元件熱重載 (顯示新 Logo)
    UI_3737->>UI_3737: <Navigation /> 元件更新 (顯示新 Logo)
```

**Task Card Example (卡片說明範例)**:
*   **Title**: `[REBRAND] Implement Project Eciton Identity`
*   **Description**: 
    > **Visual Specs**:
    > *   **Style**: Geometric Node-Link Diagram (Visualizing "Collective Intelligence").
    > *   **Palette**: Gradient from Cyan (`#00f2ff`) to Purple (`#a855f7`).
    > *   **Animation**: Pulse effect on nodes (SVG `<animate>` tag).
    >
    > **Technical Constraints**:
    > *   **Format**: SVG (Vector).
    > *   **File Name**: `logo-eciton.svg`.
    > *   **Storage**: `public/` directory (accessible by both UIs).
    >
    > **Action**:
    > *   Call **DevBot** (via `logo_tool`) to generate asset based on specs.
*   **Assignee**: **DevBot** (Agent)
*   **Status**: `TODO`

**Refined Blueprint (實作細節)**:

1.  **Backend (Agent API)**:
    *   **檔案**: `python/src/mcp_server/features/design/logo_tool.py` (New)
    *   **Agent**: Registered to **DevBot**.
    *   **邏輯**: Returns animate-capable SVG string based on geometric math.

2.  **Frontend (Shared Component)**:
    *   **檔案**: `enduser-ui-fe/src/components/BrandLogo.tsx`
    *   **檔案**: `archon-ui-main/src/features/shared/components/BrandLogo.tsx`
    *   **邏輯**: Loads SVG from `/api/assets/logo` or local public folder.

3.  **Database (Task Injection)**:
    *   **SQL**:
        ```sql
        INSERT INTO archon_tasks (title, description, assignee, status, project_id) 
        VALUES ('[REBRAND] Implement Project Eciton Identity', 'Visual Specs: ...', 'DevBot', 'todo', 'proj-123');
        ```

4.  **Admin UI (3737) Update**:
    *   **檔案**: `archon-ui-main/src/components/layout/Navigation.tsx`
    *   **行動**: 替換 `<img src="/logo-neon.png" />` 為 `<BrandLogo />`。

5.  **Quality Assurance (Integration Test)**:
    *   **檔案**: `enduser-ui-fe/tests/e2e/brand-identity.spec.tsx`
    *   **工具**: **Vitest + MSW**.
    *   **測試場景**:
        1.  **Visual Check**: 確認 Header 存在 `<BrandLogo />`。
        2.  **Asset Load**: 攔截 `/logo-eciton.svg` 回傳 200 OK。
        3.  **Agent Flow**: 模擬點擊 -> 等待任務完成 -> 驗證資產更新。

### Phase 4.4.2: Sales Nexus - Closing the Loop (銷售連結 - 閉環修復)
*Focus: Enhancing existing tables and empowering Alice with MarketBot & Librarian.*

**Workflow & Agent Role**:
1.  **MarketBot (Scout)**: Automatically crawls 104 data and populates `leads`.
2.  **MarketBot (Enricher)**: Analyzes company profile and generates draft emails.
3.  **Librarian (Archiver)**: **New Feature** - Automatically indexes generated emails and successful pitches into the Knowledge Base.
4.  **Alice (Sales)**: Claims Leads, reviews generated emails, and promotes to Vendors.
5.  **System (Follow-up)**: Uses `next_followup_date` to alert Alice (Dashboard Notification).

**Refined Blueprint (實作細節)**:

1.  **Database (Unified Enhancement)**:
    *   **檔案**: `migration/008_system_correction_phase44.sql` (New)
    *   **行動**: 
        *   `ALTER TABLE vendors` ADD `pain_points`, `owner_id`, `status`, `contact_info`.
        *   `ALTER TABLE archon_tasks` ADD `estimated_hours`, `actual_hours`.
        *   `ALTER TABLE leads` ADD `linked_project_id`.
        *   `CREATE UNIQUE INDEX idx_leads_source_url ON leads(source_job_url)`.

2.  **Backend Integration**:
    *   **Service**: Enhance `JobBoardService` to include `generate_sales_email(lead_id)` using **MarketBot**.
    *   **Service**: Hook `Librarian.archive()` into `generate_sales_email` success callback.

3.  **Frontend Integration**:
    *   **UI**: `MarketingPage.tsx` gets a "Promotion & Enrichment" toolbar for each card.
    *   **Indicator**: Add "Knowledge Indexed" badge when Librarian completes archiving.

### Phase 4.4.3: The Hive - Management (蜂巢 - 管理)
*Focus: Addressing Q1 (Admin Panel) & Q4 (Assignment) with POBot support.*

**Management Context Logic**:
*   **Single Grouped Assignee Menu**: Filtered by role (e.g., Alice sees only `MarketBot` and `Self`).
*   **Team Management Panel**: Charlie manages `Sales`/`Marketing` team passwords/roles and monitors AI cost.

**Refined Blueprint (實作細節)**:

1.  **Backend RBAC Fixes**:
    *   **檔案**: `python/src/server/auth/permissions.py` (Add `USER_MANAGE_TEAM`, `BRAND_ASSET_MANAGE`).
    *   **檔案**: `python/src/server/services/rbac_service.py` (Implement context-based assignee filtering).

2.  **Team Management Panel**:
    *   **元件**: `TeamManagementPage.tsx` (Charlie only).
    *   **新增**: AI Cost Dashboard (Token tracking per user).

3.  **POBot Integration (The Spec Writer)**:
    *   **UI**: Add "✨ Refine with AI" button in `TaskModal.tsx`.
    *   **Backend**: Add endpoint `/api/tasks/refine-description` using **POBot**.
    *   **Logic**: Convert short input to structured User Stories.

## Validation Loop (驗證迴圈)

### Level 1: Schema & RBAC Update
- [ ] **SQL**: `make db-init`.
- [ ] **Matrix**: Verify `BRAND_ASSET_MANAGE` works for Bob in integration tests.

### Level 2: Integration Tests (Vitest + MSW)
- [x] **Brand Identity**: `brand-identity.spec.tsx` (Covers Step 4, 5, 6 - SVG Rendering).
- [x] **Sales Intelligence**: `sales-intelligence.spec.tsx` (Covers Step 1 - Search & Pitch Generation).
- [x] **Management**: `management.spec.tsx` (Covers Step 3 - Refine Task with AI).
- [ ] **Missing Coverage (Gap)**:
    - **Marketing**: `content-marketing.spec.tsx` (Step 2 - Draft with AI flow is missing).
    - **Approvals**: `management.spec.tsx` (Step 3 - Approval action is mocked but not fully tested).

### Level 3: Business Scenarios (Manual)
- [ ] **Alice (Sales)**: 可以生成開發信，並看到 Librarian 自動歸檔的標記。
- [ ] **Charlie (Manager)**: 可以使用 POBot 優化任務描述，並指派給 DevBot。
- [ ] **Bob (Marketing)**: 看到 Blog 更新且能管理品牌資產。

---

## 3. Enterprise Execution Script (Deep Dive) - 企業級執行腳本詳解

> **核心目標**: 提供一份「照著做絕對不會錯」的精確指令集。
> **前置條件**: Docker Desktop 已啟動，終端機位於專案根目錄。

### Step 0: Environment Reset (環境重置)
*   **Actor**: Developer / Admin
*   **Location**: Terminal
*   **Actions**:
    1.  執行資料庫重置指令 (確保環境乾淨):
        ```bash
        make db-init
        ```
    2.  等待終端機出現以下訊息:
        > `Database initialized successfully.`
        > `Dev Auto-Login URL: http://localhost:3737/dev-token?token=...`
    3.  **複製** 該 Dev Token URL 連結 (此為 Admin 快速入口)。

### Step 1: Sales Intelligence (業務情蒐)
*   **Actor**: Alice (Sales)
*   **Credentials**: `alice@archon.com` / `alice123`
*   **Actions**:
    1.  **開啟瀏覽器**: 如果你是 Admin，直接貼上 Step 0 的連結；若要模擬 Alice，請前往 `http://localhost:5173/login` 並使用上述帳密登入。
    2.  **進入頁面**: 點擊左側導航列 (Sidebar) 的 **"Sales Nexus"** (圖示: 💼)。
    3.  **執行爬蟲**:
        *   找到右上角的 **"Fetch 104 Data"** 按鈕 (藍色)。
        *   **點擊** 並等待約 3-5 秒。
        *   **驗證**: 觀察頁面中央的表格是否新增了 3-5 筆公司資料 (如 "台積電", "聯發科")。
        *   **驗證**: 確認每一列的 "Source" 欄位顯示綠色的 **"104 Live"** 標籤 (若顯示黃色 "Mock"，代表 IP 被擋，但流程仍可繼續)。
    4.  **生成開發信**:
        *   在第一筆資料的右側，點擊 **"⚡ Generate Pitch"** 按鈕 (閃電圖示)。
        *   **等待**: 系統會彈出一個 Modal 視窗，顯示 "MarketBot is analyzing..."。
        *   **結果**: 約 2 秒後，Modal 內會顯示 AI 寫好的信件草稿。
    5.  **保存與歸檔**:
        *   點擊 Modal 右下角的 **"Approve & Save"** (綠色按鈕)。
        *   **驗證**: 右上角跳出綠色 Toast 通知 **"Success: Lead saved and indexed by Librarian"**。

### Step 2: Content Marketing (行銷內容)
*   **Actor**: Bob (Marketing)
*   **Credentials**: `bob@archon.com` / `bob123`
*   **Actions**:
    1.  **切換帳號**: 登出 Alice，改用 Bob 登入 `http://localhost:5173`。
    2.  **進入頁面**: 點擊左側導航列的 **"Brand Hub"** (圖示: 📢)。
    3.  **查看靈感**:
        *   頁面左側會顯示 **"Trending Keywords"**，確認是否有剛才 Alice 抓取到的公司相關關鍵字 (e.g., "Semiconductor", "AI").
    4.  **AI 寫作**:
        *   點擊右上角 **"New Post"** 按鈕。
        *   在彈出選單中選擇 **"Draft with AI"**。
        *   在輸入框輸入: *"寫一篇關於導入 AI 客服的優勢，針對製造業客戶"*。
        *   點擊 **"Generate"**。
    5.  **提交審核**:
        *   內容生成後，點擊編輯器右上角的 **"Submit for Review"** (藍色按鈕)。
        *   **驗證**: 文章狀態標籤從 "Draft" 變為黃色的 **"Pending Approval"**。

### Step 3: Management Decision (經理決策)
*   **Actor**: Charlie (Manager)
*   **Credentials**: `charlie@archon.com` / `charlie123`
*   **Actions**:
    1.  **切換帳號**: 登出 Bob，改用 Charlie 登入。
    2.  **審核文章**:
        *   進入 **"Team War Room"** (圖示: 🛡️)。
        *   在 **"Pending Approvals"** 區塊，找到 Bob 提交的文章。
        *   點擊 **"Approve"** (打勾圖示)。
        *   **驗證**: 該項目從列表中消失 (已發布)。
    3.  **指派任務 (人機協作)**:
        *   點擊 Dashboard 右上角的 **"+ New Task"**。
        *   **Title**: `Rebrand Logo`
        *   **Assignee**: 在下拉選單中找到 "🤖 Machine Agents" 分組，選擇 **"DevBot"**。
        *   **Description**: 輸入 *"Create a minimalist logo, geometric ant style, blue gradient"*。
        *   **AI 優化 (選擇性)**: 點擊輸入框下方的 **"✨ Refine"**，看 POBot 如何將這句話變成詳細規格。
        *   點擊 **"Create Task"**。

### Step 4: AI Execution Verification (驗收成果)
*   **Actor**: Charlie (繼續操作)
*   **Actions**:
    1.  **前往任務列表**: 點擊左側 **"Tasks"**。
    2.  **觀察狀態**: 剛建立的任務狀態應為 `TODO` -> 數秒後變為 `IN_PROGRESS` -> 最後變為 `IN_REVIEW`。
    3.  **驗收產出**:
        *   點擊該任務卡片進入詳情。
        *   在留言區或附件區，DevBot 應已上傳了 `logo-eciton.svg` 的預覽圖。
        *   **點擊預覽圖**: 確認圖片符合 "幾何螞蟻" 的描述。

### Step 5: Final Deployment (模擬上線)
*   **Actor**: System Admin
*   **Credentials**: (使用 Dev Token 或 `admin@archon.com`)
*   **Actions**:
    1.  **進入 Admin Panel**: 前往 `http://localhost:3737`。
    2.  **系統設定**:
        *   點擊 **"Global Settings"**。
        *   在 "Site Logo" 欄位，選擇剛才 DevBot 生成的 SVG 檔案。
        *   點擊 **"Save Changes"**。
    3.  **最終驗證**:
        *   回到 End-User UI (`http://localhost:5173`)。
        *   **強制重新整理 (Cmd+Shift+R)**。
        *   **驗證**: 左上角的網站 Logo 已變成新的幾何螞蟻圖示。


---

## Appendix A: AI Factory & Cost Governance
*Detailed architecture moved here to focus on business value.*

**Governance**: Charlie allocates token budgets to Alice/Bob.
**Jules (CLI Wrapper)**: Automated maintenance and bug fixing.
**AutoGen (DIND Sandbox)**: Multi-agent architectural planning.

---

## Appendix B: User Guide (Simplified SOP)

### 人機協作標準作業程序 (SOP) - 簡易版

> **核心目標**：讓 AI 成為你的神隊友，將傳統兩天的工作量，壓縮在 **一小時** 內完成。
> **適用對象**：無論您幾歲，只要會按滑鼠，就能輕鬆指揮 AI 團隊。

#### 🚀 七步工作法 (The 7-Step Workflow)

**第一步：【廠長啟動】一鍵開工 (Admin)**
1.  **動作**：按下一個神奇按鈕（執行初始化指令），就像打開工廠的總電源，並點擊「快速通關連結」(Dev Token)。
2.  **結果**：工廠燈火通明，所有機械手臂就定位，準備開工！

**第二步：【業務情蒐】AI 獵犬出動 (Alice)**
1.  **場景**：Sales Nexus (業務情報室)
2.  **動作**：點擊「搜𡦃」，AI 自動爬取 104 客戶名單，MarketBot 自動撰寫開發信草稿。
3.  **結果**：一分鐘內，桌面已放滿整理好的客戶名單與信件。

**第三步：【行銷宣傳】AI 文案大師 (Bob)**
1.  **場景**：Brand Hub (品牌中心)
2.  **動作**：指示 AI 根據資料撰寫文章，AI 瞬間產出圖文並茂的部落格文章，您只需審核提交。
3.  **結果**：喝口茶的時間，一整天的寫作工作已完成。

**第四步：【經理決策】指揮大腦運作 (Charlie)**
1.  **場景**：War Room (戰情室)
2.  **動作**：呼叫 AI 秘書 (POBot) 整理待辦事項並自動分派任務給對應的工程師或業務。
3.  **結果**：無須冗長會議，任務自動分配完畢。

**第五步：【工程製造】無人自動化產線 (DevBot)**
1.  **動作**：AI 工程師DevBot 自動接單，編寫程式碼或設計 Logo，全自動執行。
2.  **結果**：熱騰騰的「完成品草稿」直接送達審核區。

**第六步：【最終驗收】一鍵發布 (Charlie/Admin)**
1.  **場景**：Approvals (審核台)
2.  **動作**：滿意成品則按下「批准 (Approve)」。
3.  **結果**：新功能立刻上線。

**第七步：【安全下班】自動健檢 (Admin)**
1.  **動作**：工作結束時修改密碼，系統自動進行健康檢查。
2.  **結果**：安心下班，系統已準備好迎接明天。

> 🎉 **恭喜！您剛剛在一个小時內，完成了傳統團隊需要兩天才能做完的工作。**
