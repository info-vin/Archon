import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

// Mock lucide-react Loader2
vi.mock('lucide-react', async () => {
  const actual = await vi.importActual('lucide-react');
  return {
    ...actual,
    Loader2: ({ className }: { className: string }) => <div data-testid="loader" className={className}>Loader</div>,
  };
});

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

    // Check for loader
    const loader = screen.getByTestId('loader');
    expect(loader).toBeInTheDocument();
    expect(loader.className).toContain('animate-spin');
  });

  it('is disabled when the disabled prop is true', () => {
    render(<Button disabled>Click Me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders icon when provided and not loading', () => {
    const MockIcon = () => <span data-testid="mock-icon">🔥</span>;
    render(<Button icon={<MockIcon />}>With Icon</Button>);
    expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
    expect(screen.getByText('With Icon')).toBeInTheDocument();
  });

  it('does not render icon when loading', () => {
    const MockIcon = () => <span data-testid="mock-icon">🔥</span>;
    render(<Button icon={<MockIcon />} isLoading>With Icon</Button>);
    expect(screen.queryByTestId('mock-icon')).not.toBeInTheDocument();
    expect(screen.getByTestId('loader')).toBeInTheDocument();
  });
});
