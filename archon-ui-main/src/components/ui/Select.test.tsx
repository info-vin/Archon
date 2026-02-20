import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Select } from './Select';

describe('Select Component', () => {
  it('renders with label and associates it with the select', () => {
    const options = [
      { value: 'option1', label: 'Option 1' },
      { value: 'option2', label: 'Option 2' },
    ];
    render(<Select label="Test Select" options={options} />);

    // This should initially fail because the label is not associated with the select
    const select = screen.getByLabelText('Test Select');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('option1');
  });

  it('renders required asterisk when required prop is true', () => {
    const options = [{ value: '1', label: '1' }];
    render(<Select label="Required Select" options={options} required />);

    // Check for the asterisk
    const asterisk = screen.getByText('*');
    expect(asterisk).toBeInTheDocument();
    expect(asterisk).toHaveClass('text-red-500');
  });
});
