import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DashboardPage from './DashboardPage';
import React from 'react';

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
          assignee: 'AI Assistant',
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
          attachments: ['https://example.com/debug-log.txt', 'https://example.com/screenshot-error.png']
      }
  ];

  return {
    api: {
      getTasks: vi.fn().mockResolvedValue(mockTasks),
      getProjects: vi.fn().mockResolvedValue([{ id: 'proj-1', title: 'Test Project' }]),
      getAssignableUsers: vi.fn().mockResolvedValue(mockUsers),
      createTask: vi.fn().mockResolvedValue({ id: 'new-task-1' }),
    },
  };
});

describe('DashboardPage', () => {
  it('should open TaskModal and show assignable users in dropdown', async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText('Test Project Tasks')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /new task/i }));
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    expect(await screen.findByRole('option', { name: 'Alice Johnson' })).toBeInTheDocument();
    expect(await screen.findByRole('option', { name: 'AI Assistant' })).toBeInTheDocument();
  });

  it('should display user avatars correctly for humans and AI', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('Human task')).toBeInTheDocument();
      expect(screen.getByText('AI task')).toBeInTheDocument();
    });

    // Scope queries to within the specific task item to avoid ambiguity
    const humanTaskItem = screen.getByText('Human task').closest('.p-4');
    const aiTaskItem = screen.getByText('AI task').closest('.p-4');

    const humanAvatar = within(humanTaskItem).getByTitle('Alice Johnson');
    const aiAvatar = within(aiTaskItem).getByTitle('AI Assistant');

    expect(humanAvatar).toBeInTheDocument();
    expect(aiAvatar).toBeInTheDocument();

    // Human avatars are circular
    expect(humanAvatar.style.borderRadius).toBe('50%');
    // AI avatars are square with rounded corners
    expect(aiAvatar.style.borderRadius).toBe('8px');
  });

  it('should display attachments for tasks that have them', async () => {
    render(<DashboardPage />);

    // Wait for the task with the specific title to be rendered
    await waitFor(() => {
      expect(screen.getByText('Fix authentication bug')).toBeInTheDocument();
    });

    // Find the attachment links by their text content (the filename)
    const attachmentLink1 = screen.getByText('debug-log.txt');
    const attachmentLink2 = screen.getByText('screenshot-error.png');

    // Assert that the links are present
    expect(attachmentLink1).toBeInTheDocument();
    expect(attachmentLink2).toBeInTheDocument();

    // Assert that the links have the correct href attribute
    expect(attachmentLink1).toHaveAttribute('href', 'https://example.com/debug-log.txt');
    expect(attachmentLink2).toHaveAttribute('href', 'https://example.com/screenshot-error.png');
  });
});
