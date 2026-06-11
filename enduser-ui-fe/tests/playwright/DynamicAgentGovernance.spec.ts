import { test, expect } from './fixtures/systemFixtures';

test.use({ storageState: '../.playwright/admin_storage_state.json' });

test.describe('Dynamic Agent Architecture & Dynamic Task Assignment E2E Spec', () => {
    test.setTimeout(60000);

    test.beforeEach(async ({ page }) => {
        page.on('console', msg => {
            if (msg.type() === 'error' || msg.type() === 'warning') {
                console.log(`[BROWSER][${msg.type().toUpperCase()}] ${msg.text()}`);
            }
        });

        // Mock Projects list
        await page.route('**/api/projects*', async route => {
            await route.fulfill({
                status: 200,
                json: [
                    { id: 'proj-999', name: 'Strategic Expansion', description: 'Phase 5.7 Deployment' }
                ]
            });
        });

        // Mock Layout Level API dependencies to prevent fetch failure crashes
        await page.route('**/api/marketing/leads*', async route => {
            await route.fulfill({ status: 200, json: [] });
        });
        await page.route('**/api/system/fallback/status*', async route => {
            await route.fulfill({ status: 200, json: { active_tier: 1, net_status: 'online' } });
        });
        await page.route('**/api/stats/ai-usage*', async route => {
            await route.fulfill({ status: 200, json: { daily_costs: [], is_real_data: true, total_xp: 0, total_cost: 0, roi_ratio: 0 } });
        });

        // Mock Admin Users API (Identity Directory)
        await page.route('**/api/admin/users*', async route => {
            await route.fulfill({
                status: 200,
                json: {
                    profiles: [
                        { id: 'usr-111', name: 'David Howard', email: 'admin@archon.com', role: 'system_admin', status: 'active' },
                        { id: 'usr-222', name: 'Sales User Mock', email: 'sales@archon.com', role: 'sales', status: 'active' }
                    ]
                }
            });
        });

        // Mock Assignable Users endpoint used inside Task Modal
        await page.route('**/api/assignable-users*', async route => {
            await route.fulfill({
                status: 200,
                json: [
                    { id: 'usr-111', name: 'David Howard', email: 'admin@archon.com', role: 'system_admin', status: 'active' },
                    { id: 'usr-222', name: 'Sales User Mock', email: 'sales@archon.com', role: 'sales', status: 'active' }
                ]
            });
        });

        // Mock RBAC Matrix
        await page.route('**/api/admin/rbac/matrix*', async route => {
            await route.fulfill({
                status: 200,
                json: [
                    { role: 'sales', permissions: ['task.read', 'task.write'], description: 'Sales Role' },
                    { role: 'marketing', permissions: ['task.read', 'task.write', 'blog.edit'], description: 'Marketing Role' }
                ]
            });
        });

        // Mock Users & Assignable Agents (Dynamic RBAC Check)
        // Must return role: 'ai_agent' so front-end correctly maps label with '(AI) ' prefix
        await page.route('**/api/agents/assignable*', async route => {
            await route.fulfill({
                status: 200,
                json: [
                    { id: 'a11ce000-0000-0000-0000-000000000000', name: 'MarketBot (Sales)', role: 'ai_agent', tools: ['search_job_market'] },
                    { id: 'b0b00000-0000-0000-0000-000000000000', name: 'Librarian (Knowledge)', role: 'ai_agent', tools: [] }
                ]
            });
        });

        // Mock Tasks list
        await page.route('**/api/tasks?include_closed=true&include_unassigned=false&per_page=50*', async route => {
            await route.fulfill({
                status: 200,
                json: [
                    {
                        id: 'task-777',
                        title: 'Conduct Competitive Analysis',
                        status: 'done',
                        assignee_id: 'a11ce000-0000-0000-0000-000000000000',
                        collaborator_agent_ids: ['b0b00000-0000-0000-0000-000000000000'],
                        project_id: 'proj-999',
                        created_by: 'usr-111',
                        agent_output: {
                            content: "Market research analysis completed.",
                            messages: [
                                { role: "supervisor", content: "Routing task to MarketBot for initial sales lookup." },
                                { role: "marketbot", content: "Scanned market trends. Transferring to Librarian for knowledge grounding." },
                                { role: "librarian", content: "Grounding research with internal knowledge indexes." }
                            ]
                        }
                    }
                ]
            });
        });

        // Mock default task detail with dynamic Multi-Agent Group Chat output
        await page.route('**/api/tasks/task-777*', async route => {
            await route.fulfill({
                status: 200,
                json: {
                    id: 'task-777',
                    title: 'Conduct Competitive Analysis',
                    status: 'done',
                    assignee_id: 'a11ce000-0000-0000-0000-000000000000',
                    collaborator_agent_ids: ['b0b00000-0000-0000-0000-000000000000'],
                    project_id: 'proj-999',
                    created_by: 'usr-111',
                    agent_output: {
                        content: "Market research analysis completed.",
                        messages: [
                            { role: "supervisor", content: "Routing task to MarketBot for initial sales lookup." },
                            { role: "marketbot", content: "Scanned market trends. Transferring to Librarian for knowledge grounding." },
                            { role: "librarian", content: "Grounding research with internal knowledge indexes." }
                        ]
                    }
                }
            });
        });
    });

    test('should verify dynamic RBAC assignment and workflow group chat simulation', async ({ page }) => {
        // Go to dashboard
        await page.goto('/#/dashboard');
        await expect(page.getByText('My Tasks').first()).toBeVisible({ timeout: 10000 });
        await page.waitForTimeout(1500); // Wait so it's clear in video

        // 1. Click "NEW TASK" button to open modal
        await page.getByRole('button', { name: 'NEW TASK' }).first().click();
        await page.waitForTimeout(1500);

        // Switch to 'Assignment & Automation' Tab inside Create New Task dialog
        await page.getByRole('tab', { name: 'Assignment & Automation' }).click();
        await page.waitForTimeout(1500);

        // 2. Select Assignee Dropdown to show the dynamic AI agents list
        const assigneeSelect = page.getByRole('combobox', { name: 'Assignee' }); // Locate by role and name
        await assigneeSelect.selectOption({ label: '(AI) MarketBot (Sales)' });
        await page.waitForTimeout(1500);

        // Close the modal
        await page.getByRole('button', { name: 'Cancel' }).click();
        await page.waitForTimeout(1500);

        // 3. Open completed task with Multi-Agent Group Chat
        // Click on the existing Task 'Conduct Competitive Analysis'
        await page.getByText('Conduct Competitive Analysis').click();
        await page.waitForTimeout(1500);

        // Click on "AI Report" tab to see the supervisor routing outputs
        await page.getByRole('tab', { name: 'AI Report' }).click();
        await page.waitForTimeout(4000); // Hold for 4s to let supervisor routing bubbles show clearly

        // Verify route statements are visible
        await expect(page.getByText('Routing task to MarketBot').first()).toBeVisible();
        await expect(page.getByText('Scanned market trends.').first()).toBeVisible();
    });
});
