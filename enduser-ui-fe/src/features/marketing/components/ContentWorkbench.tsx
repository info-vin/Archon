import React, { useState, useEffect } from 'react';
import { 
  SparklesIcon, 
  SaveIcon, 
  CheckCircleIcon, 
  EyeIcon, 
  FileEditIcon, 
  ExternalLinkIcon,
  TrendingUpIcon,
  XIcon
} from '../../../components/Icons';
import { ContentSource } from './VictoryFeedList';

interface RAGRef {
  content: string;
  metadata: {
    source: string;
    [key: string]: any;
  };
}

interface ContextData {
  logs: any[];
  rag_refs: RAGRef[];
  context_summary: string;
}

interface ContentWorkbenchProps {
  activeSource: ContentSource | null;
  contextData: ContextData | null;
  isLoadingContext: boolean;
  onDraft: (topic: string, config?: any) => void;
  onGenerateImage: (title: string) => void;
  onPublish: (post: any) => void;
  onSave: () => void;
  isDrafting: boolean;
  isGeneratingImage: boolean;
  title: string;
  content: string;
  onTitleChange: (value: string) => void;
  onContentChange: (value: string) => void;
  usedPrompt?: string; // New: For Transparency
}

const INDUSTRIES = ["製造業", "高科技", "零售業", "生技醫療", "金融科技"];
const CHARTS = ["柱狀圖", "趨勢圖", "數據表格", "Sankey 圖", "漏斗圖"];
const STYLES = ["專業商務", "敘事故事", "技術深挖", "輕鬆科普"];
const LENGTHS = [
  { id: 'compact', label: '精簡 (300字)' },
  { id: 'standard', label: '標準 (800字)' },
  { id: 'deep', label: '深度報導 (1500字+)' }
];

