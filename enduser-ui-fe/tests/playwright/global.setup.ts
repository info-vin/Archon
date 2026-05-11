import { test as setup, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const authFile = path.join(process.cwd(), '../.playwright/admin_storage_state.json');

setup('authenticate as system admin', async ({ page }) => {
  // Ensure the .playwright directory exists
  const dir = path.dirname(authFile);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  console.log('🚀 [Global Setup] Authenticating as System Admin...');
  await page.goto('/#/auth');
  
  try {
      await page.waitForSelector('input[name="email"]', { timeout: 5000 });
  } catch (e) {
      console.log("Timeout waiting for email input. Dumping HTML:");
      const html = await page.evaluate(() => document.body.innerHTML);
      console.log(html.substring(0, 2000));
      throw e;
  }

  await page.fill('input[name="email"]', 'admin@archon.com');
  await page.fill('input[name="password"]', 'qwer45tyuiop');
  await page.click('button[type="submit"]');

  // Wait for redirect to dashboard
  await page.waitForURL('**/#/dashboard', { timeout: 15000 });
  
  // Verify login success
  await expect(page).toHaveURL(/.*dashboard/);
  
  // Save storage state (cookies and localStorage)
  await page.context().storageState({ path: authFile });
  console.log(`✅ [Global Setup] Auth state saved to ${authFile}`);
});
