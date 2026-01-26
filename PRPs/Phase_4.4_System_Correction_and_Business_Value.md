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

### Phase 4.4.1 ~ 4.4.4: Infrastructure & Workflow Stabilization (Completed)
*   **Project ECITON**: DevBot can generate SVGs. Admin UI updated.
*   **Sales Nexus**: MarketBot crawls 104, generates pitches. Librarian archives them. E2E tests passed.
*   **The Hive**: Team Management Page implemented. RBAC fixed.
*   **The Sentinel**: `make probe` established as the standard health check. Google RAG 400 fixed.

---

### Phase 4.4.5: The Soul of the Machine (賦予靈魂 - 業務邏輯補完)
*Focus: Implementing the "Human-Like" behaviors for Bob, Charlie, and System Ops as defined in the RBAC Matrix.*

#### Step 0: Foundation (Database & Dependencies)
*   **Schema**: Create `migration/012_create_archon_logs.sql`.
    *   Table `archon_logs`: `id`, `source` (e.g. 'Clockwork'), `level` ('INFO', 'ERROR'), `message`, `details` (JSONB), `created_at`.
*   **Dependency**: Update `python/pyproject.toml`.
    *   Add `APScheduler>=3.10.0` to `server` group.
    *   Run `make dev-docker` to rebuild container.

#### 1. Clockwork: The System Heartbeat & Accountant (Ops)
*The "Soul": The system should know it's sick before the user does, and know who is spending the most.*

*   **Dependency**: Add `APScheduler` to `pyproject.toml` (Server group).
*   **Service**: Create `python/src/server/services/scheduler_service.py`.
    *   **Mechanism**: Initialize `AsyncIOScheduler`.
    *   **Job 1 (Health)**: Run `run_probe_logic()` every 6 hours.
    *   **Job 2 (Accounting)**: Run `_analyze_token_usage()` every 24 hours.
        *   **Query Logic**: Fetch `gemini_logs` where `created_at` > (Now - 24h).
        *   **Calculation**: `est_tokens = len(gemini_response) / 4`. Group sum by `user_name`.
        *   **Storage**: Insert into `archon_logs`:
            *   `source`: 'clockwork-accountant'
            *   `level`: 'INFO'
            *   `message`: 'Daily Token Usage Report'
            *   `details`: `{ "usage_map": {"Alice": 1200, "Bob": 500}, "total_est_cost": 0.05 }`
*   **Verification**:
    *   [ ] **Startup**: Log shows `SchedulerService: Started`.
    *   [ ] **Data Check**: `archon_logs` contains a JSON entry with user-based token stats.

#### 2. Bob's Content Engine (MarketBot + RAG)
*The "Soul": Bob doesn't just write generic text. He writes insights **cited from** the leads Alice found.*

*   **Endpoint**: `POST /api/marketing/blog/generate` (Modify existing `draft_blog_post`)
*   **Logic**:
    1.  **Context Retrieval**: Call `RAGService.search_documents(query=topic, filter_metadata={"knowledge_type": "sales_pitch"})`.
        *   *Correction*: Use `search_documents` instead of `perform_rag_query` to support metadata filtering.
    2.  **Prompt Engineering**: Use `marketing_prompts.py`. Inject retrieved context into a "Reference Material" section.
    3.  **Generation**: MarketBot (LLM) generates a blog post citing the context.
    4.  **Output**: Returns structured JSON `{ "title": "...", "content": "...", "references": [...] }`.
*   **Verification**:
    *   [ ] **Citation Check**: Generated content mentions specific entities from the retrieved context.
    *   [ ] **Empty State**: If no context found, generates generic content with empty references.

#### 3. Charlie's Spec Refiner (POBot)
*The "Soul": Charlie is busy. He writes "Fix login". POBot transforms that into a professional User Story.*

*   **Endpoint**: `POST /api/tasks/refine-description` (Verified: Logic exists in `TaskService`)
*   **Refinement**: Ensure `pm_prompts.py` enforces Gherkin Syntax.
*   **Logic**:
    1.  **Input**: Raw, short text (e.g., "Make logo blue").
    2.  **Role Play**: Load `pm_prompts.py`. System Prompt: "You are a Senior Product Owner. Convert vague requests into Gherkin syntax specs."
    3.  **Output**: Markdown formatted text containing **User Story**, **Acceptance Criteria**, and **Technical Notes**.
*   **Verification**:
    *   [ ] **Format Check**: Output contains `**As a**`, `**I want to**`, `**So that**`.

#### 4. Charlie's Decision Console (Manager Workflow)
*The "Soul": Charlie needs a cockpit to approve Bob's creativity and direct DevBot's labor.*

