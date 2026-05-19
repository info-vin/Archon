import React from 'react';
import { useApprovalInbox } from '../features/manager/hooks/useApprovalInbox';
import { ApprovalSidebarList } from '../features/manager/components/ApprovalSidebarList';
import { ApprovalActionHeader } from '../features/manager/components/ApprovalActionHeader';
import { PolymorphicPreview } from '../features/manager/components/PolymorphicPreview';
import { 
  ShieldCheckIcon,
  ArrowPathIcon,
  SparklesIcon,
  FileTextIcon as DocumentTextIcon,
  XCircleIcon
} from '../components/Icons';

const ApprovalsPage: React.FC = () => {
  const {
      proposals,
      loading,
      error,
      actionError,
      selectedId,
      setSelectedId,
      selectedProposal,
      processingId,
      showRejectInput,
      setShowRejectInput,
      rejectReason,
      setRejectReason,
      generatingReason,
      fetchData,
      handleAction,
      handleGenerateAIReason
  } = useApprovalInbox();

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-gray-50 dark:bg-slate-950 overflow-hidden font-sans font-inter leading-relaxed text-base">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
            <ShieldCheckIcon className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
            Unified Approvals
          </h1>
          <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mt-1">
            Gatekeeper Console • {proposals.length} Pending Actions
          </p>
        </div>
        <button
          onClick={fetchData}
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full transition-colors"
          data-testid="refresh-proposals-btn"
          aria-label="Refresh proposals"
        >          <ArrowPathIcon className={`w-5 h-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar List */}
        <div data-testid="approval-inbox-list" className="w-1/3 border-r border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-y-auto">
           {error ? (
             <div className="p-8 text-center" data-testid="error-msg">
               <div className="inline-block p-4 bg-red-50 dark:bg-red-900/20 rounded-full mb-4">
                 <XCircleIcon className="w-8 h-8 text-red-500" />
               </div>
               <h3 className="text-sm font-bold text-gray-800 dark:text-gray-200">Failed to load approvals</h3>
               <p className="text-xs text-gray-500 mt-1">{error}</p>
               <button 
                 onClick={fetchData}
                 className="mt-4 px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 transition-colors"
               >
                 Retry
               </button>
             </div>
           ) : (
             <ApprovalSidebarList 
                proposals={proposals} 
                loading={loading} 
                selectedId={selectedId} 
                onSelect={(id) => { setSelectedId(id); setShowRejectInput(false); }} 
             />
           )}
        </div>

        {/* Detail Pane */}
        <div className="flex-1 overflow-y-auto p-10 md:p-14">
          {selectedProposal ? (
            <div className="max-w-5xl mx-auto shadow-sm shadow-gray-200 dark:shadow-none flex flex-col relative">
              {/* Action Failure Banner */}
              {actionError && (
                <div data-testid="action-error-banner" className="p-4 bg-red-50 border-x border-t border-red-200 text-red-800 text-sm font-bold flex justify-between items-center rounded-t-2xl animate-in fade-in">
                  <div className="flex items-center gap-2">
                    <XCircleIcon className="w-5 h-5 text-red-500" />
                    <span>{actionError}</span>
                  </div>
                </div>
              )}

              {/* Proposal Meta & Actions */}
              <ApprovalActionHeader 
                 selectedProposal={selectedProposal}
                 showRejectInput={showRejectInput}
                 setShowRejectInput={setShowRejectInput}
                 processingId={processingId}
                 handleAction={handleAction}
                 rejectReason={rejectReason}
              />
                
              {/* AI Rejection Flow UI */}
              {showRejectInput && selectedProposal.is_marketing && (
                  <div className="p-4 bg-rose-50 border-x border-rose-200 animate-in fade-in slide-in-from-top-4">
                      <div className="flex justify-between items-center mb-2">
                          <label className="text-xs font-bold text-rose-800 uppercase tracking-widest">Rejection Reason</label>
                          <button 
                              onClick={handleGenerateAIReason}
                              disabled={generatingReason}
                              data-testid="generate-ai-reason-btn"
                              className="text-xs font-bold text-indigo-600 flex items-center gap-1 hover:text-indigo-800 disabled:opacity-50"
                          >
                              {generatingReason ? <ArrowPathIcon className="w-3 h-3 animate-spin" /> : <SparklesIcon className="w-3 h-3" />}
                              Generate AI Reason
                          </button>
                      </div>
                      <textarea
                          data-testid="reject-reason-input"
                          value={rejectReason}
                          onChange={(e) => setRejectReason(e.target.value)}
                          placeholder="Explain why this content is being rejected..."
                          className="w-full p-3 rounded-lg border border-rose-200 text-sm focus:ring-2 focus:ring-rose-500 focus:border-rose-500 outline-none resize-none min-h-[100px]"
                      />
                      <p className="text-[10px] text-rose-600 mt-2 italic">
                          This feedback will be stored in the Librarian's knowledge base to prevent the AI from making the same stylistic mistakes in the future.
                      </p>
                  </div>
              )}

              {/* Content Preview (Polymorphic) */}
              <PolymorphicPreview selectedProposal={selectedProposal} />
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
              <div className="p-4 bg-gray-100 dark:bg-slate-900 rounded-full">
                <DocumentTextIcon className="w-8 h-8" />
              </div>
              <p data-testid="empty-selection-msg" className="italic text-sm">Select a contribution to begin the audit process.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApprovalsPage;