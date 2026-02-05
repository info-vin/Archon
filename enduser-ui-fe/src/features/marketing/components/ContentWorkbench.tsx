import React, { useState } from 'react';
import { 
  SparklesIcon, 
  SaveIcon, 
  CheckCircleIcon, 
  EyeIcon, 
  FileEditIcon, 
  ExternalLinkIcon,
  TrendingUpIcon
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
  onDraft: (topic: string) => void;
  onGenerateImage: (title: string) => void;
  onPublish: (post: any) => void;
  isDrafting: boolean;
  isGeneratingImage: boolean;
  title: string;
  content: string;
  onTitleChange: (value: string) => void;
  onContentChange: (value: string) => void;
  usedPrompt?: string; // New: For Transparency
}

export const ContentWorkbench: React.FC<ContentWorkbenchProps> = ({
  activeSource,
  contextData,
  isLoadingContext,
  onDraft,
  onGenerateImage,
  onPublish,
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

  // BUG-026: Save Feedback
  const handleSave = () => {
    // Persistence is managed by the parent via state lifting and localStorage
    alert("Draft saved successfully!");
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
    <div className="h-full flex flex-col bg-white dark:bg-slate-900 font-sans">
      {/* Header */}
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center">
            {activeSource.title}
            <span className="ml-3 px-2 py-0.5 rounded text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 uppercase tracking-tighter">
              Workbench
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">Source: {activeSource.type} · Score: {activeSource.score}%</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button 
            onClick={handleSave}
            className="flex items-center px-4 py-2 border rounded-lg text-sm font-medium hover:bg-slate-50 transition-all dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <SaveIcon className="w-4 h-4 mr-2" />
            Save
          </button>
          
          <button 
            onClick={() => onPublish({ title: title, content: content })}
            className="flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold transition-all shadow-sm"
          >
            <CheckCircleIcon className="w-4 h-4 mr-2" />
            Publish
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        <button 
          onClick={() => setActiveTab('context')}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${activeTab === 'context' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          <TrendingUpIcon className="w-4 h-4 inline-block mr-2" />
          Signal Context
        </button>
        <button 
          onClick={() => setActiveTab('editor')}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${activeTab === 'editor' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          <FileEditIcon className="w-4 h-4 inline-block mr-2" />
          Magic Editor
        </button>
      </div>

      {/* Content */}
      <div className="flex-1">
        {activeTab === 'context' ? (
          <div className="p-8 max-w-4xl mx-auto space-y-12">
            {isLoadingContext ? (
              <div className="py-20 text-center animate-pulse text-slate-400">
                <SparklesIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
                <p>MarketBot is gathering intelligence...</p>
              </div>
            ) : (
              <>
                {/* Transcript / Raw Logs */}
                <section>
                  <h3 className="text-xs font-black uppercase text-slate-400 mb-4 tracking-widest">Victory Signal Intelligence</h3>
                  <div className="bg-slate-50 dark:bg-slate-950 p-6 rounded-xl font-mono text-sm leading-relaxed text-slate-700 dark:text-slate-400 border dark:border-slate-800">
                    {contextData?.context_summary || "No specific transcript available for this signal."}
                  </div>
                </section>

                {/* RAG Suggestions */}
                <section>
                  <h3 className="text-xs font-black uppercase text-slate-400 mb-4 tracking-widest">Librarian Knowledge Base Suggestions</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {contextData?.rag_refs.map((ref, idx) => (
                      <div key={idx} className="p-4 border dark:border-slate-800 rounded-xl hover:shadow-md transition-all group">
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-[10px] font-bold text-indigo-600 uppercase">Context Reference #{idx + 1}</span>
                          <ExternalLinkIcon className="w-3 h-3 text-slate-300 group-hover:text-indigo-500 cursor-pointer" />
                        </div>
                        <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-4 leading-relaxed italic">"{ref.content}"</p>
                        <div className="mt-3 text-[10px] text-slate-400 truncate">Source: {ref.metadata.source}</div>
                      </div>
                    ))}
                    {(!contextData || contextData.rag_refs.length === 0) && (
                      <div className="col-span-full py-8 border-2 border-dashed dark:border-slate-800 rounded-xl text-center text-slate-400 text-xs">
                        No related knowledge references found.
                      </div>
                    )}
                  </div>
                </section>

                <div className="pt-8 border-t dark:border-slate-800 text-center">
                  <button 
                    onClick={() => setActiveTab('editor')}
                    className="px-8 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-full font-black text-sm hover:scale-105 transition-all"
                  >
                    Start Magic Draft →
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col">
            {/* ToolBar */}
            <div className="px-6 py-2 bg-slate-50 dark:bg-slate-800/50 border-b flex items-center space-x-4">
              <button 
                onClick={() => onDraft(activeSource.title)}
                disabled={isDrafting}
                className="flex items-center px-3 py-1.5 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-md text-[10px] font-bold hover:shadow-sm transition-all disabled:opacity-50"
              >
                <SparklesIcon className={`w-3 h-3 mr-1.5 ${isDrafting ? 'animate-spin' : ''}`} />
                {isDrafting ? 'Drafting...' : 'Magic Draft'}
              </button>
              <button 
                onClick={() => onGenerateImage(title || activeSource.title)}
                disabled={isGeneratingImage}
                className="flex items-center px-3 py-1.5 bg-white dark:bg-slate-700 border dark:border-slate-600 rounded-md text-[10px] font-bold text-slate-700 dark:text-slate-200 hover:shadow-sm transition-all disabled:opacity-50"
              >
                <EyeIcon className={`w-3 h-3 mr-1.5 ${isGeneratingImage ? 'animate-bounce' : ''}`} />
                {isGeneratingImage ? 'Generating Image...' : 'AI Cover Image'}
              </button>
              
              <div className="flex-1" />
              
              {usedPrompt && (
                <button 
                   onClick={() => setShowPrompt(!showPrompt)}
                   className="text-[10px] text-slate-400 hover:text-indigo-600 underline mr-4"
                >
                   {showPrompt ? 'Hide Prompt' : 'View AI Prompt'}
                </button>
              )}
              <span className="text-[10px] text-slate-400">Markdown Supported</span>
            </div>

            {/* Prompt Debug Viewer */}
            {showPrompt && usedPrompt && (
              <div className="mx-6 mt-4 p-4 bg-slate-100 dark:bg-slate-950 border rounded-lg text-xs font-mono text-slate-600 dark:text-slate-400 whitespace-pre-wrap max-h-40 overflow-y-auto shadow-inner">
                {usedPrompt}
              </div>
            )}

            {/* Markdown Editor */}
            <div className="flex-1 p-12 max-w-4xl mx-auto w-full">
              <input 
                type="text"
                placeholder="Article Title..."
                value={title}
                onChange={(e) => onTitleChange(e.target.value)}
                className="w-full text-3xl font-bold mb-8 outline-none bg-transparent dark:text-white placeholder:text-slate-200 dark:placeholder:text-slate-700 border-none"
              />
              <textarea 
                placeholder="Start writing or use Magic Draft..."
                value={content}
                onChange={(e) => onContentChange(e.target.value)}
                className="w-full h-[60vh] outline-none bg-transparent dark:text-slate-300 resize-none leading-relaxed text-lg border-none"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
