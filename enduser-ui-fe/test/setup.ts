import '@testing-library/jest-dom';
import { server } from '../src/mocks/server';
import { vi } from 'vitest';
import { Task, TaskStatus, TaskPriority } from '../src/types';

// Mock the entire api module RIGHT AT THE TOP.
// This ensures that any component that imports from 'api' gets this mock instead of the real one.
vi.mock('../src/services/api', () => ({
  api: {
    // Keep mocks for any functions that ARE http-based and handled by msw
    getAssignableUsers: vi.fn().mockResolvedValue([
        { id: '2', name: 'Alice Johnson', role: 'Engineer' },
        { id: '3', name: 'Bob Williams', role: 'Marketer' },
    ]),
    // This makes the function exist on the mock object
    getAssignableAgents: vi.fn().mockResolvedValue([]),
    getProjects: vi.fn().mockResolvedValue([]),
    getTasks: vi.fn().mockResolvedValue([]),
    getBlogPosts: vi.fn().mockResolvedValue([]),

    // Provide mock implementations for the functions that directly use the Supabase client
    createTask: vi.fn().mockImplementation((taskData: Partial<Task>) => {
      console.log('Mocked createTask called with:', taskData);
      return Promise.resolve({
        id: `task-${Date.now()}`,
        project_id: 'proj-1',
        status: TaskStatus.TODO,
        task_order: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        ...taskData,
      });
    }),
    updateTask: vi.fn().mockImplementation((taskId: string, updates: Partial<Task>) => {
      console.log(`Mocked updateTask called for ${taskId} with:`, updates);
      return Promise.resolve({
        id: taskId,
        project_id: 'proj-1',
        created_at: new Date().toISOString(),
        ...updates,
      });
    }),
    // Add mocks for any other api methods that might be called in tests
    getCurrentUser: vi.fn().mockResolvedValue(null),
  }
}));


// Establish API mocking for any remaining HTTP requests before all tests.
beforeAll(() => server.listen());

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
afterEach(() => {
  server.resetHandlers();
  // also reset mock function calls
  vi.clearAllMocks();
});

// Clean up after the tests are finished.
afterAll(() => server.close());
