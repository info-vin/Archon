// enduser-ui-fe/tests/e2e/e2e.setup.ts
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { server } from '../../src/mocks/server';

// =============================================================================
// SECTION 1: TOP-LEVEL SETUP
// =============================================================================

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

// Inject Supabase credentials into localStorage. This is always required for the
// Supabase client to initialize, even if MSW will mock the subsequent API calls.
const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

if (supabaseUrl && supabaseAnonKey) {
  localStorage.setItem('supabaseUrl', supabaseUrl);
  localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
  console.log('✅ [E2E Setup] Supabase credentials injected into localStorage for jsdom.');
} else {
  // Fail fast if the test environment is not configured.
  throw new Error('Supabase credentials (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY) must be defined in .env.test');
}

// Always inject the mock user for authentication purposes.
localStorage.setItem('user', JSON.stringify(mockUser));
console.log('✅ [E2E Setup] Mock user injected into localStorage for jsdom.');

// =============================================================================
// SECTION 2: HYBRID API MOCKING STRATEGY
// =============================================================================

// STRATEGY: We use a hybrid approach.
// 1. `vi.mock` is used *only* for `getCurrentUser`. This is because `getCurrentUser`
//    interacts directly with the Supabase client (`supabase.auth.getSession`)
//    and does not make a `fetch` request, so MSW cannot intercept it. We must
//    mock it at the module level to simulate a logged-in user.
// 2. `msw` is used for all other API calls (`getTasks`, `getProjects`, etc.),
//    which are standard `fetch` requests. This allows us to maintain our API
//    mocks in a centralized location (`/src/mocks/handlers.ts`).

console.log('✅ [E2E Setup] Using HYBRID mock mode. `vi.mock` for auth, MSW for data.');

vi.mock('../../src/services/api', async (importOriginal) => {
  const originalModule = await importOriginal<typeof import('../../src/services/api')>();
  return {
    ...originalModule,
    // Keep the original module, but surgically override the `api` object
    api: {
      ...originalModule.api, // Spread all original api functions...
      getCurrentUser: vi.fn().mockResolvedValue(mockUser), // ...and mock ONLY `getCurrentUser`.
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
