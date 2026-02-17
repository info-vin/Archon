import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import AuthPage from './AuthPage';
import { useAuth } from '../hooks/useAuth';

// Mock useAuth
vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('AuthPage', () => {
  it('renders login form by default', () => {
    (useAuth as any).mockReturnValue({
      login: vi.fn(),
      register: vi.fn(),
    });

    render(<AuthPage />);
    expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
  });

  it('displays error message on login failure', async () => {
    const user = userEvent.setup();
    const mockLogin = vi.fn().mockRejectedValue(new Error('Invalid credentials'));
    (useAuth as any).mockReturnValue({
      login: mockLogin,
      register: vi.fn(),
    });

    // Mock alert to prevent jsdom error
    const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});

    render(<AuthPage />);

    await user.type(screen.getByLabelText(/Email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'password');

    const submitButton = screen.getByRole('button', { name: /Sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Invalid credentials/i);
    });

    alertMock.mockRestore();
  });

  it('clears error message when typing', async () => {
    const user = userEvent.setup();
    const mockLogin = vi.fn().mockRejectedValue(new Error('Invalid credentials'));
    (useAuth as any).mockReturnValue({
      login: mockLogin,
      register: vi.fn(),
    });

    const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});

    render(<AuthPage />);

    // Trigger error
    await user.type(screen.getByLabelText(/Email address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'password');
    await user.click(screen.getByRole('button', { name: /Sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    // Type again (append 'a')
    const emailInput = screen.getByLabelText(/Email address/i);
    await user.type(emailInput, 'a');

    // Error should be gone
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    alertMock.mockRestore();
  });
});
