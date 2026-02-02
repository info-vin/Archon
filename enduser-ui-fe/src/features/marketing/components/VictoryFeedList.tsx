import React from 'react';
import { TrendingUpIcon, BuildingIcon, FileTextIcon } from '../../../components/Icons';

export interface ContentSource {
  id: string;
  type: 'lead' | 'task';
  title: string;
  score: number;
  summary: string;
  date: string;
}

interface VictoryFeedListProps {
  sources: ContentSource[];
  activeId?: string;
  onSelect: (source: ContentSource) => void;
  isLoading?: boolean;
}

export const VictoryFeedList: React.FC<VictoryFeedListProps> = ({
  sources,
  activeId,
  onSelect,
  isLoading
}) => {
  const formatDate = (dateStr: string) => {
    try {
      return new Intl.DateTimeFormat('en-US', { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      }).format(new Date(dateStr));
    } catch (e) {
      return dateStr;
    }
  };

  if (isLoading) {
    return (
      <div className="p-4 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse flex space-x-3">
            <div className="rounded-full bg-slate-200 h-10 w-10"></div>
            <div className="flex-1 space-y-2 py-1">
              <div className="h-4 bg-slate-200 rounded w-3/4"></div>
              <div className="h-4 bg-slate-200 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto border-r bg-white dark:bg-slate-900">
      <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-white dark:bg-slate-900 z-10 font-sans">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 flex items-center">
          <TrendingUpIcon className="w-4 h-4 mr-2" />
          Victory Feed
        </h2>
        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
          {sources.length} Signals
        </span>
      </div>
      
      <div className="divide-y font-sans text-sm">
        {sources.map((source) => (
          <button
            key={source.id}
            onClick={() => onSelect(source)}
            className={`w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors relative ${
              activeId === source.id ? 'bg-indigo-50 dark:bg-indigo-900/20 ring-inset ring-2 ring-indigo-500' : ''
            }`}
          >
            <div className="flex justify-between items-start mb-1">
              <div className="flex items-center space-x-2 overflow-hidden">
                {source.type === 'lead' ? (
                  <BuildingIcon className="w-4 h-4 text-blue-500 shrink-0" />
                ) : (
                  <FileTextIcon className="w-4 h-4 text-orange-500 shrink-0" />
                )}
                <span className="font-semibold text-slate-900 dark:text-white truncate">
                  {source.title}
                </span>
              </div>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                source.score >= 90 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
              }`}>
                {source.score}
              </span>
            </div>
            
            <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-2">
              {source.summary}
            </p>
            
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-400">
                {formatDate(source.date)}
              </span>
              <span className="text-[10px] uppercase text-slate-400 font-medium">
                {source.type}
              </span>
            </div>
          </button>
        ))}
        
        {sources.length === 0 && (
          <div className="p-8 text-center text-slate-400 text-sm italic">
            No victory signals yet.
          </div>
        )}
      </div>
    </div>
  );
};