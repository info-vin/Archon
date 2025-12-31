// enduser-ui-fe/src/pages/ApprovalsPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api'; // Import the actual api service

// Assuming DiffViewer is created and placed here
import DiffViewer from '../components/DiffViewer';

interface ChangeProposal {
  id: string;
  type: 'file' | 'git' | 'shell';
  status: string;
  created_at: string;
  request_payload: {
    [key: string]: any;
    description: string;
    original_content?: string;
    new_content?: string;
  };
}

const ApprovalsPage: React.FC = () => {
  const [proposals, setProposals] = useState<ChangeProposal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<{[key: string]: boolean}>({});

  const fetchProposals = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getPendingChanges();
      setProposals(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pending approvals.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProposals();
  }, [fetchProposals]);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    setSubmitting(prev => ({ ...prev, [id]: true }));
    try {
      if (action === 'approve') {
        await api.approveChange(id);
      } else {
        await api.rejectChange(id);
      }
      // Remove the proposal from the list for immediate UI feedback
      setProposals(prev => prev.filter(p => p.id !== id));
    } catch (err: any) {
      setError(`Failed to ${action} proposal ${id}. Please try again.`);
      console.error(err);
    } finally {
      setSubmitting(prev => ({ ...prev, [id]: false }));
    }
  };

  if (loading) {
    return <div className="p-4">Loading pending approvals...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Pending Approvals</h1>
      <div className="bg-white shadow-md rounded-lg">
        <ul className="divide-y divide-gray-200">
          {proposals.length > 0 ? (
            proposals.map((proposal) => (
              <li key={proposal.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-indigo-600">
                      {proposal.type.toUpperCase()} Proposal
                    </p>
                    <p className="text-lg font-semibold text-gray-900">
                      {proposal.request_payload.description || 'No description'}
                    </p>
                    <p className="text-xs text-gray-500">
                      ID: {proposal.id} | Submitted at: {new Date(proposal.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleAction(proposal.id, 'approve')}
                      disabled={submitting[proposal.id]}
                      className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
                    >
                      {submitting[proposal.id] ? 'Approving...' : 'Approve'}
                    </button>
                    <button
                      onClick={() => handleAction(proposal.id, 'reject')}
                      disabled={submitting[proposal.id]}
                      className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-gray-400"
                    >
                      {submitting[proposal.id] ? 'Rejecting...' : 'Reject'}
                    </button>
                  </div>
                </div>
                {/* Example of conditionally showing a DiffViewer for file changes */}
                {proposal.type === 'file' && (
                  <div className="mt-4">
                    <DiffViewer
                      oldValue={proposal.request_payload.original_content || ''}
                      newValue={proposal.request_payload.new_content || ''}
                    />
                  </div>
                )}
              </li>
            ))
          ) : (
            <li className="p-4 text-center text-gray-500">
              No pending approvals.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default ApprovalsPage;
