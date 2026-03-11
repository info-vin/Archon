import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../services/api.ts';
import { Task, TaskStatus, TaskPriority, Project } from '../types.ts';
import { GanttChartIcon, KanbanIcon, ListIcon, TableIcon, PlusIcon, ChevronDownIcon, ChevronsUpDownIcon, PaperclipIcon, ClockIcon } from '../components/Icons.tsx';
import { TaskModal } from '../components/TaskModal.tsx';
import { ProjectModal } from '../components/ProjectModal.tsx';
import { ClockInWidget } from '../components/ClockInWidget.tsx';
import UserAvatar from '../components/UserAvatar.tsx';
import { select, extent, scaleTime, scaleBand, axisTop, timeFormat, timeDay, timeWeek } from 'd3';
import { useAuth } from '@/hooks/useAuth';

type ViewMode = 'list' | 'table' | 'kanban' | 'gantt';
type SortableTaskKeys = 'title' | 'due_date' | 'priority' | 'status' | 'completed_at' | 'created_at';
type SortDirection = 'ascending' | 'descending';

// Helper functions and components for views
const PriorityBadge: React.FC<{ priority: TaskPriority; variant?: 'badge' | 'indicator' | 'stripe' }> = ({ priority, variant = 'badge' }) => {
  const p = (priority || 'low').toLowerCase();
  
  const config: Record<string, { dot: string; text: string; bg: string; stripe: string }> = {
    high: { dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50', stripe: 'bg-red-500' },
    medium: { dot: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50', stripe: 'bg-amber-500' },
    low: { dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50', stripe: 'bg-green-500' },
    critical: { dot: 'bg-purple-600', text: 'text-purple-700', bg: 'bg-purple-50', stripe: 'bg-purple-600' },
  };

  const style = config[p] || { dot: 'bg-gray-400', text: 'text-gray-700', bg: 'bg-gray-100', stripe: 'bg-gray-400' };

  if (variant === 'stripe') return <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${style.stripe}`} />;
  if (variant === 'indicator') return <span className={`${style.text.replace('700', '500')} mr-2`}>●</span>;
  
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${style.bg} ${style.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      {priority}
    </span>
  );
};

const statusIndicator = (status: TaskStatus) => {
  const s = (status || 'todo').toLowerCase();
  const styles: Record<string, string> = {
    todo: 'bg-gray-200 text-gray-800',
    doing: 'bg-blue-200 text-blue-800',
    done: 'bg-green-200 text-green-800',
    review: 'bg-purple-200 text-purple-800',
  };
  return <span className={`px-2 py-1 rounded-full text-xs font-semibold ${styles[s] || 'bg-gray-100'}`}>{status}</span>;
};

// --- View Components ---
// Optimized: Memoized view components to prevent unnecessary re-renders when parent state updates
const ListView: React.FC<{ tasks: Task[]; setEditingTask: (task: Task) => void; userMap: Record<string, any> }> = React.memo(({ tasks, setEditingTask, userMap }) => (
  <ul className="space-y-3">
    {tasks.map(task => {
        return (
            <li key={task.id} onClick={() => setEditingTask(task)} className="group relative overflow-hidden bg-white/70 backdrop-blur-md rounded-xl border border-white/50 shadow-sm hover:shadow-md transition-all cursor-pointer p-4 pl-5">
                {/* Priority Stripe */}
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
                        <span className="text-xs text-gray-400 font-mono mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity">#{task.id.slice(0,6)}</span>
                    </div>
                
                    <div className="flex items-center gap-4 mt-1">
                        {/* Assignee Avatar */}
                        {task.assignee && (
                            <div className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-50 transition-colors">
                                <UserAvatar 
                                    name={task.assignee} 
                                    isAI={task.assignee_id?.startsWith('agent-') || task.assignee.toLowerCase().includes('bot')} 
                                    role={
                                        // Try to find role by ID first, then Name. Ensure we fallback gracefully.
                                        (userMap[task.assignee_id || '']?.role) || 
                                        (userMap[task.assignee]?.role) || 
                                        (task.assignee === 'Sales' ? 'sales' : undefined) // Temporary fallback for 'Sales' user
                                    }
                                    size={24} 
                                />
                                <span className="text-xs font-semibold text-gray-600 max-w-[80px] truncate hidden sm:block">{task.assignee}</span>
                            </div>
                        )}
                        
                        {/* Attachment Badge */}
                        {task.attachments && task.attachments.length > 0 && (
                            <div data-testid="attachment-badge" className="flex items-center text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg font-medium">
                                <PaperclipIcon className="h-3 w-3 mr-1" />
                                <span>{task.attachments.length}</span>
                            </div>
                        )}
                        
                        <div className="min-w-[80px] text-center">
                             {statusIndicator(task.status)}
                        </div>
                        
                        <div className={`flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg ${task.due_date && new Date(task.due_date) < new Date() ? 'text-red-600 bg-red-50' : 'text-gray-500 bg-gray-50'}`}>
                            <ClockIcon className="w-3 h-3" />
                            {task.due_date ? new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '-'}
                        </div>
                    </div>
                </div>
            </li>
        );
    })}
  </ul>
));

const TableView: React.FC<{
  tasks: Task[];
  setEditingTask: (task: Task) => void;
  requestSort: (key: SortableTaskKeys) => void;
  sortConfig: { key: SortableTaskKeys; direction: SortDirection } | null;
  userMap: Record<string, any>;
  projectMap: Record<string, string>;
}> = React.memo(({ tasks, setEditingTask, requestSort, sortConfig, userMap, projectMap }) => {
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
                <td className="px-6 py-4">{statusIndicator(task.status)}</td>
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

const KanbanView: React.FC<{
  tasks: Task[];
  updateTaskStatus: (taskId: string, newStatus: TaskStatus) => void;
  setEditingTask: (task: Task) => void;
}> = React.memo(({ tasks, updateTaskStatus, setEditingTask }) => {
  const statuses: TaskStatus[] = [TaskStatus.TODO, TaskStatus.DOING, TaskStatus.REVIEW, TaskStatus.DONE];
  const tasksByStatus = useMemo(() => {
    const grouped: { [key in TaskStatus]?: Task[] } = {};
    statuses.forEach(status => grouped[status] = []);
    tasks.forEach(task => {
      if (grouped[task.status]) {
        grouped[task.status]!.push(task);
      }
    });
    return grouped;
  }, [tasks]);

  const onDragStart = (e: React.DragEvent<HTMLDivElement>, taskId: string) => {
    e.dataTransfer.setData("taskId", taskId);
  };
  const onDrop = (e: React.DragEvent<HTMLDivElement>, newStatus: TaskStatus) => {
    const taskId = e.dataTransfer.getData("taskId");
    updateTaskStatus(taskId, newStatus);
  };
  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 h-full p-2">
      {statuses.map(status => (
        <div key={status} className="bg-gray-50/50 rounded-2xl p-4 flex flex-col gap-4 border border-gray-100" onDrop={(e) => onDrop(e, status)} onDragOver={onDragOver}>
          <div className="flex justify-between items-center border-b border-gray-200 pb-3">
             <h3 className="font-bold text-gray-700 capitalize flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${status.toLowerCase() === 'todo' ? 'bg-gray-400' : status.toLowerCase() === 'doing' ? 'bg-blue-400' : status.toLowerCase() === 'review' ? 'bg-purple-400' : 'bg-green-400'}`}></span>
                {status}
             </h3>
             <span className="bg-white px-2 py-0.5 rounded-full text-xs font-bold text-gray-500 shadow-sm">{tasksByStatus[status]?.length || 0}</span>
          </div>
          
          <div className="flex-1 space-y-3 overflow-y-auto pr-1">
            {tasksByStatus[status]?.map(task => {
               return (
                  <div 
                    key={task.id} 
                    draggable 
                    onDragStart={(e) => onDragStart(e, task.id)} 
                    onClick={() => setEditingTask(task)} 
                    className="relative bg-white p-4 rounded-xl shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing overflow-hidden transition-all group border border-gray-100"
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
                                <UserAvatar name={task.assignee} size={18} isAI={task.assignee.toLowerCase().includes('bot')} />
                                <span className="text-[10px] font-medium text-gray-500 truncate max-w-[80px]">{task.assignee.split(' ')[0]}</span>
                            </div>
                         ) : (
                             <span className="text-[10px] py-1 px-2 bg-gray-100 rounded text-gray-400 font-medium">Unassigned</span>
                         )}
                         
                         {task.due_date && (
                             <div className={`text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 ${new Date(task.due_date) < new Date() ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'}`}>
                                 <ClockIcon className="w-3 h-3" />
                                 {new Date(task.due_date).toLocaleDateString(undefined, {month:'short', day:'numeric'})}
                             </div>
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

const GanttView: React.FC<{ tasks: Task[] }> = React.memo(({ tasks }) => {
  const svgRef = React.useRef<SVGSVGElement>(null);
  const validTasks = useMemo(() => tasks.filter(d => d.due_date && d.created_at), [tasks]);

  useEffect(() => {
    if (!svgRef.current || validTasks.length === 0) {
        if (svgRef.current) select(svgRef.current).html(""); // Clear if no valid tasks
        return;
    };

    const margin = { top: 20, right: 30, bottom: 30, left: 150 };
    const width = 800 - margin.left - margin.right;
    const height = validTasks.length * 35;

    const svg = select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .html("");

    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const timeDomain = extent(validTasks, d => new Date(d.created_at)) as [Date, Date];
    const maxDueDate = extent(validTasks, d => new Date(d.due_date!)) as [Date, Date];
    timeDomain[1] = new Date(Math.max(timeDomain[1].getTime(), maxDueDate[1].getTime()));

    timeDomain[0] = timeDay.offset(timeDomain[0], -1);
    timeDomain[1] = timeDay.offset(timeDomain[1], 1);

    const x = scaleTime().domain(timeDomain).range([0, width]);
    const y = scaleBand().domain(validTasks.map(d => d.title)).range([0, height]).padding(0.2);

    g.append("g").attr("class", "x-axis").call(axisTop(x).ticks(timeWeek).tickFormat(timeFormat("%b %d") as any));

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? "#cbd5e1" : "#475569";

    g.append("g")
        .attr("class", "y-axis")
        .call(axis => axis.selectAll("text").remove())
        .selectAll("text.label")
        .data(validTasks)
        .enter()
        .append("text")
        .attr("class", "label")
        .text(d => d.title)
        .attr("x", -10)
        .attr("y", d => y(d.title)! + y.bandwidth() / 2)
        .attr("dy", "0.35em")
        .attr("text-anchor", "end")
        .style("font-size", "12px")
        .attr("fill", textColor);

    g.selectAll(".bar")
      .data(validTasks)
      .enter().append("rect")
      .attr("class", "bar")
      .attr("y", d => y(d.title)!)
      .attr("height", y.bandwidth())
      .attr("x", d => x(new Date(d.created_at)))
      .attr("width", d => Math.max(0, x(new Date(d.due_date!)) - x(new Date(d.created_at))))
      .attr("fill", "steelblue");

  }, [validTasks]);

  return (
    <div className="p-4 overflow-auto">
      <svg ref={svgRef}></svg>
      {validTasks.length === 0 && <p>No tasks with start and end dates to display in Gantt chart.</p>}
    </div>
  );
});

// Import VisitLogModal and MapPinIcon
import { VisitLogModal } from '../features/marketing/components/VisitLogModal.tsx';
import { MapPinIcon } from '../components/Icons.tsx';

const DashboardPage: React.FC = () => {
  const { isAdmin } = useAuth();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [tasks, setTasks] = useState<Task[]>([]);
  // const [employees, setEmployees] = useState<AssignableUser[]>([]); // Removed unused
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [editingTask, setEditingTask] = useState<Task | null | undefined>(undefined);
  const [isProjectModalOpen, setProjectModalOpen] = useState(false);
  const [isProjectDropdownOpen, setProjectDropdownOpen] = useState(false);
  const [isVisitModalOpen, setVisitModalOpen] = useState(false);
  const [sortConfig, setSortConfig] = useState<{ key: SortableTaskKeys; direction: SortDirection } | null>({ key: 'created_at', direction: 'ascending' });
  const [userMap, setUserMap] = useState<Record<string, any>>({}); // Map user ID/Name to User Object for Roles

  const isTaskModalOpen = editingTask !== undefined;

  // --- Data Fetching Logic with useCallback ---
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [tasksRes, projectsData, usersRes, agentsRes] = await Promise.all([
        api.getTasks(true), // Include closed tasks so users can see/archive them
        api.getProjects(),
        api.getAssignableUsers(),
        api.getAssignableAgents()
      ]);
      
      setTasks(tasksRes || []);
      setProjects(projectsData || []);

      // Build User Map
      const map: Record<string, any> = {};
      (usersRes || []).forEach((u: any) => { map[u.id] = u; map[u.name] = u; });
      (agentsRes || []).forEach((a: any) => { 
          const agent = { ...a, role: 'ai_agent' };
          map[a.id] = agent; 
          map[a.name] = agent; 
      });
      setUserMap(map);

    } catch (error: any) {
      console.error("Failed to fetch data:", error);
      // In a real app, you might use a toast notification library here
      alert(`Failed to load dashboard data: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [selectedProjectId]); // Dependency ensures re-fetch if project selection changes, might remove if not desired

  // --- Initial Data Load ---
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ... (useMemo hooks for filteredTasks, sortedTasks, currentProject remain the same)
  const filteredTasks = useMemo(() => {
    if (selectedProjectId === 'all') return tasks;
    return tasks?.filter(task => task.project_id === selectedProjectId) || [];
  }, [tasks, selectedProjectId]);

  const projectMap = useMemo(() => {
    const map: Record<string, string> = {};
    projects.forEach(p => { map[p.id] = p.title; });
    return map;
  }, [projects]);

  const STATUS_WEIGHTS: Record<string, number> = { 'todo': 1, 'doing': 2, 'review': 3, 'done': 4 };
  const PRIORITY_WEIGHTS: Record<string, number> = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };

  const sortedTasks = useMemo(() => {
    let sortableTasks = [...filteredTasks];
    if (sortConfig !== null) {
      sortableTasks.sort((a, b) => {
        let valA: any = a[sortConfig.key] || '';
        let valB: any = b[sortConfig.key] || '';

        // Custom weights for Status and Priority
        if (sortConfig.key === 'status') {
            valA = STATUS_WEIGHTS[valA.toLowerCase()] || 0;
            valB = STATUS_WEIGHTS[valB.toLowerCase()] || 0;
        } else if (sortConfig.key === 'priority') {
            valA = PRIORITY_WEIGHTS[valA.toLowerCase()] || 0;
            valB = PRIORITY_WEIGHTS[valB.toLowerCase()] || 0;
        }

        if (valA < valB) return sortConfig.direction === 'ascending' ? -1 : 1;
        if (valA > valB) return sortConfig.direction === 'ascending' ? 1 : -1;
        return 0;
      });
    }
    return sortableTasks;
  }, [filteredTasks, sortConfig]);

  const currentProject = useMemo(() => {
    return projects?.find(p => p.id === selectedProjectId);
  }, [projects, selectedProjectId]);


  // --- Event Handlers ---
  const requestSort = useCallback((key: SortableTaskKeys) => {
    setSortConfig((currentConfig) => {
        let direction: SortDirection = 'ascending';
        if (currentConfig && currentConfig.key === key && currentConfig.direction === 'ascending') {
          direction = 'descending';
        }
        return { key, direction };
    });
  }, []);

  const updateTaskStatus = useCallback(async (taskId: string, newStatus: TaskStatus) => {
    try {
      await api.updateTask(taskId, { status: newStatus });
      await fetchData(); // Re-fetch data to ensure consistency
    } catch (error: any) {
      console.error("Failed to update task status:", error);
      alert(`Failed to update task status: ${error.message}`);
    }
  }, [fetchData]);

  // Corrected handler to re-fetch data after creation
  const handleTaskCreated = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  const handleTaskUpdated = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  const handleProjectCreated = useCallback(async () => {
    await fetchData();
  }, [fetchData]);


  if (isLoading) return <div className="flex items-center justify-center h-full">Loading...</div>;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background">
      {/* Header section remains the same */}
      <header className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">{currentProject ? `${currentProject.title} Tasks` : (isAdmin ? 'All Tasks' : 'My Tasks')}</h1>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full md:w-auto">
          {/* Project Dropdown */}
          <div className="relative">
            <button 
                onClick={() => setProjectDropdownOpen(!isProjectDropdownOpen)} 
                className="flex items-center justify-between w-full sm:w-48 px-4 py-2 bg-card border border-border rounded-md text-sm hover:bg-secondary/50 transition-colors"
            >
              <span className="truncate mr-2">{currentProject?.title || (selectedProjectId === 'all' ? 'All Projects' : 'Select Project')}</span>
              <ChevronDownIcon className="h-4 w-4 flex-shrink-0" />
            </button>
            
            {isProjectDropdownOpen && (
                <div className="absolute top-full left-0 mt-1 w-56 bg-popover border border-border rounded-md shadow-lg z-50 py-1">
                    <button
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-secondary ${selectedProjectId === 'all' ? 'bg-secondary/50 font-medium' : ''}`}
                        onClick={() => { setSelectedProjectId('all'); setProjectDropdownOpen(false); }}
                    >
                        All Projects
                    </button>
                    <div className="border-t border-border my-1"></div>
                    {projects.map(project => (
                        <button
                            key={project.id}
                            className={`w-full text-left px-4 py-2 text-sm hover:bg-secondary ${selectedProjectId === project.id ? 'bg-secondary/50 font-medium' : ''}`}
                            onClick={() => { setSelectedProjectId(project.id); setProjectDropdownOpen(false); }}
                        >
                            {project.title}
                        </button>
                    ))}
                    <div className="border-t border-border my-1"></div>
                    <button
                        className="w-full text-left px-4 py-2 text-sm text-primary hover:bg-secondary flex items-center"
                        onClick={() => { setProjectModalOpen(true); setProjectDropdownOpen(false); }}
                    >
                        <PlusIcon className="h-3 w-3 mr-2" />
                        Create New Project
                    </button>
                </div>
            )}
          </div>

          {/* View Mode Buttons */}
          <div className="flex items-center bg-card border border-border rounded-md p-1" role="group" aria-label="View mode">
            <button onClick={() => setViewMode('list')} aria-label="List view" title="List view" aria-pressed={viewMode === 'list'} className={`p-1.5 rounded-md transition-colors ${viewMode === 'list' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}><ListIcon className="h-5 w-5" /></button>
            <button onClick={() => setViewMode('table')} aria-label="Table view" title="Table view" aria-pressed={viewMode === 'table'} className={`p-1.5 rounded-md transition-colors ${viewMode === 'table' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}><TableIcon className="h-5 w-5" /></button>
            <button onClick={() => setViewMode('kanban')} aria-label="Kanban view" title="Kanban view" aria-pressed={viewMode === 'kanban'} className={`p-1.5 rounded-md transition-colors ${viewMode === 'kanban' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}><KanbanIcon className="h-5 w-5" /></button>
            <button onClick={() => setViewMode('gantt')} aria-label="Gantt chart view" title="Gantt chart view" aria-pressed={viewMode === 'gantt'} className={`p-1.5 rounded-md transition-colors ${viewMode === 'gantt' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}><GanttChartIcon className="h-5 w-5" /></button>
          </div>

          {/* New Task Button */}
          <button onClick={() => setEditingTask(null)} className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-semibold hover:bg-primary/90 flex items-center gap-2">
            <PlusIcon className="h-4 w-4" />
            New Task
          </button>
        </div>
      </header>
      
      {/* Sorting controls remain the same */}

      <div className="flex-1 overflow-auto">
        <ClockInWidget />
        {viewMode === 'list' && <ListView tasks={sortedTasks} setEditingTask={setEditingTask} userMap={userMap} />}
        {viewMode === 'table' && <TableView tasks={sortedTasks} setEditingTask={setEditingTask} requestSort={requestSort} sortConfig={sortConfig} userMap={userMap} projectMap={projectMap} />}
        {viewMode === 'kanban' && <KanbanView tasks={filteredTasks} updateTaskStatus={updateTaskStatus} setEditingTask={setEditingTask} />}
        {viewMode === 'gantt' && <GanttView tasks={sortedTasks} />}
      </div>
      
      {isTaskModalOpen && (
        <TaskModal
          task={editingTask}
          onClose={() => setEditingTask(undefined)}
          onTaskCreated={handleTaskCreated}
          onTaskUpdated={handleTaskUpdated}
          projectId={selectedProjectId !== 'all' ? selectedProjectId : (projects && projects.length > 0 ? projects[0].id : '')}
        />
      )}

      {isProjectModalOpen && (
        <ProjectModal
          onClose={() => setProjectModalOpen(false)}
          onProjectCreated={handleProjectCreated}
        />
      )}

      {isVisitModalOpen && (
        <VisitLogModal
            onClose={() => setVisitModalOpen(false)}
            onSuccess={() => {
                setVisitModalOpen(false);
            }} 
        />
      )}
      
      {/* Mobile Visit FAB */}
      <button 
          onClick={() => setVisitModalOpen(true)}
          className="md:hidden fixed bottom-20 right-4 w-14 h-14 bg-indigo-600 text-white rounded-full shadow-lg flex items-center justify-center z-40 hover:bg-indigo-700 active:scale-95 transition-all"
          aria-label="New Visit Log"
      >
          <MapPinIcon className="w-6 h-6" />
      </button>
    </div>
  );
};

// ... (Sub-components like ListView, KanbanView etc. are assumed to be in the file and correct)
export default DashboardPage;
