// src/pages/ApprovalsPage.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

// NOTE: This type should ideally be in a central `types.ts` file.
// For now, defining it here to match the backend model.
interface ChangeProposal {
  id: string;
  status: string;
  type: string;
  request_payload: {
    reason?: string;
    filepath?: string;
    branch_name?: string;
    command?: string;
    args?: string[];
  };
  user_id: string | null;
  created_at: string;
  updated_at: string;
}

const ApprovalsPage: React.FC = () => {
  const { data: proposals, isLoading, isError, error } = useQuery<ChangeProposal[], Error>({
    queryKey: ['changeProposals', 'pending'],
    queryFn: () => api.getChangeProposals('pending'),
  });

  const getProposalTitle = (proposal: ChangeProposal) => {
    switch (proposal.type) {
      case 'file_write':
        return `Write to file: ${proposal.request_payload.filepath || 'N/A'}`;
      case 'git_checkout':
        return `Checkout new branch: ${proposal.request_payload.branch_name || 'N/A'}`;
      case 'shell_command':
        return `Run command: ${proposal.request_payload.command || 'N/A'}`;
      default:
        return `Unknown proposal type: ${proposal.type}`;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="ml-4 text-lg">Loading pending approvals...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error Fetching Approvals</AlertTitle>
        <AlertDescription>
          Could not load the list of pending approvals. Please try again later.
          <br />
          <pre className="mt-2 p-2 bg-gray-100 rounded">{error?.message}</pre>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Pending Approvals</h1>

      {proposals && proposals.length > 0 ? (
        <div className="space-y-4">
          {proposals.map((proposal) => (
            <Card key={proposal.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>{getProposalTitle(proposal)}</span>
                  <Badge variant="secondary">{proposal.type.replace('_', ' ')}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Reason: {proposal.request_payload.reason || 'No reason provided.'}
                </p>
                <div className="text-xs text-gray-500 mt-4">
                  <span>Proposed at: {new Date(proposal.created_at).toLocaleString()}</span>
                  <span className="mx-2">|</span>
                  <span>Proposal ID: {proposal.id}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">No pending approvals found.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ApprovalsPage;
