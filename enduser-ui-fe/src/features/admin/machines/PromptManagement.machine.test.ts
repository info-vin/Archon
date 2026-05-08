import { describe, it, expect } from 'vitest';
import { createActor } from 'xstate';
import { promptMachine, Prompt } from '../machines/promptMachine';

const mockPrompt: Prompt = {
    prompt_name: 'test_prompt',
    is_system_protected: false,
    content: 'original content',
    updated_at: '2023-01-01'
};

describe('promptMachine MBT Logic', () => {
    it('should transition through the full editing lifecycle', () => {
        const actor = createActor(promptMachine).start();
        
        // 1. Initial State
        expect(actor.getSnapshot().value).toBe('loading');

        // 2. Fetch Success
        actor.send({ type: 'FETCH_SUCCESS', prompts: [mockPrompt] });
        expect(actor.getSnapshot().value).toStrictEqual({ ready: 'idle' });
        expect(actor.getSnapshot().context.prompts).toHaveLength(1);

        // 3. Select Prompt
        actor.send({ type: 'SELECT_PROMPT', prompt: mockPrompt });
        expect(actor.getSnapshot().value).toStrictEqual({ ready: 'editing' });
        expect(actor.getSnapshot().context.selectedPrompt).toBe(mockPrompt);
        expect(actor.getSnapshot().context.editValue).toBe('original content');
        expect(actor.getSnapshot().context.viewMode).toBe('edit');

        // 4. Edit Value
        actor.send({ type: 'UPDATE_VALUE', value: 'new content' });
        expect(actor.getSnapshot().context.editValue).toBe('new content');

        // 5. Toggle Diff
        actor.send({ type: 'TOGGLE_VIEW', mode: 'diff' });
        expect(actor.getSnapshot().context.viewMode).toBe('diff');

        // 6. Revert
        actor.send({ type: 'REVERT' });
        expect(actor.getSnapshot().context.editValue).toBe('original content');
        expect(actor.getSnapshot().context.viewMode).toBe('edit'); // Should reset to edit mode

        // 7. Edit again and Save
        actor.send({ type: 'UPDATE_VALUE', value: 'ready to save' });
        actor.send({ type: 'SAVE' });
        expect(actor.getSnapshot().value).toStrictEqual({ ready: 'saving' });

        // 8. Save Success
        actor.send({ type: 'SAVE_SUCCESS' });
        expect(actor.getSnapshot().value).toStrictEqual({ ready: 'editing' });
    });
});
