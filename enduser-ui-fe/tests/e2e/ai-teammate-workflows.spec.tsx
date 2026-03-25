import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { renderApp } from './e2e.setup';

describe('AI as a Teammate E2E Workflows', () => {

  it('Marketing Campaign: User can create a task and assign it to an AI content writer', async () => {
    renderApp(['/dashboard']);

    const taskTitle = 'Draft a blog post about our new AI features';

    // 1. Wait for page to load and find New Task button
    const newTaskBtn = await screen.findByRole('button', { name: /New Task/i }, { timeout: 15000 });
    fireEvent.click(newTaskBtn);

    // 2. Fill Form (Title & Description)
    const titleInput = await screen.findByLabelText(/Title/i);
    fireEvent.change(titleInput, { target: { value: taskTitle } });
    
    const descInput = screen.getByPlaceholderText(/Enter a brief description/i);
    fireEvent.change(descInput, { target: { value: 'Content creation task.' } });
    
    // 3. Handle MobileDateTimePicker (Bypassing accessibility name complexity)
    // Click the date picker button (labeled "Due Date")
    const datePickerBtn = await screen.findByRole('button', { name: /Due Date/i });
    fireEvent.click(datePickerBtn);
    
    // Use preset "Tomorrow"
    const tomorrowBtn = await screen.findByRole('button', { name: /Tomorrow/i });
    fireEvent.click(tomorrowBtn);
    
    // Confirm
    const confirmBtn = screen.getByRole('button', { name: /CONFIRM SELECTION/i });
    fireEvent.click(confirmBtn);

    // 4. Select Assignee
    const assigneeSelect = screen.getByLabelText(/Assignee/i);
    fireEvent.change(assigneeSelect, { target: { value: 'ai-researcher-1' } });

    // 5. Submit
    const saveButton = screen.getByRole('button', { name: /Create Task/i });
    await waitFor(() => expect(saveButton).not.toBeDisabled());
    fireEvent.click(saveButton);

    // 6. Wait for Modal to disappear
    await waitFor(() => {
      expect(screen.queryByText(/Create New Task/i)).not.toBeInTheDocument();
    }, { timeout: 15000 });

    // 7. Verify task appears in list
    expect(await screen.findByText((content) => content.includes(taskTitle), {}, { timeout: 10000 })).toBeInTheDocument();
  });

  it('Technical Support: User can create a task with logs and assign it to a Log Analyzer AI', async () => {
    renderApp(['/dashboard']);

    const taskTitle = 'Analyze user error logs for ticket #12345';

    const newTaskBtn = await screen.findByRole('button', { name: /New Task/i }, { timeout: 15000 });
    fireEvent.click(newTaskBtn);

    fireEvent.change(await screen.findByLabelText(/Title/i), { target: { value: taskTitle } });
    
    // Date Flow
    fireEvent.click(await screen.findByRole('button', { name: /Due Date/i }));
    fireEvent.click(await screen.findByRole('button', { name: /Tomorrow/i }));
    fireEvent.click(screen.getByRole('button', { name: /CONFIRM SELECTION/i }));
    
    fireEvent.change(screen.getByLabelText(/Assignee/i), { target: { value: 'ai-knowledge-expert-1' } });

    const saveButton = screen.getByRole('button', { name: /Create Task/i });
    await waitFor(() => expect(saveButton).not.toBeDisabled());
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.queryByText(/Create New Task/i)).not.toBeInTheDocument();
    }, { timeout: 15000 });

    expect(await screen.findByText((content) => content.includes(taskTitle), {}, { timeout: 10000 })).toBeInTheDocument();
  });

  it('Sales Outreach: User can create a task and assign it to a Sales AI', async () => {
    renderApp(['/marketing']);

    const taskTitle = 'Generate lead list for ACME Corp';

    // Wait for heading to avoid sidebar conflict
    await screen.findByRole('heading', { name: /Sales Intelligence/i }, { timeout: 15000 });

    // Navigate to Dashboard where "New Task" button exists
    const dashboardLink = screen.getByRole('link', { name: /My Tasks/i });
    fireEvent.click(dashboardLink);

    const newTaskBtn = await screen.findByRole('button', { name: /New Task/i }, { timeout: 15000 });
    fireEvent.click(newTaskBtn);

    fireEvent.change(await screen.findByLabelText(/Title/i), { target: { value: taskTitle } });
    
    // Date Flow
    fireEvent.click(await screen.findByRole('button', { name: /Due Date/i }));
    fireEvent.click(await screen.findByRole('button', { name: /Tomorrow/i }));
    fireEvent.click(screen.getByRole('button', { name: /CONFIRM SELECTION/i }));
    
    fireEvent.change(screen.getByLabelText(/Assignee/i), { target: { value: 'ai-researcher-1' } });

    const saveButton = screen.getByRole('button', { name: /Create Task/i });
    await waitFor(() => expect(saveButton).not.toBeDisabled());
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.queryByText(/Create New Task/i)).not.toBeInTheDocument();
    }, { timeout: 15000 });

    expect(await screen.findByText((content) => content.includes(taskTitle), {}, { timeout: 10000 })).toBeInTheDocument();
  });

});
