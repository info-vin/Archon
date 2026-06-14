import { test, expect } from '@playwright/test';

test('verify card battler runs and loads successfully', async ({ page }) => {
  console.log('🎮 [Card Battler Test] Loading game...');
  // Navigate directly to the Godot Web build
  await page.goto('/games/card-battler/index.html');
  
  // Wait for the canvas element to be visible
  const canvas = page.locator('#canvas');
  await expect(canvas).toBeVisible({ timeout: 15000 });
  console.log('✅ [Card Battler Test] Game canvas loaded!');

  // Wait 10 seconds to capture the game and recording
  await page.waitForTimeout(10000);
});
