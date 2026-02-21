import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EthicsCard } from './EthicsCard';
import { api } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';

// Mock useAuth
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: vi.fn().mockReturnValue({
    user: { id: 'm1', role: 'manager' }, // Default to manager
  }),
}));

// Mock api
vi.mock('../../../services/api', () => ({
  api: {
    getEthicsEvents: vi.fn(),
  },
}));

describe('EthicsCard', () => {
  it('renders nothing for non-managers', () => {
    // Override useAuth for this test
    vi.mocked(useAuth).mockReturnValue({ user: { role: 'sales' }, isAdmin: false, isAuthenticated: true, loading: false } as any);
    
    const { container } = render(<EthicsCard />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders events for manager', async () => {
    // Reset mock to manager
    vi.mocked(useAuth).mockReturnValue({ user: { role: 'manager' }, isAdmin: true, isAuthenticated: true, loading: false } as any);

    const mockEvents = [
      {
        id: '1',
        severity: 'high',
        event_type: 'policy_violation',
        description: 'Forbidden word detected',
        created_at: '2025-01-01T12:00:00Z',
        raw_input: 'hack the system',
      },
    ];
    (api.getEthicsEvents as any).mockResolvedValue(mockEvents);

    render(<EthicsCard />);

    await waitFor(() => {
        expect(screen.getByText('Compliance & Ethics Logs (Sentinel)')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Forbidden word detected')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getByText('policy_violation')).toBeInTheDocument();
  });

  it('renders empty state when no events', async () => {
    // Reset mock to manager
    vi.mocked(useAuth).mockReturnValue({ user: { role: 'manager' }, isAdmin: true, isAuthenticated: true, loading: false } as any);

    (api.getEthicsEvents as any).mockResolvedValue([]);
    render(<EthicsCard />);

    await waitFor(() => {
        expect(screen.getByText('No compliance violations detected.')).toBeInTheDocument();
    });
    expect(screen.getByText('System is running within safety guardrails.')).toBeInTheDocument();
  });
});
