# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: AdminPanelExhaustive.spec.ts >> Exhaustive Admin Panel Verification >> should successfully render every tab in the Admin Panel without crashing or endless loading
- Location: tests/playwright/AdminPanelExhaustive.spec.ts:30:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('AI Connectivity Exception Log').first()
Expected: visible
Timeout: 15000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 15000ms
  - waiting for getByText('AI Connectivity Exception Log').first()

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Skip to content" [ref=e4] [cursor=pointer]:
    - /url: "#main-content"
  - navigation [ref=e5]:
    - link "Myrmidon" [ref=e8] [cursor=pointer]:
      - /url: "#/dashboard"
      - generic [ref=e9]:
        - img [ref=e11]
        - generic [ref=e31]: Myrmidon
    - list [ref=e32]:
      - listitem [ref=e33]:
        - link "My Tasks" [ref=e34] [cursor=pointer]:
          - /url: "#/dashboard"
          - img [ref=e35]
          - generic [ref=e38]: My Tasks
      - listitem [ref=e39]:
        - link "HR Dashboard" [ref=e40] [cursor=pointer]:
          - /url: "#/stats"
          - img [ref=e41]
          - generic [ref=e44]: HR Dashboard
      - listitem [ref=e45]:
        - link "Sales Intel" [ref=e46] [cursor=pointer]:
          - /url: "#/marketing"
          - img [ref=e47]
          - generic [ref=e50]: Sales Intel
      - listitem [ref=e51]:
        - link "Brand Hub" [ref=e52] [cursor=pointer]:
          - /url: "#/brand"
          - img [ref=e53]
          - generic [ref=e59]: Brand Hub
      - listitem [ref=e60]:
        - link "Approvals" [ref=e61] [cursor=pointer]:
          - /url: "#/approvals"
          - img [ref=e62]
          - generic [ref=e65]: Approvals
      - listitem [ref=e66]:
        - link "Nexus Command" [ref=e67] [cursor=pointer]:
          - /url: "#/nexus"
          - img [ref=e68]
          - generic [ref=e73]: Nexus Command
      - listitem [ref=e74]:
        - link "Team Management" [ref=e75] [cursor=pointer]:
          - /url: "#/team"
          - img [ref=e76]
          - generic [ref=e79]: Team Management
      - listitem [ref=e80]:
        - link "Admin Control" [ref=e81] [cursor=pointer]:
          - /url: "#/admin"
          - img [ref=e82]
          - generic [ref=e85]: Admin Control
    - generic [ref=e86]:
      - link "Website" [ref=e88] [cursor=pointer]:
        - /url: "#/landing"
        - img [ref=e89]
        - generic [ref=e94]: Website
      - link "A Admin User admin@archon.com system_admin" [ref=e95] [cursor=pointer]:
        - /url: "#/settings"
        - generic "Admin User" [ref=e96]: A
        - generic [ref=e97]:
          - paragraph [ref=e98]: Admin User
          - generic [ref=e99]:
            - paragraph [ref=e100]: admin@archon.com
            - generic [ref=e101]: system_admin
      - button "Logout" [ref=e102] [cursor=pointer]:
        - img [ref=e103]
        - generic [ref=e106]: Logout
  - main [ref=e107]:
    - generic [ref=e109]:
      - generic [ref=e110]: May 17, 18:42
      - button "Toggle theme" [ref=e112] [cursor=pointer]:
        - img [ref=e113]
    - generic [ref=e116]:
      - generic [ref=e117]:
        - heading "Admin Control Center" [level=1] [ref=e118]
        - paragraph [ref=e119]: System-wide configuration and personnel management for L1 Administrators.
      - navigation "Tabs" [ref=e121]:
        - button "System Prompts" [ref=e122] [cursor=pointer]
        - button "System Health" [active] [ref=e123] [cursor=pointer]
        - button "User Management" [ref=e124] [cursor=pointer]
        - button "Cost & Usage" [ref=e125] [cursor=pointer]
        - button "Cognitive Analytics" [ref=e126] [cursor=pointer]
        - button "System Settings" [ref=e127] [cursor=pointer]
        - button "Data Extraction" [ref=e128] [cursor=pointer]
        - button "Blog Management" [ref=e129] [cursor=pointer]
        - button "Document Versions" [ref=e130] [cursor=pointer]
      - generic [ref=e132]:
        - img [ref=e133]
        - generic [ref=e136]:
          - heading "System Probe Failed" [level=3] [ref=e137]
          - paragraph [ref=e138]: Core health services are currently unreachable.
          - button "Retry" [ref=e139] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.use({ storageState: '../.playwright/admin_storage_state.json' });
  4  | 
  5  | test.describe('Exhaustive Admin Panel Verification', () => {
  6  |     test.setTimeout(60000); // 9 tabs may take longer than 30s to verify
  7  |     
  8  |     test.beforeEach(async ({ page }) => {
  9  |         // Prevent random network timeouts from causing flakiness
  10 |         // We are checking rendering, not backend logic here, but backend logic should be fast.
  11 |         page.on('console', msg => {
  12 |             if (msg.type() === 'error') console.log(`BROWSER ERROR: ${msg.text()}`);
  13 |         });
  14 | 
  15 |         // Fast-path intercepts to prevent slow external API checks or 404s from causing timeouts
  16 |         await page.route('**/api/system/health/ai*', async route => {
  17 |             await route.fulfill({ status: 200, json: { models: [], status: 'healthy' } });
  18 |         });
  19 |         await page.route('**/api/admin/document-versions*', async route => {
  20 |             await route.fulfill({ status: 200, json: { versions: [] } });
  21 |         });
  22 |         await page.route('**/api/admin/logs?type=system*', async route => {
  23 |             await route.fulfill({ status: 200, json: [] });
  24 |         });
  25 |         await page.route('**/api/admin/logs?type=AI_CORRECTION*', async route => {
  26 |             await route.fulfill({ status: 200, json: [] });
  27 |         });
  28 |     });
  29 | 
  30 |     test('should successfully render every tab in the Admin Panel without crashing or endless loading', async ({ page }) => {
  31 |         await page.goto('/#/admin');
  32 |         
  33 |         // Wait for the main page to load
  34 |         await expect(page.getByRole('heading', { name: 'Admin Control Center' })).toBeVisible({ timeout: 10000 });
  35 | 
  36 |         const tabsToVerify = [
  37 |             { name: 'System Prompts', expectedContent: 'Save Changes' },
  38 |             { name: 'System Health', expectedContent: 'AI Connectivity Exception Log' },
  39 |             { name: 'User Management', expectedContent: 'Identity Matrix' },
  40 |             { name: 'Cost & Usage', expectedContent: 'Token Cost & ROI Analytics' },
  41 |             { name: 'Cognitive Analytics', expectedContent: 'AI Cognitive Analytics' },
  42 |             { name: 'System Settings', expectedContent: 'Dynamic System Configuration' },
  43 |             { name: 'Data Extraction', expectedContent: 'Knowledge Base Targets (Crawler)' },
  44 |             { name: 'Blog Management', expectedContent: 'Content Assets' },
  45 |             { name: 'Document Versions', expectedContent: 'Document Version Audit Trail' }
  46 |         ];
  47 | 
  48 |         for (const tab of tabsToVerify) {
  49 |             console.log(`Verifying Tab: ${tab.name}...`);
  50 |             await page.getByRole('button', { name: tab.name, exact: true }).click();
  51 |             
  52 |             // Verify expected content appears (no white screen of death)
> 53 |             await expect(page.getByText(tab.expectedContent).first()).toBeVisible({ timeout: 15000 });
     |                                                                       ^ Error: expect(locator).toBeVisible() failed
  54 |             
  55 |             // Ensure no "Loading..." states are stuck
  56 |             const loadingElements = await page.getByText('Loading').all();
  57 |             for (const el of loadingElements) {
  58 |                 await expect(el).not.toBeVisible({ timeout: 15000 }).catch(() => {
  59 |                     console.log(`Warning: A loading element might still be visible in ${tab.name}`);
  60 |                 });
  61 |             }
  62 |             
  63 |             console.log(`✅ Tab ${tab.name} passed.`);
  64 |         }
  65 |     });
  66 | });
  67 | 
```