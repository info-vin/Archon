import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';

// --- TEST SETUP ---
beforeEach(() => {
    vi.clearAllMocks();
});

test('Manager (Charlie) can access Team Management Panel', async () => {
    const charlie = { id: 'user-3', name: 'Charlie', role: EmployeeRole.MANAGER };
    vi.mocked(api.getCurrentUser).mockResolvedValue(charlie as any);
    
    renderApp(['/team']);

    expect(await screen.findByRole('heading', { name: /Team Management/i }, { timeout: 10000 })).toBeInTheDocument();
    expect(await screen.findByText(/Alice Johnson/i)).toBeInTheDocument();
});

test('Sales (Alice) is denied access to Team Management Panel', async () => {
    const alice = { id: 'user-1', name: 'Alice', role: EmployeeRole.SALES };
    vi.mocked(api.getCurrentUser).mockResolvedValue(alice as any);

    renderApp(['/team']);

    expect(await screen.findByText(/Access Denied/i, {}, { timeout: 10000 })).toBeInTheDocument();
});

test('User can use POBot to refine task description', async () => {
    const user = userEvent.setup();
    const charlie = { id: 'user-3', name: 'Charlie', role: EmployeeRole.MANAGER };
    vi.mocked(api.getCurrentUser).mockResolvedValue(charlie as any);
    
    renderApp(['/dashboard']);

    // Ensure Dashboard loads
    expect(await screen.findByRole('heading', { name: /My Tasks/i }, { timeout: 10000 })).toBeInTheDocument();

    // Open Modal
    const newTaskBtn = await screen.findByRole('button', { name: /new task/i });
    await user.click(newTaskBtn);

    // Type Title
    const titleInput = await screen.findByLabelText(/title/i);
    await user.type(titleInput, 'Refine Me');

    // Click Refine
    const refineBtn = await screen.findByText(/Refine with AI/i);
    await user.click(refineBtn);

    // Verify Refinement (Increased patience)
    await waitFor(() => {
        const descInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;
        expect(descInput.value).toContain('User Story: As a user');
    }, { timeout: 10000 });
});

test('Manager can view pending approvals and click approve', async () => {
    const user = userEvent.setup();
    const charlie = {
        id: 'user-3',
        name: 'Charlie',
        role: EmployeeRole.MANAGER,
        permissions: ['user:manage:team', 'content:publish', 'code:approve', 'task:read:team']
    };
    vi.mocked(api.getCurrentUser).mockResolvedValue(charlie as any);

    renderApp(['/approvals']);

    // 1. Verify Strategic Approvals Header
    expect(await screen.findByRole('heading', { name: /Strategic Approvals/i }, { timeout: 10000 })).toBeInTheDocument();

    // 2. Ensure the blog item is rendered
    expect(await screen.findByText('Q3 Market Analysis', {}, { timeout: 10000 })).toBeInTheDocument();

    // 3. Approve Action
    const approveBtn = await screen.findByText('Publish');
    await user.click(approveBtn);

    // 4. Verify Success
    await waitFor(() => {
        expect(screen.getByText('Q3 Market Analysis')).toBeInTheDocument();
    });
});
