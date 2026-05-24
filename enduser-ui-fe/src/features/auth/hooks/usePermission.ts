// enduser-ui-fe/src/features/auth/hooks/usePermission.ts

import { useMemo, useCallback } from 'react';
import { EmployeeRole, PermissionScope } from '../types';
import { useAuth } from '@/hooks/useAuth';

/**
 * Frontend Role-to-Permission Mapping.
 * SSOT: PRPs/ai_docs/RBAC_Collaboration_Matrix.md
 */
export const PERMISSION_SETS: Record<string, Set<string>> = {
  admin: new Set(['*']),
  manager: new Set([
    'task:create', 'task:read:team', 'task:update:own', 'user:manage:team',
    'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:team', 'leads:view:all',
    'brand:manage', 'code:approve', 'mcp:manage', 'content:publish', 'content:reject', 'info:request'
  ]),
  sales: new Set([
    'task:create', 'task:read:own', 'task:read:team', 'task:update:own',
    'agent:trigger:mkt', 'leads:view:all', 'leads:view:sales', 'stats:view:own'
  ]),
  marketing: new Set([
    'task:create', 'task:read:own', 'task:read:team', 'task:update:own',
    'agent:trigger:mkt', 'agent:trigger:know', 'stats:view:own', 'leads:view:all',
    'brand:manage', 'info:request'
  ]),
  ai_agent: new Set([
    'task:read:own', 'task:read:team', 'agent:trigger:know', 'stats:view:own'
  ]),
  employee: new Set([
    'task:create', 'task:read:own', 'task:update:own', 'agent:trigger:know', 'stats:view:own'
  ]),
  viewer: new Set(['task:read:own', 'stats:view:own'])
};

const ROLE_MAP: Record<string, Set<string>> = {
  [EmployeeRole.SYSTEM_ADMIN]: PERMISSION_SETS.admin,
  [EmployeeRole.ADMIN]: PERMISSION_SETS.admin,
  [EmployeeRole.MANAGER]: PERMISSION_SETS.manager,
  [EmployeeRole.SALES]: PERMISSION_SETS.sales,
  [EmployeeRole.MARKETING]: PERMISSION_SETS.marketing,
  [EmployeeRole.AI_AGENT]: PERMISSION_SETS.ai_agent,
  [EmployeeRole.EMPLOYEE]: PERMISSION_SETS.employee,
  [EmployeeRole.MEMBER]: PERMISSION_SETS.employee,
  [EmployeeRole.VIEWER]: PERMISSION_SETS.viewer,
};

export function usePermission() {
  const { user } = useAuth();
  
  // PERFORMANCE: Precalculate and memoize the full permission set based on the current user.
  // This prevents O(N) array mapping, redundant string allocations (.toLowerCase()),
  // and Set instantiations on every single call to hasPermission during render.
  const allPerms = useMemo(() => {
    if (!user) return new Set<string>();

    const dynamicPerms = user.permissions || (user as any).scopes || [];
    const normalizedRole = (user.role || '').toLowerCase();
    const staticPermsSet = ROLE_MAP[normalizedRole] || new Set();
    
    return new Set([
        ...dynamicPerms.map((p: string) => p.toLowerCase()),
        ...Array.from(staticPermsSet).map((p: any) => p.toLowerCase())
    ]);
  }, [user]);

  const hasPermission = useCallback((permission: PermissionScope): boolean => {
    if (!user) return false;
    if (allPerms.has('*')) return true;

    return allPerms.has(permission.toLowerCase());
  }, [user, allPerms]);

  return { hasPermission };
}
