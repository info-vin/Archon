import { describe, test, expect, beforeEach, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { api } from '../../src/services/api';
import { renderApp } from './e2e.setup';
import { createUser } from '../factories/userFactory';
import { EmployeeRole } from '../../src/types';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';

describe('AI as a Teammate E2E Workflows', () => {
  let tasks: any[] = [];

  beforeEach(() => {
    vi.clearAllMocks();
    tasks = []; // Reset tasks

    // Stateful MSW Handlers
    server.use(
        http.get('*/api/assignable-users', () => {
            return HttpResponse.json([
                { id: 'agent-content-writer', name: 'Content Writer', role: 'ai_agent' },
                { id: 'agent-log-analyzer', name: 'Log Analyzer', role: 'ai_agent' },
                { id: 'agent-sales-intel', name: 'Sales Intel', role: 'ai_agent' }
            ]);
        }),
        http.get('*/api/projects', () => HttpResponse.json({ projects: [{ id: 'p1', title: 'Campaign Project' }] })),
        http.get('*/api/tasks', () => HttpResponse.json(tasks)),
        http.post('*/api/tasks', async ({ request }) => {
            const body = await request.json() as any;
            const newTask = { ...body, id: `task-${Date.now()}`, status: 'todo' };
            tasks.push(newTask);
            return HttpResponse.json({ task: newTask });
        })
    );
  });

  test('Marketing Campaign: User can create a task and assign it to an AI content writer', async () => {
    // Mock Marketing User to ensure "My Tasks" view
    const user = createUser({ role: EmployeeRole.MARKETING });
    vi.mocked(api.getCurrentUser).mockResolvedValue(user as any);

    renderApp();

    // Wait for loading to finish
    await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Ensure Dashboard loads first - Wait for the heading specifically to ensure page content
    await screen.findByRole('heading', { name: /My Tasks/i });

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
    // Mock Member User
    const user = createUser({ role: EmployeeRole.MEMBER });
    vi.mocked(api.getCurrentUser).mockResolvedValue(user as any);

    const mockErrorLog = `
      [2025-12-25T10:30:00.123Z] ERROR: NullPointerException at com.example.UserService:123
      ...stacktrace...
      [2025-12-25T10:30:00.124Z] INFO: User 'testuser' failed to login.
    `;
    renderApp();

    // Wait for loading to finish
    await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Ensure Dashboard loads first
    await screen.findByRole('heading', { name: /My Tasks/i });

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
    // Mock Sales User
    const user = createUser({ role: EmployeeRole.SALES });
    vi.mocked(api.getCurrentUser).mockResolvedValue(user as any);

    renderApp();

    // Wait for loading to finish
    await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    // Ensure Dashboard loads first
    await screen.findByRole('heading', { name: /My Tasks/i });

    const newTaskButton = await screen.findByRole('button', { name: /new task/i });
    fireEvent.click(newTaskButton);

    // Explicitly wait for the modal to appear
    await screen.findByRole('dialog');

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