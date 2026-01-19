import { screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { renderApp } from './e2e.setup';

describe('Task Assignee Persistence (Migration 007)', () => {
    
    it('should persist assignee after page reload', async () => {
        // 1. Initial Render: Go to Dashboard
        const { unmount } = renderApp(['/dashboard']);

        // Wait for Dashboard loading to finish
        await waitFor(() => {
            expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
        });

        // 2. Open New Task Modal
        const newTaskBtn = await screen.findByRole('button', { name: /New Task/i });
        fireEvent.click(newTaskBtn);

        // Fill modal
        const titleInput = await screen.findByLabelText(/Title/i);
        fireEvent.change(titleInput, { target: { value: 'Persist Test Task' } });
        
        const descInput = screen.getByLabelText(/Description/i);
        fireEvent.change(descInput, { target: { value: 'Testing persistence' } });

        const dueDateInput = screen.getByLabelText(/Due Date/i);
        fireEvent.change(dueDateInput, { target: { value: '2025-12-31' } });

        // Select Assignee "Alice Johnson" (ID: user-1)
        const assigneeSelect = screen.getByLabelText(/Assignee/i);
        
        await waitFor(() => {
            expect(assigneeSelect).not.toHaveTextContent('Loading...');
        });

        fireEvent.change(assigneeSelect, { target: { value: 'user-1' } });

        // Save
        const createBtn = screen.getByRole('button', { name: /Create Task/i });
        fireEvent.click(createBtn);

        // 3. Verify Task is created and assigned to Alice
        await waitFor(() => {
            expect(screen.getByText('Persist Test Task')).toBeInTheDocument();
            // Verify Alice's initials or name appears via Title
            expect(screen.getByTitle('Alice Johnson')).toBeInTheDocument();
        });

        // 4. SIMULATE RELOAD: Unmount and Re-render
        unmount();
        
        // Re-render the app at the same route
        renderApp(['/dashboard']);

        // 5. Verify Persistence
        await waitFor(() => {
            expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
            expect(screen.getByText('Persist Test Task')).toBeInTheDocument();
            
            // Verify Alice is still assigned (Data persisted in Mock Store)
            expect(screen.getByTitle('Alice Johnson')).toBeInTheDocument();
        });
    });
});
