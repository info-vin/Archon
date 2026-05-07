import React from 'react';
import { ChangeType } from '@/types';
import DiffViewer from '@/components/DiffViewer';
import ReactMarkdown from 'react-markdown';
import { CommandLineIcon, XCircleIcon } from '@/components/Icons';
import { UnifiedProposal } from '../hooks/useApprovalInbox';

interface PolymorphicPreviewProps {
  selectedProposal: UnifiedProposal;
}

export const PolymorphicPreview: React.FC<PolymorphicPreviewProps> = ({ selectedProposal }) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-b-2xl border-x border-b border-gray-200 dark:border-slate-800 overflow-hidden">
      <div className="px-8 py-5 border-b border-t border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-800/50">
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
        ) : selectedProposal.type === ChangeType.BLOG ? (
          <div className="p-8">
             <div className="prose prose-sm max-w-none text-gray-800">
               <ReactMarkdown>
                 {selectedProposal.marketing_content || '*No content available*'}
               </ReactMarkdown>
             </div>
          </div>
        ) : (
          <div className="p-8 text-gray-500 italic">Preview not available for this type.</div>
        )}
      </div>

      {selectedProposal.type === ChangeType.SHELL && (
        <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border-t border-amber-200 dark:border-amber-900/30 flex items-start gap-3 animate-pulse">
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
  );
};