
import { test, expect, beforeAll, afterEach, afterAll, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { setupServer } from 'msw/node';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';

// --- MOCK DATA ---
const MOCK_EMPLOYEES = [
  { id: 'user-1', name: 'Alice', role: 'sales', department: 'Sales', email: 'alice@archon.com' },
  { id: 'user-2', name: 'Bob', role: 'marketing', department: 'Marketing', email: 'bob@archon.com' },
  { id: 'user-3', name: 'Charlie', role: 'manager', department: 'Management', email: 'charlie@archon.com' },
];

const MOCK_AGENTS = [
    { id: 'agent-1', name: 'DevBot', role: 'ai_agent' }
];

// --- TEST SETUP ---
const server = setupServer(
    http.get('*/api/users', () => {
        return HttpResponse.json(MOCK_EMPLOYEES);
    }),
    http.get('*/api/assignable-users', () => {
        return HttpResponse.json(MOCK_EMPLOYEES);
    }),
    http.get('*/api/agents/assignable', () => {
        return HttpResponse.json(MOCK_AGENTS);
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
    // Default mocks
    http.get('*/api/projects', () => HttpResponse.json({ projects: [{ id: 'p1', title: 'Project X' }] })),
    http.get('*/api/tasks', () => HttpResponse.json([])),
    http.get('*/api/blogs', () => HttpResponse.json([])),
    http.get('*/api/knowledge-items', () => HttpResponse.json([]))
);

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => {
    server.resetHandlers();
    vi.clearAllMocks();
});
afterAll(() => server.close());

test('Manager (Charlie) can access Team Management Panel', async () => {
    // Mock Charlie
    vi.mocked(api.getCurrentUser).mockResolvedValue(MOCK_EMPLOYEES[2] as any);
    vi.mocked(api.getEmployees).mockResolvedValue(MOCK_EMPLOYEES as any);
    vi.mocked(api.getAiUsage).mockResolvedValue({
        total_budget: 1000,
        total_used: 500,
        usage_percentage: 50,
        usage_by_user: []
    });

    renderApp(['/team']);

    // Ensure Dashboard/Page loads first
    await screen.findByRole('heading', { name: /Team Management/i });

    // Check Header and AI Fleet
    expect(await screen.findByText('AI Fleet')).toBeInTheDocument();
    
    // Check Team Members
    expect(await screen.findByText('Alice')).toBeInTheDocument();
});

test('Sales (Alice) is denied access to Team Management Panel', async () => {
    // Mock Alice
    vi.mocked(api.getCurrentUser).mockResolvedValue(MOCK_EMPLOYEES[0] as any);

    renderApp(['/team']);

    expect(await screen.findByText(/Access Denied/i)).toBeInTheDocument();
    expect(screen.queryByText('AI Fleet')).not.toBeInTheDocument();
});

test('User can use POBot to refine task description', async () => {
    const user = userEvent.setup();
    // Mock Charlie
    vi.mocked(api.getCurrentUser).mockResolvedValue(MOCK_EMPLOYEES[2] as any);
    
    renderApp(['/dashboard']);

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
