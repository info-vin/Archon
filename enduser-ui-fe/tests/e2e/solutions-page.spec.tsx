import { screen, fireEvent, waitFor, act } from '@testing-library/react';
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';

describe('Solutions Page (Phase 4.3)', () => {
  
  it('Authenticated users can access all content including protected reports', async () => {
    // Default setup is Authenticated in e2e.setup
    renderApp();

    // Navigate to Solutions
    // Wait for sidebar to load
    await waitFor(() => expect(screen.getByText(/My Tasks/i)).toBeInTheDocument());
    
    await act(async () => {
        fireEvent.click(screen.getByText(/Back to Website/i));
    });
    
    await waitFor(() => expect(screen.getByText(/The Command Center for Your Projects/i)).toBeInTheDocument());
    
    await act(async () => {
        fireEvent.click(screen.getByText('Solutions'));
    });

    // 1. Verify Overview (Native Component)
    await waitFor(() => expect(screen.getByText(/Smart Manufacturing Solutions/i)).toBeInTheDocument());
    expect(screen.getByText(/專案綜合說明/i)).toBeInTheDocument();

    // 2. Verify Legacy Content (Core Technology)
    await act(async () => {
        fireEvent.click(screen.getByText('SAS Viya Architecture'));
    });
    await waitFor(() => expect(screen.getByText(/Legacy Content/i)).toBeInTheDocument());
    expect(screen.getByTitle('SAS Viya Architecture')).toBeInTheDocument();
    
    // Check for "Open in New Tab" link
    const newTabLink = screen.getByText('Open in New Tab');
    expect(newTabLink).toBeInTheDocument();
    expect(newTabLink.closest('a')).toHaveAttribute('target', '_blank');

    // 3. Verify Protected Content (Reports & Proposals)
    await act(async () => {
        fireEvent.click(screen.getByText('Solution Proposal'));
    });
    // Since we are logged in, we should see the content (iframe), NOT the lock screen
    await waitFor(() => expect(screen.getByTitle('Solution Proposal')).toBeInTheDocument());
    expect(screen.queryByText(/Protected Content/i)).not.toBeInTheDocument();
  });

  it('Guest users are blocked from accessing protected content', async () => {
    // Mock Guest
    vi.mocked(api.getCurrentUser).mockResolvedValue(null);
    vi.mocked(api.getEmployees).mockRejectedValue(new Error('Unauthorized')); // Ensure other calls don't leak
    localStorage.removeItem('user');

    renderApp();

    // Navigate to Solutions (Start from Landing since not logged in)
    await waitFor(() => expect(screen.getByText(/The Command Center for Your Projects/i)).toBeInTheDocument());
    
    await act(async () => {
        fireEvent.click(screen.getByText('Solutions'));
    });

    // 1. Verify Public Content is accessible
    await waitFor(() => expect(screen.getByText(/Smart Manufacturing Solutions/i)).toBeInTheDocument());
    expect(screen.getByText(/專案綜合說明/i)).toBeInTheDocument();

    // 2. Try to access Protected Content
    // We need to wait for the menu to be fully rendered
    await waitFor(() => expect(screen.getByText('Solution Proposal')).toBeInTheDocument());
    
    await act(async () => {
        fireEvent.click(screen.getByText('Solution Proposal'));
    });

    // 3. Verify Lock Screen
    await waitFor(() => expect(screen.getByText(/Protected Content/i)).toBeInTheDocument());
    expect(screen.getByText(/Log In to Access/i)).toBeInTheDocument();
    
    // Verify content is NOT shown
    expect(screen.queryByTitle('Solution Proposal')).not.toBeInTheDocument();
  });
});
