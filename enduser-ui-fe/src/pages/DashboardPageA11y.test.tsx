import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from './DashboardPage';
import { AuthProvider } from '@/hooks/useAuth';

// Mock the api to avoid network calls during render
vi.mock('../services/api', () => ({
  api: {
    getProjects: vi.fn().mockResolvedValue([]),
    getTasks: vi.fn().mockResolvedValue([]),
    getRecentActivity: vi.fn().mockResolvedValue([]),
    getCurrentUser: vi.fn().mockResolvedValue({ id: '1', email: 'test@example.com', role: 'user' }),
    getAssignableUsers: vi.fn().mockResolvedValue([])
  },
  supabase: null
}));

describe('DashboardPage Accessibility', () => {
  it('renders view mode buttons with proper aria labels', async () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <DashboardPage />
        </BrowserRouter>
      </AuthProvider>
    );

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