*   **Backend Verification**: Ensure `marketing_api.py` endpoints exist:
    *   `GET /api/marketing/approvals`: Filters `blog_posts` by `status='review'`.
    *   `POST /api/marketing/approvals/{type}/{id}/{action}`: Validates `manager` role via `RBACService`.
*   **Workflow Verification**:
    *   [ ] **End-to-End**: Bob submits draft (`status='review'`) -> Charlie calls approval API -> DB status updates to `published`.

---

## Validation Loop (驗證迴圈)

### Level 1: Schema & RBAC Update
- [x] **SQL**: `make db-init` (Verified).
- [ ] **Matrix**: Verify `BRAND_ASSET_MANAGE` works for Bob in integration tests.

### Level 2: Integration Tests (Vitest + MSW)
- [x] **Brand Identity**: `brand-identity.spec.tsx` (Covers Step 4, 5, 6 - SVG Rendering).
- [x] **Sales Intelligence**: `sales-intelligence.spec.tsx` (Covers Step 1 - Search & Pitch Generation).
- [x] **Management**: `management.spec.tsx` (Covers Step 3 - Refine Task with AI).
- [x] **Type Safety**: Frontend TypeScript build passed.
- [x] **PromptOps**: Backend prompts consolidated.

### Level 3: Business Scenarios (Manual)
- [x] **Alice (Sales)**: Can generate pitches, see "Indexed" badge. Can manage tasks.
- [x] **System (Ops)**: `make probe` passes with correct dimension check.
- [ ] **Charlie (Manager)**: Uses POBot to refine "Make it pop" into a spec.
- [ ] **Bob (Marketing)**: Generates a blog post that actually cites a lead Alice found.

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
        *   **關鍵驗證**: 確認每一列都清楚顯示了 **"Position" (職缺名稱)**，例如 "AI 工程師"，這是判斷 Lead 價值的關鍵。
        *   **驗證**: 確認每一列的 "Source" 欄位顯示綠色的 **"104 Live"** 標籤 (若顯示黃色 "Mock"，代表 IP 被擋，但流程仍可繼續)。
    4.  **生成開發信**:
        *   在第一筆資料的右側，點擊 **"⚡ Generate Pitch"** 按鈕 (閃電圖示)。
        *   **等待**: 系統會彈出一個 Modal 視窗，顯示 "MarketBot is analyzing..."。
        *   **結果**: 約 2 秒後，Modal 內會顯示 AI 寫好的信件草稿。
    5.  **保存與歸檔**:
        *   點擊 Modal 右下角的 **"Approve & Save"** (綠色按鈕)。
        *   **驗證**: 右上角跳出綠色 Toast 通知 **"Success: Lead saved"**。
        *   **背景運作**: 此時 **Librarian** 會在後台自動啟動，將此 Pitch 歸檔至向量資料庫 (無需人工介入)。

### Step 2: Content Marketing (行銷內容)
*   **Actor**: Bob (Marketing)
*   **Credentials**: `bob@archon.com` / `bob123`
*   **Actions**:
    1.  **切換帳號**: 登出 Alice，改用 Bob 登入 `http://localhost:5173`。
    2.  **進入頁面**: 點擊左側導航列的 **"Brand Hub"** (圖示: 📢)。
    3.  **查看靈感**:
        *   頁面左側會顯示 **"Trending Keywords"** (基於 Alice 收集的 Leads 統計)。
        *   (Future: 可在此處呼叫 Librarian 搜尋相關文章，目前版本請直接進行 AI 寫作)。
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
*Detailed architecture focusing on business value and resource control.*

**Governance**: Charlie allocates token budgets to Alice/Bob. AI usage is tracked via `gemini_logs` and visualized in the Team War Room.
**Jules (CLI Wrapper)**: Automated maintenance, Lint fixing, and Unit Test generation to maintain codebase health.
**AutoGen (DIND Sandbox)**: High-level architectural planning and multi-agent simulation for complex feature design.

### Prompt Engineering & Management (PromptOps)

To manage the "Brain" of our agents (Pitch, Logo, Blog, Refine), we define a clear evolution path from code-based to data-based management.

#### 1. Current Phase 4.4: Git-based (Transitional)
**Status**: Active Implementation
**Reason**: To ensure version control and regression testing during system stabilization.

*   **Location**: `python/src/server/prompts/*.py`
*   **Authority**: Strictly managed by **Admin/Tech Lead** via Git.
*   **Modules**: `sales_prompts.py`, `marketing_prompts.py`, `design_prompts.py`, `pm_prompts.py`.
*   **Process**: Changes require PR + E2E Test.

