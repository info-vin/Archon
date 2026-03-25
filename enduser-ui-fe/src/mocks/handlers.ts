import { http, HttpResponse } from 'msw';

// --- INDUSTRIAL GRADE MOCK DATA (With Explicit Permissions for SSOT) ---

const mockUsers = {
  alice: { 
    id: 'user-1', name: 'Alice Johnson', role: 'sales', email: 'alice@archon.com', status: 'active',
    permissions: ['task:create', 'task:read:own', 'task:update:own', 'agent:trigger:mkt', 'stats:view:own', 'leads:view:sales']
  },
  bob: { 
    id: 'user-2', name: 'Bob', role: 'marketing', email: 'bob@archon.com', status: 'active',
    permissions: ['task:create', 'task:read:own', 'task:update:own', 'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:own', 'leads:view:marketing']
  },
  charlie: { 
    id: 'user-3', name: 'Charlie', role: 'manager', email: 'charlie@archon.com', status: 'active',
    permissions: ['task:create', 'task:read:team', 'task:update:own', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'code:approve', 'content:publish', 'stats:view:team', 'stats:view:own', 'leads:view:sales', 'leads:view:marketing', 'user:manage:team']
  },
  admin: {
    id: 'admin-123', name: 'Super Admin', role: 'system_admin', email: 'admin@archon.com', status: 'active',
    permissions: ['task:create', 'task:read:all', 'task:update:all', 'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know', 'code:approve', 'content:publish', 'stats:view:all', 'stats:view:own', 'leads:view:sales', 'leads:view:marketing', 'user:manage', 'user:manage:team', 'mcp:manage']
  }
};

const mockAssignableUsers = [mockUsers.alice, mockUsers.bob, mockUsers.charlie];

const mockAiAgents = [
  { id: 'ai-researcher-1', name: 'Market Researcher', role: 'ai_agent' },
  { id: 'ai-knowledge-expert-1', name: 'Internal Knowledge Expert', role: 'ai_agent' },
];

// --- STATEFUL MOCKS FOR E2E ---
let dynamicTasks: any[] = [
  { id: 'initial-task', title: 'System Warmup', project_id: 'p1', description: 'Initial task', status: 'todo', createdAt: new Date().toISOString() }
];

export const clearMockData = () => {
  dynamicTasks = [
    { id: 'initial-task', title: 'System Warmup', project_id: 'p1', description: 'Initial task', status: 'todo', createdAt: new Date().toISOString() }
  ];
};

