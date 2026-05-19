import { test, expect } from '@playwright/test';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('AI Token Budget Warning Banner MBT Assertion', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept permission check to ensure standard access pass
    await page.route('**/api/auth/permissions', async route => {
      await route.fulfill({
        status: 200,
        json: ['user:manage:team']
      });
    });

    // Intercept standard employee fetch API to prevent backend connection dependency
    await page.route('**/api/admin/users', async route => {
      await route.fulfill({
        status: 200,
        json: [
          {
            id: 'mock-user-001',
            email: 'bob@archon.com',
            name: 'Bob Lens',
            role: 'manager',
            avatar: 'https://i.pravatar.cc/150?u=bob',
            employeeId: 'EMP-001',
            department: 'Marketing',
            status: 'active'
          }
        ]
      });
    });
  });

  test('Should NOT show budget warning banner when AI usage is within limits', async ({ page }) => {
    // Intercept AI usage API to return standard compliant budget (15% consumed)
    await page.route('**/api/stats/ai-usage', async route => {
      await route.fulfill({
        status: 200,
        json: {
          total_budget: 1000,
          total_used: 150,
          usage_percentage: 15,
          details: []
        }
      });
    });

    // Navigation to Team Management page containing the AiCollaborationWidget
    await page.goto('/#/team');

    // Confirm that the page loads the collaboration widget
    await expect(page.getByRole('heading', { name: 'Team Management' })).toBeVisible();
    await expect(page.getByText('Human-AI Collaboration')).toBeVisible();

    // Verify that the budget warning banner is NOT visible in the DOM
    const warningBanner = page.getByTestId('budget-warning-banner');
    await expect(warningBanner).not.toBeVisible();
  });

  test('Should SHOW prominent warning banner when AI budget is fully exhausted', async ({ page }) => {
    // Intercept AI usage API to return exhausted budget (110% consumed)
    await page.route('**/api/stats/ai-usage', async route => {
      await route.fulfill({
        status: 200,
        json: {
          total_budget: 1000,
          total_used: 1100,
          usage_percentage: 110,
          details: []
        }
      });
    });

    // Navigation to Team Management page
    await page.goto('/#/team');

    // Confirm that the page loads the collaboration widget
    await expect(page.getByRole('heading', { name: 'Team Management' })).toBeVisible();

    // Verify that the budget warning banner is fully visible and contains correct warning copy
    const warningBanner = page.getByTestId('budget-warning-banner');
    await expect(warningBanner).toBeVisible();
    await expect(warningBanner).toContainText('AI Budget Exhausted!');
    await expect(warningBanner).toContainText('allocation is fully depleted');
  });
});
