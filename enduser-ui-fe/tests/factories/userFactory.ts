
import { EmployeeRole, Employee } from '../../src/types';
import { PERMISSION_SETS } from '../../src/features/auth/hooks/usePermission';

/**
 * User Factory for E2E Tests.
 * Ensures that mock users always have up-to-date permissions based on the real implementation.
 */
export const createUser = (overrides: Partial<Employee> & { role: EmployeeRole }): Employee => {
  const { role } = overrides;
  
  // Map internal sets to roles
  let permissionSet: Set<string> = new Set();
  
  if (role === EmployeeRole.SYSTEM_ADMIN || role === EmployeeRole.ADMIN) {
    permissionSet = PERMISSION_SETS.admin;
  } else if (role === EmployeeRole.MANAGER || role === EmployeeRole.PROJECT_MANAGER) {
    permissionSet = PERMISSION_SETS.manager;
  } else if (role === EmployeeRole.SALES) {
    permissionSet = PERMISSION_SETS.sales;
  } else if (role === EmployeeRole.MARKETING) {
    permissionSet = PERMISSION_SETS.marketing;
  } else if (role === EmployeeRole.EMPLOYEE || role === EmployeeRole.MEMBER) {
    permissionSet = PERMISSION_SETS.employee;
  }

  const defaultUser: Employee = {
    id: `mock-id-${role}-${Math.random().toString(36).substr(2, 9)}`,
    employeeId: `EMP-${Math.floor(Math.random() * 1000)}`,
    name: `Mock ${role.charAt(0).toUpperCase() + role.slice(1)}`,
    email: `mock.${role}@archon.ai`,
    role: role,
    department: role === EmployeeRole.SALES ? 'Sales' : (role === EmployeeRole.MARKETING ? 'Marketing' : 'Management'),
    status: 'active',
    position: 'Automated Tester',
    avatar: 'https://i.pravatar.cc/150',
    permissions: Array.from(permissionSet)
  };

  return { ...defaultUser, ...overrides };
};
