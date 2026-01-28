import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { server } from '../../src/mocks/server';
import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/hooks/useAuth';
import { api } from '../../src/services/api';
import { AppRoutes } from '../../src/App';

// 1. vi.hoisted runs BEFORE anything else (even before vi.mock hoisting)
const { MOCK_ADMIN_USER } = vi.hoisted(() => {
  return {
    MOCK_ADMIN_USER: {
        id: 'user-123',
        email: 'admin@archon.com',
        role: 'system_admin',
        // SSOT: Synchronized with usePermission.ts admin set
        permissions: [
            'task:create', 'task:read:all', 'task:update:all',
            'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
            'code:approve', 'content:publish',
            'stats:view:all',
            'leads:view:sales', 'leads:view:marketing',
            'user:manage', 'user:manage:team', 'mcp:manage'
        ],
        user_metadata: { full_name: 'System Admin' }
    }
  };
});

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

// 2. Mock the API module partially
vi.mock('../../src/services/api', async (importOriginal) => {
    const actual = await importOriginal() as any;
    
    // Create a spy-able clone of the API
    const mockedApi = { ...actual.api };

    // --- Hybrid Strategy: Mock Auth Only, Pass-through Data ---
    
    // 1. Mock getCurrentUser using the HOISTED data
    mockedApi.getCurrentUser = vi.fn().mockResolvedValue(MOCK_ADMIN_USER);

    // 2. Wrap other functions to allow spying/mocking while defaulting to pass-through
    Object.keys(mockedApi).forEach(key => {
        if (key !== 'getCurrentUser' && key !== 'getTasks' && typeof mockedApi[key] === 'function') {
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
    Element.prototype.scrollIntoView = vi.fn();
    HTMLElement.prototype.scrollIntoView = vi.fn();
    
    if (!HTMLDialogElement.prototype.showModal) {
        HTMLDialogElement.prototype.showModal = vi.fn(function(this: HTMLDialogElement) {
            this.setAttribute('open', '');
        });
        HTMLDialogElement.prototype.close = vi.fn(function(this: HTMLDialogElement) {
            this.removeAttribute('open');
        });
    }
}