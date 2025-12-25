---
name: "PRP 3.9.1: End-User UI Implementation Tasks - AI as a Teammate (繁體中文版)"
description: "Detailed implementation tasks for realizing the 'AI as a Teammate' vision within the enduser-ui-fe, transitioning from mock data to real API calls, and integrating AI agent assignment. (實現 enduser-ui-fe 中「AI 作為隊友」願景的詳細實作任務，包含從模擬資料過渡到真實 API 呼叫，並整合 AI 代理指派功能。)"
---

## Original Story (原始故事)

**AI as a Teammate Vision (AI 作為隊友的願景):**
Transform Archon into a platform where users can seamlessly assign tasks to either human colleagues or specialized AI Agents directly from the `enduser-ui-fe` interface. These AI Agents will then autonomously execute or assist in task completion, enabling true human-AI collaboration. (將 Archon 轉變為一個平台，讓使用者可以直接從 `enduser-ui-fe` 介面將任務無縫地指派給人類同事或專業的 AI 代理。這些 AI 代理將自主執行或協助完成任務，實現真正的人機協作。)

## Story Metadata (故事元資料)

**Story Type (故事類型)**: Feature (功能)
**Estimated Complexity (預估複雜度)**: High (高)
**Primary Systems Affected (主要受影響系統)**: `enduser-ui-fe`, `archon-server`, `archon-mcp`, `archon-agents`, Supabase Database

---

## CONTEXT REFERENCES (情境參考資料)

- **enduser-ui-fe/src/services/api.ts**: This file currently contains the mock data fallback mechanism. Understanding its structure is critical for migrating to real API calls. (此檔案目前包含模擬資料的備用機制。理解其結構對於遷移到真實 API 呼叫至關重要。)
- **PRPs/ai_docs/ARCHITECTURE.md**: Provides the overall system architecture, including FastAPI backend and React frontend, which is essential for understanding integration points. (提供整體系統架構，包含 FastAPI 後端和 React 前端，這對於理解整合點至關重要。)
- **PRPs/ai_docs/DATA_FETCHING_ARCHITECTURE.md**: Details the TanStack Query usage in the frontend for data fetching, caching, and mutations. (詳細說明前端使用 TanStack Query 進行資料獲取、快取和突變的方式。)
- **PRPs/ai_docs/API_NAMING_CONVENTIONS.md**: Standardizes backend endpoint and frontend service method naming. (標準化後端端點和前端服務方法的命名。)
- **PRPs/ai_docs/UI_STANDARDS.md**: Essential for ensuring all new UI components and modifications adhere to project styling, accessibility, and best practices. (確保所有新的 UI 元件和修改都符合專案樣式、可訪問性和最佳實踐。)
- **PRPs/ai_docs/QUERY_PATTERNS.md**: Guides the creation of query keys and mutations using TanStack Query. (指導使用 TanStack Query 建立查詢鍵和突變。)
- **TODO.md**: The sequence diagram depicts the target architecture where `enduser-ui-fe` communicates with `archon-server` which then interacts with Supabase. This PRP bridges the current mock-data implementation with this target architecture. (時序圖描繪了 `enduser-ui-fe` 與 `archon-server` 通訊，然後 `archon-server` 與 Supabase 互動的目標架構。此 PRP 將目前的模擬資料實作與此目標架構連接起來。)

---

## IMPLEMENTATION TASKS (實作任務)

### Phase 1: Frontend Data Source Transition (`enduser-ui-fe`) (前端資料源轉換)

### MODIFY enduser-ui-fe/src/services/api.ts: (修改 enduser-ui-fe/src/services/api.ts)

