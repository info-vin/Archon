import { test, expect } from './fixtures/systemFixtures';
import { simulate500Error, simulateNetworkTimeout, waitForSpinner } from './fixtures/systemFixtures';

// Using the global setup for authentication from playwright.config.ts.

test.describe('ApprovalsPage MBT & Pessimistic Flow', () => {
  test('should display 500 error gracefully when fetching proposals fails', async ({ page }) => {
    // Mock the pending changes/approvals API to return 500
    await simulate500Error(page, /.*\/api\/marketing\/approvals.*/);
    await simulate500Error(page, /.*\/api\/changes.*/);

    // Navigate to the manager approvals page
    await page.goto('/#/approvals');
    await waitForSpinner(page);

    await expect(page.getByTestId('empty-selection-msg')).toBeVisible();
    await expect(page.getByTestId('error-msg')).toBeVisible();
  });

  test('should handle network timeout on action gracefully (prevent double submission)', async ({ page }) => {
    // Mock a normal response first so it loads
    await page.route(/.*\/api\/marketing\/approvals.*/, async route => {
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
            authorName: 'Bob',
            is_marketing: true
          }],
          leads: []
        })
      });
    });

    await page.route(/.*\/api\/changes.*/, async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.goto('/#/approvals');
    await waitForSpinner(page);

    // Verify the proposal shows up inside the hardened sidebar list container
    const sidebar = page.getByTestId('approval-inbox-list');
    await expect(sidebar.getByText('Test Blog Proposal').first()).toBeVisible();

    // Click the proposal within the sidebar container
    await sidebar.getByText('Test Blog Proposal').first().click();

    // Simulate network delay for the approve action
    await simulateNetworkTimeout(page, /.*\/api\/marketing\/approvals.*/, 5000);

    // Click Approve using our hardened test-id
    const approveButton = page.getByTestId('approve-action-button');
    await approveButton.click();

    await expect(approveButton).toBeDisabled();

    // After it completes, the item should be gone from the list.
    await expect(sidebar.getByText('Test Blog Proposal').first()).not.toBeVisible({ timeout: 10000 });
  });

  test('should handle AI reason generation error gracefully', async ({ page }) => {
    // Setup initial mock for approvals
    await page.route(/.*\/api\/marketing\/approvals.*/, async route => {
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
            authorName: 'Bob',
            is_marketing: true
          }],
          leads: []
        })
      });
    });

    // Mock the AI reason generation endpoint
    await page.route(/.*\/api\/marketing\/blogs\/.*\/reject-suggestion/, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal Server Error' })
      });
    });

    await page.route(/.*\/api\/changes.*/, async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.goto('/#/approvals');
    await waitForSpinner(page);
    
    // Ensure the blog proposal is selected from the sidebar
    const sidebar = page.getByTestId('approval-inbox-list');
    await sidebar.getByText('Another Blog').first().click();

    // Click REJECT to show the input using our hardened test-id
    const rejectBtn = page.getByTestId('reject-action-button');
    await expect(rejectBtn).toBeVisible();
    await rejectBtn.click();

    // Wait for the AI reason button to appear and click it
    const aiReasonBtn = page.getByTestId('generate-ai-reason-btn');
    await expect(aiReasonBtn).toBeVisible();
    await aiReasonBtn.click();

    // Verify it falls back to the manual input message
    await expect(page.getByTestId('reject-reason-input')).toHaveValue(/Failed to generate AI reason|The content does not align/, { timeout: 5000 });
  });

  test('should handle Action failure (500 Error on Approve) gracefully', async ({ page }) => {
    // Setup initial mock for approvals
    await page.route(/.*\/api\/marketing\/approvals.*/, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          blogs: [{
            id: 'test-id-approve-fail',
            title: 'Failed Action Blog',
            content: 'Failed approve action',
            status: 'pending',
            created_at: new Date().toISOString(),
            authorName: 'Charlie',
            is_marketing: true
          }],
          leads: []
        })
      });
    });

    await page.route(/.*\/api\/changes.*/, async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.goto('/#/approvals');
    await waitForSpinner(page);

    const sidebar = page.getByTestId('approval-inbox-list');
    await sidebar.getByText('Failed Action Blog').first().click();

    // Mock the approve endpoint to return 500 error
    await page.route(/.*\/api\/marketing\/approvals\/blog\/.*\/approve/, async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal Server Error' })
      });
    });

    const approveButton = page.getByTestId('approve-action-button');
    await expect(approveButton).toBeVisible();
    await approveButton.click();

    // Verify it doesn't crash, the item remains visible, and button is re-enabled for retry
    await expect(approveButton).toBeEnabled({ timeout: 5000 });
    await expect(sidebar.getByText('Failed Action Blog').first()).toBeVisible();
  });

  test('should disable action buttons immediately on click to prevent concurrent submissions', async ({ page }) => {
    // Setup initial mock for approvals
    await page.route(/.*\/api\/marketing\/approvals.*/, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          blogs: [{
            id: 'test-id-slow-action',
            title: 'Slow Action Blog',
            content: 'Slow Action content',
            status: 'pending',
            created_at: new Date().toISOString(),
            authorName: 'Charlie',
            is_marketing: true
          }],
          leads: []
        })
      });
    });

    await page.route(/.*\/api\/changes.*/, async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    await page.goto('/#/approvals');
    await waitForSpinner(page);

    const sidebar = page.getByTestId('approval-inbox-list');
    await sidebar.getByText('Slow Action Blog').first().click();

    // Mock the action with severe delay to keep buttons in processing state
    await simulateNetworkTimeout(page, /.*\/api\/marketing\/approvals\/blog\/.*\/approve/, 10000);

    const approveButton = page.getByTestId('approve-action-button');
    const rejectButton = page.getByTestId('reject-action-button');

    await expect(approveButton).toBeEnabled();
    await expect(rejectButton).toBeEnabled();

    // Click approve button
    await approveButton.click();

    // Both buttons must be disabled immediately while processing is active
    await expect(approveButton).toBeDisabled();
    await expect(rejectButton).toBeDisabled();
  });
});
