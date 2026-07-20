import React from 'react';
import { UnifiedProposal } from '../hooks/useApprovalInbox';
import { CheckCircleIcon, XCircleIcon, ArrowPathIcon } from '@/components/Icons';

interface ApprovalActionHeaderProps {
  selectedProposal: UnifiedProposal;
  showRejectInput: boolean;
  setShowRejectInput: (v: boolean) => void;
  processingId: string | null;
  handleAction: (id: string, action: 'approve' | 'reject') => void;
  rejectReason: string;
}

export const ApprovalActionHeader: React.FC<ApprovalActionHeaderProps> = ({
  selectedProposal,
  showRejectInput,
  setShowRejectInput,
  processingId,
  handleAction,
  rejectReason
}) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-t-2xl p-6 border-x border-t border-gray-200 dark:border-slate-800 flex justify-between items-start">
      <div>
        <span className={`px-2 py-0.5 text-[10px] font-black rounded uppercase tracking-widest ${selectedProposal.is_marketing ? 'bg-fuchsia-100 text-fuchsia-700' : 'bg-indigo-100 text-indigo-700'}`}>
          {selectedProposal.type} PROPOSAL
        </span>
        <h2 className="text-2xl font-black text-gray-900 dark:text-white mt-2 leading-tight">
          {selectedProposal.change_summary || 'Agent Contribution'}
        </h2>
        {selectedProposal.request_payload?.file_path && (
          <code className="text-xs bg-gray-100 dark:bg-slate-800 px-2 py-1 rounded mt-3 block w-fit font-mono text-gray-600 dark:text-gray-400">
            {selectedProposal.request_payload.file_path}
          </code>
        )}
      </div>
      
      <div className="flex gap-2 shrink-0">
        {showRejectInput ? (
            <div className="flex gap-2">
               <button 
                 onClick={() => setShowRejectInput(false)}
                 className="px-4 py-2 bg-gray-100 text-gray-600 text-xs font-bold rounded-lg hover:bg-gray-200 transition-colors focus-visible:ring-2 focus-visible:outline-none"
               >
                 Cancel
               </button>
               <button 
                 onClick={() => handleAction(selectedProposal.id, 'reject')}
                 disabled={!!processingId || !rejectReason.trim()}
                 aria-disabled={!!processingId || !rejectReason.trim()}
                 aria-busy={processingId === selectedProposal.id}
                 className="px-6 py-2 bg-red-600 text-white text-xs font-black rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 disabled:opacity-50 focus-visible:ring-2 focus-visible:outline-none"
               >
                 {processingId === selectedProposal.id ? (
                   <>
                     <ArrowPathIcon className="w-4 h-4 animate-spin" />
                     REJECTING...
                   </>
                 ) : 'CONFIRM REJECT'}
               </button>
            </div>
        ) : (
            <>
                <button 
                  onClick={() => handleAction(selectedProposal.id, 'reject')}
                  disabled={!!processingId}
                  aria-disabled={!!processingId}
                  aria-busy={processingId === selectedProposal.id}
                  data-testid="reject-action-button"
                  className="px-4 py-2 bg-white dark:bg-slate-800 border border-red-200 dark:border-red-900/30 text-red-600 text-xs font-black rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors flex items-center gap-2 disabled:opacity-50 focus-visible:ring-2 focus-visible:outline-none"
                >
                  {processingId === selectedProposal.id ? (
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  ) : (
                    <XCircleIcon className="w-4 h-4" />
                  )}
                  {processingId === selectedProposal.id ? 'REJECTING...' : 'REJECT'}
                </button>
                <button 
                  onClick={() => handleAction(selectedProposal.id, 'approve')}
                  disabled={!!processingId}
                  aria-disabled={!!processingId}
                  aria-busy={processingId === selectedProposal.id}
                  data-testid="approve-action-button"
                  className="px-6 py-2 bg-indigo-600 text-white text-xs font-black rounded-lg hover:bg-indigo-700 shadow-lg shadow-indigo-200 dark:shadow-none transition-all flex items-center gap-2 disabled:opacity-50 focus-visible:ring-2 focus-visible:outline-none"
                >
                  {processingId === selectedProposal.id ? (
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  ) : (
                    <CheckCircleIcon className="w-4 h-4" />
                  )}
                  APPROVE & PUBLISH
                </button>
            </>
        )}
      </div>
    </div>
  );
};