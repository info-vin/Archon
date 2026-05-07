# Phase 4.6.54: Alice/David Workflows Hardening & Empirical Test Alignment

> **Document Status**: ✅ Completed (2026-05-06)
> **Goal**: Eradicate "optimistic path" assumptions, synchronize the E2E test suite with the physical UI reality, and eliminate technical debt across Alice's mobile operations and David's Admin control plane.

## 1. Executive Summary

This phase addressed critical architectural disconnects and UI rot discovered during a deep physical audit of the system. We transitioned from relying on documentation and "green backend tests" to enforcing strict physical parity between the frontend DOM, the backend APIs, the MSW mocks, and the database schema. 

The primary accomplishments include:
1. **Alice's Workflow Decoupling**: Separated the automated job search from synchronous AI generation to prevent massive token waste and preserve the business logic of the "Hunter Mode" funnel.
2. **E2E Test Resurrection**: Rewrote failing E2E tests to match actual UI components (resolving UI rot) and added missing mock endpoints, restoring the 100% CI/CD gate.
3. **David's Admin (SRE) Plane**: Replaced hardcoded, static UI stubs on Port 5173 with dynamic, data-driven dashboards for System Settings, Cost/ROI Analytics, and Prompt Versioning.

---

## 2. Detailed Implementations

### 2.1. Alice (Sales) Workflow Hardening
*   **The "Ghost" Scheduler Fixed**: The `prune_stale_leads` logic existed but was never connected to the background scheduler. It is now properly wired into the `SchedulerService` to run every hour, ensuring stale leads are automatically archived.
*   **Decoupled Search from AI Generation**: Removed the synchronous `_infer_need` call from `search_jobs`. "Find Jobs" now purely scrapes data (capped at 8 items to prevent rate limits), consuming 0 tokens. AI generation only occurs sequentially or on-demand when Alice interacts with the lead (e.g., clicking "Generate AI Pitch").
*   **Prompt Centralization (Prompt as Data)**: The `ALICE_INFER_NEED` prompt was extracted from hardcoded strings and seeded into the `archon_prompts` database table via `migration/0.2.2/seed_mock_data.sql`.
*   **Mobile-Optimized Markdown Output**: The prompt was constrained to output exactly two bullet points (max 50 words each) for **技術棧 (Tech Stack)** and **痛點預測 (Pain Points)**. `ReactMarkdown` was integrated into `MarketingJobSearch.tsx` and `LeadCard.tsx` to render the insights cleanly on mobile devices.

### 2.2. E2E Test Suite Alignment (Eradicating UI Rot)
*   **Authentication & Role Alignment**: Fixed the `MOCK_ADMIN_USER` in `e2e.setup.tsx` by explicitly granting the missing `leads:view:all` permission, allowing the test suite to bypass the `PermissionGuard` and physically "see" the UI components.
*   **DOM Structure Synchronization**: 
    *   Updated queries in `sales-nexus-closure.spec.tsx` to match the actual user journey (e.g., navigating to the Search tab to generate a pitch, rather than looking for removed buttons).
    *   Updated the Visit Log test to select a "Visit Type" before typing into the `textarea`, aligning with the newly added required fields.
*   **Network Mocking**: Added the missing `POST /api/visit-logs/` interceptor to the MSW `handlers.ts` to resolve `ECONNREFUSED` errors during simulated network requests.
*   **Result**: 13/13 files and 25/25 test cases successfully passed.

### 2.3. David (Admin/SRE) Control Plane Hardening (Port 5173)
*   **Dynamic System Settings (`AdminSystemConfig.tsx`)**: Replaced the hardcoded array of 9 fields with a dynamic fetch from the `/api/system/settings` endpoint. Settings are now automatically grouped by category (`crawler_rbac`, `lead_scoring`, `system`), and input types (`text`, `number`, `textarea`) are inferred dynamically.
*   **Cost & Usage Dashboard (`AdminCostDashboard.tsx`)**: Replaced the duplicated System Health view with a dedicated ROI dashboard. It physically fetches token consumption data (`/api/stats/ai-usage` and `/api/stats/token-usage/recent`) to populate the `ROIAnalyticsBadge` and `TokenUsageTable`.
*   **Prompt Manager with DiffViewer (`PromptManagement.tsx`)**: 
    *   Integrated `react-diff-viewer`. 
    *   Implemented an "EDIT / DIFF" toggle, allowing the architect to compare local edits against the original database prompt with GitHub-style red/green highlighting.
    *   Added a "REVERT" button for safe rollbacks of critical system prompts.

---

## 3. Core Engineering Lessons (Recorded to Memory)

1.  **Beware the Optimistic Path**: Backend unit tests passing (`make test-be`) does not guarantee end-to-end business logic works. A feature is only "done" when the E2E tests (`pnpm test:e2e`) physically confirm the DOM elements and network calls align.
2.  **UI Rot in Tests**: E2E tests are first-class citizens. When redesigning components (e.g., changing a button's text or adding a new required dropdown), the corresponding E2E tests must be updated in the same PR.
3.  **Port Hardening**: Admin UI is strictly bound to Port **5173** (enduser-ui-fe). It is not on 3737.

---

## 4. Next Steps
*   Deploy changes and verify the new `prune_stale_leads` hourly clockwork task in the staging environment.
*   Review Bob's Marketing pipeline to ensure the new AI generation decoupling logic does not negatively impact automated blog drafting.