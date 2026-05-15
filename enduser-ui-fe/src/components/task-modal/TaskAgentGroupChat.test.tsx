import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TaskAgentGroupChat } from './TaskAgentGroupChat';
import { Task } from '../../../types';

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
            ai_metrics: { total_cost_usd: 0.05, total_tokens: 150 },
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
