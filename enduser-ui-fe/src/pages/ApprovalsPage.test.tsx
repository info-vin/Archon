// src/pages/ApprovalsPage.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ApprovalsPage from './ApprovalsPage';
import { api } from '@/services/api';
import '@testing-library/jest-dom';

// Mock the API service
vi.mock('@/services/api', () => ({
  api: {
    getChangeProposals: vi.fn(),
    approveChangeProposal: vi.fn(),
    rejectChangeProposal: vi.fn(),
  },
}));

// Mock the DiffViewer component
vi.mock('@/components/DiffViewer', () => ({
  default: () => <div data-testid="diff-viewer">Diff Viewer</div>,
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false, // Disable retries for tests
    },
  },
});

const mockProposals = [
  {
    id: '1',
    status: 'pending',
    type: 'file_write',
    request_payload: {
      filepath: 'src/components/Button.tsx',
      reason: 'Add a new variant',
      content: 'new content',
      old_content: 'old content',
    },
    user_id: 'user-1',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: '2',
    status: 'pending',
    type: 'shell_command',
    request_payload: {
      command: 'npm',
      args: ['install'],
      reason: 'Install dependencies',
    },
    user_id: 'user-2',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('ApprovalsPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('shows a loading state initially', () => {
    (api.getChangeProposals as vi.Mock).mockReturnValue(new Promise(() => {}));
    render(<ApprovalsPage />, { wrapper });
    expect(screen.getByText(/Loading pending approvals.../i)).toBeInTheDocument();
  });

  it('shows an error message if fetching proposals fails', async () => {
    (api.getChangeProposals as vi.Mock).mockRejectedValue(new Error('Failed to fetch'));
    render(<ApprovalsPage />, { wrapper });
    expect(await screen.findByText(/Error Fetching Approvals/i)).toBeInTheDocument();
    expect(await screen.findByText(/Failed to fetch/i)).toBeInTheDocument();
  });

  it('renders a list of proposals when fetch is successful', async () => {
    (api.getChangeProposals as vi.Mock).mockResolvedValue(mockProposals);
    render(<ApprovalsPage />, { wrapper });
    expect(await screen.findByText(/Write to file: src\/components\/Button.tsx/i)).toBeInTheDocument();
    expect(await screen.findByText(/Run command: npm/i)).toBeInTheDocument();
  });

  it('shows a message when there are no pending proposals', async () => {
    (api.getChangeProposals as vi.Mock).mockResolvedValue([]);
    render(<ApprovalsPage />, { wrapper });
    expect(await screen.findByText(/No pending approvals/i)).toBeInTheDocument();
  });

  it('opens a dialog with details when a proposal is clicked', async () => {
    (api.getChangeProposals as vi.Mock).mockResolvedValue(mockProposals);
    render(<ApprovalsPage />, { wrapper });

    const fileWriteProposal = await screen.findByText(/Write to file: src\/components\/Button.tsx/i);
    fireEvent.click(fileWriteProposal);

    // Check if the dialog is opened with the correct content
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Reason for change:/i)).toBeInTheDocument();
      expect(screen.getByText(/Add a new variant/i)).toBeInTheDocument();
      // Check if DiffViewer is rendered for file_write
      expect(screen.getByTestId('diff-viewer')).toBeInTheDocument();
    });
  });
});
