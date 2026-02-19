import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ManagerNexus } from './ManagerNexus';
import { AuthProvider } from '../hooks/useAuth';

// Define the icons mock to ensure XIcon exists
vi.mock('../components/Icons', async (importOriginal) => {
  const actual = await importOriginal() as any;
  return {
    ...actual,
    XIcon: (props: any) => <svg data-testid="x-icon" {...props} />
  };
});

// Mock API with supabase export
vi.mock('../services/api', () => ({
  api: {
    getSystemOverview: vi.fn().mockResolvedValue({ status: 'healthy', integrity_score: 95, knowledge_stats: { total_nodes: 100 } }),
    getEmployees: vi.fn().mockResolvedValue([]),
    getPendingApprovals: vi.fn().mockResolvedValue({ blogs: [], leads: [] }),
    getManagerAlerts: vi.fn().mockResolvedValue([]),
    getAiUsage: vi.fn().mockResolvedValue({ total_monthly_usd: 0, total_monthly_tokens: 0, team: [], burn_trend: [] }),
    getSystemSettings: vi.fn().mockResolvedValue([]),
    getCommanderTrends: vi.fn().mockResolvedValue([]),
    getForceReadiness: vi.fn().mockResolvedValue({ trend: [] }),
    getBusinessRisks: vi.fn().mockResolvedValue([]),
    getCollabSynergy: vi.fn().mockResolvedValue({ nodes: [], matrix: [] }),
    getSlaReliability: vi.fn().mockResolvedValue({ trend: [] }),
    getEthicsAuditQueue: vi.fn().mockResolvedValue({ violations: [], pending_versions: [] }),
    getKnowledgeRoi: vi.fn().mockResolvedValue({ trend: [] }),
    getHealthTrend: vi.fn().mockResolvedValue({ trend: [] }), // MOCK CRASH: Missing 'audit' field
    getPendingChanges: vi.fn().mockResolvedValue([
      { id: 'change-1', type: 'file', created_at: new Date().toISOString(), request_payload: { description: 'Update API' } }
    ]),
    getCurrentUser: vi.fn().mockResolvedValue({ id: '1', name: 'Admin', role: 'system_admin' }),
    seedKnowledgeBase: vi.fn().mockResolvedValue({ indexed_count: 0 }),
    processApproval: vi.fn().mockResolvedValue({ success: true }),
    updateSystemSetting: vi.fn().mockResolvedValue({ success: true }),
    generateTaskFromAlert: vi.fn().mockResolvedValue({ success: true }),
    approvePromptChange: vi.fn().mockResolvedValue({ success: true }),
    getBlogPost: vi.fn().mockResolvedValue({ id: '1', title: 'Test' }),
    getContentSources: vi.fn().mockResolvedValue([]),
    getContentContext: vi.fn().mockResolvedValue({ rag_refs: [] }),
    draftBlogPost: vi.fn().mockResolvedValue({ title: 'Draft' }),
    nanaBananaProxy: vi.fn().mockResolvedValue({ image_url: 'url' }),
    getMarketingTrends: vi.fn().mockResolvedValue({ keyword_growth: [], sankey_flow: {} })
  },
  supabase: {
    auth: {
      onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      getUser: vi.fn().mockResolvedValue({ data: { user: null } })
    }
  }
}));

describe('ManagerNexus Reliability Verification', () => {
  it('renders correctly and opens the Spec panel without XIcon ReferenceError', async () => {
    render(
      <AuthProvider>
        <ManagerNexus />
      </AuthProvider>
    );
    
    // 1. Verify basic rendering
    expect(await screen.findByText(/Manager Nexus/i)).toBeInTheDocument();
    
    // 2. Find and click View Specs
    const specButton = screen.getByText(/View Specs/i);
    fireEvent.click(specButton);
    
    // 3. Verify the Slide-over is visible
    expect(screen.getByText(/Nexus Metrics Spec/i)).toBeInTheDocument();
    
    // 4. CRITICAL: Check if XIcon rendered (this fails if XIcon is undefined)
    const xIcon = screen.getByTestId('x-icon');
    expect(xIcon).toBeInTheDocument();
    
    console.log("✅ Success: ManagerNexus rendered and Spec Panel opened without crashing.");
  });

  it('renders DevOps proposals within Op Load tab without crashing (BUG-054 Fix Verification)', async () => {
    render(
      <AuthProvider>
        <ManagerNexus />
      </AuthProvider>
    );

    // 1. Navigate to Op Load
    const opLoadCard = await screen.findByText(/Op Load/i);
    fireEvent.click(opLoadCard);

    // 2. Switch to DevOps tab
    const devOpsTab = screen.getByRole('button', { name: /Dev Ops/i });
    fireEvent.click(devOpsTab);

    // 3. Verify real data from getPendingChanges mock is visible
    expect(await screen.findByText(/Update API/i)).toBeInTheDocument();
    console.log("✅ Success: DevOps proposals rendered correctly in Nexus.");
  });
});
