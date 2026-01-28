
import { test, expect, vi } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { createUser } from '../factories/userFactory';

test('Admin can view and edit system prompts', async () => {
    const user = userEvent.setup();
    
    // 1. Mock Data
    const mockPrompts = [
        { prompt_name: 'pobot', prompt: 'Original POBot prompt', description: 'Product Owner persona', updated_at: new Date().toISOString() },
        { prompt_name: 'devbot', prompt: 'Original DevBot prompt', description: 'Engineer persona', updated_at: new Date().toISOString() }
    ];

    // 2. Mock API
    const admin = createUser({ role: EmployeeRole.SYSTEM_ADMIN });
    vi.mocked(api.getCurrentUser).mockResolvedValue(admin as any);
    vi.mocked(api.getSystemPrompts).mockResolvedValue(mockPrompts);
    vi.mocked(api.updateSystemPrompt).mockResolvedValue({ success: true } as any);

    renderApp(['/dashboard']);

    // 3. Navigate to Admin Panel
    await waitFor(() => expect(screen.getByText(/Admin Control Center/i)).toBeInTheDocument());
    fireEvent.click(screen.getByText(/Admin Control Center/i));

    // 4. Switch to System Prompts Tab
    const promptsTab = await screen.findByRole('button', { name: /System Prompts/i });
    await user.click(promptsTab);

    // 5. Verify List Rendering (Click the button in the list)
    const pobotListItem = await screen.findByRole('button', { name: /POBOT/i });
    expect(pobotListItem).toBeInTheDocument();
    
    const devbotListItem = await screen.findByRole('button', { name: /DEVBOT/i });
    expect(devbotListItem).toBeInTheDocument();

    // 6. Edit Action
    await user.click(devbotListItem);

    // Ensure the header updates
    const editorHeader = await screen.findByRole('heading', { name: /DEVBOT/i });
    expect(editorHeader).toBeInTheDocument();

    const textarea = screen.getByPlaceholderText(/Enter system prompt here/i);
    expect(textarea).toHaveValue('Original DevBot prompt');

    await user.clear(textarea);
    await user.type(textarea, 'Updated Pirate Persona');

    // 7. Save Action
    const saveBtn = screen.getByRole('button', { name: /SAVE CHANGES/i });
    await user.click(saveBtn);

    // 8. Verify API Call
    expect(api.updateSystemPrompt).toHaveBeenCalledWith('devbot', { prompt: 'Updated Pirate Persona' });
});
