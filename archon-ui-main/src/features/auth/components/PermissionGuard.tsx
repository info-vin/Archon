// archon-ui-main/src/features/auth/components/PermissionGuard.tsx

import React from 'react';
import { PermissionScope, EmployeeRole } from '../types';
import { usePermission } from '../hooks/usePermission';

interface PermissionGuardProps {
  permission: PermissionScope;
  userRole: EmployeeRole | undefined;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Higher-Order Component/Wrapper for RBAC.
 * Implements "Render Nothing" strategy for unauthorized access.
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  userRole,
  children,
  fallback = null
}) => {
  const { hasPermission } = usePermission(userRole);

  if (!hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
