import { test, expect } from '@playwright/test';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('Voice Scheduling E2E Workflow', () => {

  test('should successfully display suggested slots when logging a visit with scheduling intent', async ({ page }) => {
    const mockLeadId = `lead-${Date.now()}`;
    const mockCompany = `Acme Corp ${Date.now()}`;

    // 1. Mock Marketing Leads list
    await page.route('**/api/marketing/leads', async route => {
      await route.fulfill({
        status: 200,
        json: [{
          id: mockLeadId,
          company_name: mockCompany,
          job_title: 'Marketing Director',
          identified_need: 'Needs scheduling check for requirements briefing',
          status: 'shortlisted'
        }]
      });
    });

    // 2. Mock Visit Log Creation API returning scheduling recommendations
    await page.route('**/api/visit-logs/**', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          json: {
            id: 'log-uuid-123',
            voice_transcript: '我想預約下次 2026-06-01 跟 Bob 與 Charlie 的會議',
            summary: 'AI 預約會議分析成功',
            follow_up_tasks: ['預約會議'],
            scheduling_recommendation: {
              meeting_topic: '需求規格書討論',
              suggested_slots: [
                { start_time: '2026-06-01T09:00:00+08:00', end_time: '2026-06-01T10:00:00+08:00' },
                { start_time: '2026-06-01T13:00:00+08:00', end_time: '2026-06-01T14:00:00+08:00' },
                { start_time: '2026-06-01T16:00:00+08:00', end_time: '2026-06-01T17:00:00+08:00' }
              ],
              conflict_summary: '已為 Bob (MarketBot) 與 Charlie (Supervisor) 排除行程衝突。建議開會時間選項如下'
            }
          }
        });
      } else {
        await route.continue();
      }
    });

    // 3. Handle confirm popups for simulated geolocation fallback
    page.on('dialog', async dialog => {
      await dialog.accept();
    });

    // 4. Navigate to Marketing page and trigger visit log
    await page.goto('/#/marketing');
    
    // Click "My Leads"
    await page.getByRole('button', { name: 'My Leads' }).click();
    await expect(page.locator('table').getByText(mockCompany)).toBeVisible({ timeout: 15000 });

    // Open Visit Log Modal
    await page.locator('table').locator("button[title='Log Visit (Hunter Mode)']").first().click();

    // Select type
    await page.getByRole('button', { name: 'Client Meeting' }).click();

    // Get current location (will trigger confirm dialog mock fallback)
    await page.getByLabel('Get current location').click();

    // Simulate Voice Transcription notes
    await page.getByRole('button', { name: 'Simulate Voice' }).click();

    // Save and submit the log
    await page.getByRole('button', { name: 'Save Visit' }).click();

    // 5. Verification
    await expect(page.getByText('Visit Logged!')).toBeVisible({ timeout: 15000 });
    
    // Check that Suggested Slots title is visible
    await expect(page.getByText('📅 SUGGESTED MEETING SLOTS (GMT+8)')).toBeVisible();
    await expect(page.getByText('Slot A')).toBeVisible();
    await expect(page.getByText('Slot B')).toBeVisible();
    await expect(page.getByText('Slot C')).toBeVisible();

    // Click Done to dismiss
    await page.getByRole('button', { name: 'Done' }).click();
    await expect(page.getByText('Visit Logged!')).not.toBeVisible();
  });
});
