import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DashboardPage from './DashboardPage';
import React from 'react';

// Mock the api module to avoid real API calls
vi.mock('../services/api', () => ({
  api: {
    getTasks: vi.fn().mockResolvedValue([
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
    ]),
    getProjects: vi.fn().mockResolvedValue([{ id: 'proj-1', title: 'Test Project' }]),
    getAssignableUsers: vi.fn().mockResolvedValue([
      { id: '2', name: 'Alice Johnson', role: 'Engineer' },
      { id: '3', name: 'Bob Williams', role: 'Marketer' },
    ]),
    createTask: vi.fn().mockResolvedValue({ id: 'new-task-1' }),
  },
}));

describe('DashboardPage', () => {
  it('should open TaskModal and show assignable users in dropdown', async () => {
    render(<DashboardPage />);

    // Wait for the page to load
    await waitFor(() => {
      expect(screen.getByText('Test Project Tasks')).toBeInTheDocument();
    });

    // Find and click the "New Task" button
    const newTaskButton = screen.getByRole('button', { name: /new task/i });
    fireEvent.click(newTaskButton);

    // Wait for the modal to appear
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Check if the modal title is correct
    expect(screen.getByText('Create New Task')).toBeInTheDocument();

    // Find the assignee dropdown
    const assigneeSelect = screen.getByLabelText(/assignee/i);
    expect(assigneeSelect).toBeInTheDocument();

    // Check if the dropdown contains the correct, dynamically loaded users
    const option1 = await screen.findByRole('option', { name: 'Alice Johnson' });
    const option2 = await screen.findByRole('option', { name: 'Bob Williams' });

    expect(option1).toBeInTheDocument();
    expect(option2).toBeInTheDocument();

    console.log('Test passed: Assignee dropdown correctly populated with users from API.');
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