#### 2. Mature System: Prompt as Data (Target Strategy)
**Status**: Architecture Design (To be implemented)
**Philosophy**: "Modular Assembly" instead of "Forking".

*   **Architecture (架構面)**:
    *   **Storage**: `system_prompts` table (`key`, `content`, `version`, `last_updated_by`).
    *   **Runtime**: Agents fetch prompts dynamically from DB at runtime.
    *   **Management**: Admin updates via **Admin UI (3737)**. No server restart required.

*   **Collaboration Scenarios (協作面 - 拼湊應用場景)**:
    *   **Scenario A: The Feedback Loop (Alice & POBot)**
        1.  **Trigger**: Alice downvotes a MarketBot email ("Too formal").
        2.  **Analysis**: **POBot** analyzes feedback and generates a *Change Proposal* for `sales_prompts`.
        3.  **Approval**: Charlie reviews and approves.
        4.  **Result**: System updates prompt; next email reflects the change.
    *   **Scenario B: The Configuration (Charlie & DevBot)**
        1.  **Action**: Charlie updates `design_prompts` parameters (e.g., style="Neon Cyberpunk") in `system_prompts`.
        2.  **Execution**: **DevBot** reads new config in next run.
        3.  **Result**: New assets generated without code changes.

**Conclusion**: While Prompt Authority belongs to **Admin/Manager**, the maintenance burden is offloaded to **POBot** (Analysis) and **DevBot** (Implementation).

---

## Appendix B: User Guide (Simplified SOP)

### 人機協作標準作業程序 (SOP) - 業務實戰版

> **核心目標**：讓 AI 成為你的神隊友，將傳統兩天的工作量，壓縮在 **一小時** 內完成。

#### 🚀 核心工作流程 (The Core Workflow)

1.  **【業務情蒐】AI 獵犬出動 (Alice)**: 進入 Sales Nexus，由 MarketBot 爬取資料並生成開發信，Librarian 自動歸檔。
2.  **【行銷推廣】內容生產 (Bob)**: 在 Brand Hub 先詢問 Librarian 獲取靈感，再使用 "Draft with AI" 產出部落格，提交審核。
3.  **【管理決策】任務分派 (Charlie)**: 在 War Room 審核產出，使用 POBot 優化任務規格，並指派給 DevBot 執行。
4.  **【自主封存】結案工作流 (Alice)**: 完成後將任務拖至 Done，點擊卡片並按下「Archive Task」完成結案。

---

## Appendix C: 人機協作深度討論 (Human-Machine Collaboration Discussion)

> **「AI 不會取代人類，但使用 AI 的人會取代不使用 AI 的人。」**

### 1. 角色分工的轉變 (Shift in Roles)
在 Archon 系統中，我們定義了明確的「人機邊界」：
*   **人類 (The Driver)**: 負責定義價值（Value）、設立目標（Goal）與最終審核（Verify）。人類是工廠的「廠長」與「品質守門員」。
*   **AI (The Engine)**: 負責處理重複勞動、數據挖掘（Crawling）與結構化產出（Coding/Writing）。AI 是 24/7 不眠不休的「超級執行者」。

### 2. 協作的核心：POBot 的過渡作用
POBot 的引入是為了解決人機溝通的「語義鴻溝」。人類傾向於模糊指令（例如：做一個 Logo），而機器需要精確規格。POBot 扮演了**翻譯官**的角色，將人類的直覺轉化為 AI Agent 可執行的結構化任務。

### 3. 信任但驗證 (Trust but Verify)
系統設計的核心原則是 **Human-in-the-loop**。無論是 MarketBot 生成的開發信，還是 DevBot 產生的程式碼，都必須經過人類（Alice/Charlie）的點擊「批准」才能生效。這確保了技術的強大能力始終處於人類的倫理與商業邏輯管控之下。

### 4. 未來展望：共生進化
隨著系統進入 Phase 5，AI 將不再只是「工具」，而是具備身份（Identity）的「虛擬員工」。人類與虛擬員工的協作將從單向指派轉向雙向對話，共同驅動企業的數位轉型。

---

## Appendix D: The Symphony of Roles (Visual Workflow)

> **VISUAL WORKFLOW MOVED**: To ensure a Single Source of Truth, the detailed Mermaid diagram has been consolidated into the RBAC Matrix documentation.

Please refer to:
👉 **[PRPs/ai_docs/RBAC_Collaboration_Matrix.md#9-visual-workflow-reference-視覺化工作流參考]**

This diagram illustrates the complete daily workflow of:
- **4 Human Roles**: Alice (Sales), Bob (Marketing), Charlie (Management), Admin (Ops)
- **5 AI Agents**: MarketBot, Librarian, DevBot, POBot, Clockwork