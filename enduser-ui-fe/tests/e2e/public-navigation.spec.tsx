import { screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { renderApp } from './e2e.setup';
import { api } from '../../src/services/api';

describe('Public Navigation & Dashboard Access', () => {
  
  it('Guest sees Login button and restricted access', async () => {
    // 1. Mock Guest User (Not logged in)
    // We need to override the default mock which returns a user
    vi.mocked(api.getCurrentUser).mockResolvedValue(null);
    localStorage.removeItem('user'); // Clear local storage to ensure useAuth starts as unauthenticated

    renderApp();

    // 2. Start at Landing Page (default public route if not authenticated)
    // Verify "Login" button is present in Header
    await waitFor(() => expect(screen.getByText(/Get Started/i)).toBeInTheDocument());
    
    // Check Header Login Link
    const loginLinks = screen.getAllByRole('link', { name: /Login/i });
    expect(loginLinks.length).toBeGreaterThan(0);

    // 3. Verify "Go to Dashboard" is NOT present
    expect(screen.queryByText(/Go to Dashboard/i)).not.toBeInTheDocument();
  });

  it('Authenticated user sees bi-directional navigation', async () => {
    // 1. Mock Authenticated User (Default behavior of e2e.setup, but let's be explicit)
    const mockUser = {
        id: 'user-1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'member',
        status: 'active'
    };
    vi.mocked(api.getCurrentUser).mockResolvedValue(mockUser as any);
    
    renderApp();

    // 2. Start at Dashboard (redirected from / because authenticated)
    await waitFor(() => expect(screen.getByText(/My Tasks/i)).toBeInTheDocument());

    // 3. Verify "Back to Website" link exists in Sidebar
    const backToWebLink = screen.getByText(/Back to Website/i);
    expect(backToWebLink).toBeInTheDocument();

    // 4. Click "Back to Website" -> Should go to Landing Page
    fireEvent.click(backToWebLink);
    
    // 5. Verify Landing Page content
    await waitFor(() => expect(screen.getByText(/The Command Center for Your Projects/i)).toBeInTheDocument());

    // 6. Verify "Go to Dashboard" button exists in Header (instead of Login)
    expect(screen.getByText(/Go to Dashboard/i)).toBeInTheDocument();
    expect(screen.queryByText(/Login/i)).not.toBeInTheDocument();

    // 7. Click "Go to Dashboard" -> Should return to Dashboard
    fireEvent.click(screen.getByText(/Go to Dashboard/i));
    await waitFor(() => expect(screen.getByText(/My Tasks/i)).toBeInTheDocument());
  });
});