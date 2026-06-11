import { test, expect } from './fixtures/systemFixtures';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('Dynamic Agent Architecture & Flow Governance Spec', () => {
    test.setTimeout(60000);

    test.beforeEach(async ({ page }) => {
        // Prevent random network timeouts
        page.on('console', msg => {
            if (msg.type() === 'error' || msg.type() === 'warning') {
                console.log(`[BROWSER][${msg.type().toUpperCase()}] ${msg.text()}`);
            }
        });

        // Mock System Health Dashboard Overview
        await page.route('**/api/stats/system-overview*', async route => {
            await route.fulfill({
                status: 200,
                json: {
                    status: 'healthy',
                    rag: { status: 'healthy', details: { errors: [] } },
                    errors_24h: 0,
                    active_agents: [
                        { id: 'supervisor', name: 'Supervisor (Group Chat)', role: 'ai_agent', status: 'active' },
                        { id: 'librarian', name: 'Librarian (Knowledge)', role: 'ai_agent', status: 'active' },
                        { id: 'market-bot', name: 'MarketBot (Sales)', role: 'ai_agent', status: 'active' },
                        { id: 'dev-bot', name: 'DevBot (Engineering)', role: 'ai_agent', status: 'active' }
                    ],
                    cost_24h: 0.15
                }
            });
        });

        // Mock AI connectivity health
        await page.route('**/api/system/health/ai*', async route => {
            await route.fulfill({ status: 200, json: { models: [], status: 'healthy' } });
        });

        // Mock connectivity logs
        await page.route('**/api/system/logs/connectivity*', async route => {
            await route.fulfill({ status: 200, json: [] });
        });

        // Mock AI usage statistics
        await page.route('**/api/stats/ai-usage*', async route => {
            await route.fulfill({
                status: 200,
                json: {
                    daily_costs: [{ date: '2026-06-11', cost: 0.15, request_count: 7, models: ['gemini-3.1-flash', 'gemini-3-flash'] }],
                    is_real_data: true,
                    total_xp: 350,
                    total_cost: 0.15,
                    roi_ratio: 6.8
                }
            });
        });

        // Mock Agent XP rankings
        await page.route('**/api/stats/agent-xp*', async route => {
            await route.fulfill({
                status: 200,
                json: [
                    {
                        name: 'MarketBot (Sales)',
                        total_xp: 150,
                        total_cost: 0.05,
                        roi_ratio: 7.2,
                        level: 'Pro'
                    },
                    {
                        name: 'Librarian (Knowledge)',
                        total_xp: 200,
                        total_cost: 0.10,
                        roi_ratio: 6.4,
                        level: 'Elite'
                    }
                ]
            });
        });

        // Mock Token Usage endpoint showing active ROI dynamic agents
        await page.route('**/api/stats/token-usage/recent*', async route => {
            await route.fulfill({
                status: 200,
                json: [
                    {
                        id: "tx-101",
                        timestamp: new Date().toISOString(),
                        user_name: "MarketBot (Sales)",
                        role: "ai_agent",
                        model: "gemini-3.1-flash",
                        tokens: 1200,
                        cost: 0.0009,
                        context: "Sales Lead Enrichment"
                    },
                    {
                        id: "tx-102",
                        timestamp: new Date().toISOString(),
                        user_name: "Librarian (Knowledge)",
                        role: "ai_agent",
                        model: "gemini-3-flash",
                        tokens: 4500,
                        cost: 0.0034,
                        context: "RAG Document Retrieval"
                    }
                ]
            });
        });
    });

    test('should verify dynamic agent identities and trace computational costs', async ({ page }) => {
        // Go to Admin Dashboard Cost & Usage Tab to trace dynamic cost and active agent outputs
        await page.goto('/#/admin');
        await expect(page.getByRole('heading', { name: 'Admin Control Center' })).toBeVisible({ timeout: 10000 });

        // Navigate to Cost & Usage
        await page.getByRole('button', { name: 'Cost & Usage', exact: true }).click();

        // Check if dynamic token consumption is visible
        await expect(page.getByText('Token Cost & ROI Analytics').first()).toBeVisible({ timeout: 10000 });
        await expect(page.getByText('MarketBot (Sales)').first()).toBeVisible({ timeout: 10000 });
        await expect(page.getByText('Librarian (Knowledge)').first()).toBeVisible({ timeout: 10000 });

        // Navigate to System Health
        await page.getByRole('button', { name: 'System Health', exact: true }).click();
        await expect(page.getByText('Agent Status & XP').first()).toBeVisible({ timeout: 10000 });

        // Verify the dynamic list of active agents is correctly rendered
        await expect(page.getByText('Supervisor (Group Chat)').first()).toBeVisible({ timeout: 10000 });
        await expect(page.getByText('Librarian (Knowledge)').first()).toBeVisible({ timeout: 10000 });
    });
});
