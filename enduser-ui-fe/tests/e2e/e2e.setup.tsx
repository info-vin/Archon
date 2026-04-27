import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { server } from '../../src/mocks/server';
import { clearMockData } from '../../src/mocks/handlers';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/hooks/useAuth';
import { AppRoutes } from '../../src/App';

// SECTION 1: MOCK DATA TEMPLATE
const { MOCK_ADMIN_USER } = vi.hoisted(() => ({
  MOCK_ADMIN_USER: {
    id: 'user-123',
    name: 'System Admin',
    email: 'admin@archon.com',
    role: 'system_admin',
    permissions: [
        'task:create', 'task:read:all', 'task:update:all',
        'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
        'code:approve', 'content:publish', 'stats:view:all',
        'leads:view:sales', 'leads:view:marketing',
        'user:manage', 'user:manage:team', 'mcp:manage'
    ],
    user_metadata: { full_name: 'System Admin' }
  }
}));

// SECTION 2: API MOCKING
vi.mock('../../src/services/api', async (importOriginal) => {
    const actual = await importOriginal() as any;
    const mockedApi = { ...actual.api };

    // Standard Mock Implementation
    mockedApi.getCurrentUser = vi.fn().mockResolvedValue(structuredClone(MOCK_ADMIN_USER));
    mockedApi._getHeaders = vi.fn().mockResolvedValue({
        'Content-Type': 'application/json',
        'X-User-Role': 'system_admin', 
        'Authorization': 'Bearer mock-token'
    });

    // Pass-through spies
    Object.keys(mockedApi).forEach(key => {
        const ignoreList = ['getCurrentUser', 'getTasks', '_getHeaders', 'getAssignableAgents', 'getAttendanceStatus'];
        if (!ignoreList.includes(key) && typeof mockedApi[key] === 'function') {
            const originalFn = actual.api[key];
            const mockFn = vi.fn().mockImplementation((...args) => originalFn.call(mockedApi, ...args));
            (mockFn as any)._passThrough = originalFn;
            mockedApi[key] = mockFn;
        }
    });
    
    return { ...actual, api: mockedApi };
});

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  server.resetHandlers();
  clearMockData();
  localStorage.clear();
  
  // Re-inject core tokens to prevent redirect to /auth
  localStorage.setItem('supabaseUrl', 'https://mock.supabase.co');
  localStorage.setItem('supabaseKey', 'mock-key');
});

afterAll(() => {
  server.close();
});

export const renderApp = (initialEntries = ['/']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        <AppRoutes /> 
      </AuthProvider>
    </MemoryRouter>
  );
};
