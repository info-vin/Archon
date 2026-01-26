import { vi } from 'vitest';

// Polyfill window.matchMedia for JSDOM - MUST BE AT TOP LEVEL
if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

// 1. Mock the API module partially to retain supabase instance but mock the api object
vi.mock('../../src/services/api', async (importOriginal) => {
    const actual = await importOriginal() as any;
    return {
        ...actual,
        api: {
            ...actual.api,
            getCurrentUser: vi.fn().mockResolvedValue({ 
                id: 'def-1', 
                role: 'admin', 
                permissions: ['leads:view:all', 'brand_asset_manage', 'user:manage:team'] 
            }),
            getBlogPosts: vi.fn().mockResolvedValue([]),
            getMarketStats: vi.fn().mockResolvedValue({ "AI/LLM": 10, "Total Leads": 20, "Data/BI": 5 }),
            searchJobs: vi.fn().mockResolvedValue([]),
            draftBlogPost: vi.fn().mockResolvedValue({ title: 'Draft', content: 'Content with References: [Ref]' }),
            getLeads: vi.fn().mockResolvedValue([]),
            getEmployees: vi.fn().mockResolvedValue([]),
            getAiUsage: vi.fn().mockResolvedValue({ total_budget: 1000, total_used: 0 }),
            getPendingApprovals: vi.fn().mockResolvedValue({ blogs: [], leads: [] }),
            getProjects: vi.fn().mockResolvedValue([]), // Fixed: Return array, not object
            getTasks: vi.fn().mockResolvedValue([]),
            getKnowledgeItems: vi.fn().mockResolvedValue([]),
        }
    };
});

import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/hooks/useAuth';
import { api } from '../../src/services/api';
import { AppRoutes } from '../../src/App'; // Import the actual routes

// Standard render wrapper
export const renderApp = (initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        <AppRoutes /> 
      </AuthProvider>
    </MemoryRouter>
  );
};

// Global Mocks for common browser APIs
if (typeof window !== 'undefined') {
    window.scrollTo = vi.fn();
    if (!HTMLDialogElement.prototype.showModal) {
        HTMLDialogElement.prototype.showModal = vi.fn(function(this: HTMLDialogElement) {
            this.setAttribute('open', '');
        });
        HTMLDialogElement.prototype.close = vi.fn(function(this: HTMLDialogElement) {
            this.removeAttribute('open');
        });
    }
}
