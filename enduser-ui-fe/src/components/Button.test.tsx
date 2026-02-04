import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

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
    // Look for the spinner SVG (it has animate-spin class)
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

  it('applies variant classes correctly', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    let button = screen.getByRole('button');
    // Primary has 'bg-indigo-600' (default accentColor)
    expect(button.className).toContain('bg-indigo-600');

    rerender(<Button variant="danger">Danger</Button>);
    button = screen.getByRole('button');
    expect(button.className).toContain('bg-red-600');
  });

  it('renders neon line only for primary variant when enabled', () => {
    const { rerender } = render(<Button variant="primary" neonLine>Neon</Button>);
    const button = screen.getByRole('button');
    // The neon line is a span inside the button
    const spans = button.querySelectorAll('span');
    const hasNeonLine = Array.from(spans).some(span => span.className.includes('blur-'));
    expect(hasNeonLine).toBe(true);

    // Should not render for secondary variant even if neonLine is true
    rerender(<Button variant="secondary" neonLine>No Neon</Button>);
    const spansSecondary = screen.getByRole('button').querySelectorAll('span');
    const hasNeonLineSecondary = Array.from(spansSecondary).some(span => span.className.includes('blur-'));
    expect(hasNeonLineSecondary).toBe(false);
  });
});
