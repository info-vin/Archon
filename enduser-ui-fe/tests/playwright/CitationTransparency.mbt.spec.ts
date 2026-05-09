import { test, expect } from '@playwright/test';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('RAG Citation Transparency MBT Visual Test', () => {
  test('Bob can click citation tags to view RAG knowledge base sources', async ({ page }) => {
    // Intercept the API to provide a mock blog post with citations
    await page.route('**/api/blogs/post-with-citations', async route => {
      await route.fulfill({
        status: 200,
        json: {
          id: 'post-with-citations',
          title: 'The Future of AI Architecture',
          excerpt: 'A brief look into intelligent routing.',
          content: 'Modern agentic workflows rely on dynamic routing to handle tasks [1]. This ensures maximum efficiency and token optimization [2]. Some standalone links like [3](https://example.com) should not be touched.',
          authorName: 'Bob Lens',
          publishDate: new Date().toISOString(),
          imageUrl: 'https://images.unsplash.com/photo-123',
          status: 'published',
          generation_metadata: {
            citations: [
              {
                id: '1',
                title: 'Agentic Workflow Principles',
                url: 'https://docs.archon.ai/workflows',
                snippet: 'Dynamic routing is the core of modern agentic workflows, replacing static if/else chains.'
              },
              {
                id: '2',
                title: 'Token Optimization Guide',
                url: 'https://docs.archon.ai/tokens',
                snippet: 'Efficiency is achieved by reducing prompt context through targeted retrieval.'
              }
            ]
          }
        }
      });
    });

    // Navigate to the specific blog post
    await page.goto('/#/blog/post-with-citations');

    // Wait for the title to be visible
    await expect(page.getByRole('heading', { name: 'The Future of AI Architecture' })).toBeVisible();

    // Verify that standard text is rendered
    await expect(page.getByText('Modern agentic workflows rely on dynamic routing to handle tasks')).toBeVisible();

    // Verify that citations [1] and [2] are rendered as buttons (badges)
    const citation1 = page.getByRole('button', { name: '1', exact: true });
    const citation2 = page.getByRole('button', { name: '2', exact: true });
    
    await expect(citation1).toBeVisible();
    await expect(citation2).toBeVisible();

    // Click citation [1] to open the popover
    await citation1.click();

    // Verify popover content for citation [1]
    const popover1Title = page.getByRole('heading', { name: 'Agentic Workflow Principles' });
    await expect(popover1Title).toBeVisible();
    await expect(page.getByText('"Dynamic routing is the core of modern agentic workflows, replacing static if/else chains."')).toBeVisible();
    
    // Verify the external link
    const externalLink1 = page.getByRole('link', { name: 'View Original Source' });
    await expect(externalLink1).toBeVisible();
    await expect(externalLink1).toHaveAttribute('href', 'https://docs.archon.ai/workflows');

    // Click outside to close (or wait for blur)
    // We can just click the second citation to open the next popover
    await citation2.click();

    // Verify popover content for citation [2]
    const popover2Title = page.getByRole('heading', { name: 'Token Optimization Guide' });
    await expect(popover2Title).toBeVisible();
  });
});