- **REMOVE (移除)**: All `MOCK_EMPLOYEES`, `MOCK_PROJECTS`, `MOCK_TASKS`, `MOCK_DOCUMENT_VERSIONS`, `MOCK_BLOG_POSTS` arrays. (所有模擬資料陣列)
- **REMOVE (移除)**: The `mockApi` object and its implementation. (模擬 API 物件及其實作)
- **REMOVE (移除)**: The `useMockData` boolean and the conditional export `export const api = useMockData ? mockApi : supabaseApi;`. (移除 `useMockData` 布林值和條件式導出)
- **UPDATE (更新)**: Ensure `export const api = supabaseApi;` is the default. (確保 `export const api = supabaseApi;` 為預設導出)
- **UPDATE (更新)**: Modify `getSupabaseConfig` to robustly handle missing `localStorage` items, potentially throwing errors or displaying a critical warning to the user to configure them. Consider initial configuration from environment variables if not found in localStorage. (修改 `getSupabaseConfig` 以穩健處理缺少的 `localStorage` 項目，可能拋出錯誤或向使用者顯示關鍵警告以配置它們。如果 `localStorage` 中未找到，可考慮從環境變數進行初始配置。)
- **VALIDATE (驗證)**: `uv run python -c "from services.user_service import UserService; print('✓ Import successful')"`

### UPDATE enduser-ui-fe/src/features/**/services/*.ts & enduser-ui-fe/src/features/**/hooks/*.ts: (更新 enduser-ui-fe/src/features/**/services/*.ts 和 enduser-ui-fe/src/features/**/hooks/*.ts)

- **ADAPT (調整)**: All existing frontend services and TanStack Query hooks to explicitly use the `supabaseApi` methods (formerly `api.getTasks()`, `api.getProjects()`, etc.). (所有現有的前端服務和 TanStack Query 鉤子明確使用 `supabaseApi` 方法)
- **REMOVE (移除)**: Any remaining logic that checks for mock data usage. (任何剩餘的檢查模擬資料使用的邏輯)
- **ENSURE (確保)**: Error handling is in place for all API calls. (所有 API 呼叫都有錯誤處理)
- **VALIDATE (驗證)**: Run all frontend unit and integration tests (`make test-fe`). (執行所有前端單元測試和整合測試)

### Phase 2: Backend API Enhancements (`archon-server`) (後端 API 增強)

### CREATE python/src/server/api_routes/agents_api.py: (創建 python/src/server/api_routes/agents_api.py)

- **IMPLEMENT (實作)**: `GET /api/agents/assignable` endpoint to return a list of available AI agents. (實作 `GET /api/agents/assignable` 端點以返回可用 AI 代理列表)
- **LOGIC (邏輯)**: This endpoint should query a new or existing service that defines/manages AI agents and their capabilities. (此端點應查詢定義/管理 AI 代理及其功能的新服務或現有服務)
- **NAMING (命名)**: Follow `API_NAMING_CONVENTIONS.md`. (遵循 `API_NAMING_CONVENTIONS.md`)
- **VALIDATE (驗證)**: `curl http://localhost:8181/api/agents/assignable` returns a valid JSON array of AI agents.

### MODIFY python/src/server/api_routes/tasks_api.py: (修改 python/src/server/api_routes/tasks_api.py)

- **UPDATE (更新)**: `POST /api/tasks` and `PUT /api/tasks/{task_id}` endpoints to support assigning tasks to AI agents. (更新 `POST /api/tasks` 和 `PUT /api/tasks/{task_id}` 端點以支持將任務指派給 AI 代理)
- **LOGIC (邏輯)**: When an AI agent ID is provided as an assignee, trigger a background task (via `archon-mcp` or direct service call) to notify or activate the AI agent. (當提供 AI 代理 ID 作為指派人時，觸發後台任務（透過 `archon-mcp` 或直接服務呼叫）通知或激活 AI 代理。)
- **VALIDICATE (驗證)**: Ensure assignment logic correctly distinguishes human users from AI agents. (確保指派邏輯正確區分人類使用者和 AI 代理)
- **VALIDATE (驗證)**: `uv run pytest python/src/server/api_routes/tasks_api.py`

### MODIFY python/src/server/services/task_service.py: (修改 python/src/server/services/task_service.py)

