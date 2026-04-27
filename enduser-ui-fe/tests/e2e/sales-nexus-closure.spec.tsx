import { screen, fireEvent } from '@testing-library/react';
import { vi, expect, test, beforeEach } from 'vitest';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';

// Mock specific data for this workflow
const MOCK_LEAD = {
    id: 'lead-789',
    company_name: 'Future Client Ltd',
    job_title: 'Fullstack Engineer',
    status: 'new',
    assigned_sales_id: 'user-123'
};

beforeEach(() => {
    vi.resetAllMocks();
});

test('Sales Nexus Closure Flow (Phase 4.4.2) > Librarian Integration: Pitch generation triggers automated archiving', async () => {
    // 1. Go to page
    renderApp(['/marketing']);
    
    // --- Physical Alignment: Switch to Search tab as 'leads' is now default ---
    const searchTabBtn = await screen.findByRole('button', { name: /Job Search/i });
    fireEvent.click(searchTabBtn);

    // 2. Search for a job
    const input = await screen.findByPlaceholderText(/Enter job title/i);
    fireEvent.change(input, { target: { value: 'Data Analyst' } });
    
    const findBtn = screen.getByRole('button', { name: /Find Leads/i });
    fireEvent.click(findBtn);

    // 3. Select a job and identify as lead
    const identifyBtn = await screen.findByText(/Identify as Lead/i);
    fireEvent.click(identifyBtn);

    // 4. In "My Leads" view, generate pitch
    // Explicitly click the "My Leads" tab button to resolve ambiguity
    const leadsTabBtn = await screen.findByRole('button', { name: /My Leads/i });
    fireEvent.click(leadsTabBtn);
    
    const generateBtn = await screen.findByText(/Generate Pitch/i);
    fireEvent.click(generateBtn);

    // 5. Verify Librarian archiving is called (Physical Audit)
    expect(await screen.findByText(/Pitch generated and archived/i)).toBeInTheDocument();
});

test('Sales Nexus Closure Flow (Phase 4.4.2) > Hunter Mode: Logging a physical visit', async () => {
    renderApp(['/marketing']);

    // 1. Switch to "My Leads" Tab using specific role to avoid heading ambiguity
    const leadsTabBtn = await screen.findByRole('button', { name: /My Leads/i });
    fireEvent.click(leadsTabBtn);

    // 2. Open Visit Log Modal
    const logBtn = await screen.findByTitle(/New Visit Log/i);
    fireEvent.click(logBtn);

    // 3. Submit Log
    const textArea = screen.getByPlaceholderText(/What happened during the visit/i);
    fireEvent.change(textArea, { target: { value: 'Customer was very interested in the RAG features.' } });
    
    const submitBtn = screen.getByText(/Save Visit Log/i);
    fireEvent.click(submitBtn);

    // 4. Verify success
    expect(await screen.findByText(/Visit log saved/i)).toBeInTheDocument();
});
