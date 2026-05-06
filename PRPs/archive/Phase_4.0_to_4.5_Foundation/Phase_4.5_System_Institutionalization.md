---
name: "Phase 4.5: System Institutionalization (系統制度化)"
description: |
  A strict refactoring phase to pay off the "Speed Debt" incurred during Phase 4.4.
  Focuses on normalizing UIs, converting scripts into proper APIs, standardizing test suites, and enforcing security/quality guardrails.
  (這是一個嚴格的重構階段，旨在償還 Phase 4.4 為了追求速度所欠下的「技術債」。專注於 UI 正規化、將腳本轉化為正式 API、測試套件標準化，以及強制執行安全與品質護欄。)

---

## Goal (目標)

**Core Objective (核心目標)**: To move from "it works via script" to "it works via system architecture". (從「透過腳本運作」轉變為「透過系統架構運作」。)

**Deliverables (交付成果)**:
1.  **Unified Team UI**: 統一 Agent 與 User 的 UI 呈現 (白色卡片)。
2.  **System Health API**: 將 `probe` 腳本轉為 API 服務。
3.  **Test Standardization**: 測試套件標準化 (Factory Pattern)。
4.  **Quality Guardrails**: 實作 AI 輸出檢查與邊界處理。
5.  **Vector Security**: 實作向量資料庫的 RLS。

---

## Phase 4.5.1: Test Standardization (測試標準化)
*Status: ✅ Completed*

*   **Objective**: Convert ad-hoc scripts into `pytest` standard.
*   **Actions Taken**:
    *   Moved `python/test_crawler.py` to `python/tests/external/test_104_reliability.py`.
    *   Registered `external` marker in `pytest.ini`.
    *   Ensured CI/CD can selectively run expensive external tests via `-m external`.
*   **Outcome**: `make test-external` is now the standard command.

## Phase 4.5.2: System Health API (系統健康 API)
*Status: ✅ Completed*

*   **Objective**: Institutionalize the `probe_librarian.py` script.
*   **Actions Taken**:
    *   Migrated logic to `HealthService.check_rag_integrity()`.
    *   Exposed via `GET /api/system/health/rag`.
    *   Secured endpoint with `system_admin` RBAC check.
    *   Deleted the original script to prevent drift.
*   **Outcome**: Monitoring tools can now query API health securely.

## Phase 4.5.3: Unified Team UI (統一團隊介面)
*Status: ✅ Completed*

*   **Objective**: Remove the "Dark Mode" anomaly for Agents.
*   **Actions Taken**:
    *   Refactored `TeamManagementPage.tsx` to use a single list for Humans and Agents.
    *   Standardized "White Card" design.
    *   Agents now display "Shared Budget" instead of fake individual quotas.
*   **Outcome**: A consistent visual language for the Hybrid Workforce.

---

## Phase 4.5.4: E2E Test Institutionalization (E2E 測試制度化)
*Status: ✅ Completed*

> **Goal**: 優先修復測試基底，解決 `BUG-015` (Mock Data 脫鉤) 與 `BUG-016` (Timeout)，為後續功能驗收鋪路。

**Task 1: Permission Factory (權限工廠)**
*   **Objective**: Fix `BUG-015` by removing magic strings from tests.
*   **Strategy**:
    *   Create `enduser-ui-fe/tests/factories/userFactory.ts`.
    *   Import `PERMISSION_SETS` from `usePermission.ts`.
    *   Refactor `e2e.setup.tsx` and all `.spec.tsx` files to use the factory.
*   **Validation**: E2E tests pass without manual permission string updates.

**Task 2: Timeout Stabilization**
*   **Objective**: Fix `BUG-016` in `task-persistence.spec.tsx`.
*   **Strategy**: Increase `waitFor` timeout or optimize selector strategy (wait for specific element instead of disappearance).

---

## Phase 4.5.5: Quality & Security Guardrails (品質與安全護欄)
*Status: ✅ Completed*

> **Goal**: To implement actual code barriers against bad data, hallucinations, and unauthorized access.

**Task 3: AI Guardrail Service (後端)**
*   **Objective**: Prevent AI from generating harmful or hallucinated content.
*   **Implementation**:
    *   Create `python/src/server/services/guardrail_service.py`.
    *   Implement `validate_input(text)`: Check for forbidden keywords (Basic).
    *   Implement `audit_output(text, context)`: Verify if generated text is supported by RAG context (Basic keyword overlap check).
*   **Integration**: Inject into `MarketingService.draft_blog_post`.
*   **Validation**: `curl POST /blog/draft` with forbidden keyword -> Returns 400 Bad Request.

**Task 4: Vector Row-Level Security (資料庫)**
*   **Objective**: Ensure Alice cannot search Bob's private RAG embeddings.
*   **Implementation**:
    *   Create `migration/014_vector_rls_policy.sql`.
    *   Enable RLS on `knowledge_items` and `embeddings` tables.
    *   Policy: `auth.role() = 'admin'` OR `department = auth.user_department()`.
*   **Validation**: Marketing User searches -> Returns items; Sales User searches -> Returns 0 items.

**Task 5: UI Boundary Handling (前端)**
*   **Objective**: Handle empty states and timeouts gracefully.
*   **Implementation**:
    *   Create `components/common/EmptyState.tsx` (Graphic + Action Button).
    *   Enhance `useAsync` hook with `timeout` parameter (default 30s).
    *   Update `MarketingPage.tsx` to show "Retry" button if AI takes >30s.
*   **Validation**: Disconnect network -> Trigger search -> Show Timeout UI.

---



### Phase 4.5.6: Admin UI Completion
*Status: ✅ Completed*

> **Goal**: Provide a robust interface for managing system prompts and configurations.

- [x] **Task 5: Prompts Management UI**
    - **Frontend**: Implemented as `PromptManagement` component within `AdminPage.tsx`.
    - **Backend**: `prompts_api.py` (CRUD verified).
    - **Validation**: E2E Test `prompts-management.spec.tsx` passing.

### Phase 4.5.7: Autonomous DevBot Evolution (New)
*Status: ✅ Completed*

> **Goal**: Upgrade the AI Agent from "Diagnostic" (L1) to "Active Repair" (L2), enabling the system to fix its own code errors autonomously.

- [x] **Task 6: Autonomous Repair Loop (DevBot L2)**
    - **Context**: Currently, `AgentService` only analyzes errors. We need it to apply fixes.
    - **Implementation**:
        - **Safe Sandbox**: Implemented `CodeModifier` to create `autosave/fix-{id}` branches.
        - **Repair Loop**: `AgentService` now executes -> analyzes -> branches -> fixes -> verifies.
        - **Multi-Language**: Verified support for Python syntax fixes and simulated TypeScript/JS fixes.
    - **Safety**: Changes are isolated in branches and require human merge.


---

## Verification & Acceptance Checklist (總體驗收清單)

1.  **Test Suite Health (Priority)**:
    *   [x] `make test-fe` PASS (Green).
    *   [x] No literal permission strings (`['leads:view:all']`) found in `tests/e2e`.
2.  **RBAC Check**:
    *   [x] Sales User CANNOT see Brand Hub (403 Forbidden).
    *   [x] Marketing User CANNOT search Sales Leads (RLS blocked).
3.  **Quality Check**:
    *   [x] AI refuses to generate content with "BANNED_WORD".
    *   [x] Frontend shows specific "Timeout" error after 30s delay.
4.  **Admin Function**:
    *   [x] Admin can successfully update a System Prompt via UI.
