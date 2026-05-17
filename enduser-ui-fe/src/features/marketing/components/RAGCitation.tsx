import React, { useState } from 'react';
import { ExternalLinkIcon, InfoIcon } from 'lucide-react';

interface Citation {
  id: string;
  title: string;
  url: string;
  snippet?: string;
}

interface RAGCitationProps {
  citationId: string;
  citations: Citation[];
}

export const RAGCitation: React.FC<RAGCitationProps> = ({ citationId, citations }) => {
  const [isOpen, setIsOpen] = useState(false);
  const citation = citations.find(c => c.id === citationId);

  // If citation metadata isn't found, just render the text
  if (!citation) {
    return <span className="text-gray-500 font-mono text-xs mx-0.5">[{citationId}]</span>;
  }

  return (
    <span className="relative inline-block mx-0.5">
      <button
        onClick={() => setIsOpen(!isOpen)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
        className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-bold border border-indigo-200 hover:bg-indigo-200 hover:scale-110 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 z-10"
        title={`Source: ${citation.title}`}
      >
        {citationId}
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 p-3 z-50 text-left animate-in fade-in slide-in-from-bottom-2">
          <div className="flex items-start gap-2 mb-2">
            <InfoIcon className="w-4 h-4 text-indigo-500 flex-shrink-0 mt-0.5" />
            <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 leading-tight">
              {citation.title}
            </h4>
          </div>
          
          {citation.snippet && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-3 italic border-l-2 border-indigo-200 pl-2">
              "{citation.snippet}"
            </p>
          )}

          <a 
            data-testid="citation-popover-link"
            href={citation.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors"
          >
            <ExternalLinkIcon className="w-3 h-3" />
            View Original Source
          </a>

          {/* Triangle pointer */}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white dark:bg-gray-800 border-b border-r border-gray-200 dark:border-gray-700 transform rotate-45"></div>
        </div>
      )}
    </span>
  );
};
};