- **IMPLEMENT (實作)**: Logic to interact with `archon-mcp` or `archon-agents` service when a task is assigned to an AI agent. (實作當任務指派給 AI 代理時，與 `archon-mcp` 或 `archon-agents` 服務互動的邏輯。)
- **ADD (新增)**: New methods for `notify_ai_agent_of_assignment(task_id, agent_id)`. (新增 `notify_ai_agent_of_assignment(task_id, agent_id)` 方法。)
- **UPDATE (更新)**: `assign_task_to_agent(task_id, agent_id)` method. (更新 `assign_task_to_agent(task_id, agent_id)` 方法。)
- **VALIDATE (驗證)**: `uv run pytest python/src/server/services/task_service.py`

### Phase 3: UI for AI Agent Assignment (`enduser-ui-fe`) (前端 AI 代理指派介面)

### NOTE on Implementation Deviation: (關於實作差異的說明：)
- The functionality was implemented directly in `TaskModal.tsx` instead of creating a separate `useAgentQueries.ts` hook. (此功能直接在 `TaskModal.tsx` 中實作，並未創建獨立的 `useAgentQueries.ts` 鉤子。)

### MODIFY enduser-ui-fe/src/components/TaskModal.tsx: (修改 enduser-ui-fe/src/components/TaskModal.tsx)

- **INTEGRATE (整合)**: Call `api.getAssignableUsers()` and `api.getAssignableAgents()` to fetch all assignable options. (呼叫 `api.getAssignableUsers()` 和 `api.getAssignableAgents()` 以獲取所有可指派選項。)
- **UPDATE (更新)**: The assignee selection dropdown to merge and display both human users and AI agents. (更新指派人選擇下拉選單，以合併並顯示人類使用者和 AI 代理。)
- **UI/UX (使用者介面/體驗)**: Differentiate AI agents visually by prepending `(AI)` to their names. (透過在名稱前加上 `(AI)` 來視覺上區分 AI 代理。)
- **VALIDATE (驗證)**: Manually test task creation and assignment to an AI agent in the browser. (手動測試在瀏覽器中創建和指派任務給 AI 代理。)

### Phase 4: Validate and Implement Agent Execution Workflow (驗證並實作代理執行工作流)

### Task 4.1: Create End-to-End Integration Test (創建端到端整合測試)
- **Goal (目標)**: Create a single, automated integration test that validates the entire "AI as a Teammate" workflow, from task assignment to agent callback. This test will serve as the safety net and executable specification for all future agent development. (建立一個自動化整合測試，驗證從任務指派到代理回呼的完整「AI 作為隊友」工作流。此測試將作為未來所有代理開發的安全網與可執行的規範。)
- **File (檔案)**: `python/tests/server/test_projects_api_agent_callback.py`
- **Note on Implementation (實作說明)**: The core end-to-end agent workflow, including task assignment and agent callback, was implemented in this file, fulfilling the goal of Task 4.1, although the filename differs from the original plan. (核心的端到端代理工作流，包括任務指派和代理回呼，已在此檔案中實現，達成了 Task 4.1 的目標，儘管檔名與原計畫不同。)
- **Key Implementation Pattern (關鍵實作模式)**:
    - **Patching Strategy**: Must follow the "Golden Pattern" established in `commit 518312d`. Patch singleton services (like `agent_service`) at the module level *before* `app` is imported. Use `setup_module` and `teardown_module` for patch lifecycle. (必須遵循 `commit 518312d` 中建立的「黃金模式」。在 `app` 導入前，於模組級別 `patch` 單例服務（如 `agent_service`），並使用 `setup_module` 和 `teardown_module` 管理 `patch` 生命週期。)
    - **Workflow Stages**: The test must cover three stages: (測試必須涵蓋三個階段：)
        1.  **Task Assignment**: `POST /api/tasks` with an AI assignee, and assert `agent_service.run_agent_task` is `awaited`. (使用 AI 指派人 `POST /api/tasks`，並斷言 `agent_service.run_agent_task` 被 `await`。)
        2.  **Simulated Agent Callback**: Mock `run_agent_task` to use the `TestClient` to call back to `/api/tasks/{id}/agent-status` and `/api/tasks/{id}/agent-output`. (Mock `run_agent_task` 以便使用 `TestClient` 回呼 `/api/tasks/{id}/agent-status` 和 `/api/tasks/{id}/agent-output`。)
        3.  **Result Verification**: Assert that the underlying service methods (`task_service.update_task`, `task_service.save_agent_output`) are correctly called. (斷言底層的服務方法（`task_service.update_task`, `task_service.save_agent_output`）被正確呼叫。)
