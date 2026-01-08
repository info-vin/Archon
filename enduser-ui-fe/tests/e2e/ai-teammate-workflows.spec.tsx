import { describe, test, expect, beforeEach, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { api } from '../../src/services/api';
import { renderApp } from './e2e.setup';

describe('AI as a Teammate E2E Workflows', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('Marketing Campaign: User can create a task and assign it to an AI content writer', async () => {
    renderApp();

    const newTaskButton = await screen.findByRole('button', { name: /new task/i });
    expect(newTaskButton).toBeInTheDocument();
    fireEvent.click(newTaskButton);

    const titleInput = await screen.findByLabelText(/title/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const dueDateInput = screen.getByLabelText(/due date/i);
    
    const taskTitle = 'Draft a blog post about our new AI features';
    fireEvent.change(titleInput, { target: { value: taskTitle } });
    fireEvent.change(descriptionInput, { target: { value: 'The blog post should cover the benefits and use cases.' } });
    fireEvent.change(dueDateInput, { target: { value: '2025-12-31' } });

    const assigneeSelect = screen.getByLabelText(/assignee/i);
    fireEvent.change(assigneeSelect, { target: { value: 'agent-content-writer' } });

    const saveButton = screen.getByRole('button', { name: /create task/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(taskTitle)).toBeInTheDocument();
    });
  });

  test('Technical Support: User can create a task with logs and assign it to a Log Analyzer AI', async () => {
    const mockErrorLog = `
      [2025-12-25T10:30:00.123Z] ERROR: NullPointerException at com.example.UserService:123
      ...stacktrace...
      [2025-12-25T10:30:00.124Z] INFO: User 'testuser' failed to login.
    `;
    renderApp();

    const newTaskButton = await screen.findByRole('button', { name: /new task/i });
    expect(newTaskButton).toBeInTheDocument();
    fireEvent.click(newTaskButton);


    const titleInput = await screen.findByLabelText(/title/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const dueDateInput = screen.getByLabelText(/due date/i);
    
    const taskTitle = 'Analyze user error logs for ticket #12345';
    fireEvent.change(titleInput, { target: { value: taskTitle } });
    fireEvent.change(descriptionInput, { target: { value: mockErrorLog } });
    fireEvent.change(dueDateInput, { target: { value: '2025-12-28' } });

    const assigneeSelect = screen.getByLabelText(/assignee/i);
    fireEvent.change(assigneeSelect, { target: { value: 'agent-log-analyzer' } });

    const saveButton = screen.getByRole('button', { name: /create task/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(taskTitle)).toBeInTheDocument();
    });
  });

  test('Sales Outreach: User can create a task and assign it to a Sales AI', async () => {
    renderApp();

    const newTaskButton = await screen.findByRole('button', { name: /new task/i });
    fireEvent.click(newTaskButton);

    const titleInput = await screen.findByLabelText(/title/i);
    const dueDateInput = screen.getByLabelText(/due date/i);
    
    const taskTitle = 'Generate lead list for ACME Corp in the finance sector';
    fireEvent.change(titleInput, { target: { value: taskTitle } });
    fireEvent.change(dueDateInput, { target: { value: '2025-12-29' } });

    const assigneeSelect = screen.getByLabelText(/assignee/i);
    fireEvent.change(assigneeSelect, { target: { value: 'agent-sales-intel' } });

    const saveButton = screen.getByRole('button', { name: /create task/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(taskTitle)).toBeInTheDocument();
    });
  });
});