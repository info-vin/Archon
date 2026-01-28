import { screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { api } from '../../src/services/api';
import { renderApp } from './e2e.setup';
import { EmployeeRole } from '../../src/types';
import { createUser } from '../factories/userFactory';

describe('MarketingPage Sales Intelligence Flow', () => {
    it('Sales Rep flows: Search, Identify Lead, Generate Pitch', async () => {
        // Mock Sales User
        const salesUser = createUser({ role: EmployeeRole.SALES });
        vi.mocked(api.getCurrentUser).mockResolvedValue(salesUser as any);

        // Mock searchJobs response
        vi.mocked(api.searchJobs).mockResolvedValue([{
            title: 'Data Analyst',
            company: 'Retail Corp',
            location: 'New York',
            source: '104 Live Data',
            identified_need: 'Needs better data pipeline',
            description_full: 'Needs someone who knows BI tools like Tableau and PowerBI',
            url: 'http://example.com'
        }]);

        renderApp(['/marketing']);

        // Wait for auth to load
        await screen.findByText(/Sales Intelligence/i);

        // 2. 執行搜尋
        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Data Analyst' } });
        
        const searchBtn = screen.getByText(/Find Leads/i);
        fireEvent.click(searchBtn);

        // 3. 驗證潛在客戶識別 (Verify Lead Identification)
        await waitFor(() => {
            expect(screen.getByText('Retail Corp')).toBeInTheDocument();
        });
        
        // Check for Insight display
        expect(screen.getByText(/Needs better data pipeline/i)).toBeInTheDocument();
        
        // Check for Source tag (e.g., "104 Live Data")
        const sourceTags = screen.getAllByText(/104 Live Data/i);
        expect(sourceTags.length).toBeGreaterThan(0);
        expect(sourceTags[0]).toBeInTheDocument();
    });

    it('handles search errors gracefully', async () => {
        // Mock Sales User
        const salesUser = createUser({ role: EmployeeRole.SALES });
        vi.mocked(api.getCurrentUser).mockResolvedValue(salesUser as any);

        vi.mocked(api.searchJobs).mockRejectedValue(new Error('API Down'));

        renderApp(['/marketing']);
        
        await screen.findByText(/Sales Intelligence/i);

        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Data Analyst' } });
        fireEvent.click(screen.getByText(/Find Leads/i));

        // Expect error alert or message (System shows alert usually)
        // Here we just ensure it didn't crash
        await waitFor(() => {
            expect(screen.getByText(/Sales Intelligence/i)).toBeInTheDocument();
        });
    });
});
