import { act, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { getSession, authState } = vi.hoisted(() => ({
  getSession: vi.fn(),
  authState: {
    callback: null as
      | ((event: string, session: { access_token?: string } | null) => void)
      | null,
  },
}));

vi.mock('../services/api', () => ({
  api: {
    getCurrentUser: vi.fn().mockResolvedValue({ id: '1', name: 'Ada', role: 'admin' }),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  },
  supabase: {
    auth: {
      getSession: (...args: unknown[]) => getSession(...args),
      onAuthStateChange: (
        callback: (event: string, session: { access_token?: string } | null) => void,
      ) => {
        authState.callback = callback;
        return { data: { subscription: { unsubscribe: vi.fn() } } };
      },
    },
  },
}));

import { userState } from '../services/api/base';
import { EmployeeRole } from '../types';
import { AuthProvider } from './useAuth';

describe('useAuth session token', () => {
  beforeEach(() => {
    localStorage.clear();
    userState.cache = null;
    authState.callback = null;
    getSession.mockResolvedValue({ data: { session: null } });
  });

  it('stores archon_token on TOKEN_REFRESHED and other session events, and clears it on SIGNED_OUT', async () => {
    render(
      <AuthProvider>
        <div>ready</div>
      </AuthProvider>,
    );

    expect(await screen.findByText('ready')).toBeInTheDocument();
    expect(authState.callback).toEqual(expect.any(Function));

    act(() => {
      authState.callback?.('TOKEN_REFRESHED', { access_token: 'refreshed-token' });
    });
    expect(localStorage.getItem('archon_token')).toBe('refreshed-token');

    act(() => {
      authState.callback?.('USER_UPDATED', { access_token: 'updated-token' });
    });
    expect(localStorage.getItem('archon_token')).toBe('updated-token');

    localStorage.setItem('user_role', 'manager');
    act(() => {
      authState.callback?.('SIGNED_OUT', null);
    });
    expect(localStorage.getItem('archon_token')).toBeNull();
    expect(localStorage.getItem('user_role')).toBeNull();
  });

  it('clears userState.cache on SIGNED_OUT from another tab', async () => {
    userState.cache = {
      id: '1',
      employeeId: 'E-1',
      name: 'Ada',
      email: 'ada@example.com',
      department: 'Ops',
      position: 'Admin',
      status: 'active',
      role: EmployeeRole.ADMIN,
      avatar: '',
    };

    render(
      <AuthProvider>
        <div>ready</div>
      </AuthProvider>,
    );
    expect(await screen.findByText('ready')).toBeInTheDocument();
    expect(userState.cache).not.toBeNull();

    act(() => {
      authState.callback?.('SIGNED_OUT', null);
    });

    expect(userState.cache).toBeNull();
    expect(localStorage.getItem('archon_token')).toBeNull();
  });
});
