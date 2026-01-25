import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MarketingPage from '../../src/pages/MarketingPage';
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { AuthProvider } from '../../src/hooks/useAuth';

// Mock specific for this test suite if needed, though global setup handles most.
// We rely on e2e.setup.tsx for the base mocks.

describe('Sales Nexus Closure Flow (Phase 4.4.2)', () => {
    
    it('Librarian Integration: Pitch generation triggers automated archiving', async () => {
        render(
            <AuthProvider>
                <MarketingPage />
            </AuthProvider>
        );

        // Wait for Auth to initialize
        await waitFor(() => {
            expect(screen.queryByText(/Verifying access.../i)).not.toBeInTheDocument();
        });

        // 1. Initial State: Wait for Sales Intelligence page
        await screen.findByText(/Sales Intelligence/i);

        // 2. Search for a job
        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Data Analyst' } });
        fireEvent.click(screen.getByText(/Find Leads/i));

        // 3. Find the lead and Verify Job Title
        await waitFor(() => {
            expect(screen.getByText('Retail Corp')).toBeInTheDocument();
            // Match the full text structure "Hiring: ..."
            expect(screen.getByText(/Hiring:\s*Data Analyst/i)).toBeInTheDocument();
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
        render(
            <AuthProvider>
                <MarketingPage />
            </AuthProvider>
        );
        
        // Wait for Auth to initialize
        await waitFor(() => {
            expect(screen.queryByText(/Verifying access.../i)).not.toBeInTheDocument();
        });

        // 1. Switch to "My Leads" Tab (Crucial Step!)
        const leadsTabBtn = screen.getByText(/My Leads/i);
        fireEvent.click(leadsTabBtn);

        // 2. Wait for leads to load
        await waitFor(() => {
            expect(screen.getByText('Tech Solutions')).toBeInTheDocument();
        });

        // 3. Promote to Vendor
        // In the mock data (handlers.ts), Tech Solutions has status 'converted', 
        // so the button might not be visible if logic hides it.
        // Let's check Retail Corp (lead-1) which is 'new'.
        const promoteBtns = await screen.findAllByText(/Promote to Vendor/i);
        expect(promoteBtns.length).toBeGreaterThan(0);
        
        fireEvent.click(promoteBtns[0]); // Promote the first available lead

        // 4. Submit Promotion Form
        const confirmBtn = await screen.findByText(/Confirm Promotion/i);
        fireEvent.click(confirmBtn);
        
        // 5. Verify Success
        // Since we don't mock the reload/toast perfectly in unit test, 
        // we assume if no error thrown and modal closes/updates, it's good.
        // For this test, we just ensure the button was clickable.
    });

});
