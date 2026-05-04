import React from 'react';
import { AssignableUser } from '../../types.ts';
import { TaskCrawlerSettings } from './TaskCrawlerSettings';

interface TaskAssignmentTabProps {
  assigneeId: string;
  setAssigneeId: (val: string) => void;
  assignableUsers: AssignableUser[];
  isLoadingUsers: boolean;
  collaboratorAgentIds: string[];
  setCollaboratorAgentIds: React.Dispatch<React.SetStateAction<string[]>>;
  crawlerTargets: any[];
  crawlerTargetId: string;
  setCrawlerTargetId: (val: string) => void;
  isRecurring: boolean;
  setIsRecurring: (val: boolean) => void;
  frequency: string;
  setFrequency: (val: string) => void;
  inputClass: string;
}

export const TaskAssignmentTab: React.FC<TaskAssignmentTabProps> = ({
  assigneeId, setAssigneeId,
  assignableUsers,
  isLoadingUsers,
  collaboratorAgentIds, setCollaboratorAgentIds,
  crawlerTargets, crawlerTargetId, setCrawlerTargetId,
  isRecurring, setIsRecurring,
  frequency, setFrequency,
  inputClass
}) => {
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="assignee" className="block text-sm font-medium mb-1">Assignee</label>
        <select 
          id="assignee" 
          value={assigneeId || ''} 
          onChange={(e) => setAssigneeId(e.target.value)} 
          className={inputClass} 
          disabled={isLoadingUsers}
        >
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

      {/* AI Collaborators UI */}
      <div className="mt-4">
        <label className="block text-sm font-medium mb-1">AI Collaborators (Assistants)</label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
          {assignableUsers.filter(u => u.role === 'ai_agent').map(agent => (
            <label key={agent.id} className="flex items-center space-x-2 p-2 border border-border rounded-md hover:bg-secondary cursor-pointer transition-colors">
              <input 
                type="checkbox" 
                className="rounded text-primary focus:ring-primary h-4 w-4"
                checked={collaboratorAgentIds.includes(agent.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setCollaboratorAgentIds(prev => [...prev, agent.id]);
                  } else {
                    setCollaboratorAgentIds(prev => prev.filter(id => id !== agent.id));
                  }
                }}
              />
              <span className="text-sm font-medium">{agent.name}</span>
            </label>
          ))}
          {assignableUsers.filter(u => u.role === 'ai_agent').length === 0 && (
            <div className="text-sm text-muted-foreground italic col-span-2">No AI agents available.</div>
          )}
        </div>
      </div>

      <TaskCrawlerSettings
        assigneeId={assigneeId}
        assignableUsers={assignableUsers}
        isLoadingUsers={isLoadingUsers}
        crawlerTargets={crawlerTargets}
        crawlerTargetId={crawlerTargetId}
        setCrawlerTargetId={setCrawlerTargetId}
        isRecurring={isRecurring}
        setIsRecurring={setIsRecurring}
        frequency={frequency}
        setFrequency={setFrequency}
        inputClass={inputClass}
      />
    </div>
  );
};
