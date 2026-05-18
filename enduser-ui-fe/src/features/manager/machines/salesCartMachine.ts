import { setup, assign, fromPromise, fromCallback } from 'xstate';
import { api } from '@/services/api';

export const salesCartMachine = setup({
  types: {
    context: {} as {
      leads: any[];
      selectedIds: Set<string>;
      error: string | null;
      processingAction: 'export' | 'content' | 'remove' | null;
      generatingPitchId: string | null;
      pitchResult: { content: string; company: string } | null;
      activeTaskId: string | null;
    },
    events: {} as
      | { type: 'FETCH' }
      | { type: 'TOGGLE_SELECTION'; id: string }
      | { type: 'TOGGLE_SELECT_ALL' }
      | { type: 'BATCH_ACTION'; action: 'export' | 'content' | 'remove' }
      | { type: 'REMOVE_LEAD'; id: string }
      | { type: 'GENERATE_PITCH'; lead: any }
      | { type: 'CLOSE_PITCH_MODAL' }
      | { type: 'TASK_UPDATED'; data: any }
  },
  actors: {
    fetchCart: fromPromise(async () => {
      const allLeads = await api.getLeads();
      return allLeads.filter((l: any) => l.status === 'shortlisted');
    }),
    processBatchAction: fromPromise(async ({ input }: { input: { action: 'export' | 'content' | 'remove'; ids: string[] } }) => {
      const { action, ids } = input;
      if (action === 'remove') {
        await Promise.all(ids.map(id => api.updateLead(id, { status: 'new' })));
      } else if (action === 'export') {
        await new Promise(resolve => setTimeout(resolve, 1500));
      } else if (action === 'content') {
        const res = await api.draftFromLeads(ids);
        return { ...input, task_id: res.task_id };
      }
      return input;
    }),
    removeLead: fromPromise(async ({ input }: { input: { id: string } }) => {
      await api.updateLead(input.id, { status: 'new' });
      return input.id;
    }),
    generatePitch: fromPromise(async ({ input }: { input: { lead: any } }) => {
      const res = await api.generatePitch(input.lead.job_title, input.lead.company_name, input.lead.identified_need);
      return { content: res.content, company: input.lead.company_name };
    }),
    listenToSSE: fromCallback(({ sendBack }) => {
      const handler = (event: any) => {
        sendBack({ type: 'TASK_UPDATED', data: event.detail });
      };
      window.addEventListener('archon:task_updated', handler);
      return () => window.removeEventListener('archon:task_updated', handler);
    })
  }
}).createMachine({
  id: 'salesCart',
  initial: 'loading',
  context: {
    leads: [],
    selectedIds: new Set(),
    error: null,
    processingAction: null,
    generatingPitchId: null,
    pitchResult: null,
    activeTaskId: null,
  },
  invoke: {
    src: 'listenToSSE'
  },
  states: {
    loading: {
      tags: ['loading'],
      invoke: {
        src: 'fetchCart',
        onDone: {
          target: 'idle',
          actions: assign({
            leads: ({ event }) => event.output,
            error: null
          })
        },
        onError: {
          target: 'error',
          actions: assign({
            error: ({ event }) => (event.error as any)?.message || 'Failed to fetch cart'
          })
        }
      }
    },
    error: {
      on: {
        FETCH: 'loading'
      }
    },
    idle: {
      on: {
        FETCH: 'loading',
        TOGGLE_SELECTION: {
          actions: assign({
            selectedIds: ({ context, event }) => {
              const newSet = new Set(context.selectedIds);
              if (newSet.has(event.id)) {
                newSet.delete(event.id);
              } else {
                newSet.add(event.id);
              }
              return newSet;
            }
          })
        },
        TOGGLE_SELECT_ALL: {
          actions: assign({
            selectedIds: ({ context }) => {
              if (context.selectedIds.size === context.leads.length) {
                return new Set();
              }
              return new Set(context.leads.map(l => l.id));
            }
          })
        },
        BATCH_ACTION: [
          {
            guard: ({ event }) => event.action === 'content',
            target: 'awaitingDrafts',
            actions: assign({
              processingAction: ({ event }) => event.action
            })
          },
          {
            target: 'processingBatch',
            actions: assign({
              processingAction: ({ event }) => event.action
            })
          }
        ],
        REMOVE_LEAD: {
          target: 'processingRemove',
        },
        GENERATE_PITCH: {
          target: 'generatingPitch',
          actions: assign({
            generatingPitchId: ({ event }) => event.lead.id,
            pitchResult: null
          })
        },
        CLOSE_PITCH_MODAL: {
          actions: assign({
            pitchResult: null
          })
        }
      }
    },
    awaitingDrafts: {
      tags: ['processing'],
      invoke: {
        src: 'processBatchAction',
        input: ({ context }) => ({
          action: context.processingAction!,
          ids: Array.from(context.selectedIds)
        }),
        onDone: {
          actions: assign({
            activeTaskId: ({ event }) => (event.output as any).task_id
          })
        },
        onError: {
          target: 'idle',
          actions: assign({
            error: ({ event }) => (event.error as any)?.message || 'Failed to start drafting'
          })
        }
      },
      on: {
        TASK_UPDATED: {
          target: 'idle',
          guard: ({ context, event }) => 
            event.data.task_id === context.activeTaskId && 
            (event.data.status === 'done' || event.data.status === 'failed'),
          actions: [
            assign({
              selectedIds: new Set(),
              processingAction: null,
              activeTaskId: null
            }),
            () => console.log('Action completed successfully')
          ]
        }
      }
    },
    processingBatch: {
      tags: ['processing'],
      invoke: {
        src: 'processBatchAction',
        input: ({ context }) => ({
          action: context.processingAction!,
          ids: Array.from(context.selectedIds)
        }),
        onDone: {
          target: 'idle',
          actions: assign({
            leads: ({ context, event }) => {
              if (event.output.action === 'remove') {
                return context.leads.filter(l => !context.selectedIds.has(l.id));
              }
              return context.leads;
            },
            selectedIds: ({ context, event }) => {
               if (event.output.action === 'remove') {
                 return new Set();
               }
               return context.selectedIds;
            },
            processingAction: null
          })
        },
        onError: {
          target: 'idle',
          actions: assign({
            error: ({ event }) => `Batch action failed: ${(event.error as any)?.message}`,
            processingAction: null
          })
        }
      }
    },
    processingRemove: {
      tags: ['processing'],
      invoke: {
        src: 'removeLead',
        input: ({ event }: any) => ({ id: event.id }),
        onDone: {
          target: 'idle',
          actions: assign({
            leads: ({ context, event }) => context.leads.filter(l => l.id !== event.output),
            selectedIds: ({ context, event }) => {
              const newSet = new Set(context.selectedIds);
              newSet.delete(event.output);
              return newSet;
            }
          })
        },
        onError: {
          target: 'idle',
          actions: assign({
            error: ({ event }) => `Remove action failed: ${(event.error as any)?.message}`
          })
        }
      }
    },
    generatingPitch: {
      tags: ['processing'],
      invoke: {
        src: 'generatePitch',
        input: ({ event }: any) => ({ lead: event.lead }),
        onDone: {
          target: 'idle',
          actions: assign({
            pitchResult: ({ event }) => event.output,
            generatingPitchId: null
          })
        },
        onError: {
          target: 'idle',
          actions: assign({
            error: ({ event }) => `Generate pitch failed: ${(event.error as any)?.message}`,
            generatingPitchId: null
          })
        }
      }
    }
  },
  implementations: {
    actions: {
      notifySuccess: () => {
        console.log('Action completed successfully');
      }
    }
  }
});
