import React, { useState, useEffect } from 'react';
import { AssignableUser, Task, TaskPriority, NewTaskData, UpdateTaskData } from '../types.ts';
import { api } from '../services/api';
import { XIcon, RefreshCwIcon } from './Icons.tsx';
import { KnowledgeSelector } from './KnowledgeSelector.tsx';
import { TaskAgentGroupChat } from './task-modal/TaskAgentGroupChat';
import { TaskGeneralTab } from './task-modal/TaskGeneralTab';
import { TaskAssignmentTab } from './task-modal/TaskAssignmentTab';

interface TaskModalProps {
  task?: Task | null;
  onClose: () => void;
  onTaskCreated: () => void;
  onTaskUpdated: () => void;
  initialProjectId?: string;
}

const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

type TabType = 'general' | 'assignment' | 'knowledge' | 'report';

export const TaskModal: React.FC<TaskModalProps> = ({ task, onClose, onTaskCreated, onTaskUpdated, initialProjectId }) => {
  const isEditMode = !!(task && task.id);

  const [activeTab, setActiveTab] = useState<TabType>('general');
  const [title, setTitle] = useState(task?.title || '');
  const [description, setDescription] = useState(task?.description || '');
  const [assigneeId, setAssigneeId] = useState(task?.assignee_id || '');
  const [dueDate, setDueDate] = useState(() => {
    if (task?.due_date) {
      const date = new Date(task.due_date);
      return new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
    }
    return '';
  });
  const [priority, setPriority] = useState<TaskPriority>(task?.priority || TaskPriority.MEDIUM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [assignableUsers, setAssignableUsers] = useState<AssignableUser[]>([]);
  const [collaboratorAgentIds, setCollaboratorAgentIds] = useState<string[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  
  const [selectedKnowledgeIds, setSelectedKnowledgeIds] = useState<string[]>(() => {
    if (task?.sources && Array.isArray(task.sources)) {
      return task.sources
        .filter((s: any) => s.source_id && s.type === 'knowledge_item')
        .map((s: any) => s.source_id);
    }
    return [];
  });
  const [currentUser, setCurrentUser] = useState<any>(null);
  
  // David's Architect Workflow States
  const [isRecurring, setIsRecurring] = useState(task?.is_recurring || false);
  const [crawlerTargetId, setCrawlerTargetId] = useState(task?.crawler_target_id || '');
  const [crawlerTargets, setCrawlerTargets] = useState<any[]>([]);
  const [frequency, setFrequency] = useState('daily');
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(initialProjectId || task?.project_id || '');

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoadingUsers(true);
        // Step 1: Priority Data (Users, Agents, Projects)
        const [usersData, aiAgentsData, user, projectsData] = await Promise.all([
          api.getAssignableUsers(),
          api.getAssignableAgents(),
          api.getCurrentUser(),
          api.getProjects()
        ]);
        
        setCurrentUser(user);
        setProjects(projectsData || []);
        
        // PRPs Phase 4.4: Dynamic Assignee Filtering based on Role
        const isManager = user?.role === 'manager' || user?.role === 'admin' || user?.role === 'system_admin';
        
        let filteredUsers = usersData || [];
        if (!isManager && user) {
          // Member (Alice/Bob) can only assign to themselves
          filteredUsers = (usersData || []).filter(u => u.id === user.id);
        }

        // Combine humans and AI agents, removing duplicates by ID
        const combined = [...filteredUsers, ...(aiAgentsData || [])];
        const uniqueUsers = Array.from(new Map(combined.map(u => [u.id, u])).values());
        setAssignableUsers(uniqueUsers);
        
        // If no projectId passed, default to first available project
        if (!selectedProjectId && projectsData && projectsData.length > 0) {
            setSelectedProjectId(projectsData[0].id);
        }

        // PRPs FB-03: Default assignee to current user for new tasks
        if (!isEditMode && user && !assigneeId) {
            setAssigneeId(user.id);
        }

        // Step 2: Background Data (Crawler Targets) - Can fail gracefully without blocking main UI
        api.getCrawlerTargets().then(targets => {
          setCrawlerTargets(targets || []);
        }).catch(err => {
          console.warn("Non-blocking failure fetching crawler targets:", err);
          setCrawlerTargets([]);
        });

      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setIsLoadingUsers(false);
      }
    };

    fetchInitialData();
  }, []);

  useEffect(() => {
    if (isEditMode && task) {
      // In edit mode, if the task prop changes drastically we might want to reset,
      // but usually the modal is unmounted and remounted. We will keep only dynamic derivations if needed.
    }
  }, [task, isEditMode]);

  const handleRefineWithAI = async () => {
    if (!title) {
        alert("Please enter a title first.");
        return;
    }
    setIsRefining(true);
    console.log('POBot refining with:', title, description);
    try {
        const refined = await api.refineTaskDescription(title, description);
        console.log('POBot result:', refined);
        setDescription(refined);
    } catch (error) {
        console.error("POBot failed:", error);
        alert("Failed to refine description with AI.");
    } finally {
        setIsRefining(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !dueDate) {
      alert('Title and Due Date are required.');
      return;
    }
    
    const finalProjectId = isEditMode ? task.project_id : selectedProjectId;
    if (!finalProjectId) {
      alert('A project must be selected to create or update a task.');
      return;
    }

    setIsSubmitting(true);

    try {
      if (isEditMode) {
        const updatedData: UpdateTaskData = {
          id: task.id,
          title,
          description,
          status: task.status,
          assigneeId: assigneeId || null,
          due_date: new Date(dueDate).toISOString(),
          priority,
          is_recurring: isRecurring,
          crawler_target_id: crawlerTargetId || null,
          collaborator_agent_ids: collaboratorAgentIds,
          schedule_config: isRecurring ? { frequency } : null
        };
        await api.updateTask(task.id, updatedData);
        onTaskUpdated();
        alert('Task updated successfully!');
      } else {
        const newTaskData: NewTaskData = {
          project_id: finalProjectId,
          title,
          description,
          status: 'todo' as any, // Default status
          assigneeId: assigneeId || null,
          due_date: new Date(dueDate).toISOString(),
          priority,
          knowledge_source_ids: selectedKnowledgeIds,
          is_recurring: isRecurring,
          crawler_target_id: crawlerTargetId || null,
          schedule_config: isRecurring ? { frequency } : null
        };
        await api.createTask(newTaskData);
        onTaskCreated();
        alert('Task created successfully!');
      }
      onClose();
    } catch (error: any) {
        console.error("Failed to save task:", error);
        const errorMessage = error.message || (typeof error === 'object' ? JSON.stringify(error) : String(error));
        alert(`Failed to save task: ${errorMessage}`);
    } finally {
        setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!task || !task.id) return;
    if (!window.confirm('Are you sure you want to archive this task? It will be hidden from all views.')) return;

    setIsSubmitting(true);
    try {
      await api.deleteTask(task.id);
      onTaskUpdated(); // Reuse update trigger to refresh list
      alert('Task archived successfully!');
      onClose();
    } catch (error: any) {
      console.error("Failed to archive task:", error);
      alert(`Failed to archive task: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const canArchive = isEditMode && currentUser && (
    currentUser.role === 'system_admin' || 
    currentUser.role === 'manager' || 
    currentUser.id === task?.assignee_id
  );

  const tabs = [
    { id: 'general', label: 'General' },
    { id: 'assignment', label: 'Assignment & Automation' },
    { id: 'knowledge', label: 'Knowledge' }
  ];
  if (isEditMode && task?.agent_output) {
    tabs.push({ id: 'report', label: 'AI Report' });
  }

  // Ensure active tab is valid if task changes
  useEffect(() => {
    if (activeTab === 'report' && (!isEditMode || !task?.agent_output)) {
      setActiveTab('general');
    }
  }, [isEditMode, task, activeTab]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-start justify-center p-4 md:items-center overflow-y-auto" aria-modal="true" role="dialog">
      <div className="bg-card rounded-lg shadow-xl w-full max-w-lg p-6 relative my-8 md:my-0 max-h-none md:max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center mb-4 flex-shrink-0">
          <h2 className="text-2xl font-bold">{isEditMode ? 'Edit Task' : 'Create New Task'}</h2>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-secondary" aria-label="Close">
            <XIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Tabs Header */}
        <div className="flex w-full border-b border-border mb-4 flex-shrink-0 overflow-x-auto custom-scrollbar pb-0" role="tablist" aria-label="Task Details Tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex-1 px-2 py-3 text-xs sm:text-sm font-medium border-b-2 transition-colors text-center whitespace-nowrap ${activeTab === tab.id ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto custom-scrollbar pr-1">
          <div className="space-y-4">
            {/* General Tab */}
            <div className={activeTab === 'general' ? 'block' : 'hidden'}>
              <TaskGeneralTab 
                title={title} setTitle={setTitle}
                description={description} setDescription={setDescription}
                selectedProjectId={selectedProjectId} setSelectedProjectId={setSelectedProjectId}
                priority={priority} setPriority={setPriority}
                dueDate={dueDate} setDueDate={setDueDate}
                projects={projects}
                isEditMode={isEditMode}
                isRefining={isRefining}
                handleRefineWithAI={handleRefineWithAI}
                inputClass={inputClass}
              />
            </div>

            {/* Assignment Tab */}
            <div className={activeTab === 'assignment' ? 'block' : 'hidden'}>
              <TaskAssignmentTab 
                assigneeId={assigneeId} setAssigneeId={setAssigneeId}
                assignableUsers={assignableUsers}
                isLoadingUsers={isLoadingUsers}
                collaboratorAgentIds={collaboratorAgentIds} setCollaboratorAgentIds={setCollaboratorAgentIds}
                crawlerTargets={crawlerTargets} crawlerTargetId={crawlerTargetId} setCrawlerTargetId={setCrawlerTargetId}
                isRecurring={isRecurring} setIsRecurring={setIsRecurring}
                frequency={frequency} setFrequency={setFrequency}
                inputClass={inputClass}
              />
            </div>

            {/* Knowledge Tab */}
            <div className={activeTab === 'knowledge' ? 'space-y-4' : 'hidden'}>
              <KnowledgeSelector 
                selectedIds={selectedKnowledgeIds} 
                onChange={setSelectedKnowledgeIds}
                disabled={isSubmitting}
              />
            </div>

            {/* AI Report Tab */}
            <div className={activeTab === 'report' ? 'space-y-4' : 'hidden'}>
               {task && <TaskAgentGroupChat task={task} />}
            </div>
          </div>

          {/* Footer Controls */}
          <div className="flex justify-between items-center pt-4 mt-6 border-t border-border flex-shrink-0">
            <div>
              {canArchive && (
                <button 
                  type="button" 
                  onClick={handleDelete} 
                  disabled={isSubmitting}
                  aria-label={isSubmitting ? 'Archiving task...' : 'Archive Task'}
                  className="px-4 py-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50 text-sm flex items-center justify-center gap-2"
                >
                  {isSubmitting && <RefreshCwIcon className="w-4 h-4 animate-spin" />}
                  {isSubmitting ? 'Archiving...' : 'Archive Task'}
                </button>
              )}
            </div>
            <div className="flex space-x-3">
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80">
                Cancel
              </button>
              <button type="submit" disabled={isSubmitting} className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2" aria-label={isSubmitting ? 'Saving task...' : (isEditMode ? 'Save changes' : 'Create task')}>
                {isSubmitting && <RefreshCwIcon className="w-4 h-4 animate-spin" />}
                {isSubmitting ? 'Saving...' : (isEditMode ? 'Save Changes' : 'Create Task')}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

