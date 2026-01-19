import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TaskModal } from './TaskModal';
import userEvent from '@testing-library/user-event';
import { Task, TaskPriority, TaskStatus } from '../types';

// Mock API
vi.mock('../services/api.ts', () => ({
  api: {
    getAssignableUsers: vi.fn().mockResolvedValue([
      { id: '2', name: 'Alice Johnson', role: 'member' }
    ]),
    getAssignableAgents: vi.fn().mockResolvedValue([
      { id: '3', name: 'AI Assistant', role: 'ai_agent' }
    ]),
    createTask: vi.fn().mockResolvedValue({ id: 'new-task' }),
    updateTask: vi.fn().mockResolvedValue({ id: 'task-1' }),
    getKnowledgeItems: vi.fn().mockResolvedValue([]), // Needed for KnowledgeSelector
  }
}));

const mockTask: Task = {
  id: 'task-1',
  project_id: 'proj-123',
  title: 'Existing Task',
  description: 'This is an existing task to be edited.',
  status: TaskStatus.TODO,
  priority: TaskPriority.HIGH,
  created_at: new Date().toISOString(),
  due_date: '2025-11-15T00:00:00.000Z',
  assignee: 'Alice Johnson',
  assignee_id: '2',
  attachments: [],
};

describe('TaskModal', () => {

  const setup = (props: Partial<React.ComponentProps<typeof TaskModal>> = {}) => {
    const defaultProps: React.ComponentProps<typeof TaskModal> = {
      onClose: vi.fn(),
      onTaskCreated: vi.fn(),
      onTaskUpdated: vi.fn(),
      projectId: 'proj-123',
      ...props,
    };
    return render(<TaskModal {...defaultProps} />);
  };

  it('should render in create mode correctly', async () => {
    setup();
    expect(screen.getByText('Create New Task')).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toHaveValue('');
    expect(screen.getByRole('button', { name: 'Create Task' })).toBeInTheDocument();
    // Wait for users to load
    await screen.findByRole('option', { name: 'Alice Johnson' });
  });

  it('should render in edit mode and populate fields', async () => {
    setup({ task: mockTask });
    expect(screen.getByText('Edit Task')).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toHaveValue(mockTask.title);
    expect(screen.getByLabelText('Description')).toHaveValue(mockTask.description);
    expect(screen.getByLabelText('Due Date')).toHaveValue('2025-11-15');
    expect(screen.getByLabelText('Priority')).toHaveValue(TaskPriority.HIGH);
    
    // Wait for users to load to check assignee
    await screen.findByRole('option', { name: 'Alice Johnson' });
    const assigneeSelect = await screen.findByLabelText('Assignee');
    expect(assigneeSelect).toHaveValue(mockTask.assignee_id);
  });

  it('should allow selecting priority', async () => {
    const user = userEvent.setup();
    setup();
    const prioritySelect = screen.getByLabelText('Priority');
    await user.selectOptions(prioritySelect, TaskPriority.LOW);
    expect(prioritySelect).toHaveValue(TaskPriority.LOW);
  });

  it('should call onTaskCreated with correct data in create mode', async () => {
    const user = userEvent.setup();
    const onTaskCreated = vi.fn();
    setup({ onTaskCreated });

    await screen.findByRole('option', { name: 'Alice Johnson' });

    await user.type(screen.getByLabelText('Title'), 'New Test Task');
    await user.selectOptions(screen.getByLabelText('Priority'), TaskPriority.CRITICAL);
    await user.type(screen.getByLabelText('Due Date'), '2025-12-01');

    // Mock window.alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});

    await user.click(screen.getByRole('button', { name: 'Create Task' }));

    await waitFor(() => {
      expect(onTaskCreated).toHaveBeenCalledTimes(1);
    });

    alertSpy.mockRestore();
  });

  it('should call onTaskUpdated with correct data in edit mode', async () => {
    const user = userEvent.setup();
    const onTaskUpdated = vi.fn();
    setup({ task: mockTask, onTaskUpdated });

    await screen.findByRole('option', { name: 'Alice Johnson' });

    const titleInput = screen.getByLabelText('Title');
    await user.clear(titleInput);
    await user.type(titleInput, 'Updated Title');
    await user.selectOptions(screen.getByLabelText('Priority'), TaskPriority.LOW);

    // Mock window.alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});

    await user.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(onTaskUpdated).toHaveBeenCalledTimes(1);
    });
    
    alertSpy.mockRestore();
  });

  it('should show an alert if title or due date is missing', async () => {
    const user = userEvent.setup();
    const onTaskCreated = vi.fn();
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    setup({ onTaskCreated });

    const submitButton = screen.getByRole('button', { name: 'Create Task' });
    fireEvent.submit(submitButton);

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('Title and Due Date are required.');
    });
    expect(onTaskCreated).not.toHaveBeenCalled();

    alertSpy.mockRestore();
  });
});
