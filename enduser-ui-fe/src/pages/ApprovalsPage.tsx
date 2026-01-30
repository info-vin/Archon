// enduser-ui-fe/src/pages/ApprovalsPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api'; // Import the actual api service

// Assuming DiffViewer is created and placed here
// import DiffViewer from '../components/DiffViewer';

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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
          {proposals.length > 0 ? (
            proposals.map((proposal) => (
              <div key={proposal.id} className="bg-white shadow-sm border border-gray-200 rounded-xl p-5 flex flex-col justify-between h-full hover:shadow-md transition-shadow">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md">
                      {proposal.type.toUpperCase()}
                    </span>
                    <span className="text-[10px] text-gray-400">
                        {new Date(proposal.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  
                  <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
                      {proposal.request_payload.description || 'No description provided'}
                  </h3>
                  
                  <p className="text-xs text-gray-500 font-mono mb-4 break-all">
                    ID: {proposal.id}
                  </p>
                </div>

                <div className="mt-auto space-y-4">
                    {/* Example of conditionally showing a DiffViewer for file changes */}
                    {proposal.type === 'file' && (
                    <div className="max-h-40 overflow-y-auto border border-gray-100 rounded-lg text-xs bg-gray-50 p-2">
                        {/* Simplified Diff Preview for Card */}
                        <div className="font-mono text-[10px] text-gray-500">
                            Diff available (Tap to expand)
                        </div>
                    </div>
                    )}

                    <div className="grid grid-cols-2 gap-3 pt-2">
                        <button
                        onClick={() => handleAction(proposal.id, 'reject')}
                        disabled={submitting[proposal.id]}
                        className="py-3 px-4 bg-white text-red-600 border border-red-200 rounded-xl font-bold text-sm hover:bg-red-50 disabled:opacity-50 min-h-[44px] flex items-center justify-center"
                        >
                        {submitting[proposal.id] ? '...' : 'Reject'}
                        </button>
                        <button
                        onClick={() => handleAction(proposal.id, 'approve')}
                        disabled={submitting[proposal.id]}
                        className="py-3 px-4 bg-green-600 text-white rounded-xl font-bold text-sm hover:bg-green-700 disabled:opacity-50 min-h-[44px] flex items-center justify-center shadow-lg shadow-green-200"
                        >
                        {submitting[proposal.id] ? '...' : 'Approve'}
                        </button>
                    </div>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full p-8 text-center text-gray-500 bg-gray-50 rounded-xl border border-dashed border-gray-300">
              No pending approvals found. Good job!
            </div>
          )}
      </div>
    </div>
  );
};

export default ApprovalsPage;
