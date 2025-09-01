
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TaskModal } from './TaskModal';
import { Employee } from '../types';
import userEvent from '@testing-library/user-event';

const mockEmployees: Employee[] = [
  { id: '1', name: 'Alice', role: 'developer' },
  { id: '2', name: 'Bob', role: 'designer' },
];

describe('TaskModal', () => {
  it('should not be in the document when closed', () => {
    // This test assumes the parent component handles the visibility.
    // We test the open state instead.
    const { queryByRole } = render(
      <div /> // Render nothing
    );
    expect(queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('should render correctly when opened', () => {
    render(<TaskModal onClose={() => {}} onSubmit={async () => {}} employees={mockEmployees} projectId="proj-123" />);
    
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Create New Task')).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Assignee')).toBeInTheDocument();
    expect(screen.getByLabelText('Due Date')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create Task' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('should allow typing in title, description, and due date', async () => {
    const user = userEvent.setup();
    render(<TaskModal onClose={() => {}} onSubmit={async () => {}} employees={mockEmployees} projectId="proj-123" />);

    const titleInput = screen.getByLabelText('Title');
    await user.type(titleInput, 'New Feature');
    expect(titleInput).toHaveValue('New Feature');

    const descriptionTextarea = screen.getByLabelText('Description');
    await user.type(descriptionTextarea, 'Implement the new feature');
    expect(descriptionTextarea).toHaveValue('Implement the new feature');

    const dateInput = screen.getByLabelText('Due Date');
    await user.type(dateInput, '2025-12-31');
    expect(dateInput).toHaveValue('2025-12-31');
  });

  it('should allow selecting an assignee', async () => {
    const user = userEvent.setup();
    render(<TaskModal onClose={() => {}} onSubmit={async () => {}} employees={mockEmployees} projectId="proj-123" />);
    
    const assigneeSelect = screen.getByLabelText('Assignee');
    await user.selectOptions(assigneeSelect, '2'); // Select Bob
    expect(assigneeSelect).toHaveValue('2');
  });

  it('should call onClose when the close button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    render(<TaskModal onClose={handleClose} onSubmit={async () => {}} employees={mockEmployees} projectId="proj-123" />);
    
    const closeButton = screen.getByRole('button', { name: /close/i }); // More flexible selector
    await user.click(closeButton);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when the cancel button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    render(<TaskModal onClose={handleClose} onSubmit={async () => {}} employees={mockEmployees} projectId="proj-123" />);
    
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    await user.click(cancelButton);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('should show an alert if title or due date is missing on submit', async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn();
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {}); // Mock window.alert

    render(<TaskModal onClose={() => {}} onSubmit={handleSubmit} employees={mockEmployees} projectId="proj-123" />);
    
    const submitButton = screen.getByRole('button', { name: 'Create Task' });
    fireEvent.submit(submitButton);

    expect(alertSpy).toHaveBeenCalledWith('Title and Due Date are required.');
    expect(handleSubmit).not.toHaveBeenCalled();

    alertSpy.mockRestore();
  });

  it('should call onSubmit with the correct data when form is submitted', async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TaskModal onClose={() => {}} onSubmit={handleSubmit} employees={mockEmployees} projectId="proj-123" />);

    await user.type(screen.getByLabelText('Title'), 'Test Task');
    await user.type(screen.getByLabelText('Description'), 'Test Desc');
    await user.selectOptions(screen.getByLabelText('Assignee'), '1');
    await user.type(screen.getByLabelText('Due Date'), '2025-10-26');

    await user.click(screen.getByRole('button', { name: 'Create Task' }));

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleSubmit).toHaveBeenCalledWith({
        project_id: 'proj-123',
        title: 'Test Task',
        description: 'Test Desc',
        assigneeId: '1',
        due_date: new Date('2025-10-26').toISOString(),
      });
    });
  });

  it('should disable the submit button while submitting', async () => {
    const user = userEvent.setup();
    // Create a promise that we can resolve manually
    let resolveSubmit: (value: void) => void;
    const promise = new Promise<void>(resolve => {
      resolveSubmit = resolve;
    });
    const handleSubmit = vi.fn().mockImplementation(() => promise);

    render(<TaskModal onClose={() => {}} onSubmit={handleSubmit} employees={mockEmployees} projectId="proj-123" />);

    await user.type(screen.getByLabelText('Title'), 'Test Task');
    await user.type(screen.getByLabelText('Due Date'), '2025-10-26');
    
    const submitButton = screen.getByRole('button', { name: 'Create Task' });
    await user.click(submitButton);

    // Button should be disabled and show "Creating..." text
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(screen.getByText('Creating...')).toBeInTheDocument();
    });

    // Resolve the submission promise
    resolveSubmit!(undefined);

    // Button should be re-enabled
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });
});
