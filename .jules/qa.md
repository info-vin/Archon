# QA Journal
## 2024-05-14 - Fix window is not defined Unhandled Rejection
**Learning:** In Vitest test teardowns, React state updates resolving asynchronously after a test finishes may throw 'window is not defined' Unhandled Rejection errors instead of standard unmounted component warnings.
**Action:** Implement `typeof window !== 'undefined'` check inside state setters of `useEffect`/`useCallback` that run asynchronously to avoid unhandled rejections during test teardowns.
