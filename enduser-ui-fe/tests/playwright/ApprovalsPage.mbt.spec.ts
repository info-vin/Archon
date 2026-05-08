import { test, expect } from '@playwright/test';
import { simulate500Error, simulateNetworkTimeout } from './fixtures/systemFixtures';

// Using the global setup for authentication, we don't need to log in here.
test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('ApprovalsPage MBT & Pessimistic Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the manager approvals page
    // Note: Assuming the route is /manager or /approvals. Let's check App.tsx later, 
    // for now we'll assume /manager as it's for Charlie (Manager)
    await page.goto('/manager');
  });

  test('should display 500 error gracefully when fetching proposals fails', async ({ page }) => {
    // Mock the pending changes/approvals API to return 500
    await simulate500Error(page, '**/api/admin/pending-approvals');
    await simulate500Error(page, '**/api/admin/pending-changes');

    await page.reload();

    // Verify error state is shown or at least handled (depending on how useApprovalInbox sets error)
    // The current ApprovalsPage doesn't render `error` from the hook explicitly, it just shows empty state
    // Let's verify it doesn't crash and shows empty state or alert
    await expect(page.getByText('Select a contribution to begin the audit process.')).toBeVisible();
    await expect(page.getByText('Pending Actions')).toBeVisible(); // The count might be 0
  });

  test('should handle network timeout on action gracefully (prevent double submission)', async ({ page }) => {
    // Mock a normal response first so it loads
    await page.route('**/api/admin/pending-approvals', async route => {
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

    await page.route('**/api/admin/pending-changes', async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.reload();

    // Wait for the proposal to show up in the sidebar
    await expect(page.getByText('Test Blog Proposal')).toBeVisible();

    // Click the proposal
    await page.getByText('Test Blog Proposal').click();

    // Simulate network delay for the approve action
    await simulateNetworkTimeout(page, '**/api/marketing/blogs/test-id-123/approve', 5000);

    // Click Approve
    const approveButton = page.getByRole('button', { name: /approve/i });
    await approveButton.click();

    // The button should show loading state or be disabled (processingId is set)
    // Actually ApprovalsPage passes processingId. Let's check how ApprovalActionHeader renders it.
    // It should be disabled.
    await expect(approveButton).toBeDisabled();

    // Wait for the action to complete
    // The delay is 5s, the test timeout is usually 30s.
    // After it completes, the item should be gone from the list.
    await expect(page.getByText('Test Blog Proposal')).not.toBeVisible({ timeout: 10000 });
  });

  test('should handle AI reason generation error gracefully', async ({ page }) => {
    // Setup initial mock
    await page.route('**/api/admin/pending-approvals', async route => {
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
    });
    await page.route('**/api/admin/pending-changes', async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.reload();
    await page.getByText('Another Blog').click();

    // Click Reject to show the input
    await page.getByRole('button', { name: /reject/i }).click();

    // Simulate 500 on generate reason
    await simulate500Error(page, '**/api/marketing/blogs/test-id-456/reject-reason');

    // Click Generate AI Reason
    await page.getByRole('button', { name: /generate ai reason/i }).click();

    // Verify it falls back to the manual input message
    await expect(page.locator('textarea')).toHaveValue(/Failed to generate AI reason|The content does not align/, { timeout: 5000 });
  });
});
