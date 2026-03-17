import React from 'react';
import { XIcon } from '@/components/Icons';
import { ContentSource } from '../VictoryFeedList';

interface CharlieFeedbackBannerProps {
  feedback?: string;
  aiScore?: number;
  activeSource: ContentSource;
}

export const CharlieFeedbackBanner: React.FC<CharlieFeedbackBannerProps> = ({
  feedback,
  aiScore,
  activeSource
}) => {
  return (
    <>
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

      {/* GAP-023: Charlie's Rejection Feedback Banner */}
      {activeSource && (activeSource as any).review_notes && (
        <div className="mx-8 mt-8 p-6 bg-red-50 dark:bg-red-900/20 border-2 border-red-100 dark:border-red-900/30 rounded-[2rem] shadow-sm animate-in slide-in-from-top duration-500">
            <div className="flex items-start gap-4">
                <div className="p-3 bg-red-100 dark:bg-red-900/40 rounded-2xl">
                    <XIcon className="w-6 h-6 text-red-600 dark:text-red-400" aria-label="Rejected" />
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
    </>
  );
};
