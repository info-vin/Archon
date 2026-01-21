import React, { useState, useEffect } from 'react';
import { AssignableUser, Task, TaskPriority, NewTaskData, UpdateTaskData } from '../types.ts';
import { api } from '../services/api.ts';
import { XIcon, SparklesIcon } from './Icons.tsx';
import { KnowledgeSelector } from './KnowledgeSelector.tsx';

interface TaskModalProps {
  task?: Task | null;
  onClose: () => void;
  onTaskCreated: () => void;
  onTaskUpdated: () => void;
  projectId?: string;
}

const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

export const TaskModal: React.FC<TaskModalProps> = ({ task, onClose, onTaskCreated, onTaskUpdated, projectId }) => {
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

  const isEditMode = task != null && task.id;

  useEffect(() => {
    const fetchAssignableOptions = async () => {
      try {
        setIsLoadingUsers(true);
        const [users, aiAgents] = await Promise.all([
          api.getAssignableUsers(),
          api.getAssignableAgents()
        ]);
        
        const formattedAiAgents = aiAgents.map(agent => ({
          ...agent,
          name: `(AI) ${agent.name}`
        }));

        setAssignableUsers([...users, ...formattedAiAgents]);
      } catch (error) {
        console.error("Failed to fetch assignable users or agents:", error);
        // Even if one fails, we might want to show the other. For now, we fail together.
        // Or, handle partial data loading.
      } finally {
        setIsLoadingUsers(false);
      }
    };

    fetchAssignableOptions();
  }, []);

  useEffect(() => {
    if (isEditMode && task) {
      setTitle(task.title);
      setDescription(task.description || '');
      setAssigneeId(task.assignee_id || '');
      if (task.due_date) {
        setDueDate(new Date(task.due_date).toISOString().split('T')[0]);
      }
      setPriority(task.priority);
      
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
    
    const finalProjectId = isEditMode ? task.project_id : projectId;
    if (!finalProjectId) {
      alert('A project must be selected to create or update a task.');
      return;
    }

    setIsSubmitting(true);

    try {
      if (isEditMode) {
        const updatedData: UpdateTaskData = {
          title,
          description,
          assignee_id: assigneeId || null,
          due_date: new Date(dueDate).toISOString(),
          priority,
          // Note: updateTask might need knowledge_source_ids too, but for now we focus on creation
        };
        await api.updateTask(task.id, updatedData);
        onTaskUpdated();
        alert('Task updated successfully!');
      } else {
        const newTaskData: NewTaskData = {
          project_id: finalProjectId,
          title,
          description,
          assigneeId: assigneeId || undefined,
          due_date: new Date(dueDate).toISOString(),
          priority,
          knowledge_source_ids: selectedKnowledgeIds,
        };
        await api.createTask(newTaskData);
        onTaskCreated();
        alert('Task created successfully!');
      }
      onClose();
    } catch (error: any) {
        console.error("Failed to save task:", error);
        alert(`Failed to save task: ${error.message}`);
    } finally {
        setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center" aria-modal="true" role="dialog">
      <div className="bg-card rounded-lg shadow-xl w-full max-w-lg p-6 relative max-h-[90vh] overflow-y-auto">
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
              <label htmlFor="assignee" className="block text-sm font-medium mb-1">Assignee</label>
              <select id="assignee" value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)} className={inputClass} disabled={isLoadingUsers}>
                <option value="">{isLoadingUsers ? 'Loading...' : 'Unassigned'}</option>
                {assignableUsers.map(user => <option key={user.id} value={user.id}>{user.name}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="due-date" className="block text-sm font-medium mb-1">Due Date</label>
              <input id="due-date" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className={inputClass} required />
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

          <div className="flex justify-end space-x-3 pt-4">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80">
              Cancel
            </button>
            <button type="submit" disabled={isSubmitting} className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
              {isSubmitting ? 'Saving...' : (isEditMode ? 'Save Changes' : 'Create Task')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
