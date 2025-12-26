// enduser-ui-fe/tests/e2e/e2e.setup.ts
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { Task, TaskStatus } from '../../src/types';
import { server } from '../../src/mocks/server';

// =============================================================================
// SECTION 1: TOP-LEVEL SETUP (Executes before any module loads)
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

const useRealApi = process.env.VITE_E2E_USE_REAL_API === 'true';

// Inject Supabase credentials into localStorage to allow the real client to initialize.
const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

if (supabaseUrl && supabaseAnonKey) {
  localStorage.setItem('supabaseUrl', supabaseUrl);
  localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
  console.log('✅ [E2E Setup] Supabase credentials injected into localStorage for jsdom (top-level).');
} else if (useRealApi) {
  throw new Error('Supabase credentials (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY) are required for real API testing in .env.test');
}

// Inject mock user for authentication purposes.
localStorage.setItem('user', JSON.stringify(mockUser));
console.log('✅ [E2E Setup] Mock user injected into localStorage for jsdom (top-level).');

// --- Global Fetch Override for Real API Mode ---
// This is crucial for redirecting relative /api calls from jsdom to the real backend.
if (useRealApi) {
    const backendApiBaseUrl = 'http://localhost:8181'; // Assuming backend runs on 8181
    const originalFetch = window.fetch;
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
        let url = input.toString();
        if (url.startsWith('/api/')) {
            url = `${backendApiBaseUrl}${url}`; // Prefix with backend URL
        }
        return originalFetch(url, init);
    };
    console.log(`✅ [E2E Setup] window.fetch overridden to proxy /api calls to ${backendApiBaseUrl}`);
}


// =============================================================================
// SECTION 2: SURGICAL & CONDITIONAL API MOCKING
// =============================================================================

vi.mock('../../src/services/api', async (importOriginal) => {
  const originalModule = await importOriginal<typeof import('../../src/services/api')>();

  if (useRealApi) {
    console.log(' HYBRID MOCK MODE [e2e.setup.ts] - Mocking only getCurrentUser to simulate login.');
    return {
      ...originalModule,
      // Keep the original module, but override just the api object
      api: {
        ...originalModule.api, // Spread all original api functions...
        getCurrentUser: vi.fn().mockResolvedValue(mockUser), // ...and mock ONLY getCurrentUser.
      },
    };
  } else {
    console.log(' FULL MOCK MODE [e2e.setup.ts] - Mocking all API calls.');
    // The full mock implementation for isolated frontend tests
    return {
      ...originalModule,
      api: {
        ...originalModule.api,
        getAssignableUsers: vi.fn().mockResolvedValue([{ id: 'user-1', name: 'Test User', role: 'Engineer' }]),
        getAssignableAgents: vi.fn().mockResolvedValue([
          { id: 'agent-content-writer', name: 'Content Writer AI', role: 'AI Agent' },
          { id: 'agent-log-analyzer', name: 'Log Analyzer AI', role: 'AI Agent' },
          { id: 'agent-sales-intel', name: 'Sales Intelligence AI', role: 'AI Agent' },
        ]),
        getProjects: vi.fn().mockResolvedValue([{ id: 'proj-e2e-1', title: 'E2E Test Project', description: 'A project for E2E tests' }]),
        getTasks: vi.fn().mockResolvedValue([]),
        getBlogPosts: vi.fn().mockResolvedValue([]),
        createTask: vi.fn().mockImplementation((taskData: Partial<Task>) => {
          console.log('E2E Mocked createTask called with:', taskData);
          return Promise.resolve({
            id: `task-${Date.now()}`,
            project_id: 'proj-e2e-1',
            status: TaskStatus.TODO,
            task_order: 1,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            ...taskData,
          });
        }),
        updateTask: vi.fn().mockImplementation((taskId: string, updates: Partial<Task>) => {
          console.log(`E2E Mocked updateTask called for ${taskId} with:`, updates);
          return Promise.resolve({
            id: taskId,
            project_id: 'proj-e2e-1',
            created_at: new Date().toISOString(),
            ...updates,
          });
        }),
        getCurrentUser: vi.fn().mockResolvedValue(mockUser),
      }
    };
  }
});


// =============================================================================
// SECTION 3: TEST LIFECYCLE HOOKS
// =============================================================================

beforeAll(() => {
  if (!useRealApi) {
    server.listen({ onUnhandledRequest: 'bypass' });
  }
});

afterEach(() => {
  localStorage.clear();
  // Re-inject Supabase credentials for the next test if they were available
  if (supabaseUrl && supabaseAnonKey) {
      localStorage.setItem('supabaseUrl', supabaseUrl);
      localStorage.setItem('supabaseAnonKey', supabaseAnonKey);
  }
  // Re-inject mock user for the next test
  localStorage.setItem('user', JSON.stringify(mockUser));
  
  if (!useRealApi) {
    server.resetHandlers();
  }
});

afterAll(() => {
  if (!useRealApi) {
    server.close();
  }
});
