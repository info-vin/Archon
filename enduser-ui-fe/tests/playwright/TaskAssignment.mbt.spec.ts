import { test, expect } from '@playwright/test';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('Task Assignment MBT Visual Test', () => {
  test('should execute full XState lifecycle for crawler task assignment', async ({ page }) => {
    // Mock Projects
    await page.route('**/api/projects*', async route => {
      await route.fulfill({ status: 200, json: [{ id: 'proj-1', title: 'Admin Project' }] });
    });

    // Mock Assignable Users
    await page.route('**/api/assignable-users*', async route => {
      await route.fulfill({ status: 200, json: [
        { id: 'lib-1', name: 'Librarian', role: 'ai_agent', tools: ['crawler'] },
        { id: 'ai-researcher-1', name: 'Market Researcher', role: 'ai_agent', tools: ['search'] }
      ]});
    });

    // Mock Crawler Targets
    await page.route('**/api/admin/crawler-targets*', async route => {
      await route.fulfill({ status: 200, json: { 
        targets: [{ id: 'target-1', target_url: 'https://gov.site/data', description: 'Govt Target' }] 
      }});
    });

    // Navigate to Dashboard
    await page.goto('/#/dashboard');

    // Open New Task Modal
    // Using a more resilient locator for the indigo button
    const newTaskBtn = page.locator('button', { hasText: 'New Task' }).first();
    await newTaskBtn.waitFor({ state: 'visible' });
    await newTaskBtn.click();

    // Fill basic info in General Tab
    await page.getByLabel('Title').fill('Automated Crawler Task');
    
    // Wait for options to load
    const projectSelect = page.getByLabel('Project');
    await projectSelect.waitFor({ state: 'visible' });
    await projectSelect.selectOption({ label: 'Admin Project' });
    
    // Set Due Date
    await page.getByRole('button', { name: 'Due Date' }).click();
    await page.getByRole('button', { name: 'Tomorrow' }).click();
    await page.getByRole('button', { name: 'CONFIRM SELECTION' }).click();

    // 1. Transition to Assignment Tab (State: idle)
    await page.getByRole('button', { name: 'Assignment & Automation' }).click();
    
    // 2. Select Librarian (State: idle -> configuring_crawler)
    const assigneeSelect = page.getByLabel('Assignee');
    await assigneeSelect.selectOption({ label: '(AI) Librarian' });

    // 3. Verify 'David\'s Architect Tools' (configuring_crawler state UI)
    const architectTools = page.getByText("David's Architect Tools");
    await expect(architectTools).toBeVisible();

    // 4. Select Crawler Target
    const crawlerSelect = page.getByLabel('Associate Knowledge Target (from 3737)');
    await expect(crawlerSelect).toBeVisible();
    await crawlerSelect.selectOption({ index: 1 });

    // 5. Toggle Recurring (Expertise Loop)
    const recurringCheckbox = page.getByLabel('Add to Periodic Schedule (Expertise Loop)');
    await recurringCheckbox.check();
    
    // 6. Verify Frequency select appears
    const frequencySelect = page.getByLabel('Sync Frequency');
    await expect(frequencySelect).toBeVisible();
    await frequencySelect.selectOption('weekly');

    // 7. Toggle Collaborator
    const marketResearcherCheckbox = page.getByLabel('Market Researcher', { exact: true });
    await marketResearcherCheckbox.check();

    // 8. Submit and verify payload
    await page.route('**/api/tasks*', async route => {
      if (route.request().method() === 'POST') {
          const payload = route.request().postDataJSON();
          expect(payload.title).toBe('Automated Crawler Task');
          expect(payload.crawler_target_id).toBe('target-1');
          expect(payload.is_recurring).toBe(true);
          await route.fulfill({ status: 200, json: { id: 'mock-task-id' } });
      } else {
          await route.continue();
      }
    });

    // Accept success dialog
    page.on('dialog', async dialog => {
        await dialog.accept();
    });

    await page.getByRole('button', { name: 'Create task' }).click();
  });
});