export const handlers = [
  // 1. Auth & Profiles
  http.get('/api/users', () => HttpResponse.json(mockAssignableUsers)),
  http.get('/api/assignable-users', () => HttpResponse.json(mockAssignableUsers)),
  http.get('/api/agents/assignable', () => HttpResponse.json(mockAiAgents)),

  // 2. Tasks & Projects
  http.get('/api/projects', () => HttpResponse.json({ projects: [{ id: 'p1', title: 'E2E Project' }] })),
  http.get('/api/tasks', () => HttpResponse.json(dynamicTasks)),
  http.post('/api/tasks', async ({ request }) => {
    const newTask = await request.json() as any;
    
    // Auto-populate assignee name if ID exists (Fix for BUG-044)
    let assigneeName = newTask.assignee;
    if (!assigneeName && newTask.assignee_id) {
        const user = mockAssignableUsers.find(u => u.id === newTask.assignee_id);
        if (user) assigneeName = user.name;
    }

    const task = {
        ...newTask,
        id: `task-${Date.now()}`,
        project_id: newTask.project_id || 'p1', // Critical for filtering
        status: newTask.status || 'todo',
        assignee: assigneeName, // Persistence fix
        createdAt: new Date().toISOString()
    };
    dynamicTasks.push(task);
    return HttpResponse.json(task, { status: 201 });
  }),
  http.post('/api/tasks/refine-description', async () => {
    return HttpResponse.json({
      refined_description: "User Story: As a user, I want this feature so that I can be productive."
    });
  }),

  // 3. Marketing & Leads
  http.get('/api/marketing/leads', () => HttpResponse.json([
    { id: 'lead-1', company_name: 'Retail Corp', job_title: 'Senior Data Analyst', status: 'shortlisted', source: 'mock', contact_name: 'Alice Johnson', contact_email: 'alice@retail.com', match_score: 95, identified_need: 'Needs data analytics solution' }
  ])),
  http.get('/api/marketing/jobs', ({ request }) => {
    const url = new URL(request.url);
    const keyword = url.searchParams.get('keyword');
    return HttpResponse.json([
        { id: 'job-1', title: 'Senior Data Analyst', company: 'Retail Corp', location: 'Taipei', salary: '100k', description: `Hiring for ${keyword}` }
    ]);
  }),
  http.post('/api/marketing/leads', () => HttpResponse.json({ success: true })),
  http.post('/api/marketing/generate-pitch', () => HttpResponse.json({ content: 'Generated Pitch', references: ['Source A'] })),
  http.get('/api/marketing/trends', () => HttpResponse.json([])),
  http.get('/api/marketing/sources', () => HttpResponse.json([])),
  http.get('/api/marketing/market-stats', () => HttpResponse.json({})),

  // 4. System & Stats
  http.get('/api/system/overview', () => HttpResponse.json({
    status: 'healthy',
    integrity_score: 98,
    rag: { status: 'healthy', details: { steps: ['Vector Check'], detected_dimensions: 1536 } },
    knowledge_stats: { total_nodes: 1200, total_chunks: 4500 },
    errors_24h: 0,
    cost_24h: 0.45,
    active_agents: mockAiAgents.map(a => ({ ...a, status: 'active' }))
  })),
  http.get('/api/stats/system-overview', () => HttpResponse.json({
    status: 'healthy',
    rag: { status: 'healthy', details: { detected_dimensions: 1536 } },
    database: { status: 'connected' },
    storage: { status: 'connected' }
  })),
  http.get('/api/marketing/approvals', () => HttpResponse.json({
    blogs: [{ id: 'blog-1', title: 'Q3 Market Analysis', authorName: 'Bob', status: 'review', content: 'Testing content' }],
    leads: []
  })),
  http.get('/api/system/logs/connectivity', () => HttpResponse.json([])),
  http.get('/api/stats/commander-trends', () => HttpResponse.json({ daily_output: [], cumulative_momentum: [] })),
  http.get('/api/stats/force-readiness', () => HttpResponse.json({ combat_power: 85 })),
  http.get('/api/stats/collab-synergy', () => HttpResponse.json({ snapshot: { total_7d: 45 }, matrix: [] })),
  http.get('/api/stats/sla-reliability', () => HttpResponse.json({ current_sla: 96.5, trend: [] })),
  http.get('/api/stats/knowledge-roi', () => HttpResponse.json({ overall_conversion: 68.2, trend: [] })),
  http.get('/api/stats/ethics-audit-queue', () => HttpResponse.json({ violations: [], pending_versions: [], total_pending: 0 })),
  http.get('/api/marketing/manager/alerts', () => HttpResponse.json([])),
  http.get('/api/visit-logs/attendance/status', () => HttpResponse.json({ status: 'clocked_out' })),
  
  http.get('/api/system/health/ai', () => HttpResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    models: [
        { model: 'gemini-2.5-flash', agent: 'Marketing (Bob/Alice)', provider: 'google', status: 'healthy', latency_ms: 120 },
        { model: 'gemini-1.5-pro', agent: 'Manager (Charlie)', provider: 'google', status: 'healthy', latency_ms: 250 }
    ]
  })),
  http.get('/api/stats/agent-xp', () => HttpResponse.json({
    monthly_trend: [],
    recent_transactions: []
  })),
  
  // 5. Fallbacks
  http.get('/api/ethics/events', () => HttpResponse.json([])),
  http.get('/api/changes', () => HttpResponse.json([])),
  http.get('/api/stats/ai-usage', () => HttpResponse.json({ total_budget: 1000, total_used: 150 })),
  http.get('/api/blogs', () => HttpResponse.json([])),
  http.get('/api/marketing/blogs', () => HttpResponse.json([])),
  http.get('/api/knowledge', () => HttpResponse.json({ 
    items: [
      { source_id: 'know-1', title: 'Internal Wiki', knowledge_type: 'documentation', url: 'https://wiki.internal' },
      { source_id: 'know-2', title: 'Product Spec', knowledge_type: 'specification', url: 'https://docs.internal/spec' }
    ] 
  })),
  http.get('/api/knowledge-items', () => HttpResponse.json([])),
  http.get('/api/admin/crawler-targets', () => HttpResponse.json([
    { id: 'target-1', target_url: 'https://sas.com/docs', description: 'SAS Docs', is_active: true },
    { id: 'target-2', target_url: 'https://104.com.tw', description: '104 Jobs', is_active: true }
  ])),
  http.post('/api/marketing/approvals/:type/:id/:action', () => HttpResponse.json({ success: true })),
  http.get('/api/admin/users', () => HttpResponse.json(mockAssignableUsers)),
  http.post('/api/admin/users', () => HttpResponse.json({ success: true }, { status: 201 })),
  http.get('/api/system/logs', () => HttpResponse.json([])),
  http.post('/api/marketing/blog/draft', () => HttpResponse.json({ title: 'Mock', content: '...', excerpt: '...', references: [] })),
  http.post('/api/marketing/leads/:id/promote', () => HttpResponse.json({ success: true, vendor_id: 'v-123' })),
  http.get('/api/auth/me', () => HttpResponse.json(mockUsers.admin)) // Global Fallback
];
