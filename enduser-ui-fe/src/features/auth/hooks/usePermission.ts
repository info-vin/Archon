// enduser-ui-fe/src/features/auth/hooks/usePermission.ts

import { EmployeeRole, PermissionScope } from '../types';
import { useAuth } from '../../../hooks/useAuth';

/**
 * Frontend Role-to-Permission Mapping.
 * SSOT: PRPs/ai_docs/RBAC_Collaboration_Matrix.md
 */
export const PERMISSION_SETS: Record<string, Set<PermissionScope>> = {
  admin: new Set([
    'task:create', 'task:read:all', 'task:update:all',
    'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
    'code:approve', 'content:publish',
    'stats:view:all', 'stats:view:own',
    'leads:view:sales', 'leads:view:marketing', // Admin sees all
    'user:manage', 'user:manage:team', 'mcp:manage'
  ]),
  manager: new Set([
     'task:create', 'task:read:team', 'task:update:own',
     'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
     'code:approve', 'content:publish',
     'stats:view:team', 'stats:view:own',
     'leads:view:sales', 'leads:view:marketing', // Manager sees all
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
    'stats:view:own', 
    'leads:view:sales' // Sales only sees Sales Nexus
  ]),
  marketing: new Set([
    'task:create', 'task:read:own', 'task:update:own',
    'agent:trigger:mkt', 'agent:trigger:know',
    'stats:view:own', 
    'leads:view:marketing' // Marketing only sees Brand Hub
  ])
};


// Map actual EmployeeRole enum values to Permission Sets
const ROLE_MAP: Record<EmployeeRole | string, Set<PermissionScope>> = {
  [EmployeeRole.SYSTEM_ADMIN]: PERMISSION_SETS.admin,
  [EmployeeRole.ADMIN]: PERMISSION_SETS.admin,
  [EmployeeRole.MANAGER]: PERMISSION_SETS.manager,
  [EmployeeRole.PROJECT_MANAGER]: PERMISSION_SETS.manager,
  ['PM' as any]: PERMISSION_SETS.manager, // Support raw 'PM' string from DB
  ['pm']: PERMISSION_SETS.manager,
  ['project manager']: PERMISSION_SETS.manager,
  [EmployeeRole.SENIOR_MEMBER]: PERMISSION_SETS.employee, // Legacy mapping
  [EmployeeRole.MEMBER]: PERMISSION_SETS.employee,
  [EmployeeRole.EMPLOYEE]: PERMISSION_SETS.employee,
  ['engineer']: PERMISSION_SETS.employee,
  ['developer']: PERMISSION_SETS.employee,
  [EmployeeRole.SALES]: PERMISSION_SETS.sales,
  [EmployeeRole.MARKETING]: PERMISSION_SETS.marketing,
  ['marketer']: PERMISSION_SETS.marketing,
  ['market researcher']: PERMISSION_SETS.marketing,
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
    if (!user) {
        return false;
    }

    // 1. Check Dynamic Permissions (DB/Mock) - Primary Source
    if (user.permissions && Array.isArray(user.permissions) && user.permissions.length > 0) {
        if ((user.permissions as string[]).includes(permission)) return true;
    }
    
    // 2. Industrial-Grade Fallback: Check Static Role-based Mapping (SSOT)
    // This ensures that even if dynamic permissions are missing or empty, 
    // basic role-based access is preserved.
    if (user.role) {
        const normalizedRole = user.role.toLowerCase();
        const rolePermissions = ROLE_MAP[normalizedRole] || ROLE_MAP[user.role];
        if (rolePermissions?.has(permission)) return true;
    }

    return false;
  };

  return { hasPermission };
}