- **VALIDATE (驗證)**: `make test-be` must pass with zero new errors. (必須通過 `make test-be` 且沒有新錯誤。)

### Task 4.2: Implement `CodeReviewAgent` based on Test Pattern (基於測試模式實作 `CodeReviewAgent`)
- **Goal (目標)**: Create a new, simple agent that conforms to the workflow validated in Task 4.1. The `CodeReviewAgent` was implemented to fulfill this, serving as a concrete example. (創建一個符合任務 4.1 中已驗證工作流的、簡單的新代理。`CodeReviewAgent` 的實作即是為了達成此目標，作為一個具體的範例。)
- **File (檔案)**: `python/src/agents/features/code_review_agent.py`
- **Logic (邏輯)**: The agent is triggered by `agent_service.run_agent_task`. It receives code, uses the `llm_provider` to generate a mock review, and then calls back to the `archon-server` with the results. (該代理由 `agent_service.run_agent_task` 觸發，接收程式碼，使用 `llm_provider` 生成模擬的審查，然後回呼 `archon-server` 並附上結果。)
- **VALIDATE (驗證)**: `uv run pytest python/src/agents/features/tests/test_code_review_agent.py`

### Phase 5: Automated End-to-End Workflow Validation (自動化端到端工作流驗證)

#### Task 5.1: Scaffold E2E Test Suite for "AI as a Teammate" (為「AI 作為隊友」搭建 E2E 測試套件)
- **Goal (目標)**: 建立一個新的 Vitest/Playwright 測試檔案，專門用於驗證基於 `MOCK_BLOG_POSTS` 業務案例的完整使用者操作流程。此套件將模擬使用者在 UI 上的行為，並驗證後端與 AI Agent 的互動是否如預期。
- **Action (行動)**:
    - 創建新檔案 `enduser-ui-fe/tests/e2e/ai-teammate-workflows.spec.ts`。
    - 在測試設定 (`setup`) 中，配置測試環境以模擬使用者登入，並確保可以攔截和監控對 `archon-server` 的 API 請求。
- **VALIDATE (驗證)**: 能夠在該檔案中執行一個空的 `test('setup complete')` 並且通過。`pnpm test:e2e tests/e2e/ai-teammate-workflows.spec.ts`。

#### Task 5.2: Implement E2E Test for "Marketing Campaign" Use Case (實作「行銷活動」使用案例的 E2E 測試)
- **Goal (目標)**: 自動化驗證行銷人員指派 AI 撰寫部落格文章的完整流程。
- **Scenario (場景)**: 基於 `MOCK_BLOG_POSTS[0]` 的 "AI-Powered Content Creation" 案例。
- **Action (行動)**:
    1.  編寫測試，模擬使用者點擊「新增任務」。
    2.  在任務標題中輸入 "Draft a blog post about our new AI features"。
    3.  在指派人下拉選單中，選擇名為 "Content Writer AI" 的代理。
    4.  點擊「儲存」。
    5.  **斷言 (Assert)**:
        -   一個 `POST /api/tasks` 請求被發送到後端，其 `assignee_id` 對應 "Content Writer AI"。
        -   UI 上的任務狀態短時間內應顯示為 "AI Processing" 或類似狀態。
        -   (模擬 Agent 回呼後) 任務最終狀態變為 "Completed" 或 "Needs Review"。
        -   (模擬 Agent 回呼後) 任務詳情中出現由 AI 生成的內容（一個 `agent_output`）。
- **VALIDATE (驗證)**: `pnpm test:e2e tests/e2e/ai-teammate-workflows.spec.ts --test-name="Marketing Campaign"`。

