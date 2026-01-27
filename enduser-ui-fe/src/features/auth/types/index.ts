// enduser-ui-fe/src/features/auth/types/index.ts

import { EmployeeRole } from '../../../types';

export { EmployeeRole };

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
  | 'leads:view:sales'
  | 'leads:view:marketing'
  | 'user:manage'
  | 'user:manage:team'
  | 'mcp:manage';