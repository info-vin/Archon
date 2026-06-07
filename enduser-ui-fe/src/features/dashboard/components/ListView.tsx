import React, { useMemo } from 'react';
import { Task } from '../../../types';
import { PriorityBadge } from './PriorityBadge';
import UserAvatar from '../../../components/UserAvatar';
import { PaperclipIcon } from '../../../components/Icons';

interface ListViewProps {
  tasks: Task[];
  setEditingTask: (task: Task) => void;
  userMap: Record<string, any>;
}

export const ListView: React.FC<ListViewProps> = React.memo(({ tasks, setEditingTask, userMap }) => {
  const assigneeLowerMap = useMemo(() => {
    const map: Record<string, string> = {};
    tasks.forEach(task => {
      map[task.id] = task.assignee ? task.assignee.toLowerCase() : '';
    });
    return map;
  }, [tasks]);

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 bg-white/50 backdrop-blur-md rounded-2xl border border-white/50 border-dashed">
        <p className="text-gray-400 font-medium italic">No tasks assigned for today. Great job!</p>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
    {tasks.map(task => {
        return (
            <li key={task.id} onClick={() => setEditingTask(task)} className="group relative overflow-hidden bg-white/70 backdrop-blur-md rounded-xl border border-white/50 shadow-sm hover:shadow-md transition-all cursor-pointer p-4 pl-5">
                <PriorityBadge priority={task.priority} variant="stripe" />

                <div className="flex justify-between items-start">
                    <div className="flex flex-col gap-1 max-w-[60%]">
                        <div className="flex items-center gap-2">
                             <span className="font-bold text-gray-800 text-base leading-snug group-hover:text-indigo-600 transition-colors">
                                 {task.title}
                                 {task.is_recurring && <span className="ml-2 text-[10px] font-normal text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">(🔁 定期任務)</span>}
                             </span>
                             <PriorityBadge priority={task.priority} />
                        </div>
                        {task.description && (
                            <p className="text-sm text-gray-500 line-clamp-1">{task.description}</p>
                        )}
                        {/* Attachments Section - RESTORED */}
                        {task.attachments && task.attachments.length > 0 && (
                          <div 
                            data-testid="attachment-badge"
                            className="flex items-center gap-1.5 mt-2 px-2 py-0.5 bg-slate-50 border border-slate-100 rounded-md w-fit"
                          >
                            <PaperclipIcon className="h-3 w-3 text-slate-400" />
                            <span className="text-[10px] font-bold text-slate-500">{task.attachments.length} files</span>
                          </div>
                        )}
                    </div>
...
                    <div className="flex items-center gap-4">
                        <div className="flex flex-col items-end gap-1">
                            <div className="flex items-center gap-2">
                                <UserAvatar 
                                    name={userMap[task.assignee_id || '']?.name || userMap[task.assignee || '']?.name || task.assignee || 'Unassigned'} 
                                    size={24} 
                                    isAI={assigneeLowerMap[task.id]?.includes('bot') || userMap[task.assignee_id || '']?.role === 'ai_agent'}
                                    role={userMap[task.assignee_id || '']?.role || userMap[task.assignee || '']?.role}
                                />
                                <span className="text-sm font-medium text-gray-600">
                                    {userMap[task.assignee_id || '']?.name || userMap[task.assignee || '']?.name || task.assignee || 'Unassigned'}
                                </span>
                            </div>
                            {task.due_date && (
                                <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider">
                                    Due: {new Date(task.due_date).toLocaleDateString()}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </li>
        );
    })}
  </ul>
  );
  });

