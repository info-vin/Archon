name: "Phase 4.0.b Detailed Implementation Plan: AI as a Developer Teammate (AI 即開發者隊友)"
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
        └── developer_agent.py    # NEW Agent with refactored tools that propose changes instead of direct execution. (包含重構後工具的新 Agent，這些工具將提議變更而非直接執行。)
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

### Part 1: Backend Infrastructure (資料庫與核心服務)

Task 1.1: CREATE Database Migration Script (建立資料庫遷移腳本)
  - FILE: `migration/005_create_proposed_changes_table.sql`
  - IMPLEMENT: A new table `proposed_changes` with columns for `id`, `status` (pending, approved, rejected), `type` (file_write, git_checkout, shell_command), `request_payload` (jsonb), `user_id`, `created_at`, `updated_at`.
  - FOLLOW pattern: Existing migration scripts (`002_*`). Must be idempotent.

Task 1.2: CREATE Core Proposal Service (建立核心提議服務)
  - FILE: `python/src/server/services/propose_change_service.py`
  - IMPLEMENT: `ProposeChangeService` class with async methods:
    - `create_proposal(user_id, type, payload)`: Creates a new record in the `proposed_changes` table.
    - `get_proposal(change_id)`: Fetches a single proposal.
    - `list_proposals(status='pending')`: Lists proposals, filterable by status.
    - `approve_proposal(change_id, approver_id)`: Changes status to 'approved' and triggers execution.
    - `reject_proposal(change_id, rejector_id)`: Changes status to 'rejected'.
    - `_execute_approved_proposal(proposal)`: Private method to perform the actual action based on `proposal.type`.
  - LOGIC: The `_execute` method will contain a `match/case` statement for `file_write`, `git_checkout`, etc.

Task 1.3: CREATE API Endpoints (建立 API 端點)
  - FILE: `python/src/server/api_routes/changes_api.py`
  - IMPLEMENT: API endpoints, all protected by RBAC:
    - `GET /api/changes`: Calls `list_proposals`.
    - `GET /api/changes/{change_id}`: Calls `get_proposal`.
    - `POST /api/changes/{change_id}/approve`: Calls `approve_proposal`.
    - `POST /api/changes/{change_id}/reject`: Calls `reject_proposal`.

### Part 2: AI Agent Tooling (AI Agent 工具)

Task 2.1: CREATE Developer Agent (建立開發者 Agent)
  - FILE: `python/src/agents/developer_agent.py`
  - IMPLEMENT: A new `DeveloperAgent` class, inheriting from `BaseAgent`.

Task 2.2: IMPLEMENT Proposal-based Tools (實作基於提議的工具)
  - CONTEXT: Inside `developer_agent.py`.
  - REFACTOR: Instead of direct execution, these tools call `ProposeChangeService`.
  - IMPLEMENT tool `propose_file_write(filepath: str, content: str)`: Calls `propose_change_service.create_proposal` with type 'file_write'.
  - IMPLEMENT tool `propose_git_checkout(branch_name: str)`: Calls `propose_change_service.create_proposal` with type 'git_checkout'.
  - IMPLEMENT tool `propose_shell_command(command: str, args: list[str])`: Calls `propose_change_service.create_proposal` with type 'shell_command'. It MUST include a strict whitelist check for the `command`.
  - RETURN: All tools should return a message like "Your change to write file 'x' has been proposed and is awaiting approval."

### Part 3: Frontend User Interface (前端使用者介面)

Task 3.1: CREATE Approvals Page (建立審批頁面)
  - FILE: `enduser-ui-fe/src/pages/ApprovalsPage.tsx`
  - IMPLEMENT: A new page component that uses `react-query` to fetch data from the `GET /api/changes` endpoint and displays a list of pending changes.
  - UI: Each list item should be clickable, routing or opening a modal to a detail view.

Task 3.2: CREATE Diff Viewer Component (建立差異比對元件)
  - FILE: `enduser-ui-fe/src/components/DiffViewer.tsx`
  - IMPLEMENT: A component that takes `old_content` and `new_content` as props and displays a visual diff.
  - INTEGRATE: Use a library like `react-diff-viewer` to handle the rendering.

Task 3.3: IMPLEMENT Approval Workflow UI (實作審批工作流 UI)
  - CONTEXT: Inside the detail view of `ApprovalsPage.tsx`.
  - IMPLEMENT: Use the `DiffViewer` component to show proposed file changes.
  - IMPLEMENT: "Approve" and "Reject" buttons that trigger `react-query` mutations.
  - LOGIC: These mutations will call the `POST /api/changes/{id}/approve` and `POST /api/changes/{id}/reject` endpoints respectively. On success, they should invalidate the query for the list of changes to refresh the UI.

