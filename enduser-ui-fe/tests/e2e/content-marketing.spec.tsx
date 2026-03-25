import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { renderApp } from './e2e.setup';
import { createUser } from '../factories/userFactory';

describe('Content Marketing E2E Flow', () => {
    it('Bob can draft a blog post using the Workbench workflow', async () => {
        const user = userEvent.setup();
        
        // 1. Mock Bob and initial data
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

        renderApp(['/brand']);

        // 2. Verify Victory Feed is active and find the signal
        const signal = await screen.findByText('Mozilla', {}, { timeout: 15000 });
        await user.click(signal);

        // 3. Verify Context Intelligence is loaded in the left pane
        expect(await screen.findByText(/Alice said client wants privacy/i)).toBeInTheDocument();

        // 4. Open AI Command Center
        const aiCommandBtn = await screen.findByRole('button', { name: /Open AI Command Center/i });
        await user.click(aiCommandBtn);

        // 5. Execute Magic Synthesis
        const runSynthesisBtn = await screen.findByRole('button', { name: /Run Magic Synthesis/i });
        await user.click(runSynthesisBtn);

        // 6. Verify Article Draft is populated in the editor (Wait for async state update)
        // Check for the title input value
        await waitFor(() => {
            const titleInput = screen.getByPlaceholderText(/Article Title/i) as HTMLInputElement;
            expect(titleInput.value).toBe('Privacy in AI');
        }, { timeout: 10000 });

        // Check for the content textarea value
        const contentArea = screen.getByPlaceholderText(/Start typing or use the AI toolbox/i) as HTMLTextAreaElement;
        expect(contentArea.value).toContain('Article body about Privacy...');
    });
});
