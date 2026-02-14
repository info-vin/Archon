import { screen, fireEvent, waitForElementToBeRemoved } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { renderApp } from './e2e.setup';

describe('Task Assignee Persistence (Migration 007)', () => {
    it('should persist assignee after page reload', async () => {
        const { unmount } = renderApp(['/dashboard']);
        await waitForElementToBeRemoved(() => screen.queryByText(/Loading/i), { timeout: 10000 });

        const newTaskBtn = await screen.findByRole('button', { name: /New Task/i });
        fireEvent.click(newTaskBtn);

        fireEvent.change(await screen.findByLabelText(/Title/i), { target: { value: 'Persist Test Task' } });
        
        fireEvent.click(await screen.findByRole('button', { name: /Due Date/i }));
        fireEvent.click(await screen.findByRole('button', { name: /Tomorrow/i }));
        fireEvent.click(screen.getByRole('button', { name: /CONFIRM SELECTION/i }));

        fireEvent.change(screen.getByLabelText(/Assignee/i), { target: { value: 'user-1' } });
        fireEvent.click(screen.getByRole('button', { name: /Create Task/i }));

        await waitForElementToBeRemoved(() => screen.queryByRole('dialog'), { timeout: 10000 });
        expect(await screen.findByText('Persist Test Task')).toBeInTheDocument();
        expect(screen.getByText(/Alice Johnson/i)).toBeInTheDocument();

        unmount();
        renderApp(['/dashboard']);
        await waitForElementToBeRemoved(() => screen.queryByText(/Loading/i), { timeout: 10000 });
        
        expect(await screen.findByText('Persist Test Task')).toBeInTheDocument();
        expect(screen.getByText(/Alice Johnson/i)).toBeInTheDocument();
    });
});
