import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import MainLayout from './MainLayout';
import { useAuth } from '@/hooks/useAuth';
import { usePermission } from '../../features/auth/hooks/usePermission';

// Mock hooks
vi.mock('@/hooks/useAuth');
vi.mock('../../features/auth/hooks/usePermission');

describe('MainLayout Role-Based Visibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should HIDE management links for Alice (Sales role)', () => {
    // 模擬 Alice 身分
    (useAuth as any).mockReturnValue({
      user: { role: 'sales', email: 'alice@archon.com' },
      isAuthenticated: true
    });
    
    // 模擬 Sales 權限 (無管理權限)
    (usePermission as any).mockReturnValue({
      hasPermission: (p: string) => ['leads:view:sales', 'stats:view:own'].includes(p)
    });

    render(
      <MemoryRouter>
        <MainLayout><div>Content</div></MainLayout>
      </MemoryRouter>
    );

    // 斷言：不應看到 Team Management
    expect(screen.queryByText('Team Management')).not.toBeInTheDocument();
    expect(screen.queryByText('Nexus Command')).not.toBeInTheDocument();
    expect(screen.queryByText('Approvals')).not.toBeInTheDocument();
    console.log('✅ Task C2: Alice UI Isolation verified by test.');
  });
});
