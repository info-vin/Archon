// enduser-ui-fe/tests/e2e/e2e.setup.tsx
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { server } from '../../src/mocks/server';
import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../../src/App';
import { AuthProvider } from '../../src/hooks/useAuth';

// =============================================================================
// SECTION 1: TOP-LEVEL SETUP
// =============================================================================

// Note: LocalStorage initialization is now handled in `pre-setup.ts` to ensure
// it runs before any hoisted `vi.mock` calls.

const mockUser = {
    id: 'user-e2e-1',
    employeeId: 'E2E001',
    name: 'E2E Test User',
    email: 'e2e@archon.com',
    department: 'QA',
    position: 'Tester',
    status: 'active',
    role: 'Admin',
    avatar: 'https://i.pravatar.cc/150?u=e2e@archon.com'
};

// =============================================================================
// SECTION 2: HYBRID API MOCKING STRATEGY
// =============================================================================

console.log('✅ [E2E Setup] Using HYBRID mock mode. `vi.mock` for auth, MSW for data.');

vi.mock('../../src/services/api', async (importOriginal) => {
  const originalModule = await importOriginal<typeof import('../../src/services/api')>();

  // We define the mock user inline here to avoid hoisting issues (ReferenceError).
  const internalMockUser = {
    id: 'user-e2e-1',
    employeeId: 'E2E001',
    name: 'E2E Test User',
    email: 'e2e@archon.com',
    department: 'QA',
    position: 'Tester',
    status: 'active',
    role: 'Admin',
    avatar: 'https://i.pravatar.cc/150?u=e2e@archon.com'
  };

  return {
    ...originalModule,
    // Keep the original module, but surgically override the `api` object
    api: {
      ...originalModule.api, // Spread all original api functions...
      getCurrentUser: vi.fn().mockResolvedValue(internalMockUser), // ...and mock ONLY `getCurrentUser`.
    },
  };
});


// =============================================================================
// SECTION 3: TEST LIFECYCLE HOOKS
// =============================================================================

// Unconditionally start the MSW server for all E2E tests.
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' }); // Use 'error' to catch any unmocked requests
});

// Reset MSW handlers and clear localStorage after each test.
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();

  // Re-inject necessary credentials for the next test.
  // We repeat logic from pre-setup.ts here because localStorage is cleared.
  const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://mock.supabase.co';
  const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY || 'mock-key';

  if (supabaseUrl && supabaseAnonKey) {
      localStorage.setItem('supabaseUrl', supabaseUrl);
      localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
  }
  localStorage.setItem('user', JSON.stringify(mockUser));
});

// Clean up by closing the MSW server after all tests are done.
afterAll(() => {
  server.close();
});

// =============================================================================
// SECTION 4: TEST UTILITIES
// =============================================================================

export const renderApp = () => {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </MemoryRouter>
  );
};