### Part 4: Testing and Validation (測試與驗證)

Task 4.1: CREATE Backend Tests (建立後端測試)
  - IMPLEMENT: Unit tests for `ProposeChangeService`, mocking the database interaction.
  - IMPLEMENT: Integration tests for the `changes_api.py` endpoints using FastAPI's `TestClient`. The tests should cover the full lifecycle: propose (via a mocked agent tool call), approve, and verify the outcome.

Task 4.2: CREATE Frontend Tests (建立前端測試)
  - IMPLEMENT: Component tests for `DiffViewer.tsx` to ensure it renders diffs correctly.
  - IMPLEMENT: Component tests for `ApprovalsPage.tsx`, mocking the API calls to test rendering of the list, button interactions, and state updates.

## Validation Loop (驗證迴圈)

(Adapted from project's `CONTRIBUTING_tw.md` and `Phase_3.9.1` validation patterns) (改編自專案的 `CONTRIBUTING_tw.md` 和 `Phase_3.9.1` 驗證模式)

### Level 1: Syntax & Style (Immediate Feedback) (等級 1：語法與風格 (即時回饋))
```bash
# Run after each file creation/modification - fix before proceeding (在每次檔案建立/修改後運行 - 在繼續之前修復)
ruff check src/ --fix     # Auto-format and fix linting issues for Python (自動格式化並修復 Python 的 linting 問題)
mypy src/                 # Type checking with specific files for Python (對 Python 檔案進行類型檢查)
ruff format src/          # Ensure consistent formatting for Python (確保 Python 格式一致)
# For Frontend (if applicable): (針對前端，如果適用)
# pnpm run lint --fix     # Auto-format and fix linting issues for frontend (自動格式化並修復前端的 linting 問題)
# pnpm run typecheck      # Type checking for frontend (前端的類型檢查)

# Project-wide validation (專案範圍驗證)
make lint                 # Run all project linters (執行所有專案的 linter)

# Expected: Zero errors. If errors exist, READ output and fix before proceeding. (預期：零錯誤。如果存在錯誤，閱讀輸出並在繼續之前修復。)
```
### Level 2: Unit Tests (Component Validation) (等級 2：單元測試 (元件驗證))
```bash
# Test each component as it's created (在每個元件建立後進行測試)
uv run pytest python/src/server/services/tests/test_{domain}_service.py -v # Backend service unit tests (後端服務單元測試)
uv run pytest python/src/agents/tests/test_{agent_name}.py -v        # Agent tool unit tests (Agent 工具單元測試)

# Full backend unit test suite for affected areas (受影響區域的完整後端單元測試套件)
make test-be

# Full frontend test suite for affected areas (if applicable) (受影響區域的完整前端測試套件，如果適用)
# make test-fe-project project=enduser-ui-fe # Example for frontend project (前端專案範例)

# Expected: All tests pass. If failing, debug root cause and fix implementation. (預期：所有測試通過。如果失敗，偵錯根本原因並修復實作。)
```
### Level 3: Integration Testing (System Validation) (等級 3：整合測試 (系統驗證))
```bash
# Start backend services (啟動後端服務)
make dev # Or 'make dev-docker' for full environment (或使用 'make dev-docker' 啟動完整環境)
# In a separate terminal, verify services: (在單獨的終端機中，驗證服務：)
curl -f http://localhost:8181/health || echo "Archon Server health check failed" # Backend health check (後端健康檢查)
# curl -f http://localhost:8000/health || echo "Knowledge API health check failed" # Other services (其他服務)

# Feature-specific API endpoint testing (功能特定的 API 端點測試)
# Example: (範例)
# curl -X POST http://localhost:8181/api/changes -H "Content-Type: application/json" -d '{"proposal_type": "file", ...}' | jq .

# End-to-End Integration Tests (端對端整合測試)
# These simulate the full user journey and AI workflow. (這些模擬完整的用戶旅程和 AI 工作流程。)
make test # Run all project tests, including E2E (運行所有專案測試，包括 E2E)
# Or specific E2E test: (或特定的 E2E 測試)
# make test-fe-project project=enduser-ui-fe # (Run E2E tests for enduser-ui-fe) (運行 enduser-ui-fe 的 E2E 測試)

# Expected: All integrations working, proper responses, no connection errors. (預期：所有整合正常工作，回應正確，無連線錯誤。)
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
