import { setup, assign, fromPromise } from 'xstate';
import { callAPI } from '../../../services/api/apiClient';

export interface ImageResult {
  id: string;
  url: string;
  thumbnail: string;
  author: string;
  source: string;
}

export const imagePickerMachine = setup({
  types: {
    context: {} as {
      keyword: string;
      images: ImageResult[];
      selectedImage: ImageResult | null;
      error: string | null;
    },
    events: {} as
      | { type: 'UPDATE_KEYWORD'; keyword: string }
      | { type: 'SEARCH'; keyword: string }
      | { type: 'SELECT'; image: ImageResult }
      | { type: 'CONFIRM' }
      | { type: 'RETRY' }
  },
  actors: {
    searchImages: fromPromise(async ({ input }: { input: { keyword: string } }) => {
      // Calls the physical backend proxy, or falls back to Playwright mocks in test environment
      return await callAPI<ImageResult[]>(`/api/marketing/images/search?q=${encodeURIComponent(input.keyword)}`);
    })
  },
  actions: {
    updateKeyword: assign({
      keyword: ({ event }) => (event.type === 'UPDATE_KEYWORD' ? event.keyword : '')
    }),
    setKeyword: assign({
      keyword: ({ event }) => (event.type === 'SEARCH' ? event.keyword : '')
    }),
    setImages: assign({
      images: ({ event }) => (event as any).output
    }),
    setError: assign({
      error: ({ event }) => (event as any).error.message || 'Unknown error'
    }),
    clearError: assign({
      error: null
    }),
    setSelected: assign({
      selectedImage: ({ event }) => (event.type === 'SELECT' ? event.image : null)
    })
  }
}).createMachine({
  id: 'imagePicker',
  initial: 'idle',
  context: {
    keyword: '',
    images: [],
    selectedImage: null,
    error: null
  },
  states: {
    idle: {
      on: {
        UPDATE_KEYWORD: { actions: ['updateKeyword'] },
        SEARCH: {
          target: 'searching',
          actions: ['setKeyword', 'clearError']
        }
      }
    },
    searching: {
      on: {
        UPDATE_KEYWORD: { actions: ['updateKeyword'] }
      },
      invoke: {
        src: 'searchImages',
        input: ({ context }) => ({ keyword: context.keyword }),
        onDone: {
          target: 'success',
          actions: ['setImages']
        },
        onError: {
          target: 'error',
          actions: ['setError']
        }
      }
    },
    success: {
      on: {
        UPDATE_KEYWORD: { actions: ['updateKeyword'] },
        SEARCH: {
          target: 'searching',
          actions: ['setKeyword', 'clearError', 'setSelected']
        },
        SELECT: {
          target: 'selecting',
          actions: ['setSelected']
        }
      }
    },
    selecting: {
      on: {
        UPDATE_KEYWORD: { actions: ['updateKeyword'] },
        SEARCH: {
          target: 'searching',
          actions: ['setKeyword', 'clearError', 'setSelected']
        },
        SELECT: {
          actions: ['setSelected'] 
        },
        CONFIRM: {
          // This will be listened to by the parent component
          target: 'success'
        }
      }
    },
    error: {
      on: {
        UPDATE_KEYWORD: { actions: ['updateKeyword'] },
        RETRY: {
          target: 'searching',
          actions: ['clearError']
        },
        SEARCH: {
          target: 'searching',
          actions: ['setKeyword', 'clearError']
        }
      }
    }
  }
});