# Phase 4.6.55: UI/UX Testing Infrastructure & Model-Based Testing

> **Document Status**: 🟢 Active (2026-05-08)
> **Goal**: Eradicate "ghost development" and manual UI verification dependency by establishing zero-token, automated UI testing infrastructure (Model-Based Testing and Session Replay).

## 1. Executive Summary

This phase addresses the fragility of traditional E2E testing (UI rot, stateful mock deficiency, async timing issues) and the high token cost of Agentic UI testing. We are shifting left with **Model-Based Testing (MBT)** and shifting right with **Session Replay** to create an impenetrable UI/UX defense net.

The primary accomplishments of this phase will include:
1. **Infrastructure Provisioning**: Installation of XState and Playwright dependencies across frontend clients. (✅ Completed).
2. **PromptManagement MBT Integration**: Refactoring David's Admin SRE control plane (`PromptManagement.tsx` on Port 5173) to be governed by a formal XState machine. (✅ Completed).
3. **Automated Visual Validation (Session Replay)**: Integration of Playwright's native Trace Viewer to record exact DOM state, video, and network logs during E2E tests, completely eliminating manual testing and third-party Session Replay overhead. (🟢 In Progress).

---

## 2. Detailed Implementations

### 2.1. Environment & Infrastructure Setup (✅ Done)
- **Dependency Matrix**: Installed `xstate`, `@xstate/react`, and `@playwright/test` across both frontend clients.
- **Architecture Correction**: Initially planned for PostHog Session Replay, but uninstalled `posthog-js` and removed environment variables after realizing self-hosted PostHog was absent from the local `docker-compose.yml`. Transitioned to Playwright's zero-config Trace Viewer.
- **Build Verification**: Linting and production builds successfully passed post-installation.

### 2.2. PromptManagement XState Integration (✅ Done)
- **Blueprint Creation**: Designed `promptMachine` defining states (`loading`, `ready.idle`, `ready.editing`, `ready.saving`, `error`) and events (`FETCH_SUCCESS`, `SELECT_PROMPT`, `TOGGLE_VIEW`, `UPDATE_VALUE`, `REVERT`, `SAVE`).
- **Component Refactoring**: Replaced fragile `useState` and `useEffect` clusters inside `PromptManagement.tsx` with `useMachine(promptMachine)`, mapping all user actions to state machine events.
- **NodeJS Unit Test**: Wrote `PromptManagement.machine.test.ts` to execute and verify the isolated logic model via `vitest`.

### 2.3. Playwright MBT Visual Validation (✅ Done)
- **Script Creation**: Created `PromptManagement.mbt.spec.ts` to drive the XState machine paths in a real Chrome browser with `trace: 'on'` and `video: 'on'`.
- **Blocker Resolved**: Previously failed with a `Timeout 30000ms exceeded` error because Playwright starts in an isolated context and was redirected to the login page by React HashRouter. Resolved by:
  1. Fixing `page.goto` to use `/#/auth` and `/#/admin` for HashRouter.
  2. Adding explicit Network Interception (`page.route`) for Supabase Auth (`/auth/v1/token`) and Profiles API (`/rest/v1/profiles`) to mock a `system_admin` login state.
  3. Correcting the API interception endpoint from `/api/admin/prompts` to `/api/system/prompts`.
- **Result**: The MBT visual test now executes the full XState lifecycle successfully and generates valid video and trace artifacts.

---

## 3. Core Engineering Lessons (Recorded to Memory)

1. **Stateful Mocks vs Linear Scripts**: Linear E2E tests without stateful DB mocks fail to test the CRUD lifecycle. MBT shifts the focus to testing the state machine itself.
2. **Session Replay > Video Walkthroughs**: Forcing developers to record videos for UI bugs is anti-agile. Session replay captures the actual DOM tree and Network tab, providing actionable telemetry instead of a flat MP4.
3. **Zero-Token Automation**: Using local MBT traversal provides the edge-case discovery benefits of an AI agent but costs $0 and executes in milliseconds.
4. **Hallucinated Infrastructure**: Never propose backend services (like PostHog at `localhost:8000`) without physically verifying their existence in `docker-compose.yml`. (Added to `GEMINI.md` as Lesson 19).
5. **Playwright Isolated Contexts**: E2E tests executing protected UI routes will fail implicitly if authentication is not mocked or seeded prior to navigation. A browser context has no memory of the developer's local login state.
6. **HashRouter Navigation & API Alignment**: Playwright UI tests must respect frontend routing mechanisms (e.g., `/#/auth`) and mocked API paths must strictly mirror the application's actual backend requests (e.g., `/api/system/prompts` vs `/api/admin/prompts`) otherwise the mocks are bypassed, leading to implicit authentication errors from the live backend.

---

## 4. Next Steps
*   **Step 1**: (✅ Completed) Resolve the Playwright authentication blocker via Supabase Network Interception and HashRouter alignment.
*   **Step 2**: (✅ Completed) Successfully run the Playwright test and verify the output of `trace.zip` and `video.webm`.
*   **Step 3**: Conclude Phase 4.6.55 and transition to configuring Alice and David workflows hardening.
