import { test, expect, simulate500Error, waitForSpinner } from './fixtures/systemFixtures';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('Correction Analytics MBT Visual Test', () => {
  test('should execute full XState lifecycle including error and success paths', async ({ page }) => {
    // We navigate to the admin page
    await page.goto('/#/admin');

    // Click 'Cognitive Analytics' tab
    const analyticsTab = page.getByTestId('tab-cognitive-analytics');
    await analyticsTab.waitFor({ state: 'visible' });
    
    // Scenario 1: API Error Path
    await simulate500Error(page, /.*\/api\/admin\/logs.*/);
    await analyticsTab.click();
    await waitForSpinner(page);

    // Verify Error State
    await expect(page.getByTestId('error-msg')).toBeVisible();

    // Unroute the error and provide success mock
    await page.unroute(/.*\/api\/admin\/logs.*/);
    await page.route(/.*\/api\/admin\/logs.*/, async route => {
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
    const refreshBtn = page.getByTestId('refresh-analytics-btn');
    await refreshBtn.click();
    await waitForSpinner(page);

    // Verify stats are loaded
    await expect(page.getByTestId('stat-card-title')).toBeVisible();
    await expect(page.getByTestId('stat-card-value')).toHaveText('25.4%');
    await expect(page.getByTestId('post-id-cell').first()).toHaveText('test-pos...');

    // Scenario 3: Change Time Range Filter
    const timeRangeSelect = page.getByTestId('time-range-select');
    await timeRangeSelect.selectOption('30d');
    await waitForSpinner(page);
    
    // Changing time range should trigger loading and then success again.
    // We already have the route interceptor, so it will return the same data immediately.
    await expect(page.getByTestId('stat-card-value')).toHaveText('25.4%');
  });
});