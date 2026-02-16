import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EmptyState } from './EmptyState';

describe('EmptyState', () => {
  it('renders title and description correctly', () => {
    render(
      <EmptyState
        title="Test Title"
        description="Test Description"
      />
    );
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('renders action button and handles click', () => {
    const handleAction = vi.fn();
    render(
      <EmptyState
        title="Test Title"
        description="Test Description"
        actionLabel="Click Me"
        onAction={handleAction}
      />
    );

    const button = screen.getByText('Click Me');
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it('does not render action button if actionLabel is missing', () => {
    render(
      <EmptyState
        title="Test Title"
        description="Test Description"
        onAction={() => {}}
      />
    );
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders custom icon', () => {
    render(
      <EmptyState
        title="Test Title"
        description="Test Description"
        icon={<span data-testid="custom-icon">Icon</span>}
      />
    );
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });
});
