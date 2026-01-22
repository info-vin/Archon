import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MarketingPage from '../../src/pages/MarketingPage';
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider } from '../../src/hooks/useAuth';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';

// Mock scrollTo
window.scrollTo = vi.fn();
Element.prototype.scrollIntoView = vi.fn();

describe('Content Marketing E2E Flow', () => {
    beforeEach(() => {
        // Mock authenticated user with permission
        vi.spyOn(api, 'getCurrentUser').mockResolvedValue({
            id: 'bob-1',
            name: 'Bob Marketing',
            email: 'bob@archon.com',
            role: EmployeeRole.MANAGER, // Managers usually have leads:view:all
            status: 'active',
            employeeId: 'EMP-002',
            department: 'Marketing',
            position: 'Marketing Manager',
            avatar: ''
        });
    });

    it('Bob can search jobs, generate a pitch, and approve it', async () => {
        render(
            <AuthProvider>
                <MarketingPage />
            </AuthProvider>
        );

        // 1. Initial State
        await screen.findByText(/Sales Intelligence/i);

        // 2. Search
        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Data Analyst' } });
        fireEvent.click(screen.getByText(/Find Leads/i));

        // 3. Verify Results
        await waitFor(() => {
            expect(screen.getByText('Retail Corp')).toBeInTheDocument();
        });

        // 4. Generate Pitch (Draft with AI)
        const generateBtns = screen.getAllByText(/Generate Pitch/i);
        fireEvent.click(generateBtns[0]);

        // 5. Verify Generated Content & Prompt Display (ENH-005)
        await waitFor(() => {
            expect(screen.getByText(/AI System Prompt/i)).toBeInTheDocument();
            const textarea = screen.getByDisplayValue(/Subject: Collaboration regarding/i);
            expect(textarea).toBeInTheDocument();
        });

        // 6. Approve & Save (GAP-001 Coverage)
        const approveBtn = screen.getByText(/Approve & Save/i);
        expect(approveBtn).toBeInTheDocument();

        const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
        fireEvent.click(approveBtn);

        expect(alertMock).toHaveBeenCalledWith(expect.stringContaining('approved and saved'));
        alertMock.mockRestore();
    });
});
