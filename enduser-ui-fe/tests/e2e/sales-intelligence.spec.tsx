import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server'; // Use global server
import MarketingPage from '../../src/pages/MarketingPage';
import React from 'react';
import { describe, it, expect, beforeAll, afterEach } from 'vitest';

describe('MarketingPage Sales Intelligence Flow', () => {
    // Inject the specific handler for this test suite
    beforeAll(() => {
        server.use(
            http.get('/api/marketing/jobs', ({ request }) => {
                const url = new URL(request.url);
                const keyword = url.searchParams.get('keyword');
                
                // Validate that the frontend sends the keyword
                if (!keyword) {
                    return new HttpResponse(null, { status: 400 });
                }
            
                return HttpResponse.json([
                    { 
                        title: "Senior Data Analyst",
                        company: "Retail Corp", 
                        location: "Taipei",
                        url: "http://mock-104/job1",
                        source: "mock",
                        identified_need: "Potential Need: BI Tool" 
                    }
                ]);
            })
        );
    });

    // Clean up runtime handlers after tests
    afterEach(() => {
        server.resetHandlers();
    });

    it('Sales Rep flows: Search, Identify Lead, Generate Pitch', async () => {
        render(<MarketingPage />);

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
        expect(screen.getByText(/Potential Need: BI Tool/i)).toBeInTheDocument();
        
        // Check for MOCK SOURCE tag
        expect(screen.getByText(/MOCK SOURCE/i)).toBeInTheDocument();

        // 4. 生成話術 (Generate Pitch)
        const generateBtn = screen.getByText(/Generate Pitch/i);
        fireEvent.click(generateBtn);

        // 5. 驗證話術內容 (Verify Content)
        // Wait for the sticky panel to appear with the generated content
        await waitFor(() => {
            const textarea = screen.getByDisplayValue(/零售巨頭如何利用數據分析/i);
            expect(textarea).toBeInTheDocument();
            expect(textarea.textContent).toContain('Retail Corp'); // Should inject company name
        });
    });

    it('handles search errors gracefully', async () => {
        // Force API error for this specific test
        server.use(
            http.get('/api/marketing/jobs', () => {
                return new HttpResponse(null, { status: 500 });
            })
        );

        render(<MarketingPage />);
        
        const input = screen.getByPlaceholderText(/Enter job title/i);
        fireEvent.change(input, { target: { value: 'Error Test' } });
        fireEvent.click(screen.getByText(/Find Leads/i));

        await waitFor(() => {
            expect(screen.getByText(/Failed to fetch job market data/i)).toBeInTheDocument();
        });
    });
});
