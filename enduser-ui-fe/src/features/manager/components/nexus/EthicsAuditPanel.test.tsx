import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EthicsAuditPanel } from './EthicsAuditPanel';

// Mock Icons
vi.mock('../../../../components/Icons', () => ({
  ShieldCheckIcon: (props: any) => <svg data-testid="shield-icon" {...props} />,
  ZapIcon: (props: any) => <svg data-testid="zap-icon" {...props} />,
  FileTextIcon: (props: any) => <svg data-testid="file-icon" {...props} />,
  CheckCircleIcon: (props: any) => <svg data-testid="check-icon" {...props} />
}));

describe('EthicsAuditPanel Component Hardening', () => {
  const mockHandleDispatch = vi.fn();
  const mockHandleApprovePrompt = vi.fn();
  
  const mockEthicsAudit = {
    total_pending: 2,
    violations: [
      { id: 'v1', event_type: 'Injection', description: 'Malicious payload', raw_input: 'DROP TABLE users' }
    ],
    pending_versions: [
      { id: 'p1', document_id: 'System Prompt', version_number: 2, created_by: 'Bob', change_summary: 'Optimized logic', content: '{"new": "logic"}' }
    ]
  };

  it('renders safety violations and triggers dispatch', () => {
    render(
      <EthicsAuditPanel 
        ethicsAudit={mockEthicsAudit} 
        handleDispatch={mockHandleDispatch}
        handleApprovePrompt={mockHandleApprovePrompt}
        processingId={null}
      />
    );

    expect(screen.getByText(/Injection: Malicious payload/i)).toBeInTheDocument();
    expect(screen.getByText(/Attempted Input: DROP TABLE users/i)).toBeInTheDocument();
    
    const dispatchBtn = screen.getByText(/DISPATCH INVESTIGATION/i);
    fireEvent.click(dispatchBtn);
    expect(mockHandleDispatch).toHaveBeenCalledWith('v1');
  });

  it('renders prompt changes and triggers approve', () => {
    render(
      <EthicsAuditPanel 
        ethicsAudit={mockEthicsAudit} 
        handleDispatch={mockHandleDispatch}
        handleApprovePrompt={mockHandleApprovePrompt}
        processingId={null}
      />
    );

    expect(screen.getByText(/System Prompt \(v2\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Changed by Bob | Optimized logic/i)).toBeInTheDocument();
    
    const approveBtn = screen.getByText(/APPROVE/i);
    fireEvent.click(approveBtn);
    expect(mockHandleApprovePrompt).toHaveBeenCalledWith('p1');
  });

  it('shows loading state on approve button when processingId matches', () => {
    render(
      <EthicsAuditPanel 
        ethicsAudit={mockEthicsAudit} 
        handleDispatch={mockHandleDispatch}
        handleApprovePrompt={mockHandleApprovePrompt}
        processingId="p1"
      />
    );

    expect(screen.getByText('...')).toBeInTheDocument();
  });

  it('renders compliance nominal state when no items are pending', () => {
    const emptyAudit = { total_pending: 0, violations: [], pending_versions: [] };
    render(
      <EthicsAuditPanel 
        ethicsAudit={emptyAudit} 
        handleDispatch={mockHandleDispatch}
        handleApprovePrompt={mockHandleApprovePrompt}
        processingId={null}
      />
    );

    expect(screen.getByText(/Compliance Nominal/i)).toBeInTheDocument();
    expect(screen.getByTestId('check-icon')).toBeInTheDocument();
  });

  it('handles VIEW DIFF click (calls window.alert)', () => {
    const spy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    render(
      <EthicsAuditPanel 
        ethicsAudit={mockEthicsAudit} 
        handleDispatch={mockHandleDispatch}
        handleApprovePrompt={mockHandleApprovePrompt}
        processingId={null}
      />
    );

    const viewDiffBtn = screen.getByText(/VIEW DIFF/i);
    fireEvent.click(viewDiffBtn);
    
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});
