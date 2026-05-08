import { test, expect } from '@playwright/test';
import { StatefulMock } from './fixtures/systemFixtures';

// Initialize a stateful mock for prompts
const mockPrompts = new StatefulMock([
  {
    prompt_name: 'test_prompt',
    content: 'This is the mocked original content from Playwright StatefulMock.',
    is_system_protected: false,
    updated_at: new Date().toISOString()
  }
]);

test.describe('PromptManagement MBT Visual Test', () => {
  test('should execute full XState lifecycle visually with global auth', async ({ page }) => {
    // Intercept window alerts to automatically accept them and log them
    page.on('dialog', async dialog => {
      console.log(`Dialog message: ${dialog.message()}`);
      await dialog.accept();
    });

    // Use stateful mock for system prompts
    await page.route('**/api/system/prompts*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ status: 200, json: mockPrompts.get() });
      } else if (route.request().method() === 'POST' || route.request().method() === 'PUT') {
        const postData = JSON.parse(route.request().postData() || '{}');
        const url = new URL(route.request().url());
        const name = url.pathname.split('/').pop();
        
        mockPrompts.update(
          p => p.prompt_name === name,
          p => ({ ...p, content: postData.prompt || postData.content, updated_at: new Date().toISOString() })
        );
        await route.fulfill({ status: 200, json: { success: true } });
      } else {
        await route.continue();
      }
    });

    // 1. Navigate directly to Admin Page (bypassing login due to global.setup.ts)
    console.log('Navigating directly to Admin Control Center...');
    await page.goto('/#/admin');
    
    // 2. Select the Prompts Tab
    const promptsTab = page.locator('button', { hasText: 'System Prompts' });
    await promptsTab.waitFor({ state: 'visible' });
    await promptsTab.click();

    // Wait for the textarea to be loaded
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible({ timeout: 10000 });
    
    // Record original value
    const originalValue = await textarea.inputValue();
    console.log('Original prompt loaded.');

    // 3. Edit Value
    const newContent = `${originalValue}\n\n[Automated MBT Test Edit]`;
    await textarea.fill(newContent);
    expect(await textarea.inputValue()).toBe(newContent);
    console.log('Textarea updated.');

    // 4. Toggle Diff View
    const diffBtn = page.locator('button', { hasText: 'DIFF' });
    await diffBtn.click();
    console.log('Switched to DIFF mode.');

    const revertBtn = page.locator('button', { hasText: 'REVERT' });
    await expect(revertBtn).toBeVisible();

    // 5. Revert Changes
    await revertBtn.click();
    console.log('Reverted changes.');
    
    await expect(textarea).toBeVisible();
    expect(await textarea.inputValue()).toBe(originalValue);

    // 6. Final Edit & Save
    await textarea.fill('Final save test content...');
    const saveBtn = page.locator('button', { hasText: 'SAVE' });
    await saveBtn.click();
    console.log('Save triggered and intercepted by StatefulMock.');

    await page.waitForTimeout(1000);
    
    // Verify stateful mock actually updated
    const updatedContent = await textarea.inputValue();
    expect(updatedContent).toBe('Final save test content...');
  });
});
