import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { renderApp } from './e2e.setup';
import { createUser } from '../factories/userFactory';

// Using the shared server from e2e setup logic conceptually, but defining local overrides if needed.
// Actually, since we use renderApp which uses AppRoutes, we should rely on the shared infrastructure.

// Using the shared server from e2e setup logic conceptually.
// We allow e2e.setup.tsx to handle the base module mocking.
// We just override specific methods below.

describe('Content Marketing E2E Flow', () => {
    it('Bob can draft a blog post using RAG citations', async () => {
        const user = userEvent.setup();
        
        // Mock Bob via Factory
        const bob = createUser({
            id: 'bob-1',
            name: 'Bob Marketing',
            role: EmployeeRole.MARKETING
        });
        vi.mocked(api.getCurrentUser).mockResolvedValue(bob as any);

        // Mock Draft Response
        vi.mocked(api.draftBlogPost).mockResolvedValue({
            title: 'AI in Manufacturing',
            content: 'Detailed article about AI...',
            excerpt: 'AI is transforming manufacturing processes...',
            references: ['internal-whitepaper-001']
        });

        // Mock Data Loading (BrandPage MOUNT)
        vi.mocked(api.getBlogPosts).mockResolvedValue([]);
        vi.mocked(api.getMarketStats).mockResolvedValue({});
        vi.mocked(api.getMarketingTrends).mockResolvedValue({
            keyword_growth: [],
            sankey_flow: { nodes: [], links: [] }
        });

        // Start at Dashboard or Landing
        renderApp(['/dashboard']);

        // 1. Find and Click Brand Hub in Sidebar (It's a Link)
        // MainLayout.tsx uses <Link to="/brand">Brand Hub</Link>, so we query by role link or text
        const brandNavLink = await screen.findByRole('link', { name: /Brand Hub/i });
        await user.click(brandNavLink);

        // 2. Wait for Brand Hub Header
        expect(await screen.findByRole('heading', { name: /Brand Hub/i })).toBeInTheDocument();

        // 3. Click "New Post"
        const newPostBtn = await screen.findByText(/New Post/i);
        await user.click(newPostBtn);

        // Mock alert to catch potential errors
        window.alert = vi.fn();

        // 4. Fill Title
        const titleInput = screen.getByPlaceholderText(/e.g. 5 Ways/i);
        await user.type(titleInput, 'AI in Manufacturing');
        
        // Sanity check: Ensure title is actually set (controlled component)
        expect(titleInput).toHaveValue('AI in Manufacturing');

        // 5. Click "Magic Draft"
        const magicDraftBtn = await screen.findByText(/Magic Draft/i);
        await user.click(magicDraftBtn);

        // 6. Verify Citations
        // We rely on the DOM update to confirm the action succeeded
        const contentArea = screen.getByPlaceholderText(/Write your content/i);
        await waitFor(() => {
            const val = (contentArea as HTMLTextAreaElement).value;
            expect(val).toMatch(/References:/);
        });
    });
});
