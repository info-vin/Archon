import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TaskAgentGroupChat } from './TaskAgentGroupChat';
import { Task } from '../../types.ts';

describe('TaskAgentGroupChat Component', () => {
    it('should properly render multi-agent group chat bubbles from JSON array', () => {
        const fakeTask: Task = {
            id: 'task-chat-123',
            project_id: 'p-1',
            title: 'Marketing Data Deep Dive',
            description: 'Test',
            status: 'done' as any,
            assignee_id: 'f0f00000-0000-0000-0000-000000000000',
            assignee: 'Archon Supervisor',
            task_order: 1,
            priority: 'high' as any,
            agent_output: {
                step_count: 2,
                messages: [
                    { role: "supervisor", content: "I am assigning this to DevBot." },
                    { role: "devbot", content: "Here is the math: CVR is 5%." },
                    { role: "david", content: "Data extracted." }
                ]
            },
            ai_metrics: { total_cost_usd: 0.05, total_tokens: 150, is_ai_powered: true },
            due_date: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        render(<TaskAgentGroupChat task={fakeTask} />);

        // Assertions: The roles should map to the names defined in ROLE_CONFIG
        expect(screen.getByText('Supervisor (Brain)')).toBeInTheDocument();
        expect(screen.getByText('I am assigning this to DevBot.')).toBeInTheDocument();

        expect(screen.getByText('DevBot (Data Scientist)')).toBeInTheDocument();
        expect(screen.getByText('Here is the math: CVR is 5%.')).toBeInTheDocument();

        expect(screen.getByText('David (DB Admin)')).toBeInTheDocument();
        
        // Assert metrics rendered
        expect(screen.getByText('$0.0500')).toBeInTheDocument();
    });

    it('should properly render Scenario A (General Workflow) with Librarian and MarketBot', () => {
        const scenarioATask: Task = {
            id: 'task-chat-abc',
            project_id: 'p-1',
            title: 'General Task',
            description: 'Write a blog post',
            status: 'done' as any,
            assignee_id: 'f0f00000-0000-0000-0000-000000000000',
            assignee: 'Archon Supervisor',
            task_order: 1,
            priority: 'medium' as any,
            agent_output: {
                step_count: 4,
                messages: [
                    { role: "supervisor", content: "Librarian, find info." },
                    { role: "librarian", content: "Here is the info." },
                    { role: "supervisor", content: "MarketBot, write draft." },
                    { role: "marketbot", content: "Here is the draft." }
                ]
            },
            due_date: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        render(<TaskAgentGroupChat task={scenarioATask} />);

        // Assertions for Scenario A roles
        expect(screen.getAllByText('Supervisor (Brain)').length).toBe(2);
        expect(screen.getByText('Librarian (Knowledge)')).toBeInTheDocument();
        expect(screen.getByText('Here is the info.')).toBeInTheDocument();
        expect(screen.getByText('MarketBot (Writer)')).toBeInTheDocument();
        expect(screen.getByText('Here is the draft.')).toBeInTheDocument();
    });

    it('should fallback to legacy report view if messages array is missing', () => {
        const legacyTask: Task = {
            id: 'task-legacy',
            project_id: 'p-1',
            title: 'Legacy Task',
            description: 'Test',
            status: 'done' as any,
            assignee: 'Librarian',
            task_order: 1,
            priority: 'low' as any,
            agent_output: "This is a legacy string output.",
            due_date: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        render(<TaskAgentGroupChat task={legacyTask} />);

        // Assert fallback UI
        expect(screen.getByText('AI Agent Report')).toBeInTheDocument();
        expect(screen.getByText('This is a legacy string output.')).toBeInTheDocument();
        expect(screen.queryByText('Multi-Agent Group Chat')).not.toBeInTheDocument();
    });
});