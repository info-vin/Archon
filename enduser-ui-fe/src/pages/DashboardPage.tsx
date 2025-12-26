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
            {/* Project filter and view buttons remain the same */}
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
