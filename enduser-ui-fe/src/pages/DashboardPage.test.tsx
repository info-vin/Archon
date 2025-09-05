import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import DashboardPage from './DashboardPage';
import React from 'react';

// Mock the api module to avoid real API calls
vi.mock('../services/api', () => ({
  api: {
    getTasks: vi.fn().mockResolvedValue([]),
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
});
