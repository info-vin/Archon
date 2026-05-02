import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from './DashboardPage';

// Mock useAuth to avoid AuthProvider hanging
vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn().mockReturnValue({
    user: { id: 'admin-1', name: 'Admin User' },
    isAdmin: true,
    isAuthenticated: true,
    loading: false
  })
}));

// Mock the hook to return non-loading state to skip loading screen
vi.mock('../features/dashboard/hooks/useDashboardLogic', () => ({
  useDashboardLogic: () => ({
    projects: [],
    tasks: [],
    sortedTasks: [],
    recentActivity: [],
    isLoading: false,
    selectedProjectId: 'all',
    setSelectedProjectId: vi.fn(),
    refreshData: vi.fn(),
    assignableUsers: []
  })
}));

// Mock the api to avoid network calls during render
vi.mock('../services/api', () => ({
  api: {
    getProjects: vi.fn().mockResolvedValue([]),
    getTasks: vi.fn().mockResolvedValue([]),
    getRecentActivity: vi.fn().mockResolvedValue([]),
    getCurrentUser: vi.fn().mockResolvedValue({ id: '1', email: 'test@example.com', role: 'user' }),
    getAssignableUsers: vi.fn().mockResolvedValue([]),
    getAssignableAgents: vi.fn().mockResolvedValue([]),
    getAttendanceStatus: vi.fn().mockResolvedValue({ status: 'out' }),
    getEmployees: vi.fn().mockResolvedValue([])
  },
  supabase: null
}));

describe('DashboardPage Accessibility', () => {
  it('renders view mode buttons with proper aria labels', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText(/Loading tasks/i)).not.toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify the group
    await waitFor(() => {
        const viewModeGroup = screen.getByRole('group', { name: 'View mode' });
        expect(viewModeGroup).toBeInTheDocument();
    });

    // Verify buttons have aria-label and titles
    const listBtn = screen.getByRole('button', { name: 'List view' });
    expect(listBtn).toHaveAttribute('title', 'List view');
    expect(listBtn).toHaveAttribute('aria-pressed', 'true');

    const tableBtn = screen.getByRole('button', { name: 'Table view' });
    expect(tableBtn).toHaveAttribute('title', 'Table view');
    expect(tableBtn).toHaveAttribute('aria-pressed', 'false');

    const kanbanBtn = screen.getByRole('button', { name: 'Kanban view' });
    expect(kanbanBtn).toHaveAttribute('title', 'Kanban view');
    expect(kanbanBtn).toHaveAttribute('aria-pressed', 'false');

    const ganttBtn = screen.getByRole('button', { name: 'Gantt chart view' });
    expect(ganttBtn).toHaveAttribute('title', 'Gantt chart view');
    expect(ganttBtn).toHaveAttribute('aria-pressed', 'false');
  });
});
