import { setup, assign } from 'xstate';

export interface TaskAssignmentContext {
  assigneeId: string;
  crawlerTargetId: string;
  isRecurring: boolean;
  frequency: string;
  collaboratorAgentIds: string[];
  isLibrarian: boolean;
}

export const taskAssignmentMachine = setup({
  types: {
    context: {} as TaskAssignmentContext,
    input: {} as TaskAssignmentContext,
    events: {} as
      | { type: 'SELECT_ASSIGNEE'; id: string; role: string; name: string }
      | { type: 'SELECT_CRAWLER_TARGET'; id: string }
      | { type: 'TOGGLE_RECURRING'; checked: boolean }
      | { type: 'SET_FREQUENCY'; frequency: string }
      | { type: 'TOGGLE_COLLABORATOR'; agentId: string }
  },
  actions: {
    updateAssignee: assign({
      assigneeId: ({ event }) => (event.type === 'SELECT_ASSIGNEE' ? event.id : ''),
      isLibrarian: ({ event }) => {
          if (event.type !== 'SELECT_ASSIGNEE') return false;
          return event.role === 'ai_agent' || event.name.toLowerCase().includes('librarian');
      },
      // Reset crawler if switching away from Librarian
      crawlerTargetId: ({ context, event }) => {
          if (event.type !== 'SELECT_ASSIGNEE') return context.crawlerTargetId;
          const isLib = event.role === 'ai_agent' || event.name.toLowerCase().includes('librarian');
          return isLib ? context.crawlerTargetId : '';
      }
    }),
    updateCrawlerTarget: assign({
      crawlerTargetId: ({ event }) => (event.type === 'SELECT_CRAWLER_TARGET' ? event.id : '')
    }),
    toggleRecurring: assign({
      isRecurring: ({ event }) => (event.type === 'TOGGLE_RECURRING' ? event.checked : false)
    }),
    setFrequency: assign({
      frequency: ({ event }) => (event.type === 'SET_FREQUENCY' ? event.frequency : 'daily')
    }),
    toggleCollaborator: assign({
      collaboratorAgentIds: ({ context, event }) => {
        if (event.type !== 'TOGGLE_COLLABORATOR') return context.collaboratorAgentIds;
        const ids = [...context.collaboratorAgentIds];
        const idx = ids.indexOf(event.agentId);
        if (idx > -1) ids.splice(idx, 1);
        else ids.push(event.agentId);
        return ids;
      }
    })
  }
}).createMachine({
  id: 'taskAssignment',
  initial: 'idle',
  context: ({ input }) => ({
    assigneeId: input?.assigneeId || '',
    crawlerTargetId: input?.crawlerTargetId || '',
    isRecurring: input?.isRecurring || false,
    frequency: input?.frequency || 'daily',
    collaboratorAgentIds: input?.collaboratorAgentIds || [],
    isLibrarian: input?.isLibrarian || false
  }),
  states: {
    idle: {
      on: {
        SELECT_ASSIGNEE: {
          target: 'assignee_selected',
          actions: 'updateAssignee'
        },
        TOGGLE_COLLABORATOR: { actions: 'toggleCollaborator' }
      }
    },
    assignee_selected: {
      always: [
        { target: 'configuring_crawler', guard: ({ context }) => context.isLibrarian },
        { target: 'standard_assignment' }
      ]
    },
    configuring_crawler: {
      on: {
        SELECT_ASSIGNEE: {
          target: 'assignee_selected',
          actions: 'updateAssignee'
        },
        SELECT_CRAWLER_TARGET: { actions: 'updateCrawlerTarget' },
        TOGGLE_RECURRING: { actions: 'toggleRecurring' },
        SET_FREQUENCY: { actions: 'setFrequency' },
        TOGGLE_COLLABORATOR: { actions: 'toggleCollaborator' }
      }
    },
    standard_assignment: {
      on: {
        SELECT_ASSIGNEE: {
          target: 'assignee_selected',
          actions: 'updateAssignee'
        },
        TOGGLE_COLLABORATOR: { actions: 'toggleCollaborator' }
      }
    }
  }
});
