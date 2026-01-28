import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../services/api.ts';
import { Task, TaskStatus, TaskPriority, Project, AssignableUser } from '../types.ts';
import { GanttChartIcon, KanbanIcon, ListIcon, TableIcon, PlusIcon, ChevronDownIcon, ChevronsUpDownIcon, PaperclipIcon } from '../components/Icons.tsx';
import { TaskModal } from '../components/TaskModal.tsx';
import { ProjectModal } from '../components/ProjectModal.tsx';
import UserAvatar from '../components/UserAvatar.tsx';
import { select, extent, scaleTime, scaleBand, axisTop, timeFormat, timeDay, timeWeek, timeMonth } from 'd3';
import { useAuth } from '../hooks/useAuth.tsx';

type ViewMode = 'list' | 'table' | 'kanban' | 'gantt';
type SortableTaskKeys = 'title' | 'due_date' | 'priority' | 'status' | 'completed_at' | 'created_at';
type SortDirection = 'ascending' | 'descending';

// Helper functions and components for views
const priorityIndicator = (priority: TaskPriority) => {
  const colors = { high: 'text-red-500', medium: 'text-yellow-500', low: 'text-green-500', critical: 'text-purple-600' };
  return <span className={`${colors[priority]} mr-2`}>●</span>;
};

const statusIndicator = (status: TaskStatus) => {
  const styles = {
    todo: 'bg-gray-200 text-gray-800',
    doing: 'bg-blue-200 text-blue-800',
    done: 'bg-green-200 text-green-800',
    review: 'bg-purple-200 text-purple-800',
  };
  return <span className={`px-2 py-1 rounded-full text-xs font-semibold ${styles[status] || 'bg-gray-100'}`}>{status}</span>;
};

// --- View Components ---
const ListView: React.FC<{ tasks: Task[]; setEditingTask: (task: Task) => void }> = ({ tasks, setEditingTask }) => (
  <ul className="space-y-2">
    {tasks.map(task => (
      <li key={task.id} onClick={() => setEditingTask(task)} className="p-4 bg-card rounded-lg shadow-sm cursor-pointer hover:bg-card-hover transition-colors">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            {priorityIndicator(task.priority)}
            <span className="font-medium">{task.title}</span>
          </div>
          <div className="flex items-center space-x-4">
            {/* Assignee Avatar */}
            {task.assignee && (
                <UserAvatar 
                    name={task.assignee} 
                    isAI={task.assignee_id?.startsWith('agent-') || task.assignee.toLowerCase().includes('bot')} 
                    size={24} 
                />
            )}
            {/* Attachment Badge */}
            {task.attachments && task.attachments.length > 0 && (
                <div className="flex items-center text-xs text-muted-foreground bg-secondary/30 px-2 py-1 rounded">
                    <PaperclipIcon className="h-3 w-3 mr-1" />
                    {task.attachments.length} {task.attachments.length === 1 ? task.attachments[0].file_name : 'files'}
                    {/* Hidden text for tests to find filenames if needed */}
                    <span className="sr-only">{task.attachments.map(a => a.file_name).join(', ')}</span>
                </div>
            )}
            {statusIndicator(task.status)}
            <span className="text-sm text-muted-foreground">{task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}</span>
          </div>
        </div>
      </li>
    ))}
  </ul>
);

