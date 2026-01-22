import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MarketingPage from '../../src/pages/MarketingPage';
import React from 'react';
import { describe, it, expect } from 'vitest';
import { AuthProvider } from '../../src/hooks/useAuth';

describe('MarketingPage Sales Intelligence Flow', () => {
    it('Sales Rep flows: Search, Identify Lead, Generate Pitch', async () => {
        render(
            <AuthProvider>
                <MarketingPage />
            </AuthProvider>
        );

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
        // There might be multiple results, so we check if at least one exists
        const sourceTags = screen.getAllByText(/104 Live Data/i);
        expect(sourceTags.length).toBeGreaterThan(0);
        expect(sourceTags[0]).toBeInTheDocument();

        // 3.5 驗證完整職缺描述展開 (Verify Full JD Expansion)
        const viewDetailsBtn = screen.getAllByText(/View Full JD/i)[0];
        fireEvent.click(viewDetailsBtn);
        
        expect(screen.getByText(/Full description: Needs someone who knows BI tools/i)).toBeInTheDocument();
        expect(screen.getByText(/Tableau and PowerBI/i)).toBeInTheDocument();

        // 4. 生成話術 (Generate Pitch)
        // Select the first generate button
        const generateBtns = screen.getAllByText(/Generate Pitch/i);
        fireEvent.click(generateBtns[0]);

        // 5. 驗證話術內容 (Verify Content)
        // Wait for the sticky panel to appear with the generated content
        await waitFor(() => {
            const textarea = screen.getByDisplayValue(/Subject: Collaboration regarding/i);
            expect(textarea).toBeInTheDocument();
            expect(textarea.textContent).toContain('Retail Corp');
            expect(textarea.textContent).toContain('Needs someone who knows BI tools'); // Check if job description was injected
        });
    });

    it('handles search errors gracefully', async () => {
        // Relies on e2e.setup.tsx mock logic: if keyword is 'Error Test', it throws.
        render(
            <AuthProvider>
                <MarketingPage />
            </AuthProvider>
        );
        
        await screen.findByText(/Sales Intelligence/i);

        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Error Test' } });
        fireEvent.click(screen.getByText(/Find Leads/i));

        await waitFor(() => {
            expect(screen.getByText(/Failed to fetch job market data/i)).toBeInTheDocument();
        });
    });
});
