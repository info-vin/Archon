import React, { useEffect } from 'react';
import { useMachine } from '@xstate/react';
import { taskAssignmentMachine } from '../../features/admin/machines/taskAssignmentMachine';
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
  const [state, send] = useMachine(taskAssignmentMachine, {
    input: {
        assigneeId,
        crawlerTargetId,
        isRecurring,
        frequency,
        collaboratorAgentIds,
        isLibrarian: assignableUsers.find(u => u.id === assigneeId)?.role === 'ai_agent' || false
    }
  });

  // Sync machine context back to parent state
  useEffect(() => {
    const ctx = state.context;
    if (ctx.assigneeId !== assigneeId) setAssigneeId(ctx.assigneeId);
    if (ctx.crawlerTargetId !== crawlerTargetId) setCrawlerTargetId(ctx.crawlerTargetId);
    if (ctx.isRecurring !== isRecurring) setIsRecurring(ctx.isRecurring);
    if (ctx.frequency !== frequency) setFrequency(ctx.frequency);
    if (JSON.stringify(ctx.collaboratorAgentIds) !== JSON.stringify(collaboratorAgentIds)) {
        setCollaboratorAgentIds(ctx.collaboratorAgentIds);
    }
  }, [state.context]);

  const handleAssigneeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    const user = assignableUsers.find(u => u.id === id);
    send({ 
        type: 'SELECT_ASSIGNEE', 
        id, 
        role: user?.role || '', 
        name: user?.name || '' 
    });
  };

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="assignee" className="block text-sm font-medium mb-1">Assignee</label>
        <select 
          id="assignee" 
          value={state.context.assigneeId || ''} 
          onChange={handleAssigneeChange} 
          className={inputClass} 
          disabled={isLoadingUsers}
        >
          <option value="">{isLoadingUsers ? 'Loading...' : 'Unassigned'}</option>
          {assignableUsers.map((user, index) => (
            <option key={user.id || `fallback-${index}`} value={user.id}>
              {user.role === 'ai_agent' ? `(AI) ${user.name}` : user.name}
            </option>
          ))}
        </select>
        
        {/* Agent Capabilities Preview */}
        {state.context.assigneeId && (() => {
            const selected = assignableUsers.find(u => u.id === state.context.assigneeId);
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
                checked={state.context.collaboratorAgentIds.includes(agent.id)}
                onChange={() => send({ type: 'TOGGLE_COLLABORATOR', agentId: agent.id })}
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
        assigneeId={state.context.assigneeId}
        assignableUsers={assignableUsers}
        isLoadingUsers={isLoadingUsers}
        crawlerTargets={crawlerTargets}
        crawlerTargetId={state.context.crawlerTargetId}
        setCrawlerTargetId={(id) => send({ type: 'SELECT_CRAWLER_TARGET', id })}
        isRecurring={state.context.isRecurring}
        setIsRecurring={(checked) => send({ type: 'TOGGLE_RECURRING', checked })}
        frequency={state.context.frequency}
        setFrequency={(f) => send({ type: 'SET_FREQUENCY', frequency: f })}
        inputClass={inputClass}
      />
    </div>
  );
};