#### Task 5.3: Implement E2E Test for "Technical Support" Use Case (實作「技術支援」使用案例的 E2E 測試)
- **Goal (目標)**: 自動化驗證技術支援工程師指派 AI 分析日誌的流程。
- **Scenario (場景)**: 基於 `MOCK_BLOG_POSTS[1]` 的 "Automated Log Analysis" 案例。
- **Action (行動)**:
    1.  編寫測試，模擬使用者創建一個標題為 "Analyze user error logs for ticket #12345" 的任務。
    2.  在任務描述中貼上一段模擬的錯誤日誌。
    3.  在指派人下拉選單中，選擇名為 "Log Analyzer AI" 的代理。
    4.  點擊「儲存」。
    5.  **斷言 (Assert)**:
        -   `POST /api/tasks` 請求被正確發送。
        -   後續模擬 Agent 回呼，斷言任務詳情中出現分析結果，例如 "Root cause identified: NullPointerException in ... "。
- **VALIDATE (驗證)**: `pnpm test:e2e tests/e2e/ai-teammate-workflows.spec.ts --test-name="Technical Support"`。

#### Task 5.4: Implement E2E Test for "Sales Outreach" Use Case (實作「業務拓展」使用案例的 E2E 測試)
- **Goal (目標)**: 自動化驗證業務開發代表指派 AI 生成潛在客戶列表的流程。
- **Scenario (場景)**: 基於 `MOCK_BLOG_POSTS[2]` 的 "Intelligent Lead Generation" 案例。
- **Action (行動)**:
    1.  編寫測試，模擬使用者創建一個標題為 "Generate lead list for ACME Corp in the finance sector" 的任務。
    2.  在指派人下拉選單中，選擇名為 "Sales Intelligence AI" 的代理。
    3.  點擊「儲存」。
    4.  **斷言 (Assert)**:
        -   `POST /api/tasks` 請求被正確發送。
        -   後續模擬 Agent 回呼，斷言任務詳情中出現一個格式化的潛在客戶列表 (例如 Markdown 表格)。
- **VALIDATE (驗證)**: `pnpm test:e2e tests/e2e/ai-teammate-workflows.spec.ts --test-name="Sales Outreach"`。

---

## Validation Loop (驗證迴圈)

### Level 1: Syntax & Style (Immediate Feedback) (級別 1: 語法與風格 - 即時回饋)

```bash
# Run after each file creation - fix before proceeding (每個檔案創建後執行 - 在繼續之前修復)
ruff check src/{new_files} --fix     # Auto-format and fix linting issues (自動格式化和修復 linting 問題)
mypy src/{new_files}                 # Type checking with specific files (使用特定檔案進行類型檢查)
ruff format src/{new_files}          # Ensure consistent formatting (確保格式一致)

# Project-wide validation (專案範圍驗證)
ruff check src/ --fix
mypy src/
ruff format src/

# Expected: Zero errors. If errors exist, READ output and fix before proceeding. (預期：零錯誤。如果存在錯誤，請閱讀輸出並在繼續之前修復。)
```

### Level 2: Unit Tests (Component Validation) (級別 2: 單元測試 - 組件驗證)

```bash
# Test each component as it's created (創建每個組件後進行測試)
uv run pytest python/src/server/services/tests/test_{new_service}.py -v
uv run pytest python/src/server/api_routes/tests/test_{new_api}.py -v
uv run pytest enduser-ui-fe/src/features/agents/hooks/tests/test_useAgentQueries.test.ts -v

# Full test suite for affected areas (受影響區域的完整測試套件)
make test-be
make test-fe

# Expected: All tests pass. If failing, debug root cause and fix implementation. (預期：所有測試通過。如果失敗，請調試根本原因並修復實作。)
```

### Level 3: Integration Testing (System Validation) (級別 3: 整合測試 - 系統驗證)

