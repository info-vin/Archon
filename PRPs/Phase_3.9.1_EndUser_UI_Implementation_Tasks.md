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

### Phase 5.1: Mocked E2E Test Implementation & Architecture Refactor (已完成)

此階段的目標是為「AI 作為隊友」的使用者操作流程，建立一個穩健、可靠的前端 E2E 測試套件。經過一系列的偵錯與架構探索，我們不僅完成了所有預定的測試案例，還建立了一套清晰、隔離且可維護的 E2E 測試架構。

#### Final Test Architecture (最終測試架構)

為了確保測試的穩定性和可維護性，我們最終採納了以下架構：

1.  **專屬的 E2E 測試設定 (`vitest.e2e.config.ts`)**:
    *   我們為 E2E 測試創建了一個獨立的 Vitest 設定檔，使其與單元測試的設定完全隔離。

2.  **隔離的 Mocking 環境 (`tests/e2e/e2e.setup.ts`)**:
    *   所有 E2E 測試所需的 API Mock（例如，模擬登入使用者、返回 AI Agent 列表）都被集中到這個專屬的設定檔中。
    *   同時，我們修正了全域 `test/setup.ts`，使其與 E2E 的設定檔協同工作，確保了 `window.matchMedia` 等通用 Mock 能被正確載入，避免了設定衝突。

3.  **標準化的元件渲染策略**:
    *   為了解決 React Router 的巢狀嵌套問題，我們在測試中採用了標準的渲染模式：直接渲染 `AppRoutes` 元件，並為其提供 `AuthProvider` 和 `MemoryRouter` 作為包裹。

#### Completed Test Cases (已完成的測試案例)

基於上述架構，以下所有基於 `MOCK_BLOG_POSTS` 的 Mock E2E 測試案例均已實現並成功通過：

- **[x] Task 5.2: Implement Mocked E2E Test for "Marketing Campaign" Use Case**
- **[x] Task 5.3: Implement Mocked E2E Test for "Technical Support" Use Case**
- **[x] Task 5.4: Implement Mocked E2E Test for "Sales Outreach" Use Case**

---

### Phase 5.2: Transition to Full Integration Tests (下一步)

在前端的 Mock E2E 測試穩定運行的基礎上，下一步是將其過渡為與真實後端互動的完整整合測試。

- [x] **Task 5.5: Implement Automated Database Reset via API Endpoint (透過 API 端點實現自動化資料庫重置)**
    - **Status: COMPLETED (已完成)**
    - **Summary (總結):** The automated database reset mechanism is fully implemented and operational. A new backend endpoint (`POST /api/test/reset-database`) was created, protected by the `ENABLE_TEST_ENDPOINTS` flag. The E2E test suite's `globalSetup.ts` now successfully calls this endpoint before tests run, ensuring a clean and predictable database state, as confirmed by the successful `globalSetup` logs.

- [x] **Task 5.6: Configure E2E Tests to run against a real backend (設定 E2E 測試以針對真實後端運行)**
    - **Status: COMPLETED (已完成)**
    - **Summary (總結):** The E2E test setup (`e2e.setup.ts`) was successfully modified to read Supabase credentials from `.env.test` and inject them into `localStorage` (see commit `e281dad582dc`). This successfully unblocked the tests from running against a real backend. However, this progress immediately revealed subsequent issues, including a backend API hang (fixed in `574a150e91`) and new frontend component-related test failures, which are now being tracked in Task 5.7.

- [ ] **Task 5.7: Fix E2E tests broken by DashboardPage.tsx refactoring (修復因 DashboardPage.tsx 重構而損壞的 E2E 測試)**
    - **Status: PENDING (待處理)**
    - **Analysis (分析):** The E2E tests (`ai-teammate-workflows.spec.tsx`) are failing because they cannot find key elements like the "New Task" button. This was caused by a large refactoring of `DashboardPage.tsx` in commit `574a150e91`, where the header controls were removed from the component's direct output.
    - **Next Action (下一步行動):** Investigate the refactored `DashboardPage.tsx` and the test file `ai-teammate-workflows.spec.tsx` to determine if the test should be updated to find the elements in their new location, or if the component should be fixed to restore the previous structure.