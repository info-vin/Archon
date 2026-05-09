import { setup, assign, fromPromise } from 'xstate';
import { callAPI } from '../../../services/api/apiClient';

export interface AICorrectionData {
  post_id: string;
  correction_rate: number;
  old_length: number;
  new_length: number;
  created_at: string;
  prompt_name?: string; // We might want to group by prompt later
}

export const analyticsMachine = setup({
  types: {
    context: {} as {
      data: AICorrectionData[];
      error: string | null;
      timeRange: string;
    },
    events: {} as
      | { type: 'FETCH' }
      | { type: 'RETRY' }
      | { type: 'SET_TIME_RANGE'; range: string }
  },
  actors: {
    fetchData: fromPromise(async ({ input }: { input: { timeRange: string } }) => {
      // Fetch AI_CORRECTION logs from archon_logs table
      const res = await callAPI<any[]>(`/api/admin/logs?type=AI_CORRECTION&time_range=${input.timeRange}`);
      
      // Parse details from logs
      return res.map(log => ({
        post_id: log.details?.post_id,
        correction_rate: log.details?.correction_rate,
        old_length: log.details?.old_length,
        new_length: log.details?.new_length,
        created_at: log.created_at
      })) as AICorrectionData[];
    })
  },
  actions: {
    setData: assign({
      data: ({ event }) => (event as any).output,
      error: null
    }),
    setError: assign({
      error: ({ event }) => (event as any).error?.message || 'Failed to fetch analytics'
    }),
    clearError: assign({ error: null }),
    setTimeRange: assign({
      timeRange: ({ event }) => (event as any).range
    })
  }
}).createMachine({
  id: 'correctionAnalytics',
  initial: 'idle',
  context: {
    data: [],
    error: null,
    timeRange: '7d'
  },
  states: {
    idle: {
      on: {
        FETCH: { target: 'loading' }
      }
    },
    loading: {
      invoke: {
        src: 'fetchData',
        input: ({ context }) => ({ timeRange: context.timeRange }),
        onDone: {
          target: 'success',
          actions: 'setData'
        },
        onError: {
          target: 'error',
          actions: 'setError'
        }
      }
    },
    success: {
      on: {
        FETCH: { target: 'loading' },
        SET_TIME_RANGE: {
          target: 'loading',
          actions: 'setTimeRange'
        }
      }
    },
    error: {
      on: {
        RETRY: { target: 'loading', actions: 'clearError' },
        FETCH: { target: 'loading', actions: 'clearError' },
        SET_TIME_RANGE: {
          target: 'loading',
          actions: ['setTimeRange', 'clearError']
        }
      }
    }
  }
});