import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../../src/App';
import { AuthProvider } from '../../src/hooks/useAuth';
import { api } from '../../src/services/api'; // Import the mocked API

// NOTE: The vi.mock for the API service has been moved to `tests/e2e/e2e.setup.ts`
// and is loaded via `vitest.e2e.config.ts`. This keeps test files clean.

/**
 * A custom render function for E2E tests that wraps components
 * with necessary providers (AuthProvider, MemoryRouter).
 * @param ui The component to render.
 * @param param1 Router options.
 */
const renderWithProviders = (ui: React.ReactElement, { route = '/' } = {}) => {
  window.history.pushState({}, 'Test page', route);
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[route]}>
        {ui}
      </MemoryRouter>
    </AuthProvider>
  );
};


describe('AI as a Teammate E2E Workflows', () => {
  beforeEach(() => {
    // vi.clearAllMocks() is often handled globally, but can be done here for safety.
    vi.clearAllMocks();
  });

  test('E2E setup is complete and mocks from e2e.setup.ts are working', async () => {
    // This test now verifies that the mocks from the dedicated setup file are loaded.
    const user = await api.getCurrentUser();
    expect(user).toBeDefined();
    expect(user?.name).toBe('E2E Test User');

    const assignableAgents = await api.getAssignableAgents();
    expect(assignableAgents).toHaveLength(3);
    expect(assignableAgents[0].name).toBe('Content Writer AI');
  });

  test('Marketing Campaign: User can create a task and assign it to an AI content writer', async () => {
    // Render the AppRoutes component with all necessary providers
    renderWithProviders(<AppRoutes />, { route: '/dashboard' });

    // 1. Wait for the main UI to load and find the "New Task" button
    const newTaskButton = await screen.findByRole('button', { name: /new task/i });
    expect(newTaskButton).toBeInTheDocument();

    // 2. Simulate clicking "New Task" to open the modal
    fireEvent.click(newTaskButton);

    // 3. Fill in the task details in the modal
    const titleInput = await screen.findByLabelText(/title/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const dueDateInput = screen.getByLabelText(/due date/i);
    
    const taskTitle = 'Draft a blog post about our new AI features';
    fireEvent.change(titleInput, { target: { value: taskTitle } });
    fireEvent.change(descriptionInput, { target: { value: 'The blog post should cover the benefits and use cases.' } });
    fireEvent.change(dueDateInput, { target: { value: '2025-12-31' } });

    // 4. Select the AI agent from the dropdown
    const assigneeSelect = screen.getByLabelText(/assignee/i);
    // Correctly simulate selecting an option by firing a 'change' event on the <select> element
    fireEvent.change(assigneeSelect, { target: { value: 'agent-content-writer' } });

    // 5. Click the "Create Task" button
    const saveButton = screen.getByRole('button', { name: /create task/i });
    fireEvent.click(saveButton);

    // 6. Assert that the createTask API was called with the correct data
    await waitFor(() => {
      expect(api.createTask).toHaveBeenCalledTimes(1);
      expect(api.createTask).toHaveBeenCalledWith(expect.objectContaining({
        title: taskTitle,
        description: 'The blog post should cover the benefits and use cases.',
        assigneeId: 'agent-content-writer',
        project_id: 'proj-e2e-1',
        due_date: new Date('2025-12-31').toISOString(),
        priority: 'medium',
      }));
    });
  });

  test('Technical Support: User can create a task with logs and assign it to a Log Analyzer AI', async () => {
    // Arrange: Define mock log data
    const mockErrorLog = `
      [2025-12-25T10:30:00.123Z] ERROR: NullPointerException at com.example.UserService:123
      ...stacktrace...
      [2025-12-25T10:30:00.124Z] INFO: User 'testuser' failed to login.
    `;

    // Render the component starting at the dashboard
    renderWithProviders(<AppRoutes />, { route: '/dashboard' });

    // Act: Simulate user actions
    // 1. Click "New Task"
    const newTaskButton = await screen.findByRole('button', { name: /new task/i });
    fireEvent.click(newTaskButton);

    // 2. Fill form
    const titleInput = await screen.findByLabelText(/title/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const dueDateInput = screen.getByLabelText(/due date/i);
    
    const taskTitle = 'Analyze user error logs for ticket #12345';
    fireEvent.change(titleInput, { target: { value: taskTitle } });
    fireEvent.change(descriptionInput, { target: { value: mockErrorLog } });
    fireEvent.change(dueDateInput, { target: { value: '2025-12-28' } });

    // 3. Select AI agent
    const assigneeSelect = screen.getByLabelText(/assignee/i);
    fireEvent.change(assigneeSelect, { target: { value: 'agent-log-analyzer' } });

    // 4. Submit form
    const saveButton = screen.getByRole('button', { name: /create task/i });
    fireEvent.click(saveButton);

    // Assert: Verify the API call
    await waitFor(() => {
      expect(api.createTask).toHaveBeenCalledTimes(1);
      expect(api.createTask).toHaveBeenCalledWith(expect.objectContaining({
        title: taskTitle,
        description: mockErrorLog,
        assigneeId: 'agent-log-analyzer',
        project_id: 'proj-e2e-1',
        due_date: new Date('2025-12-28').toISOString(),
        priority: 'medium',
      }));
    });
  });

  test('Sales Outreach: User can create a task and assign it to a Sales AI', async () => {
    // Arrange
    renderWithProviders(<AppRoutes />, { route: '/dashboard' });

    // Act
    // 1. Click "New Task"
    const newTaskButton = await screen.findByRole('button', { name: /new task/i });
    fireEvent.click(newTaskButton);

    // 2. Fill form
    const titleInput = await screen.findByLabelText(/title/i);
    const dueDateInput = screen.getByLabelText(/due date/i);
    
    const taskTitle = 'Generate lead list for ACME Corp in the finance sector';
    fireEvent.change(titleInput, { target: { value: taskTitle } });
    fireEvent.change(dueDateInput, { target: { value: '2025-12-29' } });

    // 3. Select AI agent
    const assigneeSelect = screen.getByLabelText(/assignee/i);
    fireEvent.change(assigneeSelect, { target: { value: 'agent-sales-intel' } });

    // 4. Submit form
    const saveButton = screen.getByRole('button', { name: /create task/i });
    fireEvent.click(saveButton);

    // Assert
    await waitFor(() => {
      expect(api.createTask).toHaveBeenCalledTimes(1);
      expect(api.createTask).toHaveBeenCalledWith(expect.objectContaining({
        title: taskTitle,
        assigneeId: 'agent-sales-intel',
        project_id: 'proj-e2e-1',
        due_date: new Date('2025-12-29').toISOString(),
      }));
    });
  });
});
