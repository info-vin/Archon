// enduser-ui-fe/src/features/auth/components/PermissionGuard.tsx

import React from 'react';
import { PermissionScope, EmployeeRole } from '../types';
import { usePermission } from '../hooks/usePermission';
import { useAuth } from '../../../hooks/useAuth';

interface PermissionGuardProps {
  permission: PermissionScope;
  userRole?: EmployeeRole; // Optional as it's now internal
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Higher-Order Component for RBAC.
 * Prevents unauthorized rendering and handles auth loading state.
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  children,
  fallback = null
}) => {
  const { hasPermission } = usePermission();
  const { loading } = useAuth();

  // Wait for auth to initialize before making decisions
  if (loading) {
    return <div className="p-4 text-center text-gray-400">Verifying access...</div>;
  }

  console.log('PermissionGuard check:', { permission, has: hasPermission(permission), user: 'unavailable_here' });
  if (!hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
