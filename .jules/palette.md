## 2025-02-28 - Testing Transient Loading States
**Learning:** Playwright's `page.route` with a hanging handler (no fulfill/continue) allows perfect verification of loading states without race conditions or fragile `sleep` calls.
**Action:** Use `page.route(url, lambda route: None)` to indefinitely hang an API call when testing loading spinners or disabled buttons.
