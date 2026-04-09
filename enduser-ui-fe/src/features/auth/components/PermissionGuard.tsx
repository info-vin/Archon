// enduser-ui-fe/src/features/auth/components/PermissionGuard.tsx

import React from 'react';
import { PermissionScope } from '../types';
import { usePermission } from '../hooks/usePermission';
import { useAuth } from '@/hooks/useAuth';

interface PermissionGuardProps {
  permission: PermissionScope;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * PermissionGuard: Protects UI components based on RBAC scopes.
 * Hardened with real-time identity sensing and physical audit logging.
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({ 
  permission, 
  children, 
  fallback = null 
}) => {
  const { hasPermission } = usePermission();
  const { user, loading } = useAuth();

  // 1. Initial State: Waiting for Identity Sync
  if (loading) {
    return null; // Silent while loading
  }

  // 2. Authorization Check: Use the synchronized hasPermission logic
  const isAllowed = hasPermission(permission);

  // --- PHYSICAL AUDIT: End the fantasy ---
  if (!isAllowed) {
    console.warn(`🛡️ [RBAC_GUARD] Access Denied | User: ${user?.email || 'Anonymous'} | Role: ${user?.role || 'None'} | Missing: ${permission}`);
  }

  if (!isAllowed) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
