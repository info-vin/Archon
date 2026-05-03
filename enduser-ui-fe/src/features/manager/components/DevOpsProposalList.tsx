import React from 'react';
import { SearchIcon } from '../../../components/Icons';

interface DevOpsProposalListProps {
    proposals: any[];
    processingId: string | null;
    handleCodeAction: (id: string, action: 'approve' | 'reject') => Promise<void>;
    handleViewDiff: (item: any) => void;
}

export const DevOpsProposalList: React.FC<DevOpsProposalListProps> = ({
    proposals, processingId, handleCodeAction, handleViewDiff
}) => {
    return (
        <div className="space-y-4">
            {proposals.map((prop: any) => (
                <div key={prop.id} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-gray-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-3">
                                <span className="text-[10px] font-black uppercase tracking-widest text-indigo-600 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full border border-indigo-100 dark:border-indigo-800/50">
                                    {prop.type} proposal
                                </span>
                                <span className="text-[10px] text-gray-400 font-mono">{new Date(prop.created_at).toLocaleString()}</span>
                            </div>
                            <p className="text-gray-800 dark:text-slate-200 font-mono text-sm bg-gray-50 dark:bg-slate-950 p-4 rounded-xl border border-gray-100 dark:border-slate-800 shadow-inner">
                                {prop.request_payload?.description || 'Infrastructure change request detected.'}
                            </p>
                        </div>
                        <div className="flex gap-3 w-full md:w-auto">
                            <button 
                                onClick={() => handleViewDiff(prop)}
                                className="p-4 bg-gray-50 dark:bg-slate-800 text-gray-600 dark:text-slate-400 rounded-2xl hover:bg-gray-100 dark:hover:bg-slate-700 transition-all border border-gray-100 dark:border-slate-700"
                                title="Inspect Code Difference"
                                aria-label="Inspect Code Difference"
                            >
                                <SearchIcon className="w-5 h-5" />
                            </button>
                            <button 
                                onClick={() => handleCodeAction(prop.id, 'reject')}
                                disabled={!!processingId}
                                className="flex-1 px-6 py-4 text-xs font-bold text-red-600 border border-red-100 rounded-2xl hover:bg-red-50 transition-all active:scale-95 min-w-[80px]"
                            >
                                REJECT
                            </button>
                            <button 
                                onClick={() => handleCodeAction(prop.id, 'approve')}
                                disabled={!!processingId}
                                className="flex-1 px-6 py-4 text-xs font-black bg-amber-500 text-white rounded-2xl shadow-lg shadow-amber-100 dark:shadow-none transition-all active:scale-95 min-w-[80px]"
                            >
                                {processingId === prop.id ? '...' : 'APPROVE'}
                            </button>
                        </div>
                    </div>
                </div>
            ))}
            {proposals.length === 0 && (
                <div className="p-12 text-center border-2 border-dashed border-gray-200 rounded-3xl text-gray-400 italic text-sm">
                    No pending code proposals. Infrastructure is stable and verified.
                </div>
            )}
        </div>
    );
};
