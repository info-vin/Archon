import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NexusHeader } from './NexusHeader';

// Mock Icons
vi.mock('../../../../components/Icons', () => ({
  FileTextIcon: (props: any) => <svg data-testid="file-icon" {...props} />,
  ClockIcon: (props: any) => <svg data-testid="clock-icon" {...props} />
}));

describe('NexusHeader Component Hardening', () => {
  it('renders correctly with title and version', () => {
    const mockOnOpenSpec = vi.fn();
    render(<NexusHeader onOpenSpec={mockOnOpenSpec} />);
    
    expect(screen.getByText(/Manager Nexus/i)).toBeInTheDocument();
    expect(screen.getByText(/Command & Control v7.1/i)).toBeInTheDocument();
    expect(screen.getByTestId('file-icon')).toBeInTheDocument();
  });

  it('calls onOpenSpec when View Specs button is clicked', () => {
    const mockOnOpenSpec = vi.fn();
    render(<NexusHeader onOpenSpec={mockOnOpenSpec} />);
    
    const viewSpecsBtn = screen.getByText(/View Specs/i);
    fireEvent.click(viewSpecsBtn);
    
    expect(mockOnOpenSpec).toHaveBeenCalledTimes(1);
  });
});