export const ContentWorkbench: React.FC<ContentWorkbenchProps> = ({
  activeSource,
  contextData,
  isLoadingContext,
  onDraft,
  onGenerateImage,
  onPublish,
  onSave,
  isDrafting,
  isGeneratingImage,
  title,
  content,
  onTitleChange,
  onContentChange,
  usedPrompt
}) => {
  const [activeTab, setActiveTab] = useState<'context' | 'editor'>('context');
  const [showPrompt, setShowPrompt] = useState(false);
  const [showSelector, setShowSelector] = useState(false);
  
  // Advanced Config State
  const [config, setConfig] = useState({
    industry: [] as string[],
    charts: [] as string[],
    length: 'standard',
    style: [] as string[]
  });

  // Persistence Hook: Keep prompt visible if it exists
  useEffect(() => {
    if (usedPrompt) setShowPrompt(true);
  }, [usedPrompt]);

  const toggleItem = (category: 'industry' | 'charts' | 'style', item: string) => {
    setConfig(prev => ({
      ...prev,
      [category]: prev[category].includes(item)
        ? prev[category].filter(i => i !== item)
        : [...prev[category], item]
    }));
  };

  const handleDraftExecute = () => {
    if (activeSource) {
      onDraft(activeSource.title, config);
      setShowSelector(false);
    }
  };

  const getTempPromptPreview = () => {
    if (!activeSource) return "";
    const indStr = config.industry.length > 0 ? config.industry.join("與") : "通用";
    const lenStr = LENGTHS.find(l => l.id === config.length)?.label || "標準";
    const styleStr = config.style.length > 0 ? config.style.join("且") : "專業";
    const chartStr = config.charts.length > 0 ? `文中會預留 ${config.charts.join("、")} 的標記與描述。` : "";
    
    return `我將撰寫一篇針對「${indStr}」的「${lenStr}」文章。風格採取「${styleStr}」。${chartStr}`;
  };

  // BUG-026: Save Feedback
  const handleSave = () => {
    // Call parent handler to redirect
    onSave();
  };

  if (!activeSource) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-400">
        <div className="text-center font-sans">
          <EyeIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
          <p>Select a signal from the Victory Feed to start creating.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900 font-sans relative overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b flex items-center justify-between bg-white dark:bg-slate-900 z-10">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center">
            {activeSource.title}
            <span className="ml-3 px-2 py-0.5 rounded text-[10px] bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-black uppercase tracking-widest">
              Workbench
            </span>
          </h1>
          <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-tighter">Source: {activeSource.type} · Integrity: {activeSource.score}%</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button 
            onClick={handleSave}
            className="flex items-center px-4 py-2 border rounded-xl text-sm font-bold hover:bg-slate-50 transition-all dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 active:scale-95"
          >
            <SaveIcon className="w-4 h-4 mr-2 text-slate-400" />
            Save Draft
          </button>
          
          <button 
            onClick={() => onPublish({ title: title, content: content })}
            className="flex items-center px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-black transition-all shadow-lg shadow-indigo-100 dark:shadow-none active:scale-95"
          >
            <CheckCircleIcon className="w-4 h-4 mr-2" />
            Submit
          </button>
        </div>
      </div>

      {/* Main Layout Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Editor/Context */}
        <div className={`flex-1 flex flex-col transition-all duration-500 ${showPrompt && usedPrompt ? 'mr-80' : 'mr-0'}`}>
          {/* Tabs */}
          <div className="flex border-b bg-white dark:bg-slate-900">
            <button 
              onClick={() => setActiveTab('context')}
              className={`px-6 py-3 text-xs font-black uppercase tracking-widest border-b-2 transition-all ${activeTab === 'context' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'}`}
            >
              <TrendingUpIcon className="w-3.5 h-3.5 inline-block mr-2" />
              Source Context
            </button>
            <button 
              onClick={() => setActiveTab('editor')}
              className={`px-6 py-3 text-xs font-black uppercase tracking-widest border-b-2 transition-all ${activeTab === 'editor' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-600'}`}
            >
              <FileEditIcon className="w-3.5 h-3.5 inline-block mr-2" />
              AI Editor
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {activeTab === 'context' ? (
              <div className="p-8 max-w-4xl mx-auto space-y-12">
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
                      <div className="bg-slate-50 dark:bg-slate-950 p-6 rounded-2xl font-mono text-xs leading-relaxed text-slate-700 dark:text-slate-400 border dark:border-slate-800 shadow-inner">
                        {contextData?.context_summary || "No specific transcript available."}
                      </div>
                    </section>

                    <section>
                      <h3 className="text-[10px] font-black uppercase text-slate-400 mb-4 tracking-widest flex items-center gap-2">
                        <div className="w-1 h-4 bg-indigo-500 rounded-full" />
                        Librarian Knowledge Base
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {contextData?.rag_refs.map((ref, idx) => (
                          <div key={idx} className="p-4 bg-white dark:bg-slate-900 border dark:border-slate-800 rounded-2xl hover:shadow-lg transition-all group border-l-4 border-l-indigo-500/20">
                            <div className="flex justify-between items-start mb-2">
                              <span className="text-[9px] font-black text-indigo-600 uppercase tracking-tighter">REF #{idx + 1}</span>
                              <ExternalLinkIcon className="w-3 h-3 text-slate-300 group-hover:text-indigo-500 cursor-pointer" />
                            </div>
                            <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-4 leading-relaxed italic">"{ref.content}"</p>
                            <div className="mt-3 text-[9px] font-bold text-slate-400 truncate">Source: {ref.metadata.source}</div>
                          </div>
                        ))}
                      </div>
                    </section>


                  </>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col relative">
                {/* Editor ToolBar */}
                <div className="px-6 py-3 bg-slate-50/50 dark:bg-slate-800/30 border-b flex items-center gap-3 relative z-30">
                  <button 
                    onClick={() => setShowSelector(true)}
                    disabled={isDrafting}
                    className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-700 hover:shadow-lg transition-all disabled:opacity-50 active:scale-95 shadow-md shadow-indigo-100 dark:shadow-none"
                  >
                    <SparklesIcon className={`w-3.5 h-3.5 mr-2 ${isDrafting ? 'animate-spin' : ''}`} />
                    {isDrafting ? 'Synthesizing...' : 'Magic Draft'}
                  </button>
                  <button 
                    onClick={() => onGenerateImage(title || activeSource.title)}
                    disabled={isGeneratingImage}
                    className="flex items-center px-4 py-2 bg-white dark:bg-slate-800 border dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest hover:shadow-md transition-all disabled:opacity-50 active:scale-95"
                  >
                    <EyeIcon className={`w-3.5 h-3.5 mr-2 ${isGeneratingImage ? 'animate-bounce' : ''}`} />
                    {isGeneratingImage ? 'Generating...' : 'AI Image'}
                  </button>
                  
                  <div className="flex-1" />
                  
                  <button 
                     onClick={() => {
                         if (!usedPrompt) {
                             alert("No prompt data available yet. Please use Magic Draft to generate content first.");
                             return;
                         }
                         setShowPrompt(!showPrompt);
                     }}
                     className={`flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest transition-all hover:scale-105 active:scale-95 ${
                         showPrompt 
                           ? 'text-indigo-600' 
                           : 'text-slate-400 hover:text-indigo-600'
                     }`}
                  >
                     <SparklesIcon className="w-3.5 h-3.5" />
                     Prompt Inspector
                  </button>
                </div>

                {/* Advanced Prompt Selector Modal */}
                {showSelector && (
                  <div className="absolute inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-white dark:bg-slate-900 w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden flex flex-col border dark:border-slate-800 animate-in zoom-in-95 duration-200">
                      <div className="px-8 py-6 border-b dark:border-slate-800 flex justify-between items-center bg-slate-50/50 dark:bg-slate-800/20">
                        <div>
                          <h2 className="text-lg font-black text-slate-900 dark:text-white flex items-center gap-2">
                            <SparklesIcon className="w-5 h-5 text-indigo-600" />
                            Magic Draft Configuration
                          </h2>
                          <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mt-1">Configure your AI writing partner</p>
                        </div>
                        <button onClick={() => setShowSelector(false)} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors">
                          <XIcon className="w-5 h-5 text-slate-400" />
                        </button>
                      </div>

                      <div className="flex-1 p-8 space-y-8 overflow-y-auto custom-scrollbar">
                        {/* Industry */}
                        <section>
                          <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 block">Industry Category (Multi-select)</label>
                          <div className="flex flex-wrap gap-2">
                            {INDUSTRIES.map(ind => (
                              <button
                                key={ind}
                                onClick={() => toggleItem('industry', ind)}
                                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                                  config.industry.includes(ind)
                                    ? 'bg-indigo-600 border-indigo-600 text-white shadow-md shadow-indigo-100'
                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-indigo-300'
                                }`}
                              >
                                {ind}
                              </button>
                            ))}
                          </div>
                        </section>

                        {/* Charts */}
                        <section>
                          <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 block">Visual Insights & Charts (Multi-select)</label>
                          <div className="flex flex-wrap gap-2">
                            {CHARTS.map(chart => (
                              <button
                                key={chart}
                                onClick={() => toggleItem('charts', chart)}
                                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all border ${
                                  config.charts.includes(chart)
                                    ? 'bg-amber-500 border-amber-500 text-white shadow-md shadow-amber-100'
                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-amber-300'
                                }`}
                              >
                                {chart}
                              </button>
                            ))}
                          </div>
                        </section>

                        {/* Length */}
                        <section>
                          <label className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-3 block">Article Length (Single-select)</label>
                          <div className="flex gap-2">
                            {LENGTHS.map(len => (
                              <button
                                key={len.id}
                                onClick={() => setConfig({...config, length: len.id})}
                                className={`flex-1 px-4 py-3 rounded-xl text-xs font-bold transition-all border text-center ${
                                  config.length === len.id
                                    ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 border-slate-900 dark:border-white'
                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400'
                                }`}
                              >
                                {len.label}
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
                                    ? 'bg-emerald-600 border-emerald-600 text-white shadow-md shadow-emerald-100'
                                    : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-emerald-300'
                                }`}
                              >
                                {s}
                              </button>
                            ))}
                          </div>
                        </section>
                      </div>

                      <div className="p-8 bg-slate-50 dark:bg-slate-950 border-t dark:border-slate-800 space-y-6">
                        <div className="p-4 bg-white dark:bg-slate-900 border dark:border-slate-800 rounded-2xl shadow-inner">
                          <p className="text-[10px] font-black uppercase tracking-widest text-indigo-600 mb-2">Temp Prompt Preview</p>
                          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed italic">
                            {getTempPromptPreview()}
                          </p>
                        </div>
                        
                        <div className="flex gap-4">
                          <button 
                            onClick={() => setShowSelector(false)}
                            className="flex-1 py-4 text-xs font-black uppercase tracking-widest text-slate-400 hover:text-slate-600 transition-colors"
                          >
                            Cancel
                          </button>
                          <button 
                            onClick={handleDraftExecute}
                            className="flex-[2] py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-xs font-black uppercase tracking-widest shadow-xl shadow-indigo-100 dark:shadow-none transition-all active:scale-95"
                          >
                            Execute Synthesis (EXEC)
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Markdown Editor */}
                <div className="flex-1 p-8 md:p-12 max-w-4xl mx-auto w-full custom-scrollbar overflow-y-auto relative">
                  <input 
                    type="text"
                    placeholder="Article Title..."
                    value={title}
                    onChange={(e) => onTitleChange(e.target.value)}
                    className="w-full text-3xl font-black mb-8 outline-none bg-transparent dark:text-white placeholder:text-slate-200 dark:placeholder:text-slate-800 border-none"
                  />
                  <textarea 
                    placeholder="Start typing or use Magic Draft to let MarketBot assist you..."
                    value={content}
                    onChange={(e) => onContentChange(e.target.value)}
                    className="w-full h-full min-h-[60vh] outline-none bg-transparent dark:text-slate-300 resize-none leading-relaxed text-lg border-none font-sans"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Persistent Prompt Inspector (Sidebar Overlay) */}
        {showPrompt && usedPrompt && (
          <aside className="w-96 border-l dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl absolute right-0 top-0 bottom-0 z-50 shadow-2xl animate-in slide-in-from-right duration-300 flex flex-col">
            <div className="p-4 border-b dark:border-slate-800 flex items-center justify-between bg-indigo-50/50 dark:bg-indigo-900/10">
                <span className="text-[10px] font-black uppercase tracking-widest text-indigo-600 flex items-center gap-2">
                    <SparklesIcon className="w-3 h-3" />
                    AI Prompt Inspector
                </span>
                <button onClick={() => setShowPrompt(false)} className="p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors">
                    <XIcon className="w-4 h-4 text-slate-400" />
                </button>
            </div>
            <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
                <div className="bg-white dark:bg-slate-950 p-4 rounded-xl border dark:border-slate-800 shadow-inner">
                    <pre className="text-[10px] font-mono text-slate-600 dark:text-slate-400 whitespace-pre-wrap leading-relaxed">
                        {usedPrompt}
                    </pre>
                </div>
                <div className="mt-6 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800/50">
                    <p className="text-[10px] text-indigo-700 dark:text-indigo-300 leading-tight">
                        <SparklesIcon className="w-3 h-3 inline mr-1" />
                        This prompt was used by **MarketBot** to generate the current draft based on your selected context.
                    </p>
                </div>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};
