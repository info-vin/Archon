import { setup, assign, fromPromise } from 'xstate';
import { api } from '@/services/api';
import { ChangeType } from '@/types';
import { UnifiedProposal } from '../hooks/useApprovalInbox';

export const approvalMachine = setup({
  types: {
    context: {} as {
      proposals: UnifiedProposal[];
      selectedId: string | null;
      error: string | null;
      processingId: string | null;
      showRejectInput: boolean;
      rejectReason: string;
      generatingReason: boolean;
    },
    events: {} as
      | { type: 'FETCH' }
      | { type: 'SELECT'; id: string }
      | { type: 'APPROVE'; id: string }
      | { type: 'REJECT_INIT'; id: string }
      | { type: 'REJECT_SUBMIT'; id: string }
      | { type: 'REJECT_CANCEL' }
      | { type: 'SET_REJECT_REASON'; reason: string }
      | { type: 'GENERATE_AI_REASON' }
  },
  actors: {
    fetchData: fromPromise(async () => {
      const [devChanges, marketingApprovals] = await Promise.all([
        api.getPendingChanges(),
        api.getPendingApprovals()
      ]);
      const unifiedList: UnifiedProposal[] = [
        ...devChanges.map((c: any) => ({ ...c, is_marketing: false })),
        ...(marketingApprovals.blogs || []).map((b: any) => ({
          id: `mkt-blog-${b.id}`,
          created_at: b.created_at || b.publishDate || new Date().toISOString(),
          status: b.status,
          type: ChangeType.BLOG,
          change_summary: `Review Blog: ${b.title}`,
          request_payload: { new_content: b.content || b.excerpt },
          is_marketing: true,
          marketing_type: 'blog',
          marketing_id: b.id,
          marketing_title: b.title,
          marketing_content: b.content || b.excerpt,
          marketing_author: b.authorName
        }))
      ];

      // PERFORMANCE: Pre-calculate Date strings into numeric timestamps (O(N)) to prevent redundant object instantiations during O(N log N) sorting
      const dateWeights = new Map<any, number>();
      unifiedList.forEach(item => {
        dateWeights.set(item, new Date(item.created_at).getTime());
      });
      unifiedList.sort((a, b) => (dateWeights.get(b) || 0) - (dateWeights.get(a) || 0));
      return unifiedList;
    }),
    processAction: fromPromise(async ({ input }: { input: { id: string; action: 'approve' | 'reject'; proposal: UnifiedProposal; reason?: string } }) => {
      if (input.proposal.is_marketing) {
         await api.processApproval(
             input.proposal.marketing_type || 'blog', 
             input.proposal.marketing_id!, 
             input.action, 
             input.action === 'reject' ? input.reason : undefined
         );
      } else {
         if (input.action === 'approve') {
           await api.approveChange(input.id);
         } else {
           await api.rejectChange(input.id);
         }
      }
      return input.id;
    }),
    generateAiReason: fromPromise(async ({ input }: { input: { proposal: UnifiedProposal } }) => {
      const res = await api.generateRejectReason(
          input.proposal.marketing_type || 'blog', 
          input.proposal.marketing_id!
      );
      if (res && res.notes) {
          return res.notes;
      }
      return 'The content does not align with our current brand guidelines. Please revise the tone to be more professional.';
    })
  }
}).createMachine({
  id: 'approval',
  initial: 'loading',
  context: {
    proposals: [],
    selectedId: null,
    error: null,
    processingId: null,
    showRejectInput: false,
    rejectReason: '',
    generatingReason: false,
  },
  states: {
    loading: {
      invoke: {
        src: 'fetchData',
        onDone: {
          target: 'idle',
          actions: assign({
            proposals: ({ event }) => event.output,
            selectedId: ({ event, context }) => context.selectedId || (event.output.length > 0 ? event.output[0].id : null),
            error: null
          })
        },
        onError: {
          target: 'error',
          actions: assign({
            error: ({ event }) => (event.error as any)?.message || 'Failed to fetch proposals'
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
        SELECT: {
          actions: assign({
            selectedId: ({ event }) => event.id,
            showRejectInput: false,
            rejectReason: ''
          })
        },
        APPROVE: {
          target: 'processing',
          actions: assign({
            processingId: ({ event }) => event.id
          })
        },
        REJECT_INIT: {
           actions: assign({
             showRejectInput: true,
             rejectReason: ''
           })
        },
        REJECT_CANCEL: {
           actions: assign({
             showRejectInput: false,
             rejectReason: ''
           })
        },
        SET_REJECT_REASON: {
           actions: assign({
             rejectReason: ({ event }) => event.reason
           })
        },
        REJECT_SUBMIT: {
           target: 'processing',
           actions: assign({
             processingId: ({ event }) => event.id
           })
        },
        GENERATE_AI_REASON: {
           target: 'generatingReason',
           actions: assign({
             generatingReason: true
           })
        }
      }
    },
    processing: {
      invoke: {
        src: 'processAction',
        input: ({ context, event }) => {
           let action: 'approve' | 'reject' = 'approve';
           let id = context.processingId!;
           if (event.type === 'REJECT_SUBMIT') {
               action = 'reject';
               id = event.id;
           } else if (event.type === 'APPROVE') {
               action = 'approve';
               id = event.id;
           }
           const proposal = context.proposals.find(p => p.id === id)!;
           return {
               id,
               action,
               proposal,
               reason: action === 'reject' ? context.rejectReason : undefined
           };
        },
        onDone: {
          target: 'idle',
          actions: assign({
            proposals: ({ context, event }) => context.proposals.filter(p => p.id !== event.output),
            selectedId: ({ context, event }) => context.selectedId === event.output ? null : context.selectedId,
            processingId: null,
            showRejectInput: false,
            rejectReason: ''
          })
        },
        onError: {
          target: 'idle',
          actions: assign({
            error: ({ event }) => `Action failed: ${(event.error as any)?.message}`,
            processingId: null
          })
        }
      }
    },
    generatingReason: {
      invoke: {
        src: 'generateAiReason',
        input: ({ context }) => {
           const proposal = context.proposals.find(p => p.id === context.selectedId)!;
           return { proposal };
        },
        onDone: {
          target: 'idle',
          actions: assign({
            rejectReason: ({ event }) => event.output,
            generatingReason: false
          })
        },
        onError: {
          target: 'idle',
          actions: assign({
            rejectReason: () => 'Failed to generate AI reason. Please enter manually.',
            generatingReason: false
          })
        }
      }
    }
  }
});
