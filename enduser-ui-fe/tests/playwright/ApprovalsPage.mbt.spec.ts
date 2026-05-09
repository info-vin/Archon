import { test, expect } from '@playwright/test';
import { simulate500Error, simulateNetworkTimeout } from './fixtures/systemFixtures';

// Using the global setup for authentication from playwright.config.ts.

test.describe('ApprovalsPage MBT & Pessimistic Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the manager approvals page
    await page.goto('/#/approvals');
    // Ensure we actually stayed on the approvals page and didn't get redirected due to auth
    await expect(page).toHaveURL(/.*approvals/);
  });

  test('should display 500 error gracefully when fetching proposals fails', async ({ page }) => {
    // Mock the pending changes/approvals API to return 500
    await simulate500Error(page, '**/api/marketing/approvals*');
    await simulate500Error(page, '**/api/changes*');

    // Instead of reloading which can cause auth race conditions, let's just trigger a refetch
    // by clicking the refresh button
    await page.locator('button[aria-label="Refresh proposals"]').click();

    await expect(page.getByText('Select a contribution to begin the audit process.')).toBeVisible();
    await expect(page.getByText('Pending Actions')).toBeVisible(); // The count might be 0
  });

  test('should handle network timeout on action gracefully (prevent double submission)', async ({ page }) => {
    // Mock a normal response first so it loads
    await page.route('**/api/marketing/approvals*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          blogs: [{
            id: 'test-id-123',
            title: 'Test Blog Proposal',
            content: 'This is a test blog',
            status: 'pending',
            created_at: new Date().toISOString(),
            authorName: 'Bob'
          }],
          leads: []
        })
      });
    });

    await page.route('**/api/changes*', async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.locator('button[aria-label="Refresh proposals"]').click();

    // Wait for the proposal to show up in the sidebar
    await expect(page.getByText('Test Blog Proposal').first()).toBeVisible();

    // Click the proposal
    await page.getByText('Test Blog Proposal').first().click();

    // Simulate network delay for the approve action
    await simulateNetworkTimeout(page, '**/api/marketing/approvals/*', 5000);

    // Click Approve
    const approveButton = page.getByRole('button', { name: /approve/i });
    await approveButton.click();

    await expect(approveButton).toBeDisabled();

    // After it completes, the item should be gone from the list.
    await expect(page.getByText('Test Blog Proposal')).toHaveCount(0, { timeout: 10000 });
  });

  test('should handle AI reason generation error gracefully', async ({ page }) => {
    // Setup initial mock
    await page.route('**/api/marketing/approvals*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            blogs: [{
              id: 'test-id-456',
              title: 'Another Blog',
              content: 'Bad content',
              status: 'pending',
              created_at: new Date().toISOString(),
              authorName: 'Bob'
            }],
            leads: []
          })
        });
      } else {
        await route.continue();
      }
    });
    await page.route('**/api/changes*', async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.locator('button[aria-label="Refresh proposals"]').click();
    await page.getByText('Another Blog').first().click();

    // Click Reject to show the input
    await page.getByRole('button', { name: /reject/i }).click();

    // Simulate 500 on generate reason
    await simulate500Error(page, '**/api/marketing/approvals/reject-suggestion');

    // Click Generate AI Reason
    await page.getByRole('button', { name: /generate ai reason/i }).click();

    // Verify it falls back to the manual input message
    await expect(page.locator('textarea')).toHaveValue(/Failed to generate AI reason|The content does not align/, { timeout: 5000 });
  });
});
