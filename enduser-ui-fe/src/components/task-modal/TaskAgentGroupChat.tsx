import React, { useMemo } from 'react';
import { Task } from '../../types.ts';
import { SparklesIcon } from '../Icons.tsx';

interface TaskAgentGroupChatProps {
  task: Task;
}

const ROLE_CONFIG: Record<string, { name: string; avatar: string; color: string; align: 'left' | 'right' }> = {
  // Humans
  user: { name: 'User / Human', avatar: '👤', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100', align: 'right' },
  alice: { name: 'Alice (Sales)', avatar: '👩', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100', align: 'right' },
  bob: { name: 'Bob (Marketing)', avatar: '👨', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100', align: 'right' },
  charlie: { name: 'Charlie (Manager)', avatar: '👨‍💼', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100', align: 'right' },
  
  // AI Agents
  supervisor: { name: 'Supervisor (Brain)', avatar: '🧠', color: 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-slate-100', align: 'left' },
  librarian: { name: 'Librarian (Knowledge)', avatar: '📚', color: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-900 dark:text-emerald-100', align: 'left' },
  marketbot: { name: 'MarketBot (Writer)', avatar: '✍️', color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-900 dark:text-amber-100', align: 'left' },
  summary: { name: 'SummaryBot (Notes)', avatar: '📝', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-900 dark:text-purple-100', align: 'left' },
  devbot: { name: 'DevBot (Data Scientist)', avatar: '💻', color: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-900 dark:text-cyan-100', align: 'left' },
  david: { name: 'David (DB Admin)', avatar: '🗄️', color: 'bg-rose-100 dark:bg-rose-900/30 text-rose-900 dark:text-rose-100', align: 'left' },
};

export const TaskAgentGroupChat: React.FC<TaskAgentGroupChatProps> = ({ task }) => {
  if (!task.agent_output) return null;

  // Defensive check for JSON vs string to avoid crashes
  const output = typeof task.agent_output === 'string' 
    ? { content: task.agent_output } 
    : (task.agent_output as Record<string, any>);
    
  const messages = Array.isArray(output.messages) ? output.messages : [];
  
  // Phase 5.0.2 Anti-Pattern #1: Use primitive length to prevent rendering deadlocks
  const messagesLength = messages.length;

  const renderedMessages = useMemo(() => {
    return messages.map((msg: any, idx: number) => {
      const role = (msg.role || 'system').toLowerCase();
      const config = ROLE_CONFIG[role] || { 
        name: `System (${role})`, 
        avatar: '🤖', 
        color: 'bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200', 
        align: 'left' 
      };
      const isRight = config.align === 'right';

      return (
        <div key={idx} className={`flex w-full mb-4 ${isRight ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2`}>
          {!isRight && <div className="text-2xl mr-2 flex-shrink-0 mt-1">{config.avatar}</div>}
          
          <div className={`max-w-[75%] p-3 rounded-xl ${config.color} shadow-sm border border-black/5 dark:border-white/5`}>
            <div className="text-[10px] font-bold opacity-70 mb-1 tracking-wide uppercase">{config.name}</div>
            <div className="text-sm whitespace-pre-wrap break-words">{msg.content}</div>
          </div>

          {isRight && <div className="text-2xl ml-2 flex-shrink-0 mt-1">{config.avatar}</div>}
        </div>
      );
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messagesLength]);

  // Fallback to simple report if it's an old task without array messages
  if (messagesLength === 0) {
    return (
      <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded-xl space-y-3 animate-in fade-in zoom-in-95 duration-300">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-xs font-black text-indigo-600 dark:text-indigo-400 uppercase tracking-widest flex items-center gap-2">
              <SparklesIcon className="w-3 h-3" />
              AI Agent Report
            </h3>
            
            {task.ai_metrics && task.ai_metrics.total_cost_usd > 0 && (
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-black rounded-full border border-emerald-200 dark:border-emerald-800 animate-in fade-in slide-in-from-left-2">
                  ${task.ai_metrics.total_cost_usd.toFixed(4)}
                </span>
                <span className="text-[9px] text-slate-400 font-medium">
                  {task.ai_metrics.total_tokens.toLocaleString()} tokens
                </span>
              </div>
            )}
          </div>
          <span className="text-[9px] font-bold text-indigo-400">v1.1 Legacy Payload</span>
        </div>
        <div className="bg-white dark:bg-slate-950 p-4 rounded-lg border border-indigo-50 dark:border-indigo-900 text-sm font-mono text-slate-700 dark:text-slate-300 overflow-x-auto max-h-60 custom-scrollbar">
          {output.content || output.final_result || JSON.stringify(output, null, 2)}
        </div>
        <p className="text-[10px] text-indigo-400 italic font-medium">This report was generated by the assigned AI Agent upon task completion.</p>
      </div>
    );
  }

  // Phase 5.0.2 Native Group Chat UI
  return (
    <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden flex flex-col h-[500px] animate-in fade-in zoom-in-95 duration-300">
      <div className="bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 p-3 flex items-center justify-between z-10 shrink-0 shadow-sm">
        <div className="flex items-center gap-2">
          <SparklesIcon className="w-4 h-4 text-indigo-500" />
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
            Multi-Agent Group Chat
          </h3>
          
          {task.ai_metrics && task.ai_metrics.total_cost_usd > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-black rounded-full border border-emerald-200 dark:border-emerald-800">
              ${task.ai_metrics.total_cost_usd.toFixed(4)}
            </span>
          )}
        </div>
        <div className="flex gap-2 text-[10px] font-medium text-slate-500">
          <span className="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-full">{messagesLength} Messages</span>
          {output.step_count !== undefined && (
            <span className="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-full">{output.step_count} Steps</span>
          )}
        </div>
      </div>
      
      <div className="p-4 overflow-y-auto flex-1 custom-scrollbar bg-slate-50/50 dark:bg-slate-900/50">
        {renderedMessages}
      </div>
    </div>
  );
};
