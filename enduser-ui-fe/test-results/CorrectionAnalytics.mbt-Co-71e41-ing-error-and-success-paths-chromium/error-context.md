# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: CorrectionAnalytics.mbt.spec.ts >> Correction Analytics MBT Visual Test >> should execute full XState lifecycle including error and success paths
- Location: tests/playwright/CorrectionAnalytics.mbt.spec.ts:7:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.waitFor: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('button').filter({ hasText: 'Cognitive Analytics' }) to be visible

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Skip to content" [ref=e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=e5]:
    - generic [ref=e6]:
      - link "Myrmidon" [ref=e7] [cursor=pointer]:
        - /url: "#/landing"
        - generic [ref=e8]:
          - img [ref=e10]
          - generic [ref=e30]: Myrmidon
      - navigation [ref=e31]:
        - link "Home" [ref=e32] [cursor=pointer]:
          - /url: "#/landing"
        - link "Solutions" [ref=e33] [cursor=pointer]:
          - /url: "#/solutions"
        - link "Blog" [ref=e34] [cursor=pointer]:
          - /url: "#/blog"
      - generic [ref=e35]:
        - button "Toggle theme" [ref=e36] [cursor=pointer]:
          - img [ref=e37]
        - link "Go to Dashboard" [ref=e39] [cursor=pointer]:
          - /url: "#/dashboard"
  - main [ref=e40]:
    - generic [ref=e42]:
      - heading "Sign in to your account" [level=2] [ref=e44]
      - generic [ref=e45]:
        - generic [ref=e46]:
          - generic [ref=e47]: Email address
          - textbox "Email address" [ref=e48]
        - generic [ref=e49]:
          - generic [ref=e50]: Password
          - textbox "Password" [ref=e51]
        - button "Sign in" [ref=e53] [cursor=pointer]:
          - generic [ref=e54]: Sign in
      - button "Don't have an account? Sign up" [ref=e56] [cursor=pointer]
  - contentinfo [ref=e57]:
    - paragraph [ref=e59]: Built for efficiency. Inspired by Vik and Arc.
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import { simulate500Error, simulateNetworkTimeout } from './fixtures/systemFixtures';
  3  | 
  4  | test.use({ storageState: '../.playwright/admin_storage_state.json' });
  5  | 
  6  | test.describe('Correction Analytics MBT Visual Test', () => {
  7  |   test('should execute full XState lifecycle including error and success paths', async ({ page }) => {
  8  |     // We navigate to the admin page
  9  |     await page.goto('/#/admin');
  10 | 
  11 |     // Click 'Cognitive Analytics' tab
  12 |     const analyticsTab = page.locator('button', { hasText: 'Cognitive Analytics' });
> 13 |     await analyticsTab.waitFor({ state: 'visible' });
     |                        ^ Error: locator.waitFor: Test timeout of 30000ms exceeded.
  14 |     
  15 |     // Scenario 1: API Error Path
  16 |     await simulate500Error(page, '**/api/admin/logs?type=AI_CORRECTION*');
  17 |     await analyticsTab.click();
  18 | 
  19 |     // Verify Error State
  20 |     await expect(page.locator('p', { hasText: 'Internal Server Error' })).toBeVisible();
  21 | 
  22 |     // Unroute the error and provide success mock
  23 |     await page.unroute('**/api/admin/logs?type=AI_CORRECTION*');
  24 |     await page.route('**/api/admin/logs?type=AI_CORRECTION*', async route => {
  25 |       await route.fulfill({ 
  26 |         status: 200, 
  27 |         json: [
  28 |           {
  29 |             created_at: new Date().toISOString(),
  30 |             details: {
  31 |               post_id: 'test-post-uuid-123',
  32 |               correction_rate: 15.5,
  33 |               old_length: 1000,
  34 |               new_length: 1100
  35 |             }
  36 |           },
  37 |           {
  38 |             created_at: new Date(Date.now() - 86400000).toISOString(),
  39 |             details: {
  40 |               post_id: 'test-post-uuid-456',
  41 |               correction_rate: 35.2,
  42 |               old_length: 500,
  43 |               new_length: 200
  44 |             }
  45 |           }
  46 |         ] 
  47 |       });
  48 |     });
  49 | 
  50 |     // Scenario 2: Retry and Success Path
  51 |     // The retry in this UI is via the Refresh button or changing time range.
  52 |     // Let's click the refresh button.
  53 |     const refreshBtn = page.locator('button:has(svg.lucide-refresh-cw)');
  54 |     await refreshBtn.click();
  55 | 
  56 |     // Verify stats are loaded
  57 |     await expect(page.locator('p', { hasText: 'Avg. Correction Rate' })).toBeVisible();
  58 |     await expect(page.getByText('25.4%')).toBeVisible(); // (15.5 + 35.2) / 2
  59 |     await expect(page.getByText('test-post-uuid-123'.substring(0,8) + '...').first()).toBeVisible();
  60 | 
  61 |     // Scenario 3: Change Time Range Filter
  62 |     const timeRangeSelect = page.locator('select');
  63 |     await timeRangeSelect.selectOption('30d');
  64 |     
  65 |     // Changing time range should trigger loading and then success again.
  66 |     // We already have the route interceptor, so it will return the same data immediately.
  67 |     await expect(page.getByText('25.4%')).toBeVisible();
  68 |   });
  69 | });
```