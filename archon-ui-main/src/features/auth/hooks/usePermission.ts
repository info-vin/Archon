// archon-ui-main/src/features/auth/hooks/usePermission.ts

import { EmployeeRole, PermissionScope } from '@/features/auth/types';

/**
 * Frontend Role-to-Permission Mapping.
 * SSOT: PRPs/ai_docs/RBAC_Collaboration_Matrix.md
 */
const ROLE_PERMISSIONS: Record<EmployeeRole, Set<PermissionScope>> = {
  system_admin: new Set([
    'task:create', 'task:read:all', 'task:update:all',
    'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
    'code:approve', 'content:publish',
    'stats:view:all', 'leads:view:all',
    'user:manage', 'mcp:manage'
  ]),
  admin: new Set([ // Alias
    'task:create', 'task:read:all', 'task:update:all',
    'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
    'code:approve', 'content:publish',
    'stats:view:all', 'leads:view:all',
    'user:manage', 'mcp:manage'
  ]),
  manager: new Set([
    'task:create', 'task:read:team', 'task:update:own',
    'agent:trigger:dev', 'agent:trigger:mkt', 'agent:trigger:know',
    'code:approve', 'content:publish',
    'stats:view:team', 'leads:view:all'
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

/**
 * Custom hook for checking permissions.
 * Usage: const { hasPermission } = usePermission(userRole);
 */
export function usePermission(role: EmployeeRole | undefined) {
  const hasPermission = (permission: PermissionScope): boolean => {
    if (!role) return false;
    const permissions = ROLE_PERMISSIONS[role.toLowerCase() as EmployeeRole];
    return permissions?.has(permission) ?? false;
  };

  return { hasPermission };
}
