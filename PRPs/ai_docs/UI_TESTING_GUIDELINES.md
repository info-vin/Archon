# UI Testing Guidelines (Archon Phase 5.1.0)

> **Core Philosophy**: Balance the high maintenance cost of MBT (Model-Based Testing) with the need for robust cross-persona business flows.

## 1. Testing Tiers & Boundaries

### Tier 1: Unit & Component Tests (Vitest + React Testing Library)
- **Scope**: Individual components, utility functions, pure logic.
- **When to use**: 90% of UI features.
- **Requirement**: Fast execution, zero network dependency (use MSW for API mocking).

### Tier 2: Feature E2E (Playwright)
- **Scope**: Single feature flow (e.g., "Assign a task").
- **When to use**: Features with complex user interactions but limited external dependencies.

### Tier 3: Cross-Persona MBT (XState + Playwright)
- **Scope**: Epic business flows involving Alice (Sales), Bob (Marketing), and Charlie (Manager).
- **When to use**: **ONLY** for critical revenue/operation flows where state transitions between personas are the main source of risk.
- **Constraint**: Avoid using MBT for simple CRUD or layout checks.

## 2. Visual Regression Testing (VRT)

To reduce "test-tax" caused by minor CSS changes:
- **Thresholds**: Use `maxDiffPixelRatio: 0.05` to allow for sub-pixel anti-aliasing differences.
- **Snapshot Scoping**: Prefer element-level snapshots (`locator.screenshot()`) over full-page snapshots to isolate layout regressions.

## 3. SSE & Async Synchronization

With the introduction of SSE (Server-Sent Events) in Phase 5.1.0:
- **Mocking**: Use `msw` or a dedicated SSE mock controller to simulate server push events during tests.
- **Assertions**: Avoid `waitForTimeout`. Use `expect(locator).toBeVisible()` or custom predicates that wait for the specific state change pushed via SSE.

## 4. Maintenance & De-risking

- **Anti-Ghosting**: Every core API endpoint must have a corresponding "Negative Test" (403/404) to ensure security boundaries are physical, not just logical.
- **State SSOT**: Tests should verify that the UI reflects the `archon_tasks.status` in the DB, not a localized cache state.
