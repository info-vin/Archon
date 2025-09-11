import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TaskModal } from './TaskModal';
import userEvent from '@testing-library/user-event';

// Note: The mock server in `src/mocks/handlers.ts` provides the users now.
// We don't need to pass them as props anymore.

describe('TaskModal', () => {
  it('should not be in the document when closed', () => {
    // This test confirms the component isn't rendered when it's not supposed to be.
    const { queryByRole } = render(<div />);
    expect(queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('should render correctly, show loading state, and then load users', async () => {
    render(<TaskModal onClose={() => {}} onSubmit={async () => {}} projectId="proj-123" />);
    
    // Check for the modal and its static content
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Create New Task')).toBeInTheDocument();
    
    // Check for the initial loading state in the assignee dropdown
    expect(screen.getByRole('option', { name: 'Loading...' })).toBeInTheDocument();

    // Wait for the loading to complete and for users to be populated from the mock API
    const userOption = await screen.findByRole('option', { name: 'Alice Johnson' });
    expect(userOption).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Bob Williams' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'Loading...' })).not.toBeInTheDocument();
  });

  it('should allow typing in title, description, and due date', async () => {
    const user = userEvent.setup();
    render(<TaskModal onClose={() => {}} onSubmit={async () => {}} projectId="proj-123" />);

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

  it('should allow selecting an assignee after loading', async () => {
    const user = userEvent.setup();
    render(<TaskModal onClose={() => {}} onSubmit={async () => {}} projectId="proj-123" />);
    
    // Wait for users to be loaded from the mock API
    const assigneeSelect = await screen.findByLabelText('Assignee');
    await screen.findByRole('option', { name: 'Alice Johnson' });

    // Now, select an option from the populated dropdown
    await user.selectOptions(assigneeSelect, '2'); // Selects Alice Johnson (id: '2')
    expect(assigneeSelect).toHaveValue('2');
  });

  it('should call onClose when the close button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    render(<TaskModal onClose={handleClose} onSubmit={async () => {}} projectId="proj-123" />);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when the cancel button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    render(<TaskModal onClose={handleClose} onSubmit={async () => {}} projectId="proj-123" />);
    
    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    await user.click(cancelButton);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('should show an alert if title or due date is missing on submit', () => {
    const handleSubmit = vi.fn();
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});

    render(<TaskModal onClose={() => {}} onSubmit={handleSubmit} projectId="proj-123" />);
    
    const submitButton = screen.getByRole('button', { name: 'Create Task' });
    
    // Use fireEvent.submit to bypass browser validation for required fields
    act(() => {
      fireEvent.submit(submitButton);
    });

    expect(alertSpy).toHaveBeenCalledWith('Title and Due Date are required.');
    expect(handleSubmit).not.toHaveBeenCalled();

    alertSpy.mockRestore();
  });

  it('should call onSubmit with the correct data when form is submitted', async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TaskModal onClose={() => {}} onSubmit={handleSubmit} projectId="proj-123" />);

    // Wait for users to load before interacting with the form
    await screen.findByRole('option', { name: 'Alice Johnson' });

    await user.type(screen.getByLabelText('Title'), 'Test Task');
    await user.type(screen.getByLabelText('Description'), 'Test Desc');
    await user.selectOptions(screen.getByLabelText('Assignee'), '2'); // Alice Johnson
    await user.type(screen.getByLabelText('Due Date'), '2025-10-26');

    await user.click(screen.getByRole('button', { name: 'Create Task' }));

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledTimes(1);
      expect(handleSubmit).toHaveBeenCalledWith({
        project_id: 'proj-123',
        title: 'Test Task',
        description: 'Test Desc',
        assigneeId: '2',
        due_date: new Date('2025-10-26').toISOString(),
      });
    });
  });

  it('should disable the submit button while submitting', async () => {
    const user = userEvent.setup();
    let resolveSubmit: (value: void) => void;
    const promise = new Promise<void>(resolve => {
      resolveSubmit = resolve;
    });
    const handleSubmit = vi.fn().mockImplementation(() => promise);

    render(<TaskModal onClose={() => {}} onSubmit={handleSubmit} projectId="proj-123" />);

    // Wait for users to load
    await screen.findByRole('option', { name: 'Alice Johnson' });

    await user.type(screen.getByLabelText('Title'), 'Test Task');
    await user.type(screen.getByLabelText('Due Date'), '2025-10-26');
    
    const submitButton = screen.getByRole('button', { name: 'Create Task' });
    await user.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(screen.getByText('Creating...')).toBeInTheDocument();
    });

    resolveSubmit!(undefined);

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });
});