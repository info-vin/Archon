// enduser-ui-fe/src/features/auth/hooks/usePermission.ts

import { EmployeeRole, PermissionScope } from '../types';
import { useAuth } from '../../../hooks/useAuth';

/**
 * Frontend Role-to-Permission Mapping.
 * SSOT: PRPs/ai_docs/RBAC_Collaboration_Matrix.md
 */
const PERMISSION_SETS: Record<string, Set<PermissionScope>> = {
  admin: new Set([
    'task:create', 'task:read:all', 'task:update:all',
    'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
    'code:approve', 'content:publish',
    'stats:view:all', 'leads:view:all',
    'user:manage', 'user:manage:team', 'mcp:manage'
  ]),
  manager: new Set([
    'task:create', 'task:read:team', 'task:update:own',
    'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
    'code:approve', 'content:publish',
    'stats:view:team', 'leads:view:all',
    'user:manage:team'
  ]),
  employee: new Set([
    'task:create', 'task:read:own', 'task:update:own',
    'agent:trigger:know',
    'stats:view:own'
  ]),
  sales: new Set([
    'task:create', 'task:read:own', 'task:update:own',
    'agent:trigger:mkt',
    'stats:view:own', 'leads:view:all'
  ]),
  marketing: new Set([
    'task:create', 'task:read:own', 'task:update:own',
    'agent:trigger:mkt', 'agent:trigger:know',
    'stats:view:own', 'leads:view:all'
  ])
};

// Map actual EmployeeRole enum values to Permission Sets
const ROLE_MAP: Record<EmployeeRole, Set<PermissionScope>> = {
  [EmployeeRole.SYSTEM_ADMIN]: PERMISSION_SETS.admin,
  [EmployeeRole.ADMIN]: PERMISSION_SETS.admin,
  [EmployeeRole.MANAGER]: PERMISSION_SETS.manager,
  [EmployeeRole.PROJECT_MANAGER]: PERMISSION_SETS.manager, // Legacy mapping
  [EmployeeRole.SENIOR_MEMBER]: PERMISSION_SETS.employee, // Legacy mapping
  [EmployeeRole.MEMBER]: PERMISSION_SETS.employee,
  [EmployeeRole.EMPLOYEE]: PERMISSION_SETS.employee,
  [EmployeeRole.SALES]: PERMISSION_SETS.sales,
  [EmployeeRole.MARKETING]: PERMISSION_SETS.marketing,
  [EmployeeRole.VIEWER]: new Set(['task:read:all']), // Basic view access
  [EmployeeRole.AI_AGENT]: new Set([])
};

/**
 * Custom hook for checking permissions.
 * Integrated with the main AuthContext via useAuth hook.
 */
export function usePermission() {
  const { user } = useAuth();
  
  const hasPermission = (permission: PermissionScope): boolean => {
    if (!user?.role) {
        return false;
    }
    
    const permissions = ROLE_MAP[user.role];
    const allowed = permissions?.has(permission) ?? false;
    
    return allowed;
  };

  return { hasPermission };
}