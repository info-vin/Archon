name: "Phase 4.0 Refactored Plan: AI as a Developer Teammate (AI 即開發者隊友)"
description: |
  A detailed, phased, and implementation-focused plan to elevate the AI Agent into a "Developer Teammate." 
  (一份詳細、分階段且以實作為中心的計畫，旨在將 AI Agent 提升為「開發者隊友」。)
  This plan refactors the original vision into an executable blueprint, prioritizing a human-in-the-loop security model.
  (此計畫將原始願景重構成一個可執行的藍圖，並以「人類監督」的安全模型為優先。)
  It outlines a phased approach, starting with a secure foundation (The Cockpit), then adding version control, and finally enabling a full end-to-end workflow with testing capabilities.
  (它概述了一個分階段的方法，從一個安全的基礎（駕駛艙）開始，然後增加版本控制，最終實現一個具備測試能力的完整端對端工作流程。)

---

## Goal (目標)

**Feature Goal (功能目標)**: To evolve the AI Agent from a "task executor" into a "code contributor" capable of safely performing Git operations, file modifications, and running tests within a human-supervised workflow.
(將 AI Agent 從「任務執行者」演進為「程式碼貢獻者」，使其能夠在人類監督的工作流程中，安全地執行 Git 操作、檔案修改及運行測試。)

**Deliverable (交付成果)**: A functional end-to-end workflow where a task assigned to a "Developer AI" results in a new commit on a feature branch. This commit is only created after a human developer reviews and approves each high-risk action (e.g., file write, commit) through a dedicated UI.
(一個功能性的端對端工作流程，其中分配給「開發者 AI」的任務會產生一個新的 feature 分支 commit。此 commit 僅在人類開發者透過專屬 UI 審查並批准每一個高風險操作（例如，檔案寫入、提交）後才能建立。)

**Success Definition (成功定義)**: An AI Agent can successfully checkout a new branch, propose a code modification, run tests against it, and commit the change, but ONLY after each of these high-risk actions is explicitly approved by an authorized human user via the `enduser-ui-fe`.
(一個 AI Agent 可以成功 checkout 一個新分支、提議程式碼修改、對其運行測試並提交變更，但前提是這些高風險操作中的每一個都必須由授權的人類使用者透過 `enduser-ui-fe` 明確批准。)

## Why (為何要做)

- **Business value (商業價值)**: This bridges the "last mile" of AI-driven development. It moves beyond simple code generation to integrate the AI directly into the project's version control and CI/CD pipeline, drastically increasing development velocity.
  (這打通了 AI 驅動開發的「最後一哩路」。它超越了簡單的程式碼生成，將 AI 直接整合到專案的版本控制和 CI/CD 流程中，從而大幅提升開發速度。)
- **User impact (使用者影響)**: It transforms the AI from a simple assistant into a genuine, albeit junior, teammate that can handle tedious or repetitive coding tasks, freeing up human developers to focus on more complex architectural challenges.
  (它將 AI 從一個簡單的助理轉變為一個真正的（儘管是初階的）隊友，能夠處理繁瑣或重複的編碼任務，從而讓人類開發者能專注於更複雜的架構挑戰。)
- **Problems this solves (解決的問題)**: It automates the manual, error-prone process of copy-pasting AI-generated code, running tests, and creating commits, all within a secure and auditable framework.
  (它在一個安全且可審計的框架內，自動化了手動複製貼上 AI 生成程式碼、運行測試和建立 commit 的易錯流程。)

## What (做什麼)

This phase will introduce several new components and workflows: (此階段將引入幾個新元件和工作流程：)
1.  A new UI section within `enduser-ui-fe` for reviewing and approving/rejecting AI-proposed code changes, complete with a "diff" view for clarity.
    (在 `enduser-ui-fe` 中建立一個新的 UI 區塊，用於審查和批准/拒絕 AI 提議的程式碼變更，並附有清晰的「差異」視圖。)
2.  A new backend security framework and database schema to manage the "propose-approve-execute" lifecycle for all high-risk agent actions.
    (一個新的後端安全框架和資料庫結構，用於管理所有高風險 Agent 操作的「提議-批准-執行」生命週期。)
3.  An expanded and secured set of tools for the AI Agent, covering file operations, version control, and shell execution, where each tool can only "propose" an action rather than executing it directly.
    (為 AI Agent 提供一組擴充且安全的工具集，涵蓋檔案操作、版本控制和 shell 執行，其中每個工具只能「提議」一個操作，而不能直接執行。)

### Success Criteria (成功標準)

- [ ] An AI Agent's attempt to modify a file results in a "pending change" record in the database, not a direct file write. (AI Agent 嘗試修改檔案會在資料庫中產生一筆「待處理變更」記錄，而非直接寫入檔案。)
- [ ] An authorized human user can view this pending change, including a code diff, in the `enduser-ui-fe`. (經授權的人類使用者可以在 `enduser-ui-fe` 中查看此待處理變更，包括程式碼差異。)
- [ ] A user's click on the "Approve" button in the UI successfully triggers the backend to execute the file modification. (使用者在 UI 中點擊「批准」按鈕會成功觸發後端執行檔案修改。)
- [ ] A user's click on the "Reject" button successfully cancels the proposed change. (使用者點擊「拒絕」按鈕會成功取消提議的變更。)
- [ ] The entire "propose-approve-execute" workflow is strictly enforced for all sensitive tool calls, including `git branch`, `git commit`, and `run_shell_command`. (整個「提議-批准-執行」工作流程對所有敏感的工具呼叫（包括 `git branch`, `git commit`, 和 `run_shell_command`）都嚴格執行。)
- [ ] An unauthorized user cannot view or approve pending changes. (未經授權的使用者無法查看或批准待處理的變更。)

## All Needed Context (所有需要的上下文)

### Documentation & References (文件與參考資料)

```yaml
# MUST READ - Include these in your context window (必讀 - 將這些包含在您的上下文中)
- file: PRPs/Phase_4.0_AI_as_Developer_Plan.md
  why: Contains the original vision, sequence diagrams, and security principles that are the foundation of this refactored plan. (包含作為此重構計畫基礎的原始願景、時序圖和安全原則。)
  critical: The "Security by Design" section is mandatory reading; this implementation must adhere to it strictly. (「安全設計」一節是必讀內容；此實作必須嚴格遵守。)

- file: CONTRIBUTING_tw.md
  why: Provides established development patterns, especially the Git workflow and testing strategies (`make test`, `make test-be`). (提供既有的開發模式，特別是 Git 工作流程和測試策略。)
  pattern: All new agent tools must be designed with the existing SOPs in mind. (所有新的 Agent 工具都必須基於現有的標準作業流程進行設計。)
  gotcha: The strict separation of concerns between services, APIs, and tools. (服務、API 和工具之間的嚴格關注點分離。)

- file: GEMINI.md
  why: Contains the historical log of debugging sessions and architectural decisions. (包含偵錯會話和架構決策的歷史日誌。)
  section: "Key Lessons & Debugging Patterns" provides insight into recurring issues (e.g., async testing, environment configuration) that must be considered when building new tests for this feature. (「關鍵教訓與偵錯模式」一節提供了對重複出現問題的洞察，在為此功能建立新測試時必須考慮。)
```

### Desired Codebase tree with files to be added and responsibility of file (期望的程式碼庫結構與待增檔案及其職責)

```bash
python/
└── src/
    ├── server/
    │   ├── api_routes/
    │   │   └── changes_api.py      # New API endpoints for listing, proposing, and approving changes. (用於列出、提議和批准變更的新 API 端點。)
    │   └── services/
    │       └── propose_change_service.py # New service to manage the lifecycle of proposed changes. (用於管理提議變更生命週期的新服務。)
    └── agents/
        └── tools/
            ├── file_operation_tools.py # MODIFIED to propose changes instead of direct execution. (修改為提議變更而非直接執行。)
            ├── version_control_tools.py # NEW tools for proposing Git operations. (用於提議 Git 操作的新工具。)
            └── execution_tools.py       # NEW tools for proposing shell commands. (用於提議 shell 命令的新工具。)
enduser-ui-fe/
└── src/
    ├── pages/
    │   └── ApprovalsPage.tsx         # NEW page to list and manage pending approvals. (用於列出和管理待批准項目的新頁面。)
    └── components/
        └── DiffViewer.tsx            # NEW component to render code differences for review. (用於呈現程式碼差異以供審查的新元件。)
migration/
└── 005_create_proposed_changes_table.sql # NEW migration script for the database. (用於資料庫的新遷移腳本。)
```

