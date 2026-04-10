import React, { useState, useMemo } from 'react';
import { Task, ViewMode } from '../types';
import { GanttChartIcon, KanbanIcon, ListIcon, TableIcon, PlusIcon, ChevronDownIcon } from '../components/Icons';
import { TaskModal } from '../components/TaskModal';
import { ProjectModal } from '../components/ProjectModal';
import { ClockInWidget } from '../components/ClockInWidget';
import { useAuth } from '@/hooks/useAuth';
import { EmptyState } from '../components/common/EmptyState';

// Feature Components
import { ListView } from '../features/dashboard/components/ListView';
import { TableView } from '../features/dashboard/components/TableView';
import { KanbanView } from '../features/dashboard/components/KanbanView';
import { GanttView } from '../features/dashboard/components/GanttView';
import { useDashboardLogic } from '../features/dashboard/hooks/useDashboardLogic';

const DashboardPage: React.FC = () => {
  const { isAdmin } = useAuth();
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  const {
    projects,
    userMap,
    projectMap,
    sortedTasks,
    filteredTasks,
    isLoading,
    sortConfig,
    fetchData,
    requestSort,
    updateTaskStatus
  } = useDashboardLogic(selectedProjectId);

  const currentProject = useMemo(() => 
    projects.find(p => p.id === selectedProjectId), 
    [projects, selectedProjectId]
  );

  if (isLoading && sortedTasks.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="text-gray-500 font-medium">Loading tasks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 min-w-0 flex flex-col h-full overflow-hidden p-6 bg-background">
      {/* Header section */}
      <header className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
          {currentProject ? `${currentProject.title} Tasks` : (isAdmin ? 'All Tasks' : 'My Tasks')}
        </h1>
        
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full md:w-auto">
          {/* Project Dropdown */}
          <div className="relative">
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="appearance-none w-full bg-card border border-border px-4 py-2 pr-10 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm font-medium"
            >
              <option value="all">All Projects</option>
              {projects.map(project => (
                <option key={project.id} value={project.id}>{project.title}</option>
              ))}
            </select>
            <ChevronDownIcon className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          </div>

          <div className="flex items-center bg-card border border-border rounded-md p-1" role="group" aria-label="View mode">
            <button 
              onClick={() => setViewMode('list')} 
              aria-label="List view" 
              title="List view" 
              aria-pressed={viewMode === 'list'} 
              className={`p-1.5 rounded-md transition-colors ${viewMode === 'list' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}
            >
              <ListIcon className="h-5 w-5" />
            </button>
            <button 
              onClick={() => setViewMode('table')} 
              aria-label="Table view" 
              title="Table view" 
              aria-pressed={viewMode === 'table'} 
              className={`p-1.5 rounded-md transition-colors ${viewMode === 'table' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}
            >
              <TableIcon className="h-5 w-5" />
            </button>
            <button 
              onClick={() => setViewMode('kanban')} 
              aria-label="Kanban view" 
              title="Kanban view" 
              aria-pressed={viewMode === 'kanban'} 
              className={`p-1.5 rounded-md transition-colors ${viewMode === 'kanban' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}
            >
              <KanbanIcon className="h-5 w-5" />
            </button>
            <button 
              onClick={() => setViewMode('gantt')} 
              aria-label="Gantt chart view" 
              title="Gantt chart view" 
              aria-pressed={viewMode === 'gantt'} 
              className={`p-1.5 rounded-md transition-colors ${viewMode === 'gantt' ? 'bg-background shadow-sm' : 'hover:bg-background/50'}`}
            >
              <GanttChartIcon className="h-5 w-5" />
            </button>
          </div>

          <button
            onClick={() => setIsTaskModalOpen(true)}
            className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md font-bold transition-all shadow-lg hover:shadow-indigo-200"
          >
            <PlusIcon className="h-4 w-4" />
            <span>New Task</span>
          </button>

          {isAdmin && (
            <button
              onClick={() => setIsProjectModalOpen(true)}
              className="flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-md font-bold transition-all border border-slate-200"
            >
              <PlusIcon className="h-4 w-4" />
              <span>Project</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        <ClockInWidget />
        <div className="mt-4">
          {!isLoading && sortedTasks.length === 0 ? (
            <EmptyState 
              title="No tasks found" 
              description={selectedProjectId === 'all' ? "You don't have any tasks assigned yet." : "No tasks found for this project."}
              actionLabel="Create New Task"
              onAction={() => setIsTaskModalOpen(true)}
            />
          ) : (
            <>
              {viewMode === 'list' && <ListView tasks={sortedTasks} setEditingTask={setEditingTask} userMap={userMap} />}
              {viewMode === 'table' && <TableView tasks={sortedTasks} setEditingTask={setEditingTask} requestSort={requestSort} sortConfig={sortConfig} userMap={userMap} projectMap={projectMap} />}
              {viewMode === 'kanban' && <KanbanView tasks={filteredTasks} updateTaskStatus={updateTaskStatus} setEditingTask={setEditingTask} userMap={userMap} />}
              {viewMode === 'gantt' && <GanttView tasks={sortedTasks} />}
            </>
          )}
        </div>
      </div>

      {/* Modals */}
      {(isTaskModalOpen || !!editingTask) && (
        <TaskModal
          task={editingTask}
          onClose={() => { setIsTaskModalOpen(false); setEditingTask(null); }}
          onTaskCreated={() => fetchData()}
          onTaskUpdated={() => fetchData()}
          initialProjectId={selectedProjectId !== 'all' ? selectedProjectId : undefined}
        />
      )}
      
      {isProjectModalOpen && (
        <ProjectModal
          onClose={() => setIsProjectModalOpen(false)}
          onProjectCreated={() => fetchData()}
        />
      )}
    </div>
  );
};

export default DashboardPage;
