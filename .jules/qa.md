# QA Journal

## 2024-05-20 - MSW Mocking for New Endpoints
**Learning:** When new backend endpoints are introduced (like \`/api/system/prompts\` or \`/api/visit-logs/attendance/status\`), they need corresponding MSW handlers in \`src/mocks/handlers.ts\` for E2E tests to pass without "intercepted a request without a matching request handler" or "NETWORK_ERROR" errors.
**Action:** Always ensure \`src/mocks/handlers.ts\` covers all expected API calls during component rendering, even if the test isn't explicitly testing those features. Add empty arrays or default response bodies for new endpoints.
