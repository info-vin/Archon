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
    role: 'system_admin',
    avatar: 'https://i.pravatar.cc/150?u=e2e@archon.com'
};

// =============================================================================
// SECTION 2: HYBRID API MOCKING STRATEGY
// =============================================================================

const { mockInternalUser, mockTasksStore } = vi.hoisted(() => ({
  mockInternalUser: {
    id: 'user-e2e-1',
    employeeId: 'E2E001',
    name: 'E2E Test User',
    email: 'e2e@archon.com',
    role: 'system_admin',
    status: 'active',
    avatar: 'https://i.pravatar.cc/150?u=e2e@archon.com'
  },
  mockTasksStore: [] as any[]
}));

vi.mock('../../src/services/api', () => {
  return {
    supabase: {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: { user: mockInternalUser } }, error: null }),
        onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
      },
      from: vi.fn().mockReturnValue({
        select: vi.fn().mockReturnThis(),
        eq: vi.fn().mockReturnThis(),
        single: vi.fn().mockResolvedValue({ data: mockInternalUser, error: null }),
      }),
    },
    api: {
      getCurrentUser: vi.fn().mockResolvedValue(mockInternalUser),
      getTasks: vi.fn().mockImplementation(async () => [...mockTasksStore]),
      getProjects: vi.fn().mockResolvedValue([{ id: 'proj-1', title: 'E2E Project', status: 'active' }]),
      getAssignableUsers: vi.fn().mockResolvedValue([{ id: 'user-1', name: 'Alice Johnson', role: 'member' }]),
      getAssignableAgents: vi.fn().mockResolvedValue([
        { id: 'ai-researcher-1', name: '(AI) Market Researcher', role: 'Market Researcher' },
        { id: 'ai-content-writer', name: '(AI) Content Writer', role: 'Content Writer' },
        { id: 'ai-knowledge-expert-1', name: '(AI) Internal Knowledge Expert', role: 'Internal Knowledge Expert' },
        { id: 'agent-content-writer', name: '(AI) Content Writer', role: 'Content Writer' },
        { id: 'agent-log-analyzer', name: '(AI) Log Analyzer', role: 'Log Analyzer' },
        { id: 'agent-sales-intel', name: '(AI) Sales Intel', role: 'Sales Intel' },
      ]),
      createTask: vi.fn().mockImplementation(async (data) => {
        const newTask = { ...data, id: 'new-task-' + Date.now() };
        mockTasksStore.push(newTask);
        return newTask;
      }),
      updateTask: vi.fn().mockImplementation(async (id, data) => {
        const index = mockTasksStore.findIndex(t => t.id === id);
        if (index !== -1) {
            mockTasksStore[index] = { ...mockTasksStore[index], ...data };
            return mockTasksStore[index];
        }
        return { ...data, id };
      }),
      login: vi.fn().mockResolvedValue(mockInternalUser),
      logout: vi.fn().mockResolvedValue(undefined),
      getKnowledgeItems: vi.fn().mockResolvedValue([]),
      getPendingChanges: vi.fn().mockResolvedValue([]),
      getBlogPosts: vi.fn().mockResolvedValue([]),
      getEmployees: vi.fn().mockResolvedValue([mockInternalUser]),
      adminCreateUser: vi.fn().mockImplementation(async (data) => ({ ...data, id: 'alice-id' })),
      updateEmployee: vi.fn().mockImplementation(async (id, data) => ({ id, ...data })),
      searchJobs: vi.fn().mockImplementation(async (keyword) => {
        console.log('🔍 [Mock API] searchJobs called with keyword:', keyword);
        if (keyword === 'Error Test') {
            console.log('⚠️ [Mock API] Throwing error for Error Test');
            throw new Error('Simulated API Error');
        }
        return [
        { 
            title: 'Data Analyst', 
            company: 'Retail Corp', 
            location: 'Taipei',
            salary: '1.2M',
            url: 'https://example.com/job/1',
            description: 'Looking for a data analyst...',
            description_full: 'Full description: Needs someone who knows BI tools like Tableau and PowerBI.',
            skills: ['Python', 'SQL'],
            source: '104',
            identified_need: 'Needs better data pipeline'
        },
        { 
            title: 'Senior Data Engineer', 
            company: 'Tech Solutions', 
            location: 'Remote',
            salary: '1.5M',
            url: 'https://example.com/job/2',
            description: 'Building data warehouse...',
            description_full: 'Full description: Scaling infrastructure with Spark and AWS.',
            skills: ['Spark', 'AWS'],
            source: 'LinkedIn',
            identified_need: 'Scaling infrastructure'
        }
      ];
      }),
      generatePitch: vi.fn().mockImplementation(async (jobTitle, company, description) => {
          console.log('🤖 [Mock API] generatePitch called for:', company);
          return {
              content: `Subject: Collaboration Opportunity: Solving data challenges at ${company}\n\nDear Hiring Manager,\n\nI noticed that ${company} is currently expanding its data team and looking for a ${jobTitle}. This suggests you might be tackling challenges related to data integration or analytics scaling.\n\nAt Archon, we specialize in helping companies like yours leverage data for tangible growth. For instance, we recently helped a major retail chain reduce inventory costs by 40% and increase revenue by 30% through our automated analytics platform.\n\nYou can read the full case study here: "零售巨頭如何利用數據分析提升 30% 營收" (Attached).\n\nI would love to share more about how our "Sales Intelligence" module could support your new ${jobTitle} in hitting the ground running.\n\nBest regards,\n[Your Name]\nArchon Sales Team`,
              references: ['Case Study A', 'Capability B']
          };
      }),
    }
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
