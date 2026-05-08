import { test, expect } from '@playwright/test';

test.describe('PromptManagement MBT Visual Test', () => {
  test('should execute full XState lifecycle visually', async ({ page }) => {
    // Intercept window alerts to automatically accept them and log them
    page.on('dialog', async dialog => {
      console.log(`Dialog message: ${dialog.message()}`);
      await dialog.accept();
    });

    // Intercept Supabase Auth Login
    await page.route('**/auth/v1/token?grant_type=password*', async route => {
      await route.fulfill({
        status: 200,
        json: {
          access_token: 'mock-token',
          refresh_token: 'mock-refresh',
          expires_in: 3600,
          token_type: 'bearer',
          user: { 
            id: 'mock-admin-id', 
            email: 'admin@archon.local', 
            app_metadata: {},
            user_metadata: { role: 'system_admin', name: 'System Admin' },
            aud: 'authenticated',
            role: 'authenticated'
          }
        }
      });
    });

    // Intercept Supabase Profiles Query
    await page.route('**/rest/v1/profiles*', async route => {
      await route.fulfill({
        status: 200,
        json: [{
          id: 'mock-admin-id',
          email: 'admin@archon.local',
          name: 'System Admin',
          role: 'system_admin',
          employeeId: 'EMP-001',
          department: 'IT',
          status: 'active'
        }]
      });
    });

    // Intercept the API to prevent actual mutation and provide mock data
    await page.route('**/api/system/prompts*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          json: [{
            prompt_name: 'test_prompt',
            content: 'This is the mocked original content from Playwright interception.',
            is_system_protected: false,
            updated_at: new Date().toISOString()
          }]
        });
      } else if (route.request().method() === 'PUT' || route.request().method() === 'POST') {
        await route.fulfill({ status: 200, json: { success: true } });
      } else {
        await route.continue();
      }
    });

    // 1. Perform Mock Login
    console.log('Navigating to Auth...');
    await page.goto('/#/auth');
    await page.fill('input[name="email"]', 'admin@archon.local');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('**/#/dashboard', { timeout: 10000 });
    console.log('Login successful, navigating to Admin Control Center...');

    // 2. Navigate to Admin Page
    await page.goto('/#/admin');
    
    // 3. Select the Prompts Tab
    const promptsTab = page.locator('button', { hasText: 'System Prompts' });
    await promptsTab.waitFor({ state: 'visible' });
    await promptsTab.click();

    // Wait for the textarea to be loaded (meaning FETCH_SUCCESS and SELECT_PROMPT happened)
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible({ timeout: 10000 });
    
    // Record original value
    const originalValue = await textarea.inputValue();
    console.log('Original prompt loaded.');

    // 4. Edit Value
    const newContent = `${originalValue}\n\n[Automated MBT Test Edit]`;
    await textarea.fill(newContent);
    expect(await textarea.inputValue()).toBe(newContent);
    console.log('Textarea updated.');

    // 5. Toggle Diff View
    const diffBtn = page.locator('button', { hasText: 'DIFF' });
    await diffBtn.click();
    console.log('Switched to DIFF mode.');

    // In diff mode, textarea should be gone, and DiffViewer should be visible
    // DiffViewer usually has 'Original' and 'Modified' or similar headers/text
    // Let's just wait for the Revert button to ensure we are still interacting
    const revertBtn = page.locator('button', { hasText: 'REVERT' });
    await expect(revertBtn).toBeVisible();

    // 6. Revert Changes
    await revertBtn.click();
    console.log('Reverted changes.');
    
    // Should automatically return to edit mode and original value
    await expect(textarea).toBeVisible();
    expect(await textarea.inputValue()).toBe(originalValue);

    // 7. Final Edit & Save
    await textarea.fill('Final save test content...');
    const saveBtn = page.locator('button', { hasText: 'SAVE' });
    await saveBtn.click();
    console.log('Save triggered and intercepted.');

    // Wait a brief moment for the state machine to transition back to editing after mock save
    await page.waitForTimeout(1000);
  });
});
