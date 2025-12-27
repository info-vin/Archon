import { http, HttpResponse } from 'msw';

// Define the mock data for assignable users
const mockAssignableUsers = [
  { id: '2', name: 'Alice Johnson', role: 'Engineer' },
  { id: '3', name: 'Bob Williams', role: 'Marketer' },
];

const mockAiAgents = [
    { id: 'agent-content-writer', name: '(AI) Content Writer', role: 'AI' },
    { id: 'agent-log-analyzer', name: '(AI) Log Analyzer', role: 'AI' },
    { id: 'agent-sales-intel', name: '(AI) Sales Intel', role: 'AI' },
    { id: 'ai-researcher-1', name: '(AI) Market Researcher', role: 'Market Researcher' },
    { id: 'ai-knowledge-expert-1', name: '(AI) Internal Knowledge Expert', role: 'Internal Knowledge Expert' },
];

let mockTasks = [];

export const handlers = [
  http.get('/api/assignable-users', () => {
    return HttpResponse.json(mockAssignableUsers);
  }),

  http.get('/api/agents/assignable', () => {
    return HttpResponse.json(mockAiAgents);
  }),

  http.get('/api/projects', () => {
    // Return a more complete project object to match the application's needs
    return HttpResponse.json([
      {
        id: 'proj-1',
        title: 'E2E Test Project',
        description: 'A project for E2E testing purposes.',
        status: 'active',
        projectManagerId: 'user-1'
      }
    ]);
  }),

  http.get('/api/tasks', () => {
    return HttpResponse.json(mockTasks);
  }),

  http.post('/api/tasks', async ({ request }) => {
    const newTaskData = await request.json();

    let assigneeName = 'Unassigned';
    if (newTaskData.assignee_id) {
      const allAssignable = [...mockAssignableUsers, ...mockAiAgents];
      const assignee = allAssignable.find(u => u.id === newTaskData.assignee_id);
      if (assignee) {
        assigneeName = assignee.name;
      }
    }

    const newTask = {
      ...newTaskData,
      id: `task-${Date.now()}`,
      status: 'todo',
      assignee: assigneeName,
      task_order: mockTasks.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockTasks.push(newTask);
    return HttpResponse.json(newTask, { status: 201 });
  }),
];

// Utility to reset tasks between tests if needed
export const resetMockTasks = () => {
  mockTasks = [];
};
