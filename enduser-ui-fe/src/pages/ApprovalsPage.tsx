import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ProposedChange, ChangeType } from '../types';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  CodeBracketIcon, 
  FileTextIcon as DocumentTextIcon, 
  CommandLineIcon,
  ClockIcon,
  ChevronRightIcon,
  ArrowPathIcon,
  UserIcon,
  SparklesIcon
} from '../components/Icons';
import DiffViewer from '../components/DiffViewer';
import ReactMarkdown from 'react-markdown';

const ApprovalsPage: React.FC = () => {
  const [proposals, setProposals] = useState<ProposedChange[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await api.getPendingChanges();
      setProposals(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch proposals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const selectedProposal = proposals.find(p => p.id === selectedId);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    setProcessingId(id);
    try {
      if (action === 'approve') {
        await api.approveChange(id);
      } else {
        await api.rejectChange(id);
      }
      // Remove from list or refresh
      setProposals(prev => prev.filter(p => p.id !== id));
      if (selectedId === id) {
        setSelectedId(null);
      }
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const getIcon = (type: ChangeType) => {
    switch (type) {
      case ChangeType.FILE: return <CodeBracketIcon className="w-5 h-5 text-blue-500" />;
      case ChangeType.SHELL: return <CommandLineIcon className="w-5 h-5 text-gray-700" />;
      default: return <DocumentTextIcon className="w-5 h-5 text-indigo-500" />;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] bg-gray-50 dark:bg-slate-950 overflow-hidden">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-black text-gray-900 dark:text-white flex items-center gap-2">
            <SparklesIcon className="w-6 h-6 text-indigo-600" />
            Unified Approval Inbox
          </h1>
          <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mt-1">
            Gatekeeper Console • {proposals.length} Pending Actions
          </p>
        </div>
        <button 
          onClick={fetchData}
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full transition-colors"
          aria-label="Refresh proposals"
        >
          <ArrowPathIcon className={`w-5 h-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar List */}
        <div className="w-1/3 border-r border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-y-auto">
          {loading && proposals.length === 0 ? (
            <div className="p-8 text-center text-gray-400 italic text-sm">Loading proposals...</div>
          ) : proposals.length === 0 ? (
            <div className="p-12 text-center">
              <div className="inline-block p-4 bg-green-50 dark:bg-green-900/20 rounded-full mb-4">
                <CheckCircleIcon className="w-8 h-8 text-green-500" />
              </div>
              <h3 className="text-sm font-bold text-gray-800 dark:text-gray-200">Inbox Zero!</h3>
              <p className="text-xs text-gray-500 mt-1">All AI changes have been reviewed.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-slate-800">
              {proposals.map((item) => (
                <div 
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  className={`p-4 cursor-pointer transition-all hover:bg-indigo-50/30 dark:hover:bg-indigo-900/10 ${
                    selectedId === item.id ? 'bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-600' : 'border-l-4 border-transparent'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">{getIcon(item.type)}</div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-bold text-gray-900 dark:text-white truncate">
                        {item.change_summary || (item.request_payload?.file_path ? `Update ${item.request_payload.file_path.split('/').pop()}` : 'Proposed Change')}
                      </h4>
                      <p className="text-[10px] text-gray-500 mt-0.5 flex items-center gap-1">
                        <UserIcon className="w-3 h-3" /> {item.type.toUpperCase()} • <ClockIcon className="w-3 h-3" /> {new Date(item.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <ChevronRightIcon className="w-4 h-4 text-gray-300" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detail Pane */}
        <div className="flex-1 overflow-y-auto p-8">
          {selectedProposal ? (
            <div className="max-w-5xl mx-auto space-y-6">
              {/* Proposal Meta */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-gray-200 dark:border-slate-800 shadow-sm">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-[10px] font-black rounded uppercase tracking-widest">
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
                    <button 
                      onClick={() => handleAction(selectedProposal.id, 'reject')}
                      disabled={!!processingId}
                      className="px-4 py-2 bg-white dark:bg-slate-800 border border-red-200 dark:border-red-900/30 text-red-600 text-xs font-black rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors flex items-center gap-2"
                    >
                      <XCircleIcon className="w-4 h-4" /> REJECT
                    </button>
                    <button 
                      onClick={() => handleAction(selectedProposal.id, 'approve')}
                      disabled={!!processingId}
                      className="px-6 py-2 bg-indigo-600 text-white text-xs font-black rounded-lg hover:bg-indigo-700 shadow-lg shadow-indigo-200 dark:shadow-none transition-all flex items-center gap-2"
                    >
                      {processingId === selectedProposal.id ? (
                        <ArrowPathIcon className="w-4 h-4 animate-spin" />
                      ) : (
                        <CheckCircleIcon className="w-4 h-4" />
                      )}
                      APPROVE & EXECUTE
                    </button>
                  </div>
                </div>
              </div>

              {/* Content Preview */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-gray-200 dark:border-slate-800 overflow-hidden shadow-sm">
                <div className="px-6 py-3 border-b border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-800/50">
                  <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Inspection Layer</span>
                </div>
                
                <div className="p-0">
                  {selectedProposal.type === ChangeType.FILE && selectedProposal.request_payload?.new_content ? (
                    <div className="font-mono text-sm overflow-x-auto">
                      <DiffViewer 
                        oldCode={selectedProposal.request_payload.old_content || ''} 
                        newCode={selectedProposal.request_payload.new_content} 
                        splitView={true}
                      />
                    </div>
                  ) : selectedProposal.type === ChangeType.SHELL ? (
                    <div className="p-6 bg-slate-950 text-green-400 font-mono text-sm">
                      <div className="flex items-center gap-2 mb-2 text-slate-500">
                        <CommandLineIcon className="w-4 h-4" />
                        <span>Proposed Command</span>
                      </div>
                      <div className="bg-slate-900 p-4 rounded border border-slate-800">
                        $ {selectedProposal.request_payload?.command || 'No command provided'}
                      </div>
                    </div>
                  ) : (
                    <div className="p-8 prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>
                        {selectedProposal.request_payload?.new_content || 'No content preview available.'}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              </div>

              {/* Security Warning for Shell */}
              {selectedProposal.type === ChangeType.SHELL && (
                <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-900/30 rounded-xl flex items-start gap-3 animate-pulse">
                  <XCircleIcon className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="text-xs font-bold text-amber-800 dark:text-amber-400 uppercase tracking-wider">High Risk Action Detected</h5>
                    <p className="text-[11px] text-amber-700 dark:text-amber-500 mt-1">
                      This is a raw shell command. Approving this will execute code directly on the system. Agent-led automation is powerful but requires human vigilance.
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
              <div className="p-4 bg-gray-100 dark:bg-slate-900 rounded-full">
                <DocumentTextIcon className="w-8 h-8" />
              </div>
              <p className="italic text-sm">Select a contribution to begin the audit process.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApprovalsPage;
