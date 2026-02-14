import { test, expect, afterEach, vi } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';

const MOCK_KNOWLEDGE_ITEMS = [
  { source_id: 'doc-1', title: 'Onboarding Guide', knowledge_type: 'document', url: 'http://doc-1' },
  { source_id: 'doc-2', title: 'Engineering Standards', knowledge_type: 'document', url: 'http://doc-2' }
];

afterEach(() => {
  vi.restoreAllMocks();
});

test('User can select knowledge items when creating a task', async () => {
  const user = userEvent.setup();
  vi.mocked(api.getKnowledgeItems).mockResolvedValue(MOCK_KNOWLEDGE_ITEMS as any);
  const createSpy = vi.mocked(api.createTask).mockResolvedValue({ id: 'new-task-1' } as any);

  renderApp(['/dashboard']);
  await waitFor(() => expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument(), { timeout: 10000 });

  const newTaskBtn = await screen.findByRole('button', { name: /New Task/i });
  await user.click(newTaskBtn);

  fireEvent.change(await screen.findByLabelText(/Title/i), { target: { value: 'Task with Knowledge' } });
  
  const datePickerBtn = await screen.findByRole('button', { name: /Due Date/i });
  await user.click(datePickerBtn);
  await user.click(await screen.findByRole('button', { name: /Tomorrow/i }));
  await user.click(screen.getByRole('button', { name: /CONFIRM SELECTION/i }));

  await user.click(await screen.findByRole('button', { name: /Select internal knowledge/i }));
  await user.click(await screen.findByText('Onboarding Guide'));
  
  await user.click(screen.getByRole('button', { name: /Create Task/i }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument(), { timeout: 10000 });
  expect(createSpy).toHaveBeenCalled();
});
