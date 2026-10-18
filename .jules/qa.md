# QA & Testing Guidelines (Consolidated)

## 1. Guard Asynchronous State Updates During Vitest Teardown
**Learning:** In Vitest JSDOM tests, asynchronous React state updates resolving after a test finishes can throw `window is not defined` unhandled rejections.
**Action:** Guard asynchronous state setters in `useEffect`/`useCallback` with `typeof window !== 'undefined'` or proper abort cleanup.

## 2. Complete MSW Coverage and Recharts JSDOM Fallbacks
**Learning:** Unmocked endpoints or functions in `vi.mock` ignore lists trigger `NETWORK_ERROR` in headless E2E/unit runs, and Recharts `ResponsiveContainer` with percentage-only dimensions logs `-1` width/height warnings in JSDOM.
**Action:** Ensure all rendered API calls have MSW handlers or explicit `vi.fn()` mocks, and provide numeric dimension fallbacks for `ResponsiveContainer`.
