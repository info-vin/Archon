import { http, HttpResponse } from 'msw';
import { TaskStatus, TaskPriority } from '../types';

// --- Mock Data ---

const mockAssignableUsers = [
  { id: '2', name: 'Alice Johnson', role: 'Engineer' },
  { id: '3', name: 'Bob Williams', role: 'Marketer' },
];

const mockAiAgents = [
  { id: 'ai-researcher-1', name: '(AI) Market Researcher', role: 'Market Researcher' },
  { id: 'ai-knowledge-expert-1', name: '(AI) Internal Knowledge Expert', role: 'Internal Knowledge Expert' },
];

// Corrected mockProjects to match the Project type and the expected API response structure
const mockProjects = [
  {
    id: 'project-1',
    title: 'E2E Test Project',
    description: 'A project for E2E testing purposes.',
    status: 'active',
    projectManagerId: 'user-123', // Matches the expected type
  },
];

// Corrected mockTasks to match the Task type definition precisely
const mockTasks = [
  {
    id: 'task-1',
    project_id: 'project-1',
    title: 'My First Mock Task',
    description: 'This is a task fetched from the mock service worker.',
    status: TaskStatus.TODO,
    priority: TaskPriority.MEDIUM,
    assignee: 'Alice Johnson', // Correct field: string, not assignee_id
    task_order: 1,
    due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(), // Added required field
    completed_at: undefined,
    attachments: [],
  },
];


// --- MSW Handlers ---

export const handlers = [
  // Handler for assignable users
  http.get('/api/assignable-users', () => {
    return HttpResponse.json(mockAssignableUsers);
  }),

  // Handler for assignable AI agents
  http.get('/api/agents/assignable', () => {
    return HttpResponse.json(mockAiAgents);
  }),

  // Handler for projects, now returns the correct object structure
  http.get('/api/projects', () => {
    return HttpResponse.json({ projects: mockProjects });
  }),

  // Handler for tasks, now returns the corrected task structure
  http.get('/api/tasks', () => {
    return HttpResponse.json(mockTasks);
  }),

  // Handler for creating a new task
  http.post('/api/tasks', async ({ request }) => {
    const newTaskData = await request.json() as any;
    const newTask = {
      id: `task-${Date.now()}`,
      project_id: newTaskData.project_id || 'project-1',
      title: newTaskData.title,
      description: newTaskData.description || '',
      status: TaskStatus.TODO,
      priority: newTaskData.priority || TaskPriority.MEDIUM,
      assignee: newTaskData.assignee || 'Unassigned',
      task_order: (mockTasks.length + 1),
      due_date: newTaskData.due_date || new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      completed_at: undefined,
      attachments: [],
    };
    mockTasks.push(newTask); // Add to our mock database
    return HttpResponse.json(newTask, { status: 201 });
  }),
];