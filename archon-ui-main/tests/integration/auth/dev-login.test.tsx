import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { AuthProvider, useAuth } from '../../../src/features/auth/contexts/AuthContext';
import React from 'react';

// Define the API URL based on the config we expect
// We use the relative path because the AuthContext uses API_BASE_URL which is '/api'
const DEV_TOKEN_URL = '/api/auth/dev-token';

const server = setupServer(
  http.post(DEV_TOKEN_URL, () => {
    return HttpResponse.json({
      access_token: 'mock-dev-token',
      user: {
        id: 'dev-admin-id',
        email: 'admin@archon.com',
        role: 'system_admin'
      }
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Test Component to consume AuthContext
const TestComponent = () => {
  const { user, token, error, isLoading } = useAuth();
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No User</div>;

  return (
    <div>
      <div data-testid="user-email">{user.email}</div>
      <div data-testid="user-role">{user.role}</div>
      <div data-testid="auth-token">{token}</div>
    </div>
  );
};

describe('Dev Auto-Login Integration', () => {
  it('should automatically login as system admin on mount', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Should start with loading
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    // Should eventually show user data
    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('admin@archon.com');
      expect(screen.getByTestId('user-role')).toHaveTextContent('system_admin');
      expect(screen.getByTestId('auth-token')).toHaveTextContent('mock-dev-token');
    });
  });

  it('should handle 404 error (wrong path) gracefully', async () => {
    // Override handler to simulate 404 (e.g. if path was wrong)
    server.use(
      http.post(DEV_TOKEN_URL, () => {
        return new HttpResponse(null, { status: 404, statusText: 'Not Found' });
      })
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      // The error message format depends on how AuthContext handles it. 
      // Based on current code: `throw new Error("Auto-login failed: ${response.statusText}")`
      expect(screen.getByText(/Auto-login failed: Not Found/i)).toBeInTheDocument();
    });
  });
});