## Implementation Blueprint (實作藍圖)

### Phase 4.0: The Secure Cockpit (Foundation) (階段 4.0：安全駕駛艙 (基礎))
*Focus: Build the core "propose-approve-execute" security loop.* (焦點：建立核心的「提議-批准-執行」安全迴圈。)

```yaml
Task 1: CREATE migration/005_create_proposed_changes_table.sql (任務 1：建立遷移腳本)
  - IMPLEMENT: A new table `proposed_changes` with columns for `id`, `status` (pending, approved, rejected), `type` (file, git, shell), `request_payload` (jsonb), `created_at`, etc. (實作：一個新的 `proposed_changes` 表，包含 id, status, type, request_payload 等欄位。)
  - FOLLOW pattern: Existing migration scripts (`002_*`). Must be idempotent. (遵循模式：既有的遷移腳本 (`002_*`)。必須是冪等的。)

Task 2: CREATE python/src/server/services/propose_change_service.py (任務 2：建立服務)
  - IMPLEMENT: `ProposeChangeService` class with async methods to `create_proposal`, `get_proposal`, `list_proposals`, and `execute_proposal`. (實作：包含非同步方法的 `ProposeChangeService` 類別。)
  - LOGIC: The `execute_proposal` method will contain a large `match/case` statement based on the proposal type to perform the actual action (e.g., write file, run git command). (邏輯：`execute_proposal` 方法將根據提議類型包含一個大型的 `match/case` 語句來執行實際操作。)
  - DEPENDENCIES: Database session. (依賴：資料庫會話。)

Task 3: CREATE python/src/server/api_routes/changes_api.py (任務 3：建立 API 路由)
  - IMPLEMENT: API endpoints (`GET /api/changes`, `GET /api/changes/{id}`, `POST /api/changes/{id}/approve`, `POST /api/changes/{id}/reject`). (實作：相關的 API 端點。)
  - SECURITY: Endpoints must be protected by RBAC, ensuring only authorized users can approve/reject. (安全性：端點必須受 RBAC 保護，確保只有授權使用者可以批准/拒絕。)

Task 4: MODIFY python/src/agents/tools/file_operation_tools.py (任務 4：修改 Agent 工具)
  - REFACTOR: `write_file` and `replace_in_file` tools. (重構：`write_file` 和 `replace_in_file` 工具。)
  - LOGIC: Instead of writing to the filesystem, these tools will now call the `ProposeChangeService` to create a new "file" type proposal. They will return a message to the AI like "Your change has been proposed and is awaiting approval." (邏輯：這些工具現在將呼叫 `ProposeChangeService` 來建立一個「檔案」類型的提議，而不是直接寫入檔案系統。它們會向 AI 回傳一條訊息，如「您的變更已提議並等待批准」。)

Task 5: CREATE enduser-ui-fe/src/pages/ApprovalsPage.tsx (任務 5：建立前端頁面)
  - IMPLEMENT: A new page that fetches and displays a list of pending changes from the `GET /api/changes` endpoint. (實作：一個從 `GET /api/changes` 端點獲取並顯示待處理變更列表的新頁面。)
  - UI: Each item should be clickable, leading to a detail view. (UI：每個項目都應該是可點擊的，並導向詳細視圖。)

Task 6: CREATE enduser-ui-fe/src/components/DiffViewer.tsx (任務 6：建立前端元件)
  - IMPLEMENT: A component that takes `old_string` and `new_string` and displays a clear diff. This will be used in the approval detail view. Libraries like `react-diff-viewer` can be considered. (實作：一個接收 `old_string` 和 `new_string` 並顯示清晰差異的元件。這將用於批准詳細視圖。可以考慮使用像 `react-diff-viewer` 這樣的庫。)

Task 7: CREATE Tests for the entire loop (任務 7：為整個迴圈建立測試)
  - IMPLEMENT: Backend unit tests for the `ProposeChangeService`. (實作：後端 `ProposeChangeService` 的單元測試。)
  - IMPLEMENT: Backend integration tests for the `changes_api` endpoints. (實作：後端 `changes_api` 端點的整合測試。)
  - IMPLEMENT: Frontend component tests for `ApprovalsPage` and `DiffViewer`. (實作：前端 `ApprovalsPage` 和 `DiffViewer` 的元件測試。)
```

