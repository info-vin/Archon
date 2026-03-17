import React from 'react';
import { Task, SortableTaskKeys, SortDirection } from '../../../types';
import { PriorityBadge } from './PriorityBadge';
import { StatusBadge } from './StatusBadge';
import UserAvatar from '../../../components/UserAvatar';
import { ChevronsUpDownIcon } from '../../../components/Icons';

interface TableViewProps {
  tasks: Task[];
  setEditingTask: (task: Task) => void;
  requestSort: (key: SortableTaskKeys) => void;
  sortConfig: { key: SortableTaskKeys; direction: SortDirection } | null;
  userMap: Record<string, any>;
  projectMap: Record<string, string>;
}

export const TableView: React.FC<TableViewProps> = React.memo(({ tasks, setEditingTask, requestSort, sortConfig, userMap, projectMap }) => {
  const getSortIcon = (key: SortableTaskKeys) => {
    if (!sortConfig || sortConfig.key !== key) return <ChevronsUpDownIcon className="h-4 w-4" />;
    return sortConfig.direction === 'ascending' ? '🔼' : '🔽';
  };

  return (
    <div className="bg-white/50 backdrop-blur-sm rounded-2xl border border-white/50 shadow-sm overflow-x-auto font-sans text-xs custom-scrollbar">
        <table className="w-full text-left border-collapse min-w-[800px]">
          <thead className="bg-slate-50/50 dark:bg-slate-900/50 border-b dark:border-slate-800">
            <tr>
              <th scope="col" className="px-6 py-4 font-black uppercase tracking-widest text-slate-400 text-[10px] cursor-pointer" onClick={() => requestSort('status')}>
                Status {getSortIcon('status')}
              </th>
              <th scope="col" className="px-6 py-4 font-black uppercase tracking-widest text-slate-400 text-[10px]">Project</th>
              <th scope="col" className="px-6 py-4 font-black uppercase tracking-widest text-slate-400 text-[10px]">Title</th>
              <th scope="col" className="px-6 py-4 font-black uppercase tracking-widest text-slate-400 text-[10px]">Assignee</th>
              <th scope="col" className="px-6 py-4 font-black uppercase tracking-widest text-slate-400 text-[10px] cursor-pointer" onClick={() => requestSort('priority')}>
                Priority {getSortIcon('priority')}
              </th>
              <th scope="col" className="px-6 py-4 font-black uppercase tracking-widest text-slate-400 text-[10px] cursor-pointer" onClick={() => requestSort('due_date')}>
                Due {getSortIcon('due_date')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y dark:divide-slate-800">
            {tasks.map(task => (
              <tr key={task.id} onClick={() => setEditingTask(task)} className="hover:bg-white dark:hover:bg-slate-800/50 transition-colors cursor-pointer group">
                <td className="px-6 py-4"><StatusBadge status={task.status} /></td>
                <td className="px-6 py-4 text-slate-500 font-medium">
                    <span className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded-lg truncate block max-w-[120px]">
                        {projectMap[task.project_id] || 'General'}
                    </span>
                </td>
                <td className="px-6 py-4 font-bold text-slate-700 dark:text-slate-200 group-hover:text-indigo-600 transition-colors">
                    {task.title}
                    {task.is_recurring && <span className="ml-2 text-[10px] font-normal text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">(🔁 定期)</span>}
                </td>
                <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                        <UserAvatar 
                            name={task.assignee || 'Unassigned'} 
                            size={20} 
                            isAI={task.assignee?.toLowerCase().includes('bot')}
                            role={userMap[task.assignee_id || '']?.role || userMap[task.assignee || '']?.role}
                        />
                        <span className="text-slate-600 dark:text-slate-400 font-medium">{task.assignee || 'None'}</span>
                    </div>
                </td>
                <td className="px-6 py-4"><PriorityBadge priority={task.priority} /></td>
                <td className="px-6 py-4 font-mono text-slate-400">
                    {task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
    </div>
  );
});
