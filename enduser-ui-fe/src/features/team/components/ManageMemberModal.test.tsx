import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ManageMemberModal } from './ManageMemberModal';
import { EmployeeRole } from '@/types';

// Mock dependencies
vi.mock('../../../services/api', () => ({
  api: {
    updateEmployee: vi.fn(),
    resetPassword: vi.fn(),
  },
}));

// Mock UserAvatar since it's not the focus of this test and might have internal logic
vi.mock('../../../components/UserAvatar', () => ({
  default: () => <div data-testid="user-avatar">Avatar</div>,
}));

// Mock Icons to avoid SVG rendering issues if any
vi.mock('../../../components/Icons', () => ({
  XIcon: () => <span>X</span>,
  RefreshCwIcon: () => <span>Refresh</span>,
  ShieldCheckIcon: () => <span>Shield</span>,
  KeyIcon: () => <span>Key</span>,
}));

describe('ManageMemberModal Accessibility', () => {
  const mockMember = {
    id: '123',
    employeeId: 'E123',
    name: 'Test User',
    email: 'test@example.com',
    department: 'Engineering',
    position: 'Developer',
    status: 'active' as const,
    role: EmployeeRole.MEMBER,
    avatar: '',
  };

  const defaultProps = {
    member: mockMember,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  it('renders with correct accessibility attributes', () => {
    render(<ManageMemberModal {...defaultProps} />);

    // Check for dialog role
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', `modal-title-${mockMember.id}`);

    // Check for modal title
    const title = screen.getByRole('heading', { level: 3 });
    expect(title).toHaveAttribute('id', `modal-title-${mockMember.id}`);
    expect(title).toHaveTextContent('Test User');

    // Check for close button label
    const closeButton = screen.getByRole('button', { name: /close modal/i });
    expect(closeButton).toBeInTheDocument();

    // Check for input labels association
    expect(screen.getByLabelText(/position/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/status/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/access role/i)).toBeInTheDocument();

    // Check for password input label (might be hidden visually but accessible)
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
  });
});