const TableView: React.FC<{
  tasks: Task[];
  setEditingTask: (task: Task) => void;
  requestSort: (key: SortableTaskKeys) => void;
  sortConfig: { key: SortableTaskKeys; direction: SortDirection } | null;
}> = ({ tasks, setEditingTask, requestSort, sortConfig }) => {
  const getSortIcon = (key: SortableTaskKeys) => {
    if (!sortConfig || sortConfig.key !== key) return <ChevronsUpDownIcon className="h-4 w-4" />;
    return sortConfig.direction === 'ascending' ? '🔼' : '🔽';
  };

  return (
    <table className="w-full text-sm text-left">
      <thead className="text-xs text-muted-foreground uppercase bg-card">
        <tr>
          <th scope="col" className="px-6 py-3 cursor-pointer" onClick={() => requestSort('title')}>Title {getSortIcon('title')}</th>
          <th scope="col" className="px-6 py-3 cursor-pointer" onClick={() => requestSort('status')}>Status {getSortIcon('status')}</th>
          <th scope="col" className="px-6 py-3 cursor-pointer" onClick={() => requestSort('priority')}>Priority {getSortIcon('priority')}</th>
          <th scope="col" className="px-6 py-3 cursor-pointer" onClick={() => requestSort('due_date')}>Due Date {getSortIcon('due_date')}</th>
        </tr>
      </thead>
      <tbody>
        {tasks.map(task => (
          <tr key={task.id} onClick={() => setEditingTask(task)} className="bg-card border-b hover:bg-card-hover cursor-pointer">
            <td className="px-6 py-4 font-medium text-foreground whitespace-nowrap">{task.title}</td>
            <td className="px-6 py-4">{statusIndicator(task.status)}</td>
            <td className="px-6 py-4">{priorityIndicator(task.priority)} {task.priority}</td>
            <td className="px-6 py-4">{task.due_date ? new Date(task.due_date).toLocaleDateString() : 'N/A'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const KanbanView: React.FC<{
  tasks: Task[];
  updateTaskStatus: (taskId: string, newStatus: TaskStatus) => void;
  setEditingTask: (task: Task) => void;
}> = ({ tasks, updateTaskStatus, setEditingTask }) => {
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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-full">
      {statuses.map(status => (
        <div key={status} className="bg-card rounded-lg p-3 flex flex-col" onDrop={(e) => onDrop(e, status)} onDragOver={onDragOver}>
          <h3 className="font-semibold mb-3 capitalize">{status} ({tasksByStatus[status]?.length || 0})</h3>
          <div className="flex-1 space-y-3 overflow-y-auto">
            {tasksByStatus[status]?.map(task => (
              <div key={task.id} draggable onDragStart={(e) => onDragStart(e, task.id)} onClick={() => setEditingTask(task)} className="p-3 bg-background rounded-md shadow-sm cursor-pointer">
                <p className="font-medium text-sm">{task.title}</p>
                 <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-muted-foreground">{task.due_date ? new Date(task.due_date).toLocaleDateString() : ''}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const GanttView: React.FC<{ tasks: Task[] }> = ({ tasks }) => {
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
        .style("font-size", "12px");

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
};

const DashboardPage: React.FC = () => {
  const { isAdmin } = useAuth();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [employees, setEmployees] = useState<AssignableUser[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [editingTask, setEditingTask] = useState<Task | null | undefined>(undefined);
  const [isProjectModalOpen, setProjectModalOpen] = useState(false);
  const [isProjectDropdownOpen, setProjectDropdownOpen] = useState(false);
  const [sortConfig, setSortConfig] = useState<{ key: SortableTaskKeys; direction: SortDirection } | null>({ key: 'created_at', direction: 'ascending' });

  const isTaskModalOpen = editingTask !== undefined;

  // --- Data Fetching Logic with useCallback ---
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [tasksData, projectsData, employeesData] = await Promise.all([
        api.getTasks(true), // Include closed tasks so users can see/archive them
        api.getProjects(),
        api.getAssignableUsers()
      ]);
      setTasks(tasksData || []);
      setEmployees(employeesData || []);
      setProjects(projectsData || []);
      // Auto-selection of the first project removed to support the "All Projects" dashboard view.
    } catch (error: any) {
      console.error("Failed to fetch data:", error);
      // In a real app, you might use a toast notification library here
      alert(`Failed to load dashboard data: ${error.message}`);
    } finally {
      setLoading(false);
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

  const sortedTasks = useMemo(() => {
    let sortableTasks = [...filteredTasks];
    if (sortConfig !== null) {
      sortableTasks.sort((a, b) => {
        if (a[sortConfig.key]! < b[sortConfig.key]!) return sortConfig.direction === 'ascending' ? -1 : 1;
        if (a[sortConfig.key]! > b[sortConfig.key]!) return sortConfig.direction === 'ascending' ? 1 : -1;
        return 0;
      });
    }
    return sortableTasks;
  }, [filteredTasks, sortConfig]);

  const currentProject = useMemo(() => {
    return projects?.find(p => p.id === selectedProjectId);
  }, [projects, selectedProjectId]);


  // --- Event Handlers ---
  const requestSort = (key: SortableTaskKeys) => {
    let direction: SortDirection = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

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


  if (loading) return <div className="flex items-center justify-center h-full">Loading...</div>;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background">
      {/* Header section remains the same */}
      <header className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">{currentProject ? `${currentProject.title} Tasks` : (isAdmin ? 'All Tasks' : 'My Tasks')}</h1>
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
          <div className="flex items-center bg-card border border-border rounded-md p-1">
            <button onClick={() => setViewMode('list')} className={`p-1.5 ${viewMode === 'list' ? 'bg-background' : ''}`}><ListIcon className="h-5 w-5" /></button>
            <button onClick={() => setViewMode('table')} className={`p-1.5 ${viewMode === 'table' ? 'bg-background' : ''}`}><TableIcon className="h-5 w-5" /></button>
            <button onClick={() => setViewMode('kanban')} className={`p-1.5 ${viewMode === 'kanban' ? 'bg-background' : ''}`}><KanbanIcon className="h-5 w-5" /></button>
            <button onClick={() => setViewMode('gantt')} className={`p-1.5 ${viewMode === 'gantt' ? 'bg-background' : ''}`}><GanttChartIcon className="h-5 w-5" /></button>
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
        {viewMode === 'list' && <ListView tasks={sortedTasks} setEditingTask={setEditingTask} />}
        {viewMode === 'table' && <TableView tasks={sortedTasks} setEditingTask={setEditingTask} requestSort={requestSort} sortConfig={sortConfig} />}
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
    </div>
  );
};

// ... (Sub-components like ListView, KanbanView etc. are assumed to be in the file and correct)
export default DashboardPage;
