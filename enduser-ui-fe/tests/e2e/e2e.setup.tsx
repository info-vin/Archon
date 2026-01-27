import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { server } from '../../src/mocks/server';
import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/hooks/useAuth';
import { api } from '../../src/services/api';
import { AppRoutes } from '../../src/App';

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
    
    // Create a spy-able clone of the API
    const mockedApi = { ...actual.api };

    // --- Hybrid Strategy: Mock Auth Only, Pass-through Data ---
    
    // 1. Mock getCurrentUser for Auth context
    // We default to a system admin user. Tests can override this via mockImplementation.
    mockedApi.getCurrentUser = vi.fn().mockResolvedValue({
        id: 'user-123',
        email: 'admin@archon.com',
        role: 'system_admin',
        permissions: ['leads:view:all', 'brand_asset_manage', 'user:manage:team', 'stats:view:own'],
        user_metadata: { full_name: 'System Admin' }
    });

    // 2. Wrap other functions to allow spying/mocking while defaulting to pass-through
    // This allows tests to use vi.mocked(api.method).mockResolvedValue(...)
    Object.keys(mockedApi).forEach(key => {
        // Exclude getTasks from spying to avoid potential Promise/Loading issues in E2E tests.
        // No tests currently mock getTasks, so direct pass-through is safer.
        if (key !== 'getCurrentUser' && key !== 'getTasks' && typeof mockedApi[key] === 'function') {
            // Fix: Use actual.api[key] to preserve 'this' context (e.g. for _getHeaders)
            mockedApi[key] = vi.fn().mockImplementation((...args) => actual.api[key](...args));
        }
    });
    
    return {
        ...actual,
        api: mockedApi
    };
});

// =============================================================================
// SECTION 2: TEST LIFECYCLE HOOKS (MSW)
// =============================================================================

// Start MSW server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

// Reset handlers after each test to ensure test isolation
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
  
  // Re-inject necessary credentials for the next test to prevent "Supabase credentials not set" errors
  const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://mock.supabase.co';
  const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY || 'mock-key';

  if (supabaseUrl && supabaseAnonKey) {
      localStorage.setItem('supabaseUrl', supabaseUrl);
      localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
  }
});

// Stop MSW server after all tests
afterAll(() => {
  server.close();
});

// =============================================================================
// SECTION 3: TEST UTILITIES
// =============================================================================

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