### Phase 4.1: Integrate 104 Job Board API (階段 4.1：整合 104 人力銀行 API)
*Focus: Connect the system to a real-world, external API for practical marketing analysis.* (焦點：將系統連接到真實世界的外部 API，以進行實用的市場分析。)

**User Persona (使用者畫像)**: Marketing Analyst (行銷分析師).

**Use Case (使用案例)**: The analyst needs to quickly understand the hiring landscape for "SaaS" companies in a specific region. They use the Archon UI, enter "SaaS" as a keyword, and instantly receive a list of current, real-world job descriptions. They use this data to analyze competitor messaging and tailor their own company's marketing and recruitment campaigns, all without leaving the platform or manually scraping websites. (分析師需要快速了解特定地區「SaaS」公司的招聘情況。他們使用 Archon UI，輸入「SaaS」作為關鍵字，立即獲得當前真實的職位描述列表。他們利用這些數據來分析競爭對手的訊息，並調整自己公司的行銷和招聘活動，所有操作都在平台內完成，無需手動抓取網站。)

```yaml
Task 1: CREATE python/src/server/services/job_board_service.py (任務 1：建立職缺看板服務)
  - IMPLEMENT: A `JobBoardService` with a method `search_104_jobs(keyword: str)`. (實作：一個包含 `search_104_jobs` 方法的 `JobBoardService`。)
  - LOGIC: This service will use `httpx` to call the 104 API, handle authentication with an API key stored in environment variables, and parse the JSON response. (邏輯：此服務將使用 `httpx` 呼叫 104 API，使用環境變數中儲存的 API 金鑰進行身份驗證，並解析 JSON 回應。)

Task 2: CREATE a new API route for jobs. (任務 2：為職缺建立新的 API 路由)
  - IMPLEMENT: A new endpoint `POST /api/marketing/fetch-jobs` that takes a keyword and returns the data from the `JobBoardService`. (實作：一個新的 `POST /api/marketing/fetch-jobs` 端點，接收關鍵字並從 `JobBoardService` 返回數據。)

Task 3: CREATE a new UI page in `enduser-ui-fe`. (任務 3：在 `enduser-ui-fe` 中建立新 UI 頁面)
  - IMPLEMENT: A simple page with a text input for the keyword and a button to trigger the API call. The results will be displayed in a list or table. (實作：一個帶有關鍵字輸入框和觸發 API 呼叫按鈕的簡單頁面。結果將顯示在列表或表格中。)
```

### Phase 4.2: HR Statistics Dashboard (階段 4.2：人事統計儀表板)
*Focus: Provide managers with data-driven insights through data visualization.* (焦點：透過數據視覺化為管理者提供數據驅動的洞察。)

**User Persona (使用者畫像)**: Project Manager / Team Lead (專案經理 / 團隊負責人).

**Use Case (使用案例)**: Before the weekly sprint planning meeting, the manager opens the "Stats Dashboard" in Archon. They immediately see a bar chart showing the task distribution across the team, identifying that one developer is overloaded while another has available bandwidth. They also see a pie chart showing that a high number of tasks are "In Review." This allows them to start the meeting with concrete data, facilitating a quick and effective discussion about reallocating work and addressing review bottlenecks. (在每週的衝刺計畫會議之前，經理在 Archon 中打開「統計儀表板」。他們立即看到一個顯示團隊任務分配的長條圖，從而識別出某位開發人員超載，而另一位則有空閒。他們還看到一個顯示大量任務處於「審查中」狀態的圓餅圖。這使他們能夠帶著具體數據開始會議，從而促進關於重新分配工作和解決審查瓶頸的快速有效討論。)

