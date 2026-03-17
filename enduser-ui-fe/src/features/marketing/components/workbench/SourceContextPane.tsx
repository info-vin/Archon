import React from 'react';
import { SparklesIcon, ExternalLinkIcon } from '@/components/Icons';
import { ContextData } from './types';

interface SourceContextPaneProps {
  isContextOpen: boolean;
  isLoadingContext: boolean;
  contextData: ContextData | null;
  onToggleContext: () => void;
}

export const SourceContextPane: React.FC<SourceContextPaneProps> = ({
  isContextOpen,
  isLoadingContext,
  contextData,
  onToggleContext
}) => {
  return (
    <>
      {/* Left Pane: Source Context (Collapsible) */}
      <div className={`border-r dark:border-slate-800 bg-slate-50/30 dark:bg-slate-900/30 transition-all duration-500 ease-in-out overflow-y-auto custom-scrollbar ${isContextOpen ? 'w-1/3 opacity-100' : 'w-0 opacity-0 pointer-events-none'}`}>
        <div className="p-8 space-y-10 min-w-[320px]">
          {isLoadingContext ? (
            <div className="py-20 text-center animate-pulse text-slate-400">
              <SparklesIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p className="font-black uppercase text-[10px] tracking-widest">MarketBot is gathering intelligence...</p>
            </div>
          ) : (
            <>
              <section>
                <h3 className="text-[10px] font-black uppercase text-slate-400 mb-4 tracking-widest flex items-center gap-2">
                  <div className="w-1 h-4 bg-indigo-500 rounded-full" />
                  Victory Signal Intelligence
                </h3>
                <div className="bg-white dark:bg-slate-950 p-6 rounded-2xl font-mono text-xs leading-relaxed text-slate-700 dark:text-slate-400 border dark:border-slate-800 shadow-sm">
                  {contextData?.context_summary || "No specific transcript available."}
                </div>
              </section>

              <section>
                <h3 className="text-[10px] font-black uppercase text-slate-400 mb-4 tracking-widest flex items-center gap-2">
                  <div className="w-1 h-4 bg-indigo-500 rounded-full" />
                  Librarian Knowledge Base
                </h3>
                <div className="space-y-4">
                  {contextData?.rag_refs.map((ref, idx) => (
                    <div key={idx} className="p-4 bg-white dark:bg-slate-900 border dark:border-slate-800 rounded-2xl hover:shadow-md transition-all group border-l-4 border-l-indigo-500/20">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-[9px] font-black text-indigo-600 uppercase tracking-tighter">REF #{idx + 1}</span>
                        <ExternalLinkIcon className="w-3 h-3 text-slate-300 group-hover:text-indigo-500 cursor-pointer" />
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-6 leading-relaxed italic">"{ref.content}"</p>
                      <div className="mt-3 text-[9px] font-bold text-slate-400 truncate">Source: {ref.metadata.source}</div>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
        </div>
      </div>

      {/* Floating Sidebar Toggle [2] - Local Context Control */}
      <button
        onClick={onToggleContext}
        className={`absolute bottom-10 z-40 p-2 bg-white dark:bg-slate-800 border dark:border-slate-700 rounded-r-lg shadow-md transition-all duration-500 hover:w-8 group ${
            isContextOpen ? 'left-[33.333333%]' : 'left-0'
        }`}
        title={isContextOpen ? "Collapse Context" : "Expand Context"}
      >
        <div className={`w-1 h-4 bg-slate-300 dark:bg-slate-600 rounded-full group-hover:bg-indigo-500 transition-colors ${!isContextOpen && 'bg-indigo-400'}`} />
      </button>
    </>
  );
};
