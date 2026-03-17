import React from 'react';
import { RefreshCwIcon, EyeIcon } from '@/components/Icons';
import { ContentSource } from '../VictoryFeedList';

interface EditorBodyProps {
  activeSource: ContentSource;
  previewUrl: string | null;
  isGeneratingImage: boolean;
  title: string;
  content: string;
  onGenerateImage: (title: string) => void;
  onTitleChange: (value: string) => void;
  onContentChange: (value: string) => void;
}

export const EditorBody: React.FC<EditorBodyProps> = ({
  activeSource,
  previewUrl,
  isGeneratingImage,
  title,
  content,
  onGenerateImage,
  onTitleChange,
  onContentChange
}) => {
  return (
    <>
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
    </>
  );
};
