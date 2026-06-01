// archon-ui-main/src/features/auth/hooks/usePermission.ts

import { useMemo, useCallback } from "react";
import { EmployeeRole, PermissionScope } from "@/features/auth/types";

/**
 * Frontend Role-to-Permission Mapping.
 * SSOT: PRPs/ai_docs/RBAC_Collaboration_Matrix.md
 */
const ROLE_PERMISSIONS: Record<EmployeeRole, Set<PermissionScope>> = {
  system_admin: new Set([
    "task:create",
    "task:read:all",
    "task:update:all",
    "agent:trigger:dev",
    "agent:trigger:mkt",
    "agent:trigger:know",
    "code:approve",
    "content:publish",
    "stats:view:all",
    "leads:view:all",
    "user:manage",
    "mcp:manage",
  ]),
  admin: new Set([
    // Alias
    "task:create",
    "task:read:all",
    "task:update:all",
    "agent:trigger:dev",
    "agent:trigger:mkt",
    "agent:trigger:know",
    "code:approve",
    "content:publish",
    "stats:view:all",
    "leads:view:all",
    "user:manage",
    "mcp:manage",
  ]),
  manager: new Set([
    "task:create",
    "task:read:team",
    "task:update:own",
    "agent:trigger:dev",
    "agent:trigger:mkt",
    "agent:trigger:know",
    "code:approve",
    "content:publish",
    "stats:view:team",
    "leads:view:all",
  ]),
  employee: new Set(["task:create", "task:read:own", "task:update:own", "agent:trigger:know", "stats:view:own"]),
  sales: new Set([
    "task:create",
    "task:read:own",
    "task:update:own",
    "agent:trigger:mkt",
    "stats:view:own",
    "leads:view:all",
  ]),
  marketing: new Set([
    "task:create",
    "task:read:own",
    "task:update:own",
    "agent:trigger:mkt",
    "agent:trigger:know",
    "stats:view:own",
    "leads:view:all",
  ]),
};

/**
 * Custom hook for checking permissions.
 * Usage: const { hasPermission } = usePermission(userRole);
 */
export function usePermission(role: EmployeeRole | undefined) {
  // PERFORMANCE: Memoize derived state outside of the returned callback to prevent
  // redundant string allocations (.toLowerCase()) on every single invocation during render.
  const permissions = useMemo(() => {
    if (!role) return undefined;
    return ROLE_PERMISSIONS[role.toLowerCase() as EmployeeRole];
  }, [role]);

  const hasPermission = useCallback(
    (permission: PermissionScope): boolean => {
      return permissions?.has(permission) ?? false;
    },
    [permissions],
  );

  return { hasPermission };
}
