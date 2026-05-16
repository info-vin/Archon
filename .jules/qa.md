# QA Journal

## 2024-05-20 - MSW Mocking for New Endpoints
**Learning:** When new backend endpoints are introduced (like \`/api/system/prompts\` or \`/api/visit-logs/attendance/status\`), they need corresponding MSW handlers in \`src/mocks/handlers.ts\` for E2E tests to pass without "intercepted a request without a matching request handler" or "NETWORK_ERROR" errors.
**Action:** Always ensure \`src/mocks/handlers.ts\` covers all expected API calls during component rendering, even if the test isn't explicitly testing those features. Add empty arrays or default response bodies for new endpoints.

## 2026-05-15 - Recharts ResponsiveContainer in JSDOM (Vitest/Jest)
**Learning:** Recharts `ResponsiveContainer` components that rely entirely on percentage values (`width="100%" height="100%"`) will fail to render dimensions in headless JSDOM environments, resulting in error logs like: `The width(-1) and height(-1) of chart should be greater than 0`.
**Action:** Always provide explicit numeric fallbacks or fixed values for at least one dimension (e.g. `height={160}`) when using `ResponsiveContainer` to ensure test stability and prevent console errors that muddy test logs.
