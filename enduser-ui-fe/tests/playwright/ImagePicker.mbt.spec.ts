import { test, expect } from '@playwright/test';
import { StatefulMock, simulateNetworkTimeout, simulate500Error } from './fixtures/systemFixtures';
import { ImageResult } from '../../src/features/marketing/machines/imagePickerMachine';

const mockImages = new StatefulMock<ImageResult>([
  {
    id: 'img-1',
    url: 'https://images.unsplash.com/photo-1',
    thumbnail: 'https://images.unsplash.com/photo-1?w=200',
    author: 'Alice Photographer',
    source: 'Unsplash'
  },
  {
    id: 'img-2',
    url: 'https://images.unsplash.com/photo-2',
    thumbnail: 'https://images.unsplash.com/photo-2?w=200',
    author: 'Bob Lens',
    source: 'Unsplash'
  }
]);

test.describe('Smart Image Picker MBT Visual Test', () => {
  test('should execute full XState lifecycle including error and success paths', async ({ page }) => {
    // We navigate to a new blog editor to trigger the picker
    await page.goto('/#/brand/editor/new');

    // Scenario 1: API Error Path
    await simulate500Error(page, '**/api/marketing/images/search*');

    // Click 'Smart Asset Search' for cover image
    const smartAssetBtn = page.locator('button', { hasText: 'Smart Asset Search' });
    await smartAssetBtn.waitFor({ state: 'visible' });
    await smartAssetBtn.click();

    // Verify Modal appears
    const modalHeader = page.locator('h2', { hasText: 'Smart Image Picker' });
    await expect(modalHeader).toBeVisible();

    // Type and search - Use specific role to avoid ambiguity with 'Smart Asset Search'
    const searchInput = page.locator('input[placeholder*="Search high-quality images"]');
    await searchInput.fill('business');
    await page.getByRole('button', { name: 'Search', exact: true }).click();

    // Verify Error State
    await expect(page.locator('p', { hasText: 'Error searching images' })).toBeVisible();

    // Unroute the error and provide success mock
    await page.unroute('**/api/marketing/images/search*');
    await page.route('**/api/marketing/images/search*', async route => {
      await route.fulfill({ status: 200, json: mockImages.get() });
    });

    // Scenario 2: Retry and Success Path
    const retryBtn = page.locator('button', { hasText: 'Retry' });
    await retryBtn.click();

    // Verify images are loaded
    await expect(page.locator('p', { hasText: 'By Alice Photographer' })).toBeVisible();

    // Select an image by clicking its author text (bubbles up and avoids overlay interception)
    await page.getByText('By Alice Photographer').click();

    // Verify selection feedback (border color change)
    await expect(page.locator('div.border-indigo-600')).toBeVisible();

    // Verify 'Insert Image' is enabled and click it
    const insertBtn = page.getByRole('button', { name: 'Insert Image' });
    await expect(insertBtn).toBeEnabled();
    await insertBtn.click();

    // Modal should close and the cover image should be updated in the editor
    await expect(modalHeader).not.toBeVisible();
    
    // The img src should now be the selected image URL
    const coverImage = page.locator('img[alt="Cover"]');
    await expect(coverImage).toBeVisible();
    await expect(coverImage).toHaveAttribute('src', 'https://images.unsplash.com/photo-1');
  });

  test('should handle network timeout gracefully', async ({ page }) => {
    await page.goto('/#/brand/editor/new');

    // Simulate 3 second delay
    await simulateNetworkTimeout(page, '**/api/marketing/images/search*', 3000);
    // Provide empty result after delay
    await page.route('**/api/marketing/images/search*', async route => {
      await route.fulfill({ status: 200, json: [] });
    });

    const smartAssetBtn = page.locator('button', { hasText: 'Smart Asset Search' });
    await smartAssetBtn.waitFor({ state: 'visible' });
    await smartAssetBtn.click();
    
    await page.getByPlaceholder(/Search high-quality images/).fill('empty result test');
    
    // Start search
    await page.getByRole('button', { name: 'Search', exact: true }).click();

    // Verify loading state
    await expect(page.locator('p', { hasText: 'Searching smart assets...' })).toBeVisible();

    // Wait for empty state
    await expect(page.locator('p', { hasText: 'No images found. Try a different keyword.' })).toBeVisible({ timeout: 5000 });
  });
});