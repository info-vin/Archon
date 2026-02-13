import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Input } from './Input';

describe('Input Component', () => {
  it('associates label with input using auto-generated ID', () => {
    render(<Input label="Email Address" />);

    // If the label is correctly associated with htmlFor/id, getByLabelText will find the input
    const input = screen.getByLabelText('Email Address');
    expect(input).toBeInTheDocument();
    expect(input.tagName).toBe('INPUT');

    // Verify ID is generated
    expect(input.id).toBeTruthy();
  });

  it('uses provided ID if supplied', () => {
    const customId = 'custom-email-id';
    render(<Input label="Email Address" id={customId} />);

    const input = screen.getByLabelText('Email Address');
    expect(input.id).toBe(customId);
  });

  it('shows required indicator when required prop is true', () => {
    render(<Input label="Username" required />);

    const input = screen.getByLabelText(/Username/);
    expect(input).toBeRequired();

    // Check for the visual indicator
    const asterisk = screen.getByText('*');
    expect(asterisk).toBeInTheDocument();
    expect(asterisk).toHaveClass('text-red-500');
    expect(asterisk).toHaveAttribute('aria-hidden', 'true');
  });

  it('renders without label', () => {
    render(<Input placeholder="No label here" />);
    const input = screen.getByPlaceholderText('No label here');
    expect(input).toBeInTheDocument();
  });
});
