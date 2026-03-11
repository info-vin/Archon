import React, { useState, useEffect } from 'react';
import { 
  SparklesIcon, 
  SaveIcon, 
  CheckCircleIcon, 
  EyeIcon, 
  ExternalLinkIcon,
  XIcon,
  RefreshCwIcon,
  SettingsIcon,
  FileEditIcon
} from '@/components/Icons';
import { ContentSource } from './VictoryFeedList';
import { useNavigate } from 'react-router-dom';

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
  usedPrompt?: string; 
  feedback?: string; // GAP-023: Instructions from Charlie
  aiScore?: number; // AI Quality Metric
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
  usedPrompt,
  feedback,
  aiScore
}) => {
  const [isContextOpen, setIsContextOpen] = useState(true);
  const [promptCenterOpen, setPromptCenterOpen] = useState(false);
  const [promptTab, setPromptTab] = useState<'config' | 'inspect'>('config');
  const navigate = useNavigate();
  
  // Advanced Config State (Refactored for Center)
  const [config, setConfig] = useState({
    industry: [] as string[],
    charts: [] as string[],
    length: 'standard',
    style: [] as string[],
    enableWebSearch: false
  });

  // Automatically switch to 'inspect' tab when a new prompt is received
  useEffect(() => {
    if (usedPrompt) setPromptTab('inspect');
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
      onDraft(activeSource.title, {
        ...config,
        enable_web_research: config.enableWebSearch
      });
      // Keep panel open to show feedback if needed, or close based on UX
    }
  };

  const getTempPromptPreview = () => {
    if (!activeSource) return "";
    const indStr = config.industry.length > 0 ? config.industry.join("與") : "通用";
    const lenStr = LENGTHS.find(l => l.id === config.length)?.label || "標準";
    const styleStr = config.style.length > 0 ? config.style.join("且") : "專業";
    const chartStr = config.charts.length > 0 ? `預留 ${config.charts.join("、")}。` : "";
    const searchStr = config.enableWebSearch ? "結合 Google 搜尋。" : "";
    
    return `針對「${indStr}」的「${lenStr}」文章。風格「${styleStr}」。${chartStr}${searchStr}`;
  };

  // Helper to extract image from content for Visual Header
  const getPreviewImage = () => {
    // If we have an explicit image from nana-banana, it might be in state
    // But since it's injected into markdown, we can also parse it.
    const match = content.match(/!\[.*?\]\((.*?)\)/);
    return match ? match[1] : null;
  };

  // BUG-026: Save Feedback
  const handleSave = () => {
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

  const previewUrl = getPreviewImage();

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900 font-sans relative overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b flex items-center justify-between bg-white dark:bg-slate-900 z-10">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center">
              {activeSource.title}
              <span className="ml-3 px-2 py-0.5 rounded text-[10px] bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-black uppercase tracking-widest">
                Workbench
              </span>
            </h1>
            <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-tighter">Source: {activeSource.type} · Integrity: {activeSource.score}%</p>
          </div>
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

      {/* Visual Feedback Banner (Charlie's Instructions) */}
      {(feedback || (aiScore !== undefined && aiScore < 100)) && (
        <div className="bg-red-50 dark:bg-red-900/20 border-b border-red-100 dark:border-red-900/30 px-6 py-3 flex items-start gap-4 animate-in slide-in-from-top duration-300">
            <div className="flex flex-col gap-1.5 shrink-0">
                <div className="px-2 py-0.5 bg-red-100 dark:bg-red-800 rounded text-[10px] font-black text-red-600 dark:text-red-200 uppercase tracking-tighter text-center">
                    Signal
                </div>
                {aiScore !== undefined && (
                    <div className={`px-2 py-0.5 rounded text-[10px] font-black text-white text-center ${
                        aiScore >= 80 ? 'bg-green-500' : aiScore >= 60 ? 'bg-amber-500' : 'bg-red-600'
                    }`}>
                        AI: {aiScore}
                    </div>
                )}
            </div>
            <div className="flex-1">
                <p className="text-[10px] font-black text-red-800 dark:text-red-200 uppercase tracking-widest mb-1 opacity-70">
                    Charlie's Command Logic
                </p>
                <p className="text-sm text-red-900 dark:text-red-100 leading-relaxed font-bold italic">
                    "{feedback}"
                </p>
            </div>
        </div>
      )}

      {/* Main Layout Area: Split View */}
      <div className="flex-1 flex overflow-hidden relative">
        
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
            onClick={() => setIsContextOpen(!isContextOpen)}
            className={`absolute bottom-10 z-40 p-2 bg-white dark:bg-slate-800 border dark:border-slate-700 rounded-r-lg shadow-md transition-all duration-500 hover:w-8 group ${
                isContextOpen ? 'left-[33.333333%]' : 'left-0'
            }`}
            title={isContextOpen ? "Collapse Context" : "Expand Context"}
        >
            <div className={`w-1 h-4 bg-slate-300 dark:bg-slate-600 rounded-full group-hover:bg-indigo-500 transition-colors ${!isContextOpen && 'bg-indigo-400'}`} />
        </button>

        {/* Right Pane: Editor战場 */}
        <div className="flex-1 flex flex-col relative bg-white dark:bg-slate-900 overflow-y-auto custom-scrollbar">
          
          {/* GAP-023: Charlie's Rejection Feedback Banner */}
          {activeSource && (activeSource as any).review_notes && (
            <div className="mx-8 mt-8 p-6 bg-red-50 dark:bg-red-900/20 border-2 border-red-100 dark:border-red-900/30 rounded-[2rem] shadow-sm animate-in slide-in-from-top duration-500">
                <div className="flex items-start gap-4">
                    <div className="p-3 bg-red-100 dark:bg-red-900/40 rounded-2xl">
                        <XIcon className="w-6 h-6 text-red-600 dark:text-red-400" />
                    </div>
                    <div className="flex-1">
                        <h4 className="text-sm font-black text-red-900 dark:text-red-200 uppercase tracking-widest flex items-center gap-2">
                            Feedback from Charlie (Manager)
                        </h4>
                        <p className="mt-2 text-sm text-red-700 dark:text-red-300 leading-relaxed font-medium italic">
                            "{(activeSource as any).review_notes}"
                        </p>
                    </div>
                </div>
            </div>
          )}

          {/* Visual Header (Image Preview) */}
          {previewUrl && (
            <div className="w-full h-64 md:h-80 relative group overflow-hidden bg-slate-900 shrink-0">
              <img 
                src={previewUrl} 
                alt="AI Generated Cover" 
                className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent opacity-60" />
              <div className="absolute bottom-6 left-12 right-12">
                <span className="px-3 py-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-[10px] font-black text-white uppercase tracking-widest">
                  Live AI Asset Preview
                </span>
              </div>
              <button 
                onClick={() => onGenerateImage(title || activeSource.title)}
                className="absolute top-6 right-6 p-3 bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl text-white hover:bg-white/20 transition-all opacity-0 group-hover:opacity-100 shadow-xl"
                title="Regenerate Image"
              >
                <RefreshCwIcon className={`w-5 h-5 ${isGeneratingImage ? 'animate-spin' : ''}`} />
              </button>
            </div>
          )}

          {/* Editor Body */}
          <div className="flex-1 p-8 md:p-16 max-w-4xl mx-auto w-full relative">
            <input 
              type="text"
              placeholder="Article Title..."
              value={title}
              onChange={(e) => onTitleChange(e.target.value)}
              className="w-full text-4xl font-black mb-8 outline-none bg-transparent dark:text-white placeholder:text-slate-200 dark:placeholder:text-slate-800 border-none"
            />
            
            <div className="flex items-center gap-4 mb-8">
               <button 
                onClick={() => onGenerateImage(title || activeSource.title)}
                disabled={isGeneratingImage}
                className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-indigo-50 hover:text-indigo-600 transition-all disabled:opacity-50"
              >
                <EyeIcon className={`w-3.5 h-3.5 mr-2 ${isGeneratingImage ? 'animate-bounce' : ''}`} />
                {isGeneratingImage ? 'Generating...' : 'AI Image'}
              </button>
              <div className="h-4 w-px bg-slate-200 dark:bg-slate-800" />
              <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest italic">
                Markdown & AI Collaboration Active
              </span>
            </div>

            <textarea 
              placeholder="Start typing or use the AI toolbox to synthesize your draft..."
              value={content}
              onChange={(e) => onContentChange(e.target.value)}
              className="w-full min-h-[80vh] outline-none bg-transparent dark:text-slate-300 resize-none leading-relaxed text-lg border-none font-sans"
            />
          </div>

          {/* Floating Action Buttons */}
          <div className="fixed bottom-8 right-8 flex flex-col gap-4 z-50">
            {/* Pro Editor Access */}
            <button 
              onClick={() => navigate(`/brand/editor/${activeSource.id}`)}
              className="w-16 h-16 bg-white dark:bg-slate-800 border-2 border-indigo-100 dark:border-slate-700 hover:border-indigo-500 text-indigo-600 rounded-2xl shadow-xl flex items-center justify-center transition-all hover:scale-110 active:scale-95 group"
              title="Open Pro Editor"
            >
              <FileEditIcon className="w-7 h-7 group-hover:rotate-12 transition-transform" />
            </button>
            
            {/* AI Command Center Trigger */}
            <button 
              onClick={() => setPromptCenterOpen(true)}
              className="w-16 h-16 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl shadow-2xl flex items-center justify-center transition-all hover:scale-110 active:scale-95 group relative"
            >
              <SparklesIcon className="w-8 h-8 group-hover:rotate-12 transition-transform" />
              <div className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full border-2 border-white flex items-center justify-center text-[10px] font-black">!</div>
            </button>
          </div>

          {/* UNIFIED PROMPT CENTER (Drawer/Overlay) */}
          {promptCenterOpen && (
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
                <button onClick={() => setPromptCenterOpen(false)} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors" aria-label="Close AI Command Center">
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

              <div className="flex-1 overflow-y-auto p-8 custom-scrollbar space-y-8">
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
          )}
        </div>
      </div>
    </div>
  );
};
