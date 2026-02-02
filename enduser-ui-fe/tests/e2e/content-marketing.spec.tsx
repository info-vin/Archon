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
    it('Bob can draft a blog post using the Workbench workflow', async () => {
        const user = userEvent.setup();
        const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
        
        // Mock Bob via Factory
        const bob = createUser({
            id: 'bob-1',
            name: 'Bob Marketing',
            role: EmployeeRole.MARKETING
        });
        vi.mocked(api.getCurrentUser).mockResolvedValue(bob as any);

        // Mock Sources
        vi.mocked(api.getContentSources).mockResolvedValue([
            { id: 'lead-123', type: 'lead', title: 'Mozilla', score: 95, summary: 'Privacy concern', date: new Date().toISOString() }
        ]);

        // Mock Context
        vi.mocked(api.getContentContext).mockResolvedValue({
            source_id: 'lead-123',
            source_type: 'lead',
            logs: [],
            rag_refs: [{ content: 'Security baseline', metadata: { source: 'Whitepaper' } }],
            context_summary: 'Alice said client wants privacy.'
        });

        // Mock Draft Response
        vi.mocked(api.draftBlogPost).mockResolvedValue({
            title: 'Privacy in AI',
            content: 'Article body about Privacy...',
            excerpt: 'AI Privacy excerpt...',
            references: ['Whitepaper']
        });

        // Mock generic data
        vi.mocked(api.getBlogPosts).mockResolvedValue([]);
        vi.mocked(api.getMarketStats).mockResolvedValue({});
        vi.mocked(api.getMarketingTrends).mockResolvedValue(null);

        // Start at Dashboard
        renderApp(['/dashboard']);

        // 1. Navigate to Brand Hub
        const brandNavLink = await screen.findByRole('link', { name: /Brand Hub/i });
        await user.click(brandNavLink);

        // 2. Verify Workbench is active
        expect(await screen.findByRole('heading', { name: /Victory Feed/i })).toBeInTheDocument();

        // 3. Select a signal (Mozilla)
        const signal = await screen.findByText('Mozilla');
        await user.click(signal);

        // 4. Verify Context Tab content
        expect(await screen.findByText(/Alice said client wants privacy/i)).toBeInTheDocument();

        // 5. Switch to Editor Tab
        const editorTabBtn = screen.getByRole('button', { name: /Editor/i });
        await user.click(editorTabBtn);

        // 6. Click Magic Draft
        const magicDraftBtn = await screen.findByText(/Magic Draft/i);
        await user.click(magicDraftBtn);

        // 7. Verify Draft is created
        await waitFor(() => {
            expect(alertSpy).toHaveBeenCalledWith(expect.stringMatching(/Draft generated/i));
        }, { timeout: 5000 });
    });
});
