import { test, expect } from '@playwright/test';
import { StatefulMock, simulateNetworkTimeout, simulate500Error, waitForSpinner } from './fixtures/systemFixtures';
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
    await simulate500Error(page, /.*\/api\/marketing\/images\/search.*/);

    // Click 'Smart Asset Search' for cover image
    const smartAssetBtn = page.getByTestId('smart-asset-search-btn');
    await smartAssetBtn.waitFor({ state: 'visible' });
    await smartAssetBtn.click();

    // Verify Modal appears
    const modalHeader = page.getByTestId('image-picker-modal-title');
    await expect(modalHeader).toBeVisible();

    // Type and search
    const searchInput = page.getByTestId('image-search-input');
    await searchInput.fill('business');
    await page.getByTestId('image-search-submit-btn').click();
    await waitForSpinner(page);

    // Verify Error State
    await expect(page.getByTestId('image-search-error-msg')).toBeVisible();

    // Unroute the error and provide success mock
    await page.unroute(/.*\/api\/marketing\/images\/search.*/);
    await page.route(/.*\/api\/marketing\/images\/search.*/, async route => {
      await route.fulfill({ status: 200, json: mockImages.get() });
    });

    // Scenario 2: Retry and Success Path
    const retryBtn = page.getByTestId('image-search-retry-btn');
    await retryBtn.click();
    await waitForSpinner(page);

    // Verify images are loaded
    await expect(page.getByText('By Alice Photographer')).toBeVisible();

    // Select an image by clicking its author text (bubbles up and avoids overlay interception)
    await page.getByText('By Alice Photographer').click();

    // Verify selection feedback (border color change)
    await expect(page.getByTestId('image-result').first()).toHaveClass(/border-indigo-600/);

    // Verify 'Insert Image' is enabled and click it
    const insertBtn = page.getByTestId('insert-image-btn');
    await expect(insertBtn).toBeEnabled();
    await insertBtn.click();

    // Modal should close and the cover image should be updated in the editor
    await expect(modalHeader).not.toBeVisible();
    
    // The img src should now be the selected image URL
    const coverImage = page.getByTestId('cover-image');
    await expect(coverImage).toBeVisible();
    await expect(coverImage).toHaveAttribute('src', 'https://images.unsplash.com/photo-1');
  });

  test('should handle network timeout gracefully', async ({ page }) => {
    await page.goto('/#/brand/editor/new');

    // Provide empty result after delay
    await page.route(/.*\/api\/marketing\/images\/search.*/, async route => {
      await new Promise(resolve => setTimeout(resolve, 3000));
      await route.fulfill({ status: 200, json: [] });
    });

    const smartAssetBtn = page.getByTestId('smart-asset-search-btn');
    await smartAssetBtn.waitFor({ state: 'visible' });
    await smartAssetBtn.click();
    
    await page.getByTestId('image-search-input').fill('empty result test');
    
    // Start search
    await page.getByTestId('image-search-submit-btn').click();

    // Verify loading state
    await expect(page.getByTestId('searching-assets-msg')).toBeVisible();

    await waitForSpinner(page);

    // Wait for empty state
    await expect(page.getByTestId('no-images-found-msg')).toBeVisible({ timeout: 5000 });
  });
});