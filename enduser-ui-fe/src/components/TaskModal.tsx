import React, { useState, useEffect } from 'react';
import { AssignableUser, Task, TaskPriority, NewTaskData, UpdateTaskData } from '../types.ts';
import { api } from '../services/api.ts';
import { XIcon } from './Icons.tsx';

interface TaskModalProps {
  task?: Task | null;
  onClose: () => void;
  onTaskCreated: (newTask: Task) => void;
  onTaskUpdated: (updatedTask: Task) => void;
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
  const [assignableUsers, setAssignableUsers] = useState<AssignableUser[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);

  const isEditMode = task != null;

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
    if (isEditMode) {
      setTitle(task.title);
      setDescription(task.description || '');
      setAssigneeId(task.assignee_id || '');
      setDueDate(new Date(task.due_date).toISOString().split('T')[0]);
      setPriority(task.priority);
    }
  }, [task, isEditMode]);

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
        };
        const updatedTask = await api.updateTask(task.id, updatedData);
        onTaskUpdated(updatedTask);
        alert('Task updated successfully!');
      } else {
        const newTaskData: NewTaskData = {
          project_id: finalProjectId,
          title,
          description,
          assigneeId: assigneeId || undefined,
          due_date: new Date(dueDate).toISOString(),
          priority,
        };
        const newTask = await api.createTask(newTaskData);
        onTaskCreated(newTask);
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
      <div className="bg-card rounded-lg shadow-xl w-full max-w-lg p-6 relative">
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
            <label htmlFor="description" className="block text-sm font-medium mb-1">Description</label>
            <textarea id="description" value={description} onChange={(e) => setDescription(e.target.value)} className={inputClass} rows={3}></textarea>
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
