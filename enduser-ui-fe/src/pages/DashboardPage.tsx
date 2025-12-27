import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../services/api.ts';
import { Task, TaskStatus, TaskPriority, Project, AssignableUser } from '../types.ts';
import { GanttChartIcon, KanbanIcon, ListIcon, TableIcon, PlusIcon, ChevronDownIcon, ChevronsUpDownIcon, PaperclipIcon } from '../components/Icons.tsx';
import { TaskModal } from '../components/TaskModal.tsx';
import { ProjectModal } from '../components/ProjectModal.tsx';
import UserAvatar from '../components/UserAvatar.tsx';
import { select, extent, scaleTime, scaleBand, axisTop, timeFormat, timeDay, timeWeek, timeMonth } from 'd3';

type ViewMode = 'list' | 'table' | 'kanban' | 'gantt';
type SortableTaskKeys = 'title' | 'due_date' | 'priority' | 'status' | 'completed_at' | 'created_at';
type SortDirection = 'ascending' | 'descending';

// ... (color and indicator constants remain the same)

const DashboardPage: React.FC = () => {
  // ... (state definitions remain the same)
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [employees, setEmployees] = useState<AssignableUser[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [editingTask, setEditingTask] = useState<Task | null | undefined>(undefined);
  const [isProjectModalOpen, setProjectModalOpen] = useState(false);
  const [sortConfig, setSortConfig] = useState<{ key: SortableTaskKeys; direction: SortDirection } | null>({ key: 'created_at', direction: 'ascending' });

  const isTaskModalOpen = editingTask !== undefined;

  // --- Data Fetching Logic with useCallback ---
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [tasksData, employeesData, projectsData] = await Promise.all([
        api.getTasks(),
        api.getAssignableUsers(),
        api.getProjects(),
      ]);
      setTasks(tasksData || []);
      setEmployees(employeesData || []);
      setProjects(projectsData || []);
      if (projectsData && projectsData.length > 0 && selectedProjectId === 'all') {
        setSelectedProjectId(projectsData[0].id);
      }
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
        <h1 className="text-3xl font-bold">{currentProject ? `${currentProject.title} Tasks` : 'All Tasks'}</h1>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full md:w-auto">
            <div className="relative">
                <select
                    id="project-filter"
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="w-full sm:w-48 appearance-none rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                    {projects.map((project) => (
                        <option key={project.id} value={project.id}>
                            {project.title}
                        </option>
                    ))}
                </select>
                <ChevronDownIcon className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            </div>

            <div className="flex items-center rounded-md bg-gray-100 p-1">
                 <button onClick={() => setViewMode('list')} className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}><ListIcon className="h-5 w-5" /></button>
                 <button onClick={() => setViewMode('table')} className={`p-1.5 rounded ${viewMode === 'table' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}><TableIcon className="h-5 w-5" /></button>
                 <button onClick={() => setViewMode('kanban')} className={`p-1.5 rounded ${viewMode === 'kanban' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}><KanbanIcon className="h-5 w-5" /></button>
                 <button onClick={() => setViewMode('gantt')} className={`p-1.5 rounded ${viewMode === 'gantt' ? 'bg-white shadow-sm' : 'hover:bg-gray-200'}`}><GanttChartIcon className="h-5 w-5" /></button>
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <button
                onClick={() => setProjectModalOpen(true)}
                className="rounded-md border bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                New Project
              </button>

              <button
                onClick={() => setEditingTask(null)}
                className="flex items-center justify-center gap-2 rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                <PlusIcon className="h-5 w-5" />
                New Task
              </button>
            </div>
        </div>
      </header>
      
      {/* Sorting controls remain the same */}

      <div className="flex-1 overflow-auto">
        {/* View components remain the same */}
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
