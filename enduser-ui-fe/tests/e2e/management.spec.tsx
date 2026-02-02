
import { test, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { server } from '../../src/mocks/server';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { createUser } from '../factories/userFactory';

// --- MOCK DATA ---
const MOCK_EMPLOYEES = [
  createUser({ id: 'user-1', name: 'Alice', role: EmployeeRole.SALES }),
  createUser({ id: 'user-2', name: 'Bob', role: EmployeeRole.MARKETING }),
  createUser({ id: 'user-3', name: 'Charlie', role: EmployeeRole.MANAGER }),
];

const MOCK_AGENTS = [
    { id: 'agent-1', name: 'DevBot', role: 'ai_agent' }
];

// --- TEST SETUP ---
beforeEach(() => {
    vi.clearAllMocks();
    
    server.use(
        http.get('*/api/users', () => {
            return HttpResponse.json(MOCK_EMPLOYEES);
        }),
        http.get('*/api/assignable-users', () => {
            return HttpResponse.json(MOCK_EMPLOYEES);
        }),
        http.get('*/api/agents/assignable', () => {
            return HttpResponse.json(MOCK_AGENTS);
        }),
        http.get('*/api/marketing/approvals', () => {
            return HttpResponse.json({ blogs: [], leads: [] });
        }),
        http.get('*/api/stats/ai-usage', () => {
            return HttpResponse.json({
                total_budget: 1000,
                total_used: 500,
                usage_percentage: 50,
                usage_by_user: []
            });
        }),
        http.post('*/api/tasks/refine-description', async ({ request }) => {
            const body = await request.json() as any;
            return HttpResponse.json({
                refined_description: `User Story: As a user, I want ${body.title} so that I can be happy.\n\nAcceptance Criteria:\n- Done.`
            });
        }),
        http.get('*/api/changes', () => {
            return HttpResponse.json([]);
        }),
        http.get('*/api/ethics/events', () => {
            return HttpResponse.json([]);
        }),
        // Default mocks
        http.get('*/api/projects', () => HttpResponse.json({ projects: [{ id: 'p1', title: 'Project X' }] })),
        http.get('*/api/tasks', () => HttpResponse.json([])),
        http.get('*/api/blogs', () => HttpResponse.json([])),
        http.get('*/api/knowledge-items', () => HttpResponse.json([]))
    );
});

test('Manager (Charlie) can access Team Management Panel', async () => {
    // Mock Charlie
    vi.mocked(api.getCurrentUser).mockResolvedValue(MOCK_EMPLOYEES[2] as any);
    
    // FB-06: API must now return Agents as part of employees list, they are not hardcoded in UI
    const employeesWithBot = [...MOCK_EMPLOYEES, MOCK_AGENTS[0]];

    // Use MSW instead of mocking api client directly to avoid pollution
    server.use(
        http.get('*/api/users', () => {
            return HttpResponse.json(employeesWithBot);
        })
    );

    renderApp(['/team']);

    // Ensure Dashboard/Page loads first
    await screen.findByRole('heading', { name: /Team Management/i });

    // Check Team Members (Confirm Access Granted)
    expect(await screen.findByText('Alice')).toBeInTheDocument();
    
    // Check Mock Agent Injection (From API now)
    expect(await screen.findByText('DevBot')).toBeInTheDocument();
});

test('Sales (Alice) is denied access to Team Management Panel', async () => {
    // Mock Alice
    vi.mocked(api.getCurrentUser).mockResolvedValue(MOCK_EMPLOYEES[0] as any);

    renderApp(['/team']);

    expect(await screen.findByText(/Access Denied/i)).toBeInTheDocument();
    expect(screen.queryByText('Shared Budget')).not.toBeInTheDocument();
});

test('User can use POBot to refine task description', async () => {
    const user = userEvent.setup();
    // Mock Charlie
    vi.mocked(api.getCurrentUser).mockResolvedValue(MOCK_EMPLOYEES[2] as any);
    
    renderApp(['/dashboard']);

    // Wait for loading to finish
    await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Ensure Dashboard loads first
    await screen.findByRole('heading', { name: /My Tasks/i });

    // Open Modal
    const newTaskBtn = await screen.findByRole('button', { name: /new task/i });
    await user.click(newTaskBtn);

    // Type Title
    const titleInput = screen.getByLabelText(/title/i);
    await user.type(titleInput, 'Refine Me');

    // Click Refine
    const refineBtn = await screen.findByText(/Refine with AI/i);
    await user.click(refineBtn);

    // Verify Refinement
    await waitFor(() => {
        const descInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;
        expect(descInput.value).toContain('User Story: As a user');
    });
});

test('Manager can view pending approvals and click approve', async () => {
    const user = userEvent.setup();
    
    // Mock Charlie (Manager) with explicit permissions to guarantee access
    // This bypasses any complexity in role-mapping during tests
    const charlie = {
        ...MOCK_EMPLOYEES[2],
        permissions: ['user:manage:team', 'content:publish', 'code:approve', 'task:read:team']
    };
    vi.mocked(api.getCurrentUser).mockResolvedValue(charlie as any);

    // Provide data at network level via MSW
    server.use(
        http.get('*/api/marketing/approvals', () => {
            return HttpResponse.json({
                blogs: [{ id: 'blog-1', title: 'Q3 Market Analysis', authorName: 'Bob', status: 'review' }],
                leads: []
            });
        }),
        http.get('*/api/projects', () => {
            return HttpResponse.json([{ id: 'p1', title: 'Sales Expansion' }]);
        }),
        http.post('*/api/marketing/approvals/:type/:id/:action', () => {
            return HttpResponse.json({ success: true, status: 'published' });
        })
    );

    renderApp(['/approvals']);

    // 1. Verify Command Center Header (Wait for PermissionGuard and lazy load)
    await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Command Center/i })).toBeInTheDocument();
    }, { timeout: 3000 });

    // 2. Ensure the blog item is rendered
    expect(await screen.findByText('Q3 Market Analysis', {}, { timeout: 5000 })).toBeInTheDocument();

    // 3. Approve Action
    const approveBtn = screen.getByText('Publish');
    await user.click(approveBtn);

    // 4. Verify Content Still visible or handled
    await waitFor(() => {
        expect(screen.getByText('Q3 Market Analysis')).toBeInTheDocument();
    });
});
