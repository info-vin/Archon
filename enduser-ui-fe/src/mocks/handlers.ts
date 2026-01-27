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

  // Handler for tasks, returning array as frontend expects
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
    return HttpResponse.json({ task: newTask }, { status: 201 });
  }),

  // --- Marketing & Approvals Handlers ---

  // Search Jobs
  http.get('/api/marketing/jobs', ({ request }) => {
    const url = new URL(request.url);
    const keyword = url.searchParams.get('keyword');

    if (keyword === 'Error Test') {
        return new HttpResponse(null, { status: 500, statusText: 'Internal Server Error' });
    }

    return HttpResponse.json([
        {
            id: 'job-1',
            title: 'Senior Data Analyst',
            company: 'Retail Corp',
            source: '104 Live Data',
            description: 'Needs someone who knows BI tools like Tableau and PowerBI.',
            description_full: 'Full description: Needs someone who knows BI tools like Tableau and PowerBI.',
            url: 'http://example.com/job/1',
            identified_need: 'Needs better data pipeline'
        },
        {
            id: 'job-2',
            title: 'Senior Data Engineer',
            company: 'Tech Solutions',
            source: '104 Live Data',
            description: 'Scaling infrastructure.',
            description_full: 'Full description: Scaling infrastructure.',
            url: 'http://example.com/job/2',
            identified_need: 'Scaling infrastructure'
        }
    ]);
  }),

  // Get Leads (My Leads Tab)
  http.get('/api/marketing/leads', () => {
    return HttpResponse.json([
      {
        id: 'lead-1',
        company_name: 'Retail Corp',
        job_title: 'Senior Data Analyst',
        status: 'new',
        source_job_url: 'http://example.com/job/1',
        next_followup_date: new Date().toISOString()
      },
      {
        id: 'lead-2',
        company_name: 'Tech Solutions',
        job_title: 'Senior Data Engineer',
        status: 'converted',
        source_job_url: 'http://example.com/job/2',
        next_followup_date: null
      }
    ]);
  }),

  // Generate Pitch
  http.post('/api/marketing/generate-pitch', async () => {
    return HttpResponse.json({
        content: `Subject: Collaboration regarding your Data needs\n\nDear Manager,\n\nI noticed Retail Corp is hiring and Needs someone who knows BI tools...`,
        references: ['Source A']
    });
  }),

  // Get Pending Approvals
  http.get('/api/marketing/approvals', () => {
    return HttpResponse.json({
        blogs: [
            {
                id: 'blog-approval-1',
                title: 'Q3 Market Analysis',
                authorName: 'Bob Williams',
                publishDate: new Date().toISOString(),
                status: 'review'
            }
        ],
        leads: []
    });
  }),

  // Approve/Reject Action
  http.post('/api/marketing/approvals/:type/:id/:action', ({ params }) => {
    return HttpResponse.json({ success: true, status: params.action === 'approve' ? 'published' : 'draft' });
  }),

  // --- System Prompts Handlers ---
  http.get('/api/system/prompts', () => {
    return HttpResponse.json([
        { prompt_name: 'developer_persona', prompt: 'You are a coding expert.', updated_at: new Date().toISOString() },
        { prompt_name: 'sales_persona', prompt: 'You are a sales expert.', updated_at: new Date().toISOString() }
    ]);
  }),

  http.post('/api/system/prompts/:name', async ({ request }) => {
    const body = await request.json() as any;
    return HttpResponse.json({ success: true, prompt: body.prompt });
  }),

  // --- Missing Handlers for E2E (Restored) ---
  http.post('/api/admin/users', async ({ request }) => {
      const body = await request.json() as any;
      return HttpResponse.json({ profile: { ...body, id: 'new-user-123' } }, { status: 201 });
  }),

  http.get('/api/users', () => {
      return HttpResponse.json([
          { id: 'user-1', name: 'Alice', role: 'sales', email: 'alice@archon.com', status: 'active' },
          { id: 'user-2', name: 'Bob', role: 'marketing', email: 'bob@archon.com', status: 'active' },
          { id: 'user-3', name: 'Charlie', role: 'manager', email: 'charlie@archon.com', status: 'active' }
      ]);
  }),

  http.get('/api/stats/ai-usage', () => {
      return HttpResponse.json({ total_budget: 1000, total_used: 150, usage_percentage: 15 });
  }),

  http.get('/api/marketing/market-stats', () => {
      return HttpResponse.json({ "AI/LLM": 10, "Total Leads": 20, "Data/BI": 5 });
  }),

  http.get('/api/blogs', () => {
      return HttpResponse.json([]);
  }),

  http.post('/api/tasks/refine-description', async ({ request }) => {
      const body = await request.json() as any;
      return HttpResponse.json({ 
          refined_description: `User Story: As a user, I want ${body.title} so that I can be happy.\n\nAcceptance Criteria:\n- Done.` 
      });
  })
];
