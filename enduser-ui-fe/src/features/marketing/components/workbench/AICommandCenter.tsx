import React from 'react';
import { SparklesIcon, XIcon, SettingsIcon, EyeIcon, ExternalLinkIcon, CheckCircleIcon } from '@/components/Icons';
import { INDUSTRIES, CHARTS, STYLES, LENGTHS } from './useWorkbenchLogic';

interface AICommandCenterProps {
  promptCenterOpen: boolean;
  setPromptCenterOpen: (open: boolean) => void;
  promptTab: 'config' | 'inspect';
  setPromptTab: (tab: 'config' | 'inspect') => void;
  config: {
    industry: string[];
    charts: string[];
    length: string;
    style: string[];
    enableWebSearch: boolean;
  };
  setConfig: React.Dispatch<React.SetStateAction<any>>;
  toggleItem: (category: 'industry' | 'charts' | 'style', item: string) => void;
  usedPrompt?: string;
  getTempPromptPreview: () => string;
  handleDraftExecute: () => void;
  isDrafting: boolean;
}

export const AICommandCenter: React.FC<AICommandCenterProps> = ({
  promptCenterOpen,
  setPromptCenterOpen,
  promptTab,
  setPromptTab,
  config,
  setConfig,
  toggleItem,
  usedPrompt,
  getTempPromptPreview,
  handleDraftExecute,
  isDrafting
}) => {
  if (!promptCenterOpen) return null;

  return (
    <aside className="fixed inset-y-0 right-0 w-[450px] bg-white/95 dark:bg-slate-900/95 backdrop-blur-2xl shadow-[-20px_0_50px_rgba(0,0,0,0.1)] z-[60] animate-in slide-in-from-right duration-300 flex flex-col border-l dark:border-slate-800">
      <div className="p-6 border-b dark:border-slate-800 flex items-center justify-between bg-indigo-50/50 dark:bg-indigo-900/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600 rounded-xl">
            <SparklesIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-900 dark:text-white">AI Command Center</h2>
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-tighter">Unified Prompt & Logic Console</p>
          </div>
        </div>
        <button onClick={() => setPromptCenterOpen(false)} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors" aria-label="Close AI Command Center" title="Close AI Command Center">
          <XIcon className="w-5 h-5 text-slate-400" />
        </button>
      </div>

      {/* Center Tabs */}
      <div className="flex border-b dark:border-slate-800">
        <button
          onClick={() => setPromptTab('config')}
          className={`flex-1 py-4 text-[10px] font-black uppercase tracking-widest border-b-2 transition-all ${promptTab === 'config' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/30' : 'border-transparent text-slate-400 hover:text-slate-600'}`}
        >
          <SettingsIcon className="w-3.5 h-3.5 inline mr-2" />
          Synthesis Config
        </button>
        <button
          onClick={() => setPromptTab('inspect')}
          className={`flex-1 py-4 text-[10px] font-black uppercase tracking-widest border-b-2 transition-all ${promptTab === 'inspect' ? 'border-indigo-600 text-indigo-600 bg-indigo-50/30' : 'border-transparent text-slate-400 hover:text-slate-600'}`}
        >
          <EyeIcon className="w-3.5 h-3.5 inline mr-2" />
          Inspect Logic
        </button>
      </div>

      <div className="flex-1 min-w-0 overflow-y-auto p-8 custom-scrollbar space-y-8">
        {promptTab === 'config' ? (
          <div className="space-y-8">
            {/* Industry */}
            <section>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 block">Industry Domain (Multi-select)</label>
              <div className="flex flex-wrap gap-2">
                {INDUSTRIES.map(ind => (
                  <button
                    key={ind}
                    onClick={() => toggleItem('industry', ind)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                      config.industry.includes(ind)
                        ? 'bg-indigo-600 border-indigo-600 text-white'
                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {ind}
                  </button>
                ))}
              </div>
            </section>

            {/* Charts */}
            <section>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 block">Visual Strategy (Multi-select)</label>
              <div className="flex flex-wrap gap-2">
                {CHARTS.map(chart => (
                  <button
                    key={chart}
                    onClick={() => toggleItem('charts', chart)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                      config.charts.includes(chart)
                        ? 'bg-amber-500 border-amber-500 text-white'
                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {chart}
                  </button>
                ))}
              </div>
            </section>

            {/* Length */}
            <section>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 block">Article Depth (Single-select)</label>
              <div className="flex flex-col gap-2">
                {LENGTHS.map(len => (
                  <button
                    key={len.id}
                    onClick={() => setConfig({...config, length: len.id})}
                    className={`px-4 py-3 rounded-xl text-xs font-bold transition-all border text-left flex justify-between items-center ${
                      config.length === len.id
                        ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 border-slate-900 dark:border-white'
                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {len.label}
                    {config.length === len.id && <CheckCircleIcon className="w-4 h-4" />}
                  </button>
                ))}
              </div>
            </section>

            {/* Style */}
            <section>
              <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 block">Presentation Style (Multi-select)</label>
              <div className="flex flex-wrap gap-2">
                {STYLES.map(s => (
                  <button
                    key={s}
                    onClick={() => toggleItem('style', s)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                      config.style.includes(s)
                        ? 'bg-emerald-600 border-emerald-600 text-white'
                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </section>

            {/* Web Research Toggle */}
            <section className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-2xl border border-blue-100 dark:border-blue-800 flex items-center justify-between">
                <div>
                    <h4 className="text-xs font-black text-blue-700 dark:text-blue-300 flex items-center gap-2">
                        <ExternalLinkIcon className="w-3.5 h-3.5" />
                        Google Search Grounding
                    </h4>
                    <p className="text-[10px] text-blue-600/80 dark:text-blue-400 mt-1">Enrich draft with live market intelligence.</p>
                </div>
                <button
                    onClick={() => setConfig({...config, enableWebSearch: !config.enableWebSearch})}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${config.enableWebSearch ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-700'}`}
                    aria-label="Toggle Google Search Grounding"
                >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${config.enableWebSearch ? 'translate-x-6' : 'translate-x-1'}`} />
                </button>
            </section>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-slate-50 dark:bg-slate-950 p-6 rounded-2xl border dark:border-slate-800 shadow-inner">
              <p className="text-[10px] font-black uppercase tracking-widest text-indigo-600 mb-4 flex items-center gap-2">
                <SparklesIcon className="w-3 h-3" />
                What AI Saw (Used Prompt)
              </p>
              {usedPrompt ? (
                <pre className="text-[11px] font-mono text-slate-600 dark:text-slate-400 whitespace-pre-wrap leading-relaxed">
                  {usedPrompt}
                </pre>
              ) : (
                <div className="py-12 text-center text-slate-400 italic text-xs">
                  No synthesis has been performed yet.
                </div>
              )}
            </div>
            <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800/50">
                <p className="text-[10px] text-indigo-700 dark:text-indigo-300 leading-tight">
                    Use this view to verify if Alice's custom requirements or RAG contexts were correctly mapped into the AI instructions.
                </p>
            </div>
          </div>
        )}
      </div>

      <div className="p-8 bg-slate-50 dark:bg-slate-950 border-t dark:border-slate-800 space-y-6 shrink-0">
        {promptTab === 'config' && (
          <div className="p-4 bg-white dark:bg-slate-900 border dark:border-slate-800 rounded-2xl shadow-inner">
            <p className="text-[10px] font-black uppercase tracking-widest text-indigo-600 mb-2">Synthesis Logic Preview</p>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed italic line-clamp-2">
              {getTempPromptPreview()}
            </p>
          </div>
        )}

        <button
          onClick={handleDraftExecute}
          disabled={isDrafting}
          className="w-full py-5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-xs font-black uppercase tracking-widest shadow-2xl shadow-indigo-200 dark:shadow-none transition-all active:scale-95 flex items-center justify-center gap-3 disabled:opacity-50"
        >
          {isDrafting ? (
            <>
              <SparklesIcon className="w-4 h-4 animate-spin" />
              Synthesizing...
            </>
          ) : (
            <>
              <SparklesIcon className="w-4 h-4" />
              Run Magic Synthesis (EXEC)
            </>
          )}
        </button>
      </div>
    </aside>
  );
};
