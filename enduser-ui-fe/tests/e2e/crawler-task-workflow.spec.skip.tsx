import { screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';

vi.mock('../../src/services/api', () => ({
  api: {
    getCurrentUser: vi.fn(),
    getProjects: vi.fn().mockResolvedValue([]),
    getAssignableUsers: vi.fn().mockResolvedValue([]),
    getCrawlerTargets: vi.fn().mockResolvedValue([]),
    createTask: vi.fn().mockResolvedValue({ id: 'task-1' }),
    getPendingChanges: vi.fn().mockResolvedValue([]),
    getPendingApprovals: vi.fn().mockResolvedValue({ blogs: [], leads: [] }),
    getSystemStats: vi.fn().mockResolvedValue({}),
    getMarketingStats: vi.fn().mockResolvedValue({}),
    getTasks: vi.fn().mockResolvedValue([]),
  }
}));

beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'alert').mockImplementation(() => {});

    // 1. Mock the user as Charlie (Manager)
    const charlie = { id: 'user-3', name: 'Charlie', role: EmployeeRole.MANAGER };
    vi.mocked(api.getCurrentUser).mockResolvedValue(charlie as any);

    // 2. Mock required data for task creation selects
    vi.mocked(api.getProjects).mockResolvedValue([{ id: 'proj-1', title: 'Admin Project' }] as any);
    vi.mocked(api.getAssignableUsers).mockResolvedValue([
        { id: 'lib-1', name: 'Librarian', role: 'ai_agent', tools: ['crawler'] }
    ] as any);
    vi.mocked(api.getCrawlerTargets).mockResolvedValue([
        { id: 'target-1', target_url: 'https://gov.site/data', description: 'Govt Target' }
    ] as any);
});

test('Manager (Charlie) can assign a Crawler Target to Librarian (Phase 4.6.58 Workflow)', async () => {
    const user = userEvent.setup();
    
    // Mount Dashboard
    renderApp(['/dashboard']);

    // Ensure Dashboard loads
    expect(await screen.findByRole('heading', { name: /My Tasks/i }, { timeout: 10000 })).toBeInTheDocument();

    // Open New Task Modal
    const newTaskBtn = await screen.findByRole('button', { name: /new task/i });
    await user.click(newTaskBtn);

    // --- GENERAL TAB ---
    // Wait for the modal to open and fill Title
    const titleInput = await screen.findByLabelText(/Title/i);
    await user.type(titleInput, 'Crawl Govt Target');

    // Select Project (Required)
    const projectSelect = screen.getByLabelText(/Project/i);
    fireEvent.change(projectSelect, { target: { value: 'proj-1' } });

    // Set Due Date (Required)
    const datePickerBtn = screen.getByRole('button', { name: /Due Date/i });
    await user.click(datePickerBtn);
    const tomorrowBtn = await screen.findByRole('button', { name: /Tomorrow/i });
    await user.click(tomorrowBtn);
    const confirmDateBtn = screen.getByRole('button', { name: /CONFIRM SELECTION/i });
    await user.click(confirmDateBtn);

    // --- ASSIGNMENT TAB ---
    // Switch to Assignment Tab
    const assignmentTabBtn = screen.getByRole('button', { name: /Assignment & Automation/i });
    await user.click(assignmentTabBtn);

    // Assign to Librarian
    const assigneeSelect = await screen.findByLabelText(/Assignee/i);
    fireEvent.change(assigneeSelect, { target: { value: 'lib-1' } });

    // When Librarian is selected, the Crawler Target dropdown should appear
    const crawlerSelect = await screen.findByLabelText(/Associate Knowledge Target/i);
    expect(crawlerSelect).toBeInTheDocument();
    
    // Select a crawler target
    fireEvent.change(crawlerSelect, { target: { value: 'target-1' } });

    // --- SUBMIT ---
    // Leave description empty to trigger the direct pipeline
    const saveBtn = screen.getByRole('button', { name: /Create Task/i });
    await user.click(saveBtn);

    // Verify api.createTask was called with the crawler_target_id
    await waitFor(() => {
        expect(api.createTask).toHaveBeenCalledWith(expect.objectContaining({
            title: 'Crawl Govt Target',
            assigneeId: 'lib-1',
            crawler_target_id: 'target-1',
            description: ''
        }));
    });
});
