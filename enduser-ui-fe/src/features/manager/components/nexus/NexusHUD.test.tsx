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
    overview: { integrity_score: 95, status: 'healthy', cost_24h: 1.2345, rag: { status: 'healthy' }, knowledge_stats: { total_nodes: 21 } },
    alerts: [1, 2, 3, 4],
    ethicsAudit: { total_pending: 2, violations: [1], pending_versions: [1] },
    collabSynergy: { snapshot: { momentum_pct: 15, total_7d: 120, hot_bridge: 'Sales-IT' } },
    knowledgeRoi: { overall_conversion: 85 },
    slaReliability: { current_sla: 98 }
  };

  it('renders 6 deduplicated HUD metrics without redundant sidebar/static cards', () => {
    render(<NexusHUD {...mockProps} />);
    expect(screen.getByText('Integrity')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('21 Nodes Indexed')).toBeInTheDocument();
    expect(screen.getByText('Resources')).toBeInTheDocument();
    expect(screen.getByText('$1.2345')).toBeInTheDocument();
    expect(screen.getByText('24H Token Cost')).toBeInTheDocument();
    expect(screen.getByText('Risk & Ethics')).toBeInTheDocument();
    expect(screen.getByText('6 Alerts')).toBeInTheDocument();
    expect(screen.getByText('4 Risks | 2 Audit')).toBeInTheDocument();
    expect(screen.getByText('Collab')).toBeInTheDocument();
    expect(screen.getByText('Graph')).toBeInTheDocument();
    expect(screen.getByText('Reliability')).toBeInTheDocument();

    expect(screen.queryByText('Op Load')).not.toBeInTheDocument();
    expect(screen.queryByText('Act Force')).not.toBeInTheDocument();
    expect(screen.queryByText('Prompts')).not.toBeInTheDocument();
  });
});
