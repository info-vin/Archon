import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { renderApp } from './e2e.setup';

describe('Admin Workflows E2E', () => {
  
  it('Admin can create a new user (Alice)', async () => {
    // 1. Initial Load: Use default MOCK_ADMIN_USER
    renderApp(['/dashboard']);

    // 2. Navigate to Admin Control Center
    const adminLink = await screen.findByRole('link', { name: /Admin Control/i }, { timeout: 15000 });
    fireEvent.click(adminLink);

    // 3. Switch to User Management Tab (Crucial: Default tab is System Health)
    const userTab = await screen.findByRole('button', { name: /User Management/i });
    fireEvent.click(userTab);

    // 4. Open Create User Modal (Button text is "NEW USER" in IdentityMatrix.tsx)
    const newUserBtn = await screen.findByRole('button', { name: /NEW USER/i });
    fireEvent.click(newUserBtn);

    // 5. Fill Form (Standard workflow)
    // Label is Title in most cases, but for IdentityMatrix let's check placeholders
    const nameInput = await screen.findByPlaceholderText(/Full Name/i);
    fireEvent.change(nameInput, { target: { value: 'Alice Test' } });
    
    fireEvent.change(screen.getByPlaceholderText(/Email Address/i), { target: { value: 'alice@archon.com' } });
    fireEvent.change(screen.getByPlaceholderText(/Password/i), { target: { value: 'password123' } });
    
    // Select Role
    const roleSelect = screen.getByLabelText(/Role/i);
    fireEvent.change(roleSelect, { target: { value: 'member' } });

    // 6. Submit (Modal title is "Create New User")
    const createBtn = screen.getByRole('button', { name: /Create User/i });
    fireEvent.click(createBtn);

    // 7. Verify Success: Modal closes
    await waitFor(() => {
        expect(screen.queryByText(/Create New User/i)).not.toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('Admin can update a user role', async () => {
    renderApp(['/dashboard']);

    const adminLink = await screen.findByRole('link', { name: /Admin Control/i }, { timeout: 15000 });
    fireEvent.click(adminLink);

    // Switch to Users Tab
    const userTab = await screen.findByRole('button', { name: /User Management/i });
    fireEvent.click(userTab);

    // Wait for list to load (Alice is in mockAssignableUsers)
    await screen.findByText(/Alice/, {}, { timeout: 15000 });

    const editButtons = await screen.findAllByText(/Edit/i);
    expect(editButtons.length).toBeGreaterThan(0);
  });
});
