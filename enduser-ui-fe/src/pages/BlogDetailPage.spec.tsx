
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import BlogDetailPage from './BlogDetailPage.tsx';
import { api } from '../services/api.ts';

// Mock the API
vi.mock('../services/api.ts', () => ({
    api: {
        getBlogPost: vi.fn()
    }
}));

// Simple mock for react-markdown if needed, but let's see if it works naturally
// vi.mock('react-markdown', () => ({
//     default: ({ children }: { children: string }) => <div data-testid="markdown">{children}</div>
// }));

describe('BlogDetailPage Rendering (Phase 6 Verification)', () => {
    
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should fetch and render blog content with markdown support', async () => {
        const mockPost = {
            id: 'post-1',
            title: 'Markdown Test Post',
            content: '# Heading 1\n\n**Bold Text**\n\n- List Item',
            authorName: 'Professor Archon',
            publishDate: new Date().toISOString(),
            imageUrl: 'https://example.com/image.jpg'
        };

        (api.getBlogPost as any).mockResolvedValue(mockPost);

        render(
            <MemoryRouter initialEntries={['/blog/post-1']}>
                <Routes>
                    <Route path="/blog/:id" element={<BlogDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        // 1. Verify loading state initially
        expect(screen.getByText(/Loading/i)).toBeInTheDocument();

        // 2. Wait for content to appear
        await waitFor(() => {
            expect(screen.getByText('Markdown Test Post')).toBeInTheDocument();
        });

        // 3. Verify Markdown elements (this depends on react-markdown rendering)
        // Check if Heading 1 is rendered as an h1
        const heading = screen.getByRole('heading', { level: 1, name: 'Heading 1' });
        expect(heading).toBeInTheDocument();

        // Check for bold text
        const boldText = screen.getByText('Bold Text');
        expect(boldText.tagName).toBe('STRONG');

        // Check for list item
        expect(screen.getByText('List Item')).toBeInTheDocument();
    });

    it('should show error message when post is not found', async () => {
        (api.getBlogPost as any).mockRejectedValue(new Error('Post not found'));

        render(
            <MemoryRouter initialEntries={['/blog/post-invalid']}>
                <Routes>
                    <Route path="/blog/:id" element={<BlogDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        await waitFor(() => {
            expect(screen.getByText(/Failed to load blog post/i)).toBeInTheDocument();
        });
    });
});
