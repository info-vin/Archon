import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, it, expect, vi, beforeAll, afterEach, afterAll } from 'vitest';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/hooks/useAuth';
import { HttpResponse, http } from 'msw';
import { setupServer } from 'msw/node';
import MarketingPage from '../../src/pages/MarketingPage';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { renderApp } from './e2e.setup';
import { createUser } from '../factories/userFactory';

// Using the shared server from e2e setup logic conceptually, but defining local overrides if needed.
// Actually, since we use renderApp which uses AppRoutes, we should rely on the shared infrastructure.

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
            content: 'Draft content with References: [Lead 104]'
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
        await waitFor(() => {
            expect(screen.getByDisplayValue(/References:/)).toBeInTheDocument();
        });
    });
});
