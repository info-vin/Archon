import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NexusHUD } from './NexusHUD';

vi.mock('@/components/ui/Tooltip', () => ({
  Tooltip: ({ children }: any) => <div>{children}</div>,
  TooltipTrigger: ({ children }: any) => <div>{children}</div>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
  TooltipProvider: ({ children }: any) => <div>{children}</div>
}));

describe('NexusHUD Component Hardening', () => {
  const mockSetActiveMetric = vi.fn();
  const mockProps = {
    activeMetric: 'integrity' as any,
    setActiveMetric: mockSetActiveMetric,
    loading: false,
    overview: { integrity_score: 95, status: 'healthy', cost_24h: 1.23, knowledge_stats: { total_nodes: 150 } },
    approvals: { blogs: [1, 2], leads: [3] },
    alerts: [1, 2, 3, 4],
    team: [{ status: 'active' }, { status: 'active' }, { status: 'offline' }],
    ethicsAudit: { total_pending: 2, violations: [1], pending_versions: [1] },
    collabSynergy: { snapshot: { momentum_pct: 15, total_7d: 120, hot_bridge: 'Sales-IT' } },
    knowledgeRoi: { overall_conversion: 85 },
    slaReliability: { current_sla: 98 }
  };

  it('renders all HUD metrics', () => {
    render(<NexusHUD {...mockProps} />);
    expect(screen.getByText((content) => content.includes('95%'))).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes('.23'))).toBeInTheDocument();
  });
});
