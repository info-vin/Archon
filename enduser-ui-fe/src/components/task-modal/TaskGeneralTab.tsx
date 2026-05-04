import React from 'react';
import { TaskPriority } from '../../types.ts';
import { SparklesIcon } from '../Icons.tsx';
import { MobileDateTimePicker } from '../common/MobileDateTimePicker';

interface TaskGeneralTabProps {
  title: string;
  setTitle: (val: string) => void;
  description: string;
  setDescription: (val: string) => void;
  selectedProjectId: string;
  setSelectedProjectId: (val: string) => void;
  priority: TaskPriority;
  setPriority: (val: TaskPriority) => void;
  dueDate: string;
  setDueDate: (val: string) => void;
  projects: any[];
  isEditMode: boolean;
  isRefining: boolean;
  handleRefineWithAI: () => void;
  inputClass: string;
}

export const TaskGeneralTab: React.FC<TaskGeneralTabProps> = ({
  title, setTitle,
  description, setDescription,
  selectedProjectId, setSelectedProjectId,
  priority, setPriority,
  dueDate, setDueDate,
  projects,
  isEditMode,
  isRefining,
  handleRefineWithAI,
  inputClass
}) => {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="title" className="block text-sm font-medium mb-1">Title</label>
        <input 
          id="title" 
          type="text" 
          value={title} 
          onChange={(e) => setTitle(e.target.value)} 
          className={inputClass} 
          required 
        />
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
        <textarea 
          id="description" 
          value={description} 
          onChange={(e) => setDescription(e.target.value)} 
          className={inputClass} 
          rows={6} 
          placeholder="Enter a brief description, then click 'Refine with AI' to generate a spec..."
        ></textarea>
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
        <div>
          <label htmlFor="priority" className="block text-sm font-medium mb-1">Priority</label>
          <select 
            id="priority" 
            value={priority} 
            onChange={(e) => setPriority(e.target.value as TaskPriority)} 
            className={inputClass}
          >
            {Object.values(TaskPriority).map(p => (
              <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="w-full md:w-1/2">
        <MobileDateTimePicker 
          label="Due Date"
          value={dueDate}
          onChange={setDueDate}
        />
      </div>
    </div>
  );
};