```bash
# Service startup validation (服務啟動驗證)
docker compose up -d

# Health check validation (健康檢查驗證)
curl -f http://localhost:3737/health || echo "Frontend health check failed" (前端健康檢查失敗)
curl -f http://localhost:8181/health || echo "Backend API health check failed" (後端 API 健康檢查失敗)
curl -f http://localhost:8051/health || echo "MCP Server health check failed" (MCP 服務器健康檢查失敗)
curl -f http://localhost:8052/health || echo "Agents Service health check failed" (代理服務健康檢查失敗)

# Feature-specific endpoint testing (功能特定端點測試)
curl -X GET http://localhost:8181/api/agents/assignable | jq . # Verify AI agents list (驗證 AI 代理列表)

# Manually test in browser: (在瀏覽器中手動測試：)
# 1. Access http://localhost:3737 (訪問 http://localhost:3737)
# 2. Create a new task. (創建新任務。)
# 3. Verify AI agents appear in the assignee dropdown. (驗證 AI 代理出現在指派人下拉選單中。)
# 4. Assign a task to an AI agent. (將任務指派給 AI 代理。)
# 5. Observe task status updates (e.g., "AI processing", "AI done"). (觀察任務狀態更新（例如，「AI 處理中」、「AI 完成」）。)

# Expected: All integrations working, proper responses, no connection errors (預期：所有整合正常工作，響應正確，無連接錯誤)
```

### Level 4: Creative & Domain-Specific Validation (級別 4: 創意與領域特定驗證)

```bash
# Verify AI agent execution (驗證 AI 代理執行)
docker compose logs -f archon-agents # Monitor logs for AI agent activity (監控 AI 代理活動日誌)

# Check database for task updates (檢查資料庫中的任務更新)
psql $DATABASE_URL -c "SELECT id, title, assignee, status FROM archon_tasks WHERE assignee_id IS NOT NULL;"

# Expected: AI agent successfully processes task, updates status, and potentially adds output. (預期：AI 代理成功處理任務，更新狀態，並可能添加輸出。)
```

---

## COMPLETION CHECKLIST (完成檢查清單)

- [ ] All tasks completed (所有任務完成)
- [ ] Each task validation passed (每個任務驗證通過)
- [ ] Full test suite passes (完整測試套件通過)
- [ ] No linting errors (無 linting 錯誤)
- [ ] All available validation gates passed (所有可用驗證關卡通過)
- [ ] Story acceptance criteria met (符合故事驗收標準)

---

## Notes (備註)

- This PRP assumes that `archon-mcp` and `archon-agents` services are running and accessible by `archon-server`. (此 PRP 假設 `archon-mcp` 和 `archon-agents` 服務正在運行並可由 `archon-server` 訪問。)
- The specific logic for individual AI agents will be developed within the `python/src/agents/features/` directory, following a separate PRP for each agent's capability. (單個 AI 代理的具體邏輯將在 `python/src/agents/features/` 目錄中開發，並為每個代理的功能遵循單獨的 PRP。)
- Consider implementing robust error handling and fallback mechanisms for AI agent communication failures. (考慮為 AI 代理通訊故障實施強大的錯誤處理和備用機制。)
- Performance implications, especially for AI agent response times, should be monitored and optimized. (應監控和優化效能影響，特別是 AI 代理響應時間。)

---

### Phase 5 Remaining Tasks (Phase 5 剩餘任務)

The initial E2E test architecture and the first test case ("Marketing Campaign") are now complete. The following tasks remain to complete the full scope of Phase 5.

- **Phase 5.1: Complete Mocked E2E Tests (完成前端模擬 E2E 測試)**
  - [ ] **Task 5.3: Implement Mocked E2E Test for "Technical Support" Use Case**
  - [ ] **Task 5.4: Implement Mocked E2E Test for "Sales Outreach" Use Case**

- **Phase 5.2: Transition to Full Integration E2E Tests (過渡到完整整合 E2E 測試)**
  - [ ] **Task 5.5: Create Automated Database Reset/Seed Mechanism** (Revisit the `test:db:setup` script, likely using a Node.js/TypeScript approach based on project patterns).
  - [ ] **Task 5.6: Configure E2E Tests to run against a real backend** (This will involve disabling the API mocking and running against a live `archon-server`).