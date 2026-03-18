import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { NexusFooter } from './NexusFooter';

describe('NexusFooter Component Hardening', () => {
  it('renders metrics definitions and color codes correctly', () => {
    render(<NexusFooter />);
    
    // Check section headers
    expect(screen.getByText(/Metrics Definition/i)).toBeInTheDocument();
    expect(screen.getByText(/Color Codes/i)).toBeInTheDocument();
    expect(screen.getByText(/System Info/i)).toBeInTheDocument();
    
    // Check specific content
    expect(screen.getByText(/Reliability:/i)).toBeInTheDocument();
    expect(screen.getByText(/Optimal Range/i)).toBeInTheDocument();
    expect(screen.getByText(/ManagerNexus v7.1/i)).toBeInTheDocument();
  });
});
