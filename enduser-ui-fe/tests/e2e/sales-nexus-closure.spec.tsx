import { screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { createUser } from '../factories/userFactory';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';

// Mock specific for this test suite if needed, though global setup handles most.
// We rely on e2e.setup.tsx for the base mocks.

describe('Sales Nexus Closure Flow (Phase 4.4.2)', () => {
    
    it('Librarian Integration: Pitch generation triggers automated archiving', async () => {
        // Mock Sales User
        const salesUser = createUser({ role: EmployeeRole.SALES });
        vi.mocked(api.getCurrentUser).mockResolvedValue(salesUser as any);

        renderApp(['/marketing']);

        // 1. Initial State: Wait for Sales Intelligence page
        await screen.findByText(/Sales Intelligence/i);

        // 2. Search for a job
        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Data Analyst' } });
        fireEvent.click(screen.getByText(/Find Leads/i));

        // 3. Find the lead and Verify Job Title
        await waitFor(() => {
            expect(screen.getByText('Retail Corp')).toBeInTheDocument();
            // Match the full text structure "Hiring: ..." - Updated to match MSW data
            expect(screen.getByText(/Hiring:\s*Senior Data Analyst/i)).toBeInTheDocument();
        });

        // 4. Generate Pitch
        const generateBtns = screen.getAllByText(/Generate Pitch/i);
        fireEvent.click(generateBtns[0]);

        // 5. Approve & Save (Triggers Librarian)
        const approveBtn = await screen.findByText(/Approve & Save/i);
        const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
        fireEvent.click(approveBtn);

        await waitFor(() => {
            expect(alertMock).toHaveBeenCalledWith(expect.stringContaining("Pitch approved"));
        });
        alertMock.mockRestore();
    });

    it('Vendor Promotion: Promoting a lead to a vendor', async () => {
        // Mock Sales User
        const salesUser = createUser({ role: EmployeeRole.SALES });
        vi.mocked(api.getCurrentUser).mockResolvedValue(salesUser as any);

        // Runtime MSW Handler for Promotion
        server.use(
            http.post('*/api/marketing/leads/:id/promote', () => {
                return HttpResponse.json({ success: true, vendor_id: 'v-123' });
            })
        );

        renderApp(['/marketing']);
        await screen.findByText(/Sales Intelligence/i);

        // 1. Switch to "My Leads" Tab (Crucial Step!)
        const leadsTabBtn = screen.getByText(/My Leads/i);
        fireEvent.click(leadsTabBtn);

        // 2. Verify Identified Leads are visible
        await waitFor(async () => {
            expect(await screen.findByRole('heading', { name: /My Leads/i })).toBeInTheDocument();
        });

        // 3. Promote Action
        const promoteBtn = screen.getAllByText(/Promote to Vendor/i)[0];
        fireEvent.click(promoteBtn);

        // 4. Fill Vendor Details (Only Email and Notes exist in UI)
        const emailInput = await screen.findByLabelText(/Contact Email/i);
        fireEvent.change(emailInput, { target: { value: 'partner@example.com' } });

        const confirmBtn = screen.getByRole('button', { name: /Confirm Promotion/i });
        const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
        fireEvent.click(confirmBtn);

        // 5. Success Check (Alert based)
        // MarketingPage calls alert() on catch, but success usually refreshes list.
        // We check if fetchLeads was called or just wait for no error.
        // Actually, MarketingPage.tsx closes modal on success.
        
        await waitFor(() => {
            expect(screen.queryByText(/Confirm Promotion/i)).not.toBeInTheDocument();
        });
        alertMock.mockRestore();
    });
});
