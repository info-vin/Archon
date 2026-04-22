import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { server } from '../../src/mocks/server';
import { clearMockData } from '../../src/mocks/handlers';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/hooks/useAuth';
import { AppRoutes } from '../../src/App';

// 1. vi.hoisted runs BEFORE anything else (even before vi.mock hoisting)
const { MOCK_ADMIN_USER } = vi.hoisted(() => {
  return {
    MOCK_ADMIN_USER: {
        id: 'user-123',
        name: 'System Admin',
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
    mockedApi.getCurrentUser = vi.fn().mockResolvedValue(structuredClone(MOCK_ADMIN_USER));

    // 2. Mock _getHeaders to avoid hanging on supabase.auth.getSession() (Fix for BUG-028)
    mockedApi._getHeaders = vi.fn().mockResolvedValue({
        'Content-Type': 'application/json',
        'X-User-Role': 'system_admin', 
        'Authorization': 'Bearer mock-token'
    });

    // 3. Wrap other functions to allow spying/mocking while defaulting to pass-through
    Object.keys(mockedApi).forEach(key => {
        const ignoreList = ['getCurrentUser', 'getTasks', '_getHeaders', 'getAssignableAgents', 'getAttendanceStatus'];
        
        if (!ignoreList.includes(key) && typeof mockedApi[key] === 'function') {
            const originalFn = actual.api[key];
            const mockFn = vi.fn().mockImplementation((...args) => originalFn.call(mockedApi, ...args));
            (mockFn as any)._passThrough = originalFn;
            mockedApi[key] = mockFn;
        } else if (ignoreList.includes(key) && typeof mockedApi[key] === 'function') {
             // Keep the original function reference for testing fallbacks
             mockedApi[key] = actual.api[key];
        }
    });
    
    // Explicitly re-attach for specific test suites that might rely on them
    mockedApi.getCurrentUser = vi.fn().mockResolvedValue(structuredClone(MOCK_ADMIN_USER));
    mockedApi._getHeaders = vi.fn().mockResolvedValue({
        'Content-Type': 'application/json',
        'X-User-Role': 'system_admin', 
        'Authorization': 'Bearer mock-token'
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
  clearMockData();
  localStorage.clear();
  
  // Re-inject necessary credentials for the next test to prevent "Supabase credentials not set" errors
  const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://mock.supabase.co';
  const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY || 'mock-key';

  if (supabaseUrl && supabaseAnonKey) {
      localStorage.setItem('supabaseUrl', supabaseUrl);
      localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
  }

  // Restore the default user mock to prevent leaks between tests
  // This is crucial because tests use vi.mocked(api.getCurrentUser).mockResolvedValue(...)
  // which permanently overrides the implementation until changed again.
  import('../../src/services/api').then(module => {
      const { api } = module as any;
      if (vi.isMockFunction(api.getCurrentUser)) {
          api.getCurrentUser.mockResolvedValue(structuredClone(MOCK_ADMIN_USER));
      }
      if (vi.isMockFunction(api._getHeaders)) {
          api._getHeaders.mockResolvedValue({
              'Content-Type': 'application/json',
              'X-User-Role': 'system_admin', 
              'Authorization': 'Bearer mock-token'
          });
      }
      
      // Restore all pass-through mocks to their original pass-through implementation
      Object.keys(api).forEach(key => {
          if (typeof api[key] === 'function' && vi.isMockFunction(api[key]) && (api[key] as any)._passThrough) {
              const originalFn = (api[key] as any)._passThrough;
              api[key].mockImplementation((...args: any[]) => originalFn.call(api, ...args));
          }
      });
  });
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
    window.alert = vi.fn();
    window.confirm = vi.fn(() => true);
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