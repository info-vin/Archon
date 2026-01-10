// archon-ui-main/src/features/auth/types/index.ts

/**
 * Roles supported by the system.
 * Must be kept in sync with Backend (python/src/server/auth/permissions.py)
 */
export type EmployeeRole = 
  | 'system_admin' 
  | 'admin' 
  | 'manager' 
  | 'employee' 
  | 'sales' 
  | 'marketing';

/**
 * Basic user profile structure including Role.
 */
export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: EmployeeRole;
  avatar?: string;
}

/**
 * Permissions scopes for granular access control.
 * Naming convention: resource:action
 */
export type PermissionScope =
  | 'task:create'
  | 'task:read:own'
  | 'task:read:team'
  | 'task:read:all'
  | 'task:update:own'
  | 'task:update:all'
  | 'agent:trigger:dev'
  | 'agent:trigger:mkt'
  | 'agent:trigger:know'
  | 'code:approve'
  | 'content:publish'
  | 'stats:view:own'
  | 'stats:view:team'
  | 'stats:view:all'
  | 'leads:view:all'
  | 'user:manage'
  | 'mcp:manage';
