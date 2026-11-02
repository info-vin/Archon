import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ProjectModal } from './ProjectModal';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    createProject: vi.fn(),
  },
}));

describe('ProjectModal Accessibility & Functionality', () => {
  it('renders modal with accessible dialog attributes', () => {
    render(<ProjectModal onClose={vi.fn()} onProjectCreated={vi.fn()} />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'project-modal-title');

    const title = screen.getByRole('heading', { level: 2, name: 'New Project' });
    expect(title).toHaveAttribute('id', 'project-modal-title');
  });

  it('closes when pressing Escape key', () => {
    const handleClose = vi.fn();
    render(<ProjectModal onClose={handleClose} onProjectCreated={vi.fn()} />);

    const dialogContainer = screen.getByRole('dialog').parentElement!;
    fireEvent.keyDown(dialogContainer, { key: 'Escape', code: 'Escape' });

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('closes when clicking Cancel or Close button', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<ProjectModal onClose={handleClose} onProjectCreated={vi.fn()} />);

    const closeBtn = screen.getByRole('button', { name: 'Close' });
    await user.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);

    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    await user.click(cancelBtn);
    expect(handleClose).toHaveBeenCalledTimes(2);
  });

  it('announces validation error via accessible alert role when submitting empty title', async () => {
    render(<ProjectModal onClose={vi.fn()} onProjectCreated={vi.fn()} />);

    const submitBtn = screen.getByRole('button', { name: 'Create project' });
    // Fire submit directly on form or click button
    fireEvent.submit(submitBtn.closest('form')!);

    const alertMessage = await screen.findByRole('alert');
    expect(alertMessage).toHaveTextContent('Project title is required.');
    expect(alertMessage).toHaveAttribute('aria-live', 'polite');
  });

  it('submits successfully and calls onProjectCreated and onClose', async () => {
    const handleClose = vi.fn();
    const handleProjectCreated = vi.fn();
    const user = userEvent.setup();

    vi.mocked(api.createProject).mockResolvedValueOnce({
      project: { id: 'proj-1', title: 'A11y Redesign', description: 'Enhance a11y' } as any,
    });

    render(<ProjectModal onClose={handleClose} onProjectCreated={handleProjectCreated} />);

    await user.type(screen.getByLabelText('Project Title'), 'A11y Redesign');
    await user.type(screen.getByLabelText('Description (Optional)'), 'Enhance a11y');

    const submitBtn = screen.getByRole('button', { name: 'Create project' });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(api.createProject).toHaveBeenCalledWith({
        title: 'A11y Redesign',
        description: 'Enhance a11y',
      });
      expect(handleProjectCreated).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'proj-1', title: 'A11y Redesign' })
      );
      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });
});
