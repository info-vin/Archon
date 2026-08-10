import React from 'react';
import ReactMarkdown, { Components } from 'react-markdown';

interface AudioMarkdownRendererProps {
  content: string;
}

export const audioMarkdownComponents: Components = {
  a: ({ href, children, ...props }) => {
    if (href && (href.endsWith('.wav') || href.endsWith('.mp3') || href.includes('.wav?token='))) {
      return (
        <div className="my-4 border border-indigo-100 dark:border-indigo-900 rounded-lg p-3 bg-indigo-50/50 dark:bg-indigo-950/50">
          <audio controls className="w-full h-10 rounded-md" src={href}>
            Your browser does not support the audio element.
          </audio>
          <div className="text-xs text-indigo-600 dark:text-indigo-400 mt-2 flex items-center justify-between">
            <span className="font-medium">🎧 Podcast Episode</span>
            <a href={href} target="_blank" rel="noopener noreferrer" className="hover:underline opacity-80 hover:opacity-100 flex items-center gap-1">
              Download <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            </a>
          </div>
        </div>
      );
    }
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline" {...props}>
        {children}
      </a>
    );
  },
};

export const AudioMarkdownRenderer: React.FC<AudioMarkdownRendererProps> = ({ content }) => {
  return (
    <div className="prose prose-sm prose-indigo max-w-none dark:prose-invert">
      <ReactMarkdown components={audioMarkdownComponents}>{content || ''}</ReactMarkdown>
    </div>
  );
};