```yaml
Task 1: CREATE backend statistics endpoints. (任務 1：建立後端統計端點)
  - IMPLEMENT: `GET /api/stats/tasks-by-employee`, `GET /api/stats/tasks-by-status`, etc., as originally planned. (實作：如原計畫的 `GET /api/stats/tasks-by-employee` 等端點。)
  - LOGIC: These endpoints will perform SQL aggregate queries against the `archon_tasks` and `profiles` tables. (邏輯：這些端點將對 `archon_tasks` 和 `profiles` 表執行 SQL 聚合查詢。)

Task 2: CHOOSE and INTEGRATE a charting library. (任務 2：選擇並整合圖表庫)
  - ACTION: Add `recharts` to `enduser-ui-fe`'s `package.json`. (行動：將 `recharts` 加入 `enduser-ui-fe` 的 `package.json`。)

Task 3: CREATE `HRStatsPage.tsx` in `enduser-ui-fe`. (任務 3：在 `enduser-ui-fe` 中建立 `HRStatsPage.tsx`)
  - IMPLEMENT: A new page that fetches data from the stats endpoints upon loading. (實作：一個在載入時從統計端點獲取數據的新頁面。)
  - UI: Use components from `recharts` (e.g., `<BarChart>`, `<PieChart>`) to visualize the data. (UI：使用 `recharts` 的元件來視覺化數據。)
```

## Validation Loop (驗證迴圈)

(Copied from `prp_base.md` template) (從 `prp_base.md` 範本複製)

### Level 1: Syntax & Style (Immediate Feedback) (等級 1：語法與風格 (即時回饋))
```bash
ruff check src/ --fix && mypy src/ && ruff format src/
```
### Level 2: Unit Tests (Component Validation) (等級 2：單元測試 (元件驗證))
```bash
uv run pytest src/services/tests/ -v && uv run pytest src/tools/tests/ -v
```
### Level 3: Integration Testing (System Validation) (等級 3：整合測試 (系統驗證))
```bash
make dev # Start backend (啟動後端)
# In another terminal (在另一個終端機中)
curl -f http://localhost:8181/health || echo "Service health check failed"
# ... further integration tests for new endpoints ... (新端點的進一步整合測試)
```

## Final Validation Checklist (最終驗證清單)
### Technical Validation (技術驗證)
- [ ] All `Implementation Blueprint` tasks completed. (所有「實作藍圖」任務已完成。)
- [ ] All tests pass: `make test` (所有測試通過)
- [ ] No linting errors: `make lint` (沒有 linting 錯誤)
- [ ] Backend starts successfully with new components. (後端與新元件成功啟動。)
### Feature Validation (功能驗證)
- [ ] All `Success Criteria` from the "What" section are met. (所有「做什麼」一節中的「成功標準」均已滿足。)
- [ ] Manual E2E test of the approval workflow is successful. (批准工作流程的手動端對端測試成功。)
- [ ] Error cases (e.g., rejecting a change, unauthorized access) are handled gracefully. (錯誤案例（例如，拒絕變更、未經授權的存取）已妥善處理。)

## Anti-Patterns to Avoid (要避免的反模式)
- ❌ Do not allow any tool to directly execute a high-risk action. Every sensitive operation must go through the `ProposeChangeService`. (不允許任何工具直接執行高風險操作。每個敏感操作都必須經過 `ProposeChangeService`。)
- ❌ Do not implement the "shell" execution tool with a loose or absent whitelist. This is a major security vulnerability. (不要在沒有嚴格白名單的情況下實作「shell」執行工具。這是一個重大的安全漏洞。)
- ❌ Don't skip creating tests for the approval logic. The security of the entire system depends on it. (不要跳過為批准邏輯建立測試。整個系統的安全性都依賴於它。)
