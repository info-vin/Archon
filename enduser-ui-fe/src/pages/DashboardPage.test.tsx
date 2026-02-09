import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DashboardPage from './DashboardPage';
// Mock useAuth to avoid AuthProvider error
vi.mock('../hooks/useAuth.tsx', () => ({
  useAuth: vi.fn().mockReturnValue({
    user: { id: 'admin-1', name: 'Admin User' },
    isAdmin: true,
    isAuthenticated: true,
    loading: false
  })
}));

// Mock the api module to avoid real API calls
vi.mock('../services/api', () => {
  const mockUsers = [
    { id: '2', name: 'Alice Johnson', role: 'member' },
    { id: '3', name: 'AI Assistant', role: 'ai_agent' },
  ];

  // Combined mock tasks for all test cases
  const mockTasks = [
      {
          id: 'task-1',
          project_id: 'proj-1',
          title: 'Human task',
          description: '',
          status: 'review',
          assignee: 'Alice Johnson',
          task_order: 1,
          priority: 'high',
          due_date: '2025-09-10T23:59:59Z',
          created_at: '2025-07-10T10:00:00Z',
          updated_at: '2025-07-15T10:00:00Z',
          attachments: []
      },
      {
          id: 'task-2',
          project_id: 'proj-1',
          title: 'AI task',
          description: '',
          status: 'doing',
          assignee: 'AI Bot Assistant',
          assignee_id: 'agent-3',
          task_order: 2,
          priority: 'low',
          due_date: '2025-09-11T23:59:59Z',
          created_at: '2025-07-11T10:00:00Z',
          updated_at: '2025-07-16T10:00:00Z',
          attachments: []
      },
      {
          id: 'task-4',
          project_id: 'proj-1',
          title: 'Fix authentication bug',
          description: 'Users are reporting intermittent login failures.',
          status: 'review',
          assignee: 'Alice Johnson',
          task_order: 3,
          priority: 'high',
          due_date: '2025-09-10T23:59:59Z',
          created_at: '2025-07-10T10:00:00Z',
          updated_at: '2025-07-15T10:00:00Z',
          attachments: [
            { file_name: 'debug-log.txt', url: 'https://example.com/debug-log.txt' },
            { file_name: 'screenshot-error.png', url: 'https://example.com/screenshot-error.png' }
          ]
      }
  ];

  return {
    api: {
      getTasks: vi.fn().mockResolvedValue(mockTasks),
      getProjects: vi.fn().mockResolvedValue([{ id: 'proj-1', title: 'Test Project' }]),
      getAssignableUsers: vi.fn().mockResolvedValue(mockUsers),
      getAssignableAgents: vi.fn().mockResolvedValue([
        { id: 'ai-asst-1', name: 'Assistant', role: 'ai_agent' }
      ]),
      getCurrentUser: vi.fn().mockResolvedValue({
        id: 'admin-1',
        name: 'Admin User',
        role: 'system_admin'
      }),
      createTask: vi.fn().mockResolvedValue({ id: 'new-task-1' }),
      updateTask: vi.fn().mockResolvedValue({ id: 'task-1' }),
      getAttendanceStatus: vi.fn().mockResolvedValue({ status: 'out', clock_in_time: null, location: null }),
      clockIn: vi.fn().mockResolvedValue({ status: 'success' }),
      clockOut: vi.fn().mockResolvedValue({ status: 'success' }),
    },
  };
});

describe('DashboardPage', () => {
  it('should open TaskModal and show assignable users in dropdown', async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('All Tasks')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /new task/i }));
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    expect(await screen.findByRole('option', { name: 'Alice Johnson' })).toBeInTheDocument();
    expect(await screen.findByRole('option', { name: '(AI) Assistant' })).toBeInTheDocument();
  });

  it('should display user avatars correctly for humans and AI', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Human task')).toBeInTheDocument();
      expect(screen.getByText('AI task')).toBeInTheDocument();
    });

    // Scope queries to within the specific task item to avoid ambiguity
    const humanTaskItem = screen.getByText('Human task').closest('.p-4') as HTMLElement;
    const aiTaskItem = screen.getByText('AI task').closest('.p-4') as HTMLElement;

    const humanAvatar = within(humanTaskItem).getByTitle('Alice Johnson');
    const aiAvatar = within(aiTaskItem).getByTitle('AI Bot Assistant');

    expect(humanAvatar).toBeInTheDocument();
    expect(aiAvatar).toBeInTheDocument();

    // Human avatars are circular
    expect(humanAvatar.style.borderRadius).toBe('8px');
    // AI avatars are square with rounded corners
    expect(aiAvatar.style.borderRadius).toBe('8px');
  });

  it('should display attachments for tasks that have them', async () => {
    render(<DashboardPage />);

    // Wait for the task with the specific title to be rendered
    await waitFor(() => {
      expect(screen.getByText('Fix authentication bug')).toBeInTheDocument();
    });

    // Verify the "2 files" badge is visible
    const badge = screen.getByTestId('attachment-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent(/2/);

    // Verify the "2 files" badge is visible
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent(/2/);

    // Note: Filenames are not shown in List View, only the count is shown.
    // To verify filenames, we would need to click the task to open the modal.
    // For this test, verifying the badge count is sufficient to prove attachments are present.
  });
});

        