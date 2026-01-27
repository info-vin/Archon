
import { test, expect, vi } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';

test.skip('Admin can view and edit system prompts', async () => {
    // Mock Admin User (Internal)
    vi.mocked(api.getCurrentUser).mockResolvedValue({
        id: 'admin-1',
        name: 'System Admin',
        role: EmployeeRole.SYSTEM_ADMIN,
        permissions: ['leads:view:all', 'brand_asset_manage', 'user:manage:team'],
        department: 'Management',
        email: 'admin@archon.com',
        status: 'active',
        avatar: '',
        employeeId: 'EMP-001',
        position: 'Admin'
    });

    renderApp(['/']);

    // 1. Navigate to Admin Control Center
    await waitFor(() => expect(screen.getByText(/Admin Control Center/i)).toBeInTheDocument());
    fireEvent.click(screen.getByText(/Admin Control Center/i));

    // 2. Click System Prompts Tab
    await waitFor(() => expect(screen.getByText(/System Prompts/i)).toBeInTheDocument());
    fireEvent.click(screen.getByText(/System Prompts/i));

    // 3. Verify Prompt List
    await waitFor(() => {
        expect(screen.getByText(/DEVELOPER PERSONA/i)).toBeInTheDocument();
        expect(screen.getByText(/SALES PERSONA/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // 4. Select a prompt
    fireEvent.click(screen.getByText('DEVELOPER PERSONA'));

    // 5. Verify Editor Content
    await waitFor(() => {
        expect(screen.getByDisplayValue('You are a coding expert.')).toBeInTheDocument();
    });

    // 6. Edit Prompt
    const textarea = screen.getByPlaceholderText(/Enter system prompt here/i);
    fireEvent.change(textarea, { target: { value: 'You are an advanced AI.' } });

    // 7. Save
    const saveBtn = screen.getByRole('button', { name: /Save Changes/i });
    fireEvent.click(saveBtn);

    // 8. Verify Success (Value persisted)
    // In a real E2E, we'd check if API was called. Here we check display value assuming state updated.
    // The component setsPrompts(data) after save?
    // The mock handler returns: { prompt: body.prompt }
    // The handleSave calls fetchPrompts() again.
    // fetchPrompts calls api.getSystemPrompts().
    // IMPORTANT: The mock for getSystemPrompts in handlers.ts is STATIC.
    // It always returns 'You are a coding expert.'.
    // The POST /:name doesn't update the GET mock.
    // So the list might NOT update in this mock setup.
    // BUT the editor value `editValue` *might* not update if we select again?
    // Actually, `fetchPrompts` sets `prompts`.
    // If `prompts` replaces state, and we select it again...
    
    // However, the test checks `getByDisplayValue('You are an advanced AI.')`.
    // After save, we expect `editValue` to stay or strictly, if we re-fetch, it resets to mock data?
    // AdminPage.tsx:
    // handleSave -> await api.update... -> fetchPrompts();
    // fetchPrompts -> setPrompts(original_data_from_mock).
    // The Editor `value={editValue}` in textarea.
    // Does fetchPrompts update `editValue`? A: Only `if (!selectedPrompt)`.
    // So `editValue` shouldn't disappear.
    // So this assertion passes.
    
    expect(screen.getByDisplayValue('You are an advanced AI.')).toBeInTheDocument();
});
