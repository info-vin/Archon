import { screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { describe, it, expect } from 'vitest';
import { renderApp } from './e2e.setup';

describe('Solutions Page (Phase 4.3)', () => {
  it('Users can navigate to Solutions and switch tabs', async () => {
    renderApp();

    // 1. Navigate to Solutions page
    // (In a real scenario, we'd click "Solutions" in the header, 
    // but since we are mocking navigation via renderApp and links, let's assume we start from Landing)
    
    // Check if we are at Dashboard (since e2e.setup defaults to auth)
    const dashboardTitle = await screen.findByText(/My Tasks/i);
    expect(dashboardTitle).toBeInTheDocument();

    // Go to Landing (via Sidebar)
    fireEvent.click(screen.getByText(/Back to Website/i));
    await waitFor(() => expect(screen.getByText(/The Command Center for Your Projects/i)).toBeInTheDocument());

    // Click "Solutions" in Header
    fireEvent.click(screen.getByText('Solutions'));

    // 2. Verify Solutions Page Load (Overview Tab default)
    await waitFor(() => expect(screen.getByText(/Smart Manufacturing Solutions/i)).toBeInTheDocument());
    expect(screen.getByText(/專案綜合說明/i)).toBeInTheDocument(); // Content from SmartManufacturing.tsx

    // 3. Switch to Tech Specs Tab
    fireEvent.click(screen.getByText('Tech Specs'));
    await waitFor(() => expect(screen.getByText(/專案技術與套件需求/i)).toBeInTheDocument());
    expect(screen.getByText(/Sortable.js/i)).toBeInTheDocument();

    // 4. Switch to Live Demo Tab (Legacy Viewer)
    fireEvent.click(screen.getByText('Live Demo'));
    await waitFor(() => expect(screen.getByText(/RPA Flow Demo/i)).toBeInTheDocument());
    
    // Check if iframe is rendered
    const iframe = screen.getByTitle('RPA Flow Demo');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', '/ai/original_files/RPA_canvas.html');
  });
});
