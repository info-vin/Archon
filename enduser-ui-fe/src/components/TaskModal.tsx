import React, { useState, useEffect } from 'react';
import { AssignableUser, Task, TaskPriority, NewTaskData, UpdateTaskData } from '../types.ts';
import { api } from '../services/api';
import { XIcon, SparklesIcon, RefreshCwIcon } from './Icons.tsx';
import { KnowledgeSelector } from './KnowledgeSelector.tsx';
import { MobileDateTimePicker } from './common/MobileDateTimePicker';

interface TaskModalProps {
  task?: Task | null;
  onClose: () => void;
  onTaskCreated: () => void;
  onTaskUpdated: () => void;
  initialProjectId?: string;
}

const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

export const TaskModal: React.FC<TaskModalProps> = ({ task, onClose, onTaskCreated, onTaskUpdated, initialProjectId }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [assigneeId, setAssigneeId] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [priority, setPriority] = useState<TaskPriority>(TaskPriority.MEDIUM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [assignableUsers, setAssignableUsers] = useState<AssignableUser[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [selectedKnowledgeIds, setSelectedKnowledgeIds] = useState<string[]>([]);
  const [currentUser, setCurrentUser] = useState<any>(null);
  
  // David's Architect Workflow States
  const [isRecurring, setIsRecurring] = useState(false);
  const [crawlerTargetId, setCrawlerTargetId] = useState('');
  const [crawlerTargets, setCrawlerTargets] = useState<any[]>([]);
  const [frequency, setFrequency] = useState('daily');
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>(initialProjectId || '');

  const isEditMode = !!(task && task.id);

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
        
        // Combine humans and AI agents for the assignee list
        const allAssignable = [...(usersData || []), ...(aiAgentsData || [])];
        setAssignableUsers(allAssignable);
        
        // If no projectId passed, default to first available project
        if (!selectedProjectId && projectsData && projectsData.length > 0) {
            setSelectedProjectId(projectsData[0].id);
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
      setTitle(task.title);
      setDescription(task.description || '');
      setAssigneeId(task.assignee_id || '');
      if (task.due_date) {
        // Convert ISO string to local datetime string for input
        const date = new Date(task.due_date);
        const localIso = new Date(date.getTime() - (date.getTimezoneOffset() * 60000)).toISOString().slice(0, 16);
        setDueDate(localIso);
      }
      setPriority(task.priority);
      setIsRecurring(task.is_recurring || false);
      setCrawlerTargetId(task.crawler_target_id || '');
      
      // Initialize selected knowledge IDs from existing sources
      if (task.sources && Array.isArray(task.sources)) {
        const ids = task.sources
          .filter(s => s.source_id && s.type === 'knowledge_item')
          .map(s => s.source_id);
        setSelectedKnowledgeIds(ids);
      }
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
        // Extract readable error from potential JSON object
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-start justify-center p-4 md:items-center overflow-y-auto" aria-modal="true" role="dialog">
      <div className="bg-card rounded-lg shadow-xl w-full max-w-lg p-6 relative my-8 md:my-0 max-h-none md:max-h-[90vh] md:overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">{isEditMode ? 'Edit Task' : 'Create New Task'}</h2>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-secondary" aria-label="Close">
            <XIcon className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="title" className="block text-sm font-medium mb-1">Title</label>
            <input id="title" type="text" value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} required />
          </div>
          <div>
            <div className="flex justify-between items-center mb-1">
                <label htmlFor="description" className="block text-sm font-medium">Description</label>
                <button 
                    type="button" 
                    onClick={handleRefineWithAI} 
                    disabled={isRefining || !title}
                    className="text-xs flex items-center gap-1 text-indigo-600 hover:text-indigo-800 disabled:opacity-50 transition-colors font-medium"
                >
                    <SparklesIcon className="w-3 h-3" />
                    {isRefining ? 'POBot is thinking...' : 'Refine with AI'}
                </button>
            </div>
            <textarea id="description" value={description} onChange={(e) => setDescription(e.target.value)} className={inputClass} rows={6} placeholder="Enter a brief description, then click 'Refine with AI' to generate a spec..."></textarea>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="project" className="block text-sm font-medium mb-1">Project</label>
              <select 
                id="project" 
                value={selectedProjectId} 
                onChange={(e) => setSelectedProjectId(e.target.value)} 
                className={inputClass}
                disabled={isEditMode}
              >
                {!selectedProjectId && <option value="">Select Project</option>}
                {projects.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
              </select>
            </div>
            <div className="flex-1">
              <label htmlFor="assignee" className="block text-sm font-medium mb-1">Assignee</label>
              <select id="assignee" value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)} className={inputClass} disabled={isLoadingUsers}>
                <option value="">{isLoadingUsers ? 'Loading...' : 'Unassigned'}</option>
                {assignableUsers.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.role === 'ai_agent' ? `(AI) ${user.name}` : user.name}
                  </option>
                ))}
              </select>
              
              {/* Agent Capabilities Preview */}
              {assigneeId && (() => {
                  const selected = assignableUsers.find(u => u.id === assigneeId);
                  if (selected?.tools && selected.tools.length > 0) {
                      return (
                          <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded text-xs text-blue-700 dark:text-blue-300">
                              <p className="font-semibold mb-1">🤖 {selected.description || 'Agent Capabilities'}</p>
                              <div className="flex flex-wrap gap-1">
                                  {selected.tools.map((tool) => (
                                      <span key={tool} className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-800 rounded-full border border-blue-200 dark:border-blue-700">
                                          {tool}
                                      </span>
                                  ))}
                              </div>
                          </div>
                      );
                  }
                  return null;
              })()}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex-1">
              {/* David's Architect Workflow: Dynamic Crawler Settings */}
              {(() => {
                  const selected = assignableUsers.find(u => u.id === assigneeId);
                  // Identify Librarian Bot (Knowledge Manager)
                  const isLibrarian = selected?.name.toLowerCase().includes('librarian') || selected?.role === 'ai_agent';
                  
                  if (isLibrarian && !isLoadingUsers) {
                      return (
                          <div className="mt-4 p-4 bg-rose-50 dark:bg-rose-900/10 border border-rose-100 dark:border-rose-800 rounded-lg space-y-3 transition-all animate-in fade-in slide-in-from-top-2">
                              <p className="text-[10px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-widest flex items-center gap-1">
                                  <span className="w-2 h-2 bg-rose-500 rounded-full animate-pulse"></span>
                                  David's Architect Tools
                              </p>
                              
                              <div>
                                  <label htmlFor="crawlerTarget" className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Associate Knowledge Target (from 3737)</label>
                                  <select 
                                      id="crawlerTarget" 
                                      value={crawlerTargetId} 
                                      onChange={(e) => setCrawlerTargetId(e.target.value)}
                                      className={`${inputClass} border-rose-200 focus:ring-rose-500 focus:border-rose-500`}
                                  >
                                      <option value="">-- No Specific Target --</option>
                                      {crawlerTargets.map(t => (
                                          <option key={t.id} value={t.id}>{t.target_url}</option>
                                      ))}
                                  </select>
                              </div>

                              <div className="flex items-center gap-2 pt-1">
                                  <input 
                                      type="checkbox" 
                                      id="isRecurring" 
                                      checked={isRecurring} 
                                      onChange={(e) => setIsRecurring(e.target.checked)}
                                      className="rounded border-rose-300 text-rose-600 focus:ring-rose-500 h-4 w-4"
                                  />
                                  <label htmlFor="isRecurring" className="text-xs font-bold text-rose-800 dark:text-rose-200 cursor-pointer">Add to Periodic Schedule (Expertise Loop)</label>
                              </div>

                              {isRecurring && (
                                  <div className="pl-6 border-l-2 border-rose-200 dark:border-rose-800 py-1 space-y-2">
                                      <label className="block text-[10px] font-bold text-rose-600 uppercase">Sync Frequency</label>
                                      <select 
                                          value={frequency} 
                                          onChange={(e) => setFrequency(e.target.value)}
                                          className={`${inputClass} py-1 text-xs border-rose-100`}
                                      >
                                          <option value="daily">Daily (System Patrol at 04:00 AM)</option>
                                          <option value="weekly">Weekly (Monday morning)</option>
                                          <option value="monthly">Monthly (1st day)</option>
                                      </select>
                                  </div>
                              )}
                          </div>
                      );
                  }
                  return null;
              })()}
            </div>
            <div className="flex-1">
              <MobileDateTimePicker 
                label="Due Date"
                value={dueDate}
                onChange={setDueDate}
              />
            </div>
          </div>
          <div>
            <label htmlFor="priority" className="block text-sm font-medium mb-1">Priority</label>
            <select id="priority" value={priority} onChange={(e) => setPriority(e.target.value as TaskPriority)} className={inputClass}>
              {Object.values(TaskPriority).map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
          </div>
          
          <KnowledgeSelector 
            selectedIds={selectedKnowledgeIds} 
            onChange={setSelectedKnowledgeIds}
            disabled={isSubmitting}
          />

          {/* AI Agent Report Section (Restored) */}
          {isEditMode && task?.agent_output && (
            <div className="mt-6 p-4 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 rounded-xl space-y-3 animate-in fade-in zoom-in-95 duration-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="text-xs font-black text-indigo-600 dark:text-indigo-400 uppercase tracking-widest flex items-center gap-2">
                    <SparklesIcon className="w-3 h-3" />
                    AI Agent Report
                  </h3>
                  
                  {/* Phase 4.6.15: Token Cost Badge */}
                  {task.ai_metrics && task.ai_metrics.total_cost_usd > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-black rounded-full border border-emerald-200 dark:border-emerald-800 animate-in fade-in slide-in-from-left-2">
                        ${task.ai_metrics.total_cost_usd.toFixed(4)}
                      </span>
                      <span className="text-[9px] text-slate-400 font-medium">
                        {task.ai_metrics.total_tokens.toLocaleString()} tokens
                      </span>
                    </div>
                  )}
                </div>
                <span className="text-[9px] font-bold text-indigo-400">v1.1 Economic Payload</span>
              </div>
              <div className="bg-white dark:bg-slate-950 p-4 rounded-lg border border-indigo-50 dark:border-indigo-900 text-xs font-mono text-slate-700 dark:text-slate-300 overflow-x-auto max-h-60 custom-scrollbar">
                {typeof task.agent_output === 'string' ? task.agent_output : JSON.stringify(task.agent_output, null, 2)}
              </div>
              <p className="text-[10px] text-indigo-400 italic font-medium">This report was generated by the assigned AI Agent upon task completion.</p>
            </div>
          )}

          <div className="flex justify-between items-center pt-4">
            <div>
              {canArchive && (
                <button 
                  type="button" 
                  onClick={handleDelete} 
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50 text-sm"
                >
                  Archive Task
                </button>
              )}
            </div>
            <div className="flex space-x-3">
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80">
                Cancel
              </button>
              <button type="submit" disabled={isSubmitting} className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2">
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
