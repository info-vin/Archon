import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { renderApp } from './e2e.setup';

describe('Task Assignee Persistence (Migration 007)', () => {
    it('should persist assignee after page reload', async () => {
        const { unmount } = renderApp(['/dashboard']);
        await waitFor(() => expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument(), { timeout: 10000 });

        const newTaskBtn = await screen.findByRole('button', { name: /New Task/i }, { timeout: 15000 });
        fireEvent.click(newTaskBtn);

        fireEvent.change(await screen.findByLabelText(/Title/i, {}, { timeout: 15000 }), { target: { value: 'Persist Test Task' } });
        
        fireEvent.click(await screen.findByRole('button', { name: /Due Date/i }, { timeout: 5000 }));
        fireEvent.click(await screen.findByRole('button', { name: /Tomorrow/i }, { timeout: 5000 }));
        fireEvent.click(screen.getByRole('button', { name: /CONFIRM SELECTION/i }));

        fireEvent.change(screen.getByLabelText(/Assignee/i), { target: { value: 'user-1' } });
        fireEvent.click(screen.getByRole('button', { name: /Create Task/i }));

        await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument(), { timeout: 10000 });
        expect(await screen.findByText('Persist Test Task', {}, { timeout: 15000 })).toBeInTheDocument();
        expect(await screen.findByTitle(/Alice/i, {}, { timeout: 15000 })).toBeInTheDocument();

        unmount();
        renderApp(['/dashboard']);
        await waitFor(() => expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument(), { timeout: 10000 });
        
        expect(await screen.findByText('Persist Test Task', {}, { timeout: 15000 })).toBeInTheDocument();
        expect(await screen.findByTitle(/Alice/i, {}, { timeout: 15000 })).toBeInTheDocument();
    });
});
