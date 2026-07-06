import React, { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { Employee, Task } from '@/types';
import UserAvatar from '@/components/UserAvatar';
import { XIcon, ClockIcon } from '@/components/Icons';
import { EmptyState } from '@/components/common/EmptyState';

// PERFORMANCE: Hoist Intl.DateTimeFormat instance outside the component to avoid expensive repeated instantiations (implicitly called by toLocaleDateString) inside the render loop.
const dateFormatter = new Intl.DateTimeFormat(undefined);

export const ActivityLogModal: React.FC<{ member: Employee; onClose: () => void }> = ({ member, onClose }) => {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadTasks = async () => {
            try {
                // Fetch tasks for specific member + unassigned, with higher limit
                // Passing member.id to backend allows efficient filtering and avoids pagination issues (BUG-027)
                const tasks = await api.getTasks(true, true, member.id, 100);

                // Client-side fallback filter for legacy name-based assignment consistency
                const memberTasks = tasks.filter(t =>
                    t.assignee_id === member.id || 
                    t.assignee === member.name ||
                    (t.assignee === 'User' && member.role === 'marketing')
                ).sort((a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime());

                setTasks(memberTasks);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadTasks();
    }, [member]);

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
             <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <div className="flex items-center gap-3">
                        <UserAvatar name={member.name || ''} role={member.role} className="w-10 h-10 shadow-sm" />
                        <div>
                            <h3 className="font-bold text-gray-900">{member.name}'s Activity</h3>
                            <p className="text-xs text-gray-500">Recent Assignments & Tasks</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition-colors" aria-label="Close activity log"><XIcon className="w-5 h-5" /></button>
                </div>
                
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>
                    ) : tasks.length === 0 ? (
                        <div className="py-8">
                            <EmptyState
                                title="No Recent Activity"
                                description="This user hasn't been assigned any tasks recently."
                                icon={<ClockIcon className="w-12 h-12 text-gray-300 dark:text-gray-500" />}
                            />
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {tasks.map(task => (
                                <div key={task.id} className="p-4 bg-white border border-gray-100 rounded-xl shadow-sm hover:border-indigo-100 transition-colors">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h4 className="font-bold text-gray-800 text-sm flex items-center flex-wrap gap-1">
                                                {task.title}
                                                {task.is_recurring && <span className="text-[10px] font-normal text-blue-500 bg-blue-50 px-1 py-0.5 rounded border border-blue-100">(🔁 定期)</span>}
                                            </h4>
                                            <p className="text-xs text-gray-500 mt-1 line-clamp-1">{task.description}</p>
                                        </div>
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                            task.status === 'done' ? 'bg-green-100 text-green-700' :
                                            task.status === 'doing' ? 'bg-blue-100 text-blue-700' :
                                            'bg-gray-100 text-gray-600'
                                        }`}>
                                            {task.status}
                                        </span>
                                    </div>
                                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                                        <span>Updated: {dateFormatter.format(new Date(task.updated_at || Date.now()))}</span>
                                        <span>Priority: {task.priority}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
             </div>
        </div>
    );
};
