import { test, expect } from '@playwright/test';
import { simulate500Error } from './fixtures/systemFixtures';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('Correction Analytics MBT Visual Test', () => {
  test('should execute full XState lifecycle including error and success paths', async ({ page }) => {
    // We navigate to the admin page
    await page.goto('/#/admin');

    // Click 'Cognitive Analytics' tab
    const analyticsTab = page.locator('button', { hasText: 'Cognitive Analytics' });
    await analyticsTab.waitFor({ state: 'visible' });
    
    // Scenario 1: API Error Path
    await simulate500Error(page, '**/api/admin/logs?type=AI_CORRECTION*');
    await analyticsTab.click();

    // Verify Error State
    await expect(page.locator('p', { hasText: 'Internal Server Error' })).toBeVisible();

    // Unroute the error and provide success mock
    await page.unroute('**/api/admin/logs?type=AI_CORRECTION*');
    await page.route('**/api/admin/logs?type=AI_CORRECTION*', async route => {
      await route.fulfill({ 
        status: 200, 
        json: [
          {
            created_at: new Date().toISOString(),
            details: {
              post_id: 'test-post-uuid-123',
              correction_rate: 15.5,
              old_length: 1000,
              new_length: 1100
            }
          },
          {
            created_at: new Date(Date.now() - 86400000).toISOString(),
            details: {
              post_id: 'test-post-uuid-456',
              correction_rate: 35.2,
              old_length: 500,
              new_length: 200
            }
          }
        ] 
      });
    });

    // Scenario 2: Retry and Success Path
    // The retry in this UI is via the Refresh button or changing time range.
    // Let's click the refresh button.
    const refreshBtn = page.locator('button:has(svg.lucide-refresh-cw)');
    await refreshBtn.click();

    // Verify stats are loaded
    await expect(page.locator('p', { hasText: 'Avg. Correction Rate' })).toBeVisible();
    await expect(page.getByText('25.4%')).toBeVisible(); // (15.5 + 35.2) / 2
    await expect(page.getByText('test-post-uuid-123'.substring(0,8) + '...').first()).toBeVisible();

    // Scenario 3: Change Time Range Filter
    const timeRangeSelect = page.locator('select');
    await timeRangeSelect.selectOption('30d');
    
    // Changing time range should trigger loading and then success again.
    // We already have the route interceptor, so it will return the same data immediately.
    await expect(page.getByText('25.4%')).toBeVisible();
  });
});