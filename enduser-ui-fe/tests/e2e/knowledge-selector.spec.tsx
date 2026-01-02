import { test, expect, beforeAll, afterEach, afterAll, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HttpResponse, http } from 'msw';
import { setupServer } from 'msw/node';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';

// --- MOCK DATA ---
const MOCK_KNOWLEDGE_ITEMS = [
  { source_id: 'doc-1', title: 'Onboarding Guide', knowledge_type: 'document', url: 'http://doc-1' },
  { source_id: 'doc-2', title: 'Engineering Standards', knowledge_type: 'document', url: 'http://doc-2' }
];

// --- TEST SETUP ---
const server = setupServer(
    // We mock other endpoints normally
    http.post('*/api/tasks', async ({ request }) => {
      const body = await request.json() as any;
      return HttpResponse.json({
        task: {
            id: 'new-task-123',
            ...body,
            status: 'todo',
            created_at: new Date().toISOString()
        }
      }, { status: 201 });
    }),
    http.get('*/api/assignable-users', () => {
        return HttpResponse.json([
            { id: 'user-1', name: 'Alice', role: 'member' }
        ]);
    }),
    http.get('*/api/agents/assignable', () => {
        return HttpResponse.json([]);
    }),
     http.get('*/api/projects', () => {
        return HttpResponse.json({ projects: [
             { id: 'proj-1', title: 'Project Alpha', status: 'active' }
        ]});
    }),
    http.get('*/api/tasks', () => {
         return HttpResponse.json([]);
    }),
    http.get('*/api/blogs', () => { return HttpResponse.json([]); })
);

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => {
    server.resetHandlers();
    vi.clearAllMocks();
});
afterAll(() => server.close());

test('User can select knowledge items when creating a task', async () => {
  const user = userEvent.setup();

  // Directly mock the service method to bypass potential network/MSW issues
  const serviceSpy = vi.spyOn(api, 'getKnowledgeItems').mockResolvedValue(MOCK_KNOWLEDGE_ITEMS);

  renderApp();

  // 1. Open the "New Task" modal
  const newTaskBtn = await screen.findByRole('button', { name: /new task/i });
  await user.click(newTaskBtn);

  // 2. Fill in basic task details
  await user.type(screen.getByLabelText(/title/i), 'Task with Knowledge');
  await user.type(screen.getByLabelText(/description/i), 'This task needs references.');
  await user.type(screen.getByLabelText(/due date/i), '2024-12-31');

  // 3. Interact with KnowledgeSelector
  const selectorButton = await screen.findByText(/select internal knowledge/i);
  await user.click(selectorButton);

  // 4. Verify API call was made
  await waitFor(() => {
      expect(serviceSpy).toHaveBeenCalled();
  });

  // 5. Verify items are displayed
  const item1 = await screen.findByText('Onboarding Guide');
  expect(item1).toBeInTheDocument();
  expect(screen.getByText('Engineering Standards')).toBeInTheDocument();

  // 6. Select an item
  await user.click(item1);

  // 7. Verify item is selected (tag appears)
  await user.click(screen.getByLabelText(/description/i));
  expect(await screen.findByText('1 items selected')).toBeInTheDocument();

  // 8. Submit the task
  const createBtn = screen.getByRole('button', { name: /create task/i });
  await user.click(createBtn);

  // 9. Verify the success message or modal closing
  await waitFor(() => {
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
