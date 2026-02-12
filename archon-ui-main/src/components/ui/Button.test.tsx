import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';
import React from 'react';

describe('Button Component', () => {
  it('renders children correctly', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    fireEvent.click(screen.getByText('Click Me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading spinner and is disabled when isLoading is true', () => {
    render(<Button isLoading>Click Me</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();

    // Look for the spinner. We expect it to have 'animate-spin' class.
    const spinner = button.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('is disabled when the disabled prop is true', () => {
    render(<Button disabled>Click Me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders icon when provided', () => {
    const MockIcon = () => <span data-testid="mock-icon">🔥</span>;
    render(<Button icon={<MockIcon />}>With Icon</Button>);
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
    expect(screen.getByText('With Icon')).toBeInTheDocument();
  });

  it('replaces icon with spinner when isLoading is true', () => {
    const MockIcon = () => <span data-testid="mock-icon">🔥</span>;
    render(<Button isLoading icon={<MockIcon />}>With Icon</Button>);

    // Icon should NOT be present (replaced by spinner)
    expect(screen.queryByTestId('mock-icon')).not.toBeInTheDocument();

    // Spinner SHOULD be present
    const button = screen.getByRole('button');
    const spinner = button.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('applies disabled styles', () => {
    render(<Button disabled>Disabled Button</Button>);
    const button = screen.getByRole('button');
    // We check for opacity-50 directly as it's applied conditionally in our implementation
    expect(button.className).toContain('opacity-50');
    expect(button.className).toContain('cursor-not-allowed');
  });
});
