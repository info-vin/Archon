import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { createUser } from '../factories/userFactory';

describe('Sales Nexus Closure Flow (Phase 4.4.2)', () => {
    
    it('Librarian Integration: Pitch generation triggers automated archiving', async () => {
        // Mock Sales User
        const salesUser = createUser({ role: EmployeeRole.SALES });
        vi.mocked(api.getCurrentUser).mockResolvedValue(salesUser as any);

        renderApp(['/marketing']);

        // 1. Initial State: Wait for Sales Intelligence page
        await screen.findByRole('heading', { name: /Sales Intelligence/i }, { timeout: 15000 });

        // 2. Search for a job
        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Data Analyst' } });
        fireEvent.click(screen.getByText(/Find Leads/i));

        // 3. Find the lead and Verify Job Title
        await screen.findByText('Retail Corp', {}, { timeout: 15000 });
        expect(screen.getByText(/Hiring:\s*Senior Data Analyst/i)).toBeInTheDocument();

        // 4. Generate Pitch
        const generateBtns = screen.getAllByText(/Generate Pitch/i);
        fireEvent.click(generateBtns[0]);

        // 5. Approve & Save (Triggers Librarian)
        const approveBtn = await screen.findByText(/Approve & Save/i, {}, { timeout: 15000 });
        
        // Mock window.alert to capture result
        const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
        fireEvent.click(approveBtn);

        // 6. Verify Correct Success Message (Matches MarketingPage.tsx)
        await waitFor(() => {
            expect(alertMock).toHaveBeenCalledWith(expect.stringContaining("Pitch saved and Lead created!"));
        }, { timeout: 10000 });
        
        alertMock.mockRestore();
    });

    it('Vendor Promotion: Promoting a lead to a vendor', async () => {
        const salesUser = createUser({ role: EmployeeRole.SALES });
        vi.mocked(api.getCurrentUser).mockResolvedValue(salesUser as any);

        renderApp(['/marketing']);
        await screen.findByRole('heading', { name: /Sales Intelligence/i }, { timeout: 15000 });

        // 1. Switch to "My Leads" Tab
        const leadsTabBtn = screen.getByText(/My Leads/i);
        fireEvent.click(leadsTabBtn);

        // 2. Verify Identified Leads are visible
        await screen.findByText(/Retail Corp/i, {}, { timeout: 10000 });

        // 3. Promote Action
        const promoteBtn = screen.getAllByText(/Promote/i)[0];
        fireEvent.click(promoteBtn);

        // 4. Fill Vendor Details
        const emailInput = await screen.findByLabelText(/Contact Email/i);
        fireEvent.change(emailInput, { target: { value: 'partner@example.com' } });

        const confirmBtn = screen.getByRole('button', { name: /Confirm Promotion/i });
        fireEvent.click(confirmBtn);

        // 5. Success Check
        await waitFor(() => {
            expect(screen.queryByText(/Confirm Promotion/i)).not.toBeInTheDocument();
        }, { timeout: 10000 });
    });
});
