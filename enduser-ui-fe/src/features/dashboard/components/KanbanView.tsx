import React, { useMemo } from 'react';
import { Task, TaskStatus } from '../../../types';
import { PriorityBadge } from './PriorityBadge';
import UserAvatar from '../../../components/UserAvatar';

interface KanbanViewProps {
  tasks: Task[];
  updateTaskStatus: (taskId: string, newStatus: TaskStatus) => void;
  setEditingTask: (task: Task) => void;
  userMap: Record<string, any>;
}

const statuses: TaskStatus[] = [TaskStatus.TODO, TaskStatus.DOING, TaskStatus.REVIEW, TaskStatus.DONE];

// PERFORMANCE: Hoisted static lookup dictionary outside the component to prevent allocations and O(N) inline .toLowerCase() calls
const STATUS_COLORS: Record<string, string> = {
  [TaskStatus.TODO]: 'bg-gray-400',
  [TaskStatus.DOING]: 'bg-blue-400',
  [TaskStatus.REVIEW]: 'bg-purple-400',
  [TaskStatus.DONE]: 'bg-green-400'
};

// PERFORMANCE: Hoisted Intl.DateTimeFormat out of the component to prevent expensive re-instantiation on every render cycle
const kanbanDateFormatter = new Intl.DateTimeFormat(undefined, {month:'short', day:'numeric'});
const safeFormatKanbanDate = (dateStr: string) => {
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? 'Invalid Date' : kanbanDateFormatter.format(d);
};

export const KanbanView: React.FC<KanbanViewProps> = React.memo(({ tasks, updateTaskStatus, setEditingTask, userMap }) => {
  // PERFORMANCE: Hoisted expensive date parsing out of the render loop to prevent O(N) allocations
  const formattedDates = React.useMemo(() => {
    const dates: Record<string, string> = {};
    tasks.forEach(t => {
      if (t.due_date) dates[t.id] = safeFormatKanbanDate(t.due_date);
    });
    return dates;
  }, [tasks]);

  const tasksByStatus = useMemo(() => {
    const grouped: { [key in TaskStatus]?: Task[] } = {};
    tasks.forEach(task => {
      if (!grouped[task.status]) grouped[task.status] = [];
      grouped[task.status]?.push(task);
    });
    return grouped;
  }, [tasks]);

  const onDragStart = (e: React.DragEvent, taskId: string) => {
    e.dataTransfer.setData('taskId', taskId);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const onDrop = (e: React.DragEvent, newStatus: TaskStatus) => {
    const taskId = e.dataTransfer.getData('taskId');
    updateTaskStatus(taskId, newStatus);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 w-full p-2">
      {statuses.map(status => (
        <div key={status} className="bg-gray-50/50 rounded-2xl p-4 flex flex-col gap-4 border border-gray-100" onDrop={(e) => onDrop(e, status)} onDragOver={onDragOver}>
          <div className="flex justify-between items-center border-b border-gray-200 pb-3">
             <h3 className="font-bold text-gray-700 capitalize flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[status] || 'bg-gray-400'}`}></span>
                {status}
             </h3>
             <span className="bg-white px-2 py-0.5 rounded-full text-xs font-bold text-gray-500 shadow-sm">{tasksByStatus[status]?.length || 0}</span>
          </div>
          
          <div className="flex-1 min-w-0 space-y-3 w-full pr-1">
            {tasksByStatus[status]?.map(task => {
               return (
                  <div 
                    key={task.id} 
                    draggable 
                    onDragStart={(e) => onDragStart(e, task.id)} 
                    onClick={() => setEditingTask(task)} 
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setEditingTask(task);
                        }
                    }}
                    tabIndex={0}
                    role="button"
                    aria-label={`View details for task: ${task.title}`}
                    className="relative bg-white p-4 rounded-xl shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing overflow-hidden transition-all group border border-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
                  >
                    <PriorityBadge priority={task.priority} variant="stripe" />
                    
                    <div className="font-semibold text-gray-800 text-sm leading-snug mb-3 group-hover:text-indigo-600 transition-colors">
                        {task.title}
                        {task.is_recurring && <span className="ml-1 text-[10px] font-normal text-blue-500 bg-blue-50 px-1 py-0.5 rounded">(🔁 定期)</span>}
                    </div>
                    
                    <div className="mb-2">
                        <PriorityBadge priority={task.priority} />
                    </div>
                    
                    <div className="flex items-center justify-between mt-auto pt-2 border-t border-gray-50">
                         {task.assignee ? (
                            <div className="flex items-center gap-1.5 opacity-80 group-hover:opacity-100">
                                <UserAvatar 
                                    name={userMap[task.assignee_id || '']?.name || userMap[task.assignee || '']?.name || task.assignee} 
                                    size={18} 
                                    // PERFORMANCE: Replaced O(N) assignee map allocation and .toLowerCase() calls with a fast inline case-insensitive regex test.
                                    isAI={/bot/i.test(task.assignee || '') || userMap[task.assignee_id || '']?.role === 'ai_agent'}
                                    role={userMap[task.assignee_id || '']?.role || userMap[task.assignee || '']?.role}
                                />
                                <span className="text-[11px] text-gray-500 font-medium truncate max-w-[80px]">
                                    {userMap[task.assignee_id || '']?.name || userMap[task.assignee || '']?.name || task.assignee}
                                </span>
                            </div>
                         ) : (
                            <span className="text-[11px] text-gray-400 italic">Unassigned</span>
                         )}
                         {task.due_date && (
                            <span className="text-[10px] text-gray-400 font-mono">{formattedDates[task.id]}</span>
                         )}
                    </div>
                  </div>
               );
            })}
          </div>
        </div>
      ))}
    </div>
  );
});
