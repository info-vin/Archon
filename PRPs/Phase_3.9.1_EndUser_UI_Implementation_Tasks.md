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

### CREATE enduser-ui-fe/src/features/agents/hooks/useAgentQueries.ts: (創建 enduser-ui-fe/src/features/agents/hooks/useAgentQueries.ts)

- **IMPLEMENT (實作)**: `useAssignableAgents()` query hook to fetch the list of AI agents from `/api/agents/assignable`. (實作 `useAssignableAgents()` 查詢鉤子，從 `/api/agents/assignable` 獲取 AI 代理列表。)
- **PATTERN (模式)**: Follow `QUERY_PATTERNS.md` and existing `useProjectQueries.ts` for structure and caching. (遵循 `QUERY_PATTERNS.md` 和現有的 `useProjectQueries.ts` 的結構和快取模式。)
- **VALIDATE (驗證)**: `make test-fe` (unit tests for this hook).

### MODIFY enduser-ui-fe/src/features/projects/tasks/components/TaskForm.tsx: (修改 enduser-ui-fe/src/features/projects/tasks/components/TaskForm.tsx)

- **INTEGRATE (整合)**: The `useAssignableAgents()` hook to fetch AI agents. (整合 `useAssignableAgents()` 鉤子以獲取 AI 代理。)
- **UPDATE (更新)**: The assignee selection dropdown/component to include both human users (from `useAssignableUsers()`) and AI agents. (更新指派人選擇下拉選單/組件，以包含人類使用者和 AI 代理。)
- **UI/UX (使用者介面/體驗)**: Differentiate AI agents visually (e.g., specific icon, color, or label) as per `UI_STANDARDS.md`. (根據 `UI_STANDARDS.md` 在視覺上區分 AI 代理（例如，特定圖示、顏色或標籤）。)
- **VALIDATE (驗證)**: Manually test task creation and assignment to an AI agent in the browser. (手動測試在瀏覽器中創建和指派任務給 AI 代理。)

### Phase 4: AI Agent Orchestration & Execution (`archon-mcp` / `archon-agents`) (AI 代理協調與執行)

### CREATE python/src/mcp_server/services/agent_orchestration_service.py: (創建 python/src/mcp_server/services/agent_orchestration_service.py)

- **IMPLEMENT (實作)**: A new service to manage the lifecycle of AI agent tasks. (實作一個新服務來管理 AI 代理任務的生命週期。)
- **METHODS (方法)**: `trigger_agent_task(task_id, agent_id)`, `report_agent_status(task_id, status)`, `report_agent_output(task_id, output)`. (觸發代理任務、報告代理狀態、報告代理輸出。)
- **VALIDATE (驗證)**: `uv run pytest python/src/mcp_server/services/agent_orchestration_service.py`

### CREATE python/src/agents/features/example_agent.py: (創建 python/src/agents/features/example_agent.py)

- **IMPLEMENT (實作)**: A basic example AI agent (e.g., `MarketingContentAgent`, `KnowledgeBaseAgent`) that can receive a task. (實作一個基本的 AI 代理範例（例如，行銷內容代理、知識庫代理），它可以接收任務。)
- **LOGIC (邏輯)**: Agent should simulate processing a task and reporting its status/output back via the orchestration service. (代理應模擬處理任務，並透過協調服務報告其狀態/輸出。)
- **VALIDATE (驗證)**: `uv run pytest python/src/agents/features/example_agent.py`

### Phase 5: End-to-End Validation & Refinements (端到端驗證與優化)

### INTEGRATE & TEST (整合與測試):

- **END-TO-END (端到端)**: Perform comprehensive end-to-end testing of the entire flow: (對整個流程執行全面的端到端測試：)
    1.  Create a task in `enduser-ui-fe`. (在 `enduser-ui-fe` 中創建任務。)
    2.  Assign it to an AI agent. (將其指派給 AI 代理。)
    3.  Verify `archon-server` correctly triggers the AI agent. (驗證 `archon-server` 正確觸發 AI 代理。)
    4.  Verify AI agent processes the task and reports status/output. (驗證 AI 代理處理任務並報告狀態/輸出。)
    5.  Verify `enduser-ui-fe` correctly displays AI agent's status and output. (驗證 `enduser-ui-fe` 正確顯示 AI 代理的狀態和輸出。)
- **UI/UX REVIEW (使用者介面/體驗審查)**: Ensure the user experience for assigning tasks to AI is intuitive and clear. (確保將任務指派給 AI 的使用者體驗直觀清晰。)
- **PERFORMANCE (效能)**: Monitor performance for task assignment and AI agent processing. (監控任務指派和 AI 代理處理的效能。)

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