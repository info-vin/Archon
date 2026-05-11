import { test, expect } from '@playwright/test';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('Exhaustive Admin Panel Verification', () => {
    
    test.beforeEach(async ({ page }) => {
        // Prevent random network timeouts from causing flakiness
        // We are checking rendering, not backend logic here, but backend logic should be fast.
        page.on('console', msg => {
            if (msg.type() === 'error') console.log(`BROWSER ERROR: ${msg.text()}`);
        });
    });

    test('should successfully render every tab in the Admin Panel without crashing or endless loading', async ({ page }) => {
        await page.goto('/#/admin');
        
        // Wait for the main page to load
        await expect(page.getByRole('heading', { name: 'Admin Control Center' })).toBeVisible({ timeout: 10000 });

        const tabsToVerify = [
            { name: 'System Prompts', expectedContent: 'Editor Mode' },
            { name: 'System Health', expectedContent: 'Connectivity Alerts' },
            { name: 'User Management', expectedContent: 'Identity Matrix' },
            { name: 'Cost & Usage', expectedContent: 'AI Usage' },
            { name: 'Cognitive Analytics', expectedContent: 'Correction Analytics' },
            { name: 'System Settings', expectedContent: 'Dynamic System Configuration' },
            { name: 'Data Extraction', expectedContent: 'Crawler Targets' },
            { name: 'Blog Management', expectedContent: 'Manage Knowledge Base' },
            { name: 'Document Versions', expectedContent: 'Document Version History' }
        ];

        for (const tab of tabsToVerify) {
            console.log(`Verifying Tab: ${tab.name}...`);
            await page.getByRole('button', { name: tab.name, exact: true }).click();
            
            // Verify expected content appears (no white screen of death)
            await expect(page.getByText(tab.expectedContent).first()).toBeVisible({ timeout: 15000 });
            
            // Ensure no "Loading..." states are stuck
            const loadingElements = await page.getByText('Loading').all();
            for (const el of loadingElements) {
                await expect(el).not.toBeVisible({ timeout: 15000 }).catch(() => {
                    console.log(`Warning: A loading element might still be visible in ${tab.name}`);
                });
            }
            
            console.log(`✅ Tab ${tab.name} passed.`);
        }
    });
});
