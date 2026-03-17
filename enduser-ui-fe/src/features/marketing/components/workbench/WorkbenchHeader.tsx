import React from 'react';
import { SaveIcon, CheckCircleIcon } from '@/components/Icons';
import { ContentSource } from '../VictoryFeedList';

interface WorkbenchHeaderProps {
  activeSource: ContentSource;
  title: string;
  content: string;
  onSave: () => void;
  onPublish: (post: any) => void;
}

export const WorkbenchHeader: React.FC<WorkbenchHeaderProps> = ({
  activeSource,
  title,
  content,
  onSave,
  onPublish
}) => {
  return (
    <div className="px-6 py-4 border-b flex items-center justify-between bg-white dark:bg-slate-900 z-10">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center">
            {activeSource.title}
            <span className="ml-3 px-2 py-0.5 rounded text-[10px] bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-black uppercase tracking-widest">
              Workbench
            </span>
          </h1>
          <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-tighter">
            Source: {activeSource.type} · Integrity: {activeSource.score}%
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <button
          onClick={onSave}
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
  );
};
