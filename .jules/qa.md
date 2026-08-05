# QA Journal
## 2024-05-14 - Fix window is not defined Unhandled Rejection
**Learning:** In Vitest test teardowns, React state updates resolving asynchronously after a test finishes may throw 'window is not defined' Unhandled Rejection errors instead of standard unmounted component warnings.
**Action:** Implement `typeof window !== 'undefined'` check inside state setters of `useEffect`/`useCallback` that run asynchronously to avoid unhandled rejections during test teardowns.

## 2024-05-14 - Missing Test Environment Variables
**Learning:** Playwright/Vitest E2E test setup relies on a `.env.test` file located at the project root to properly configure backend and API connection variables (e.g. `VITE_API_URL` and `ENABLE_TEST_ENDPOINTS`). Without this file, `globalSetup.ts` will fail immediately with `ENOENT`.
**Action:** Ensure that the `.env.test` file is explicitly created or included in the repository setup script before running `pnpm test:e2e`.
