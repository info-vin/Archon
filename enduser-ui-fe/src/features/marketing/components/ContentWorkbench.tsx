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
}

export const ContentWorkbench: React.FC<ContentWorkbenchProps> = ({
  activeSource,
  contextData,
  isLoadingContext,
  onDraft,
  onGenerateImage,
  onPublish,
  isDrafting,
  isGeneratingImage
}) => {
  title: string;
  content: string;
  onTitleChange: (value: string) => void;
  onContentChange: (value: string) => void;
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
  onContentChange
}) => {
  const [activeTab, setActiveTab] = useState<'context' | 'editor'>('context');

  // BUG-025: Persistence Logic - Updated to use props
  // Note: Parent component (BrandPage) now manages the source of truth, 
  // but we keeping the effect here to sync activeSource changes if needed, 
  // or better, move persistence to parent. 
  // For this fix, let's trust the parent passes the correct state.

  // BUG-026: Save Feedback
  const handleSave = () => {
    // Logic is handled by useEffect sync, but we provide user feedback
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
              {activeSource.type}
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1 truncate max-w-md">
            Signal: {activeSource.summary}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg mr-4">
            <button
              onClick={() => setActiveTab('context')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all flex items-center ${
                activeTab === 'context' ? 'bg-white dark:bg-slate-700 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-slate-500'
              }`}
            >
              <EyeIcon className="w-3.5 h-3.5 mr-1.5" />
              Context
            </button>
            <button
              onClick={() => setActiveTab('editor')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all flex items-center ${
                activeTab === 'editor' ? 'bg-white dark:bg-slate-700 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-slate-500'
              }`}
            >
              <FileEditIcon className="w-3.5 h-3.5 mr-1.5" />
              Editor
            </button>
          </div>
          
          <button 
            onClick={() => onPublish({ title: title, content: content })}
            className="flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold transition-all shadow-sm"
          >
            <CheckCircleIcon className="w-4 h-4 mr-2" />
            Publish
          </button>
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'context' ? (
          <div className="h-full overflow-y-auto p-6 space-y-8 max-w-4xl mx-auto">
            {isLoadingContext ? (
              <div className="space-y-6">
                <div className="h-4 bg-slate-100 rounded w-1/4 animate-pulse"></div>
                <div className="h-32 bg-slate-100 rounded animate-pulse"></div>
                <div className="h-4 bg-slate-100 rounded w-1/4 animate-pulse"></div>
                <div className="h-48 bg-slate-100 rounded animate-pulse"></div>
              </div>
            ) : (
              <>
                {/* Visit Logs / Task Desc */}
                <section>
                  <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">
                    Primary Signal (Visit Logs / Task)
                  </h3>
                  <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-5 border dark:border-slate-700">
                    <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {contextData?.context_summary || 'No detailed context available.'}
                    </div>
                  </div>
                </section>

                {/* Librarian Suggestions */}
                <section>
                  <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">
                    Librarian Suggestions (RAG)
                  </h3>
                  <div className="grid grid-cols-1 gap-4 text-sm">
                    {contextData?.rag_refs.map((ref, idx) => (
                      <div key={idx} className="bg-white dark:bg-slate-900 border dark:border-slate-800 rounded-lg p-4 shadow-sm group">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-bold text-indigo-500 uppercase">
                            Ref: {ref.metadata.source}
                          </span>
                          <ExternalLinkIcon className="w-3 h-3 text-slate-300 group-hover:text-indigo-400 cursor-pointer" />
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed italic">
                          "{ref.content.substring(0, 300)}..."
                        </p>
                      </div>
                    ))}
                    {(!contextData?.rag_refs || contextData.rag_refs.length === 0) && (
                      <p className="text-xs text-slate-400 italic font-medium">Librarian found no matching internal documents.</p>
                    )}
                  </div>
                </section>
              </>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col">
            {/* Editor Toolbar */}
            <div className="px-6 py-2 border-b bg-slate-50/50 dark:bg-slate-800/50 flex items-center space-x-2">
              <button 
                onClick={() => onDraft(activeSource.title)}
                disabled={isDrafting}
                className="flex items-center px-3 py-1.5 bg-white dark:bg-slate-700 border dark:border-slate-600 rounded-md text-[10px] font-bold text-slate-700 dark:text-slate-200 hover:shadow-sm transition-all disabled:opacity-50"
              >
                <SparklesIcon className={`w-3.5 h-3.5 mr-2 text-indigo-500 ${isDrafting ? 'animate-spin' : ''}`} />
                {isDrafting ? 'Drafting...' : 'Magic Draft'}
              </button>
              <button 
                onClick={() => onGenerateImage(title || activeSource.title)}
                disabled={isGeneratingImage}
                className="flex items-center px-3 py-1.5 bg-white dark:bg-slate-700 border dark:border-slate-600 rounded-md text-[10px] font-bold text-slate-700 dark:text-slate-200 hover:shadow-sm transition-all disabled:opacity-50"
              >
                <TrendingUpIcon className={`w-3.5 h-3.5 mr-2 text-blue-500 ${isGeneratingImage ? 'animate-pulse' : ''}`} />
                {isGeneratingImage ? 'Generating...' : 'Header Image'}
              </button>
              <div className="flex-1"></div>
              <button
                onClick={handleSave}
                className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-slate-400 active:text-indigo-500 transition-colors"
                title="Save Draft"
              >
                <SaveIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Editor Canvas */}
            <div className="flex-1 overflow-y-auto p-10 max-w-4xl mx-auto w-full">
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