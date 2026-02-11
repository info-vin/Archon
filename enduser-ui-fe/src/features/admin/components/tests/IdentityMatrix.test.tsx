
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { IdentityMatrix } from '../IdentityMatrix.tsx';
import { api } from '../../../../services/api.ts';
import { EmployeeRole } from '../../../../types.ts';

// Mock the API
vi.mock('../../../../services/api.ts', () => ({
  api: {
    getEmployees: vi.fn(),
    updateEmployee: vi.fn(),
    adminCreateUser: vi.fn(),
    getSystemPermissions: vi.fn().mockResolvedValue(['task:create', 'agent:trigger:dev', 'content:publish']),
  },
}));

describe('IdentityMatrix', () => {
    const mockEmployees = [
        {
            id: '1',
            name: 'Alice Admin',
            email: 'alice@test.com',
            role: EmployeeRole.ADMIN,
            status: 'active',
            avatar: '',
            employeeId: 'EMP-001'
        },
        {
            id: '2',
            name: 'Bob Manager',
            email: 'bob@test.com',
            role: EmployeeRole.MANAGER,
            status: 'active',
            avatar: '',
            employeeId: 'EMP-002'
        }
    ];

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders loading state initially', () => {
        (api.getEmployees as any).mockImplementation(() => new Promise(() => {}));
        render(<IdentityMatrix />);
        expect(screen.getByText(/Loading Identity Matrix/i)).toBeInTheDocument();
    });

    it('renders employee list after fetching', async () => {
        (api.getEmployees as any).mockResolvedValue(mockEmployees);
        render(<IdentityMatrix />);
        
        await waitFor(() => {
            expect(screen.getByText('Alice Admin')).toBeInTheDocument();
        });
        
        expect(screen.getByText('bob@test.com')).toBeInTheDocument();
        expect(screen.getByText('Identity Matrix')).toBeInTheDocument();
        expect(screen.getAllByText('Edit').length).toBe(2);
    });

    it('opens edit modal when clicking edit', async () => {
        (api.getEmployees as any).mockResolvedValue(mockEmployees);
        render(<IdentityMatrix />);
        
        await waitFor(() => {
            expect(screen.getByText('Alice Admin')).toBeInTheDocument();
        });

        const editButtons = screen.getAllByText('Edit');
        fireEvent.click(editButtons[0]); // Click Alice's edit

        expect(screen.getByText(/Access Overrides: Alice Admin/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Base Role/i)).toBeInTheDocument();
    });
});
