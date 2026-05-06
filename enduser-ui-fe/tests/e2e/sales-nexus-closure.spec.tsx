import { screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, expect, test, beforeEach } from 'vitest';
import { renderApp } from './e2e.setup';

beforeEach(() => {
    vi.clearAllMocks();
    // Spy on window.alert to verify success messages
    vi.spyOn(window, 'alert').mockImplementation(() => {});
});

test('Sales Nexus Closure Flow (Phase 4.4.2) > Librarian Integration: Pitch generation from search', async () => {
    renderApp(['/marketing']);
    
    // Switch to Job Search tab (if not already there)
    const searchTabBtn = await screen.findByRole('button', { name: /Job Search/i });
    fireEvent.click(searchTabBtn);

    // Search for a job
    const input = await screen.findByPlaceholderText(/Enter job title/i);
    fireEvent.change(input, { target: { value: 'Data Analyst' } });
    
    const findBtn = screen.getByRole('button', { name: /Find Leads/i });
    fireEvent.click(findBtn);

    // Select a job and generate pitch directly from the search results
    const generateBtns = await screen.findAllByRole('button', { name: /Generate Pitch/i });
    fireEvent.click(generateBtns[0]);

    // Verify the AI Pitch is generated and displayed
    const generatedPitchTitle = await screen.findByRole('heading', { name: /Generated Pitch/i });
    expect(generatedPitchTitle).toBeInTheDocument();

    // Click Approve & Save
    const approveBtn = await screen.findByRole('button', { name: /Approve & Save/i });
    fireEvent.click(approveBtn);

    // Verify alert was called
    await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Saved!');
    });
});

test('Sales Nexus Closure Flow (Phase 4.4.2) > Hunter Mode: Logging a physical visit', async () => {
    renderApp(['/marketing']);

    // Switch to "My Leads" Tab 
    const leadsTabBtn = await screen.findByRole('button', { name: /My Leads/i });
    fireEvent.click(leadsTabBtn);

    // Open Visit Log Modal
    // Desktop view uses 'Log Visit'
    const logBtns = await screen.findAllByTitle(/Log Visit/i);
    fireEvent.click(logBtns[0]);

    // Submit Log
    // First, select a type (e.g., Client Meeting)
    const typeBtn = await screen.findByText(/Client Meeting/i);
    fireEvent.click(typeBtn);

    // Then, enter notes into the textarea
    const textArea = await screen.findByPlaceholderText(/Type summary or upload audio/i);
    fireEvent.change(textArea, { target: { value: 'Customer was very interested in the RAG features.' } });
    
    // Click Save Visit
    const submitBtn = screen.getByRole('button', { name: /Save Visit/i });
    fireEvent.click(submitBtn);

    // Verify success screen is shown
    expect(await screen.findByText(/Visit Logged!/i)).toBeInTheDocument();
});
