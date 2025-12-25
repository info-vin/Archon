// tests/e2e/e2e.setup.ts
import { vi } from 'vitest';
import { Task, TaskStatus } from '../../src/types';

// This file contains the shared mock setup for ALL E2E tests.
// It mocks the entire api.ts service layer to provide a consistent,
// controlled environment for testing the frontend application flow.

vi.mock('../../src/services/api', async (importOriginal) => {
  const originalModule = await importOriginal<typeof import('../../src/services/api')>();
  return {
    ...originalModule,
    api: {
      ...originalModule.api,
      // Mock specific API calls relevant to E2E scenarios
      getAssignableUsers: vi.fn().mockResolvedValue([
        { id: 'user-1', name: 'Test User', role: 'Engineer' },
      ]),
      getAssignableAgents: vi.fn().mockResolvedValue([
        { id: 'agent-content-writer', name: 'Content Writer AI', role: 'AI Agent' },
        { id: 'agent-log-analyzer', name: 'Log Analyzer AI', role: 'AI Agent' },
        { id: 'agent-sales-intel', name: 'Sales Intelligence AI', role: 'AI Agent' },
      ]),
      getProjects: vi.fn().mockResolvedValue([
        { id: 'proj-e2e-1', title: 'E2E Test Project', description: 'A project for E2E tests' }
      ]),
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
      // Simulate a logged-in user for all E2E tests
      getCurrentUser: vi.fn().mockResolvedValue({
        id: 'user-e2e-1',
        employeeId: 'E2E001',
        name: 'E2E Test User',
        email: 'e2e@archon.com',
        department: 'QA',
        position: 'Tester',
        status: 'active',
        role: 'Admin',
        avatar: 'https://i.pravatar.cc/150?u=e2e@archon.com'
      }),
    }
  };
});
