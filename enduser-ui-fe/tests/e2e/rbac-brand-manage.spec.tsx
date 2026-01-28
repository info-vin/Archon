import { test, expect, beforeAll, afterEach, afterAll, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';
import { EmployeeRole } from '../../src/types';
import { createUser } from '../factories/userFactory';

// Note: Global server is already setup in e2e.setup.tsx. 
// We rely on that for API calls, and override specific behavior via vi.mocked(api.*).

test('Bob (Marketing) can access Brand Settings', async () => {
    // Mock Bob via Factory
    const bob = createUser({ 
        id: 'bob-1', 
        name: 'Bob', 
        role: EmployeeRole.MARKETING 
    });
    vi.mocked(api.getCurrentUser).mockResolvedValue(bob as any);

    renderApp(['/brand']);

    // Should see the page header (Specific Heading)
    expect(await screen.findByRole('heading', { name: /Brand Hub/i })).toBeInTheDocument();
});

test('Alice (Sales) cannot see Brand Settings controls', async () => {
    // Mock Alice via Factory
    const alice = createUser({ 
        id: 'alice-1', 
        name: 'Alice', 
        role: EmployeeRole.SALES 
    });
    vi.mocked(api.getCurrentUser).mockResolvedValue(alice as any);

    renderApp(['/brand']);

    // Alice validation: Expect Access Denied
    expect(await screen.findByText(/Access Denied/i)).toBeInTheDocument();
    
    // She should NOT see the Brand Hub heading
    expect(screen.queryByRole('heading', { name: /Brand Hub/i })).not.toBeInTheDocument();
    // She should NOT see "New Post"
    expect(screen.queryByText(/New Post/i)).not.toBeInTheDocument();
});