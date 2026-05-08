import { setup, assign } from 'xstate';

export interface Prompt {
    prompt_name: string;
    description?: string;
    is_system_protected: boolean;
    content?: string;
    prompt?: string;
    updated_at: string;
}

export interface PromptContext {
    prompts: Prompt[];
    selectedPrompt: Prompt | null;
    editValue: string;
    viewMode: 'edit' | 'diff';
    error: string | null;
}

export type PromptEvent = 
    | { type: 'FETCH_SUCCESS'; prompts: Prompt[] }
    | { type: 'FETCH_ERROR'; error: string }
    | { type: 'SELECT_PROMPT'; prompt: Prompt }
    | { type: 'UPDATE_VALUE'; value: string }
    | { type: 'TOGGLE_VIEW'; mode: 'edit' | 'diff' }
    | { type: 'REVERT' }
    | { type: 'SAVE' }
    | { type: 'SAVE_SUCCESS' }
    | { type: 'SAVE_ERROR'; error: string };

export const promptMachine = setup({
    types: {
        context: {} as PromptContext,
        events: {} as PromptEvent
    },
    actions: {
        assignPrompts: assign({
            prompts: ({ event }) => {
                if (event.type === 'FETCH_SUCCESS') return event.prompts;
                return [];
            },
            error: null
        }),
        assignSelectedPrompt: assign({
            selectedPrompt: ({ event }) => {
                if (event.type === 'SELECT_PROMPT') return event.prompt;
                return null;
            },
            editValue: ({ event }) => {
                if (event.type === 'SELECT_PROMPT') return event.prompt.prompt || event.prompt.content || '';
                return '';
            },
            viewMode: 'edit'
        }),
        assignEditValue: assign({
            editValue: ({ event }) => {
                if (event.type === 'UPDATE_VALUE') return event.value;
                return '';
            }
        }),
        assignViewMode: assign({
            viewMode: ({ event }) => {
                if (event.type === 'TOGGLE_VIEW') return event.mode;
                return 'edit';
            }
        }),
        revertEditValue: assign({
            editValue: ({ context }) => context.selectedPrompt?.prompt || context.selectedPrompt?.content || '',
            viewMode: 'edit'
        }),
        assignError: assign({
            error: ({ event }) => {
                if (event.type === 'FETCH_ERROR' || event.type === 'SAVE_ERROR') return event.error;
                return null;
            }
        })
    }
}).createMachine({
    id: 'promptMachine',
    initial: 'loading',
    context: {
        prompts: [],
        selectedPrompt: null,
        editValue: '',
        viewMode: 'edit',
        error: null
    },
    states: {
        loading: {
            on: {
                FETCH_SUCCESS: {
                    target: 'ready',
                    actions: 'assignPrompts'
                },
                FETCH_ERROR: {
                    target: 'error',
                    actions: 'assignError'
                }
            }
        },
        ready: {
            initial: 'idle',
            on: {
                // Global events within 'ready'
                SELECT_PROMPT: {
                    target: '.editing',
                    actions: 'assignSelectedPrompt'
                },
                FETCH_SUCCESS: {
                    actions: 'assignPrompts'
                }
            },
            states: {
                idle: {},
                editing: {
                    on: {
                        UPDATE_VALUE: {
                            actions: 'assignEditValue'
                        },
                        TOGGLE_VIEW: {
                            actions: 'assignViewMode'
                        },
                        REVERT: {
                            actions: 'revertEditValue'
                        },
                        SAVE: {
                            target: 'saving'
                        }
                    }
                },
                saving: {
                    on: {
                        SAVE_SUCCESS: {
                            target: 'editing'
                        },
                        SAVE_ERROR: {
                            target: 'editing',
                            actions: 'assignError'
                        }
                    }
                }
            }
        },
        error: {
            on: {
                FETCH_SUCCESS: {
                    target: 'ready',
                    actions: 'assignPrompts'
                }
            }
        }
    }
});
