import { useState } from 'react';
import { useAuth } from '../../../hooks/useAuth';

export const useAdminPageLogic = () => {
  const { user, isAdmin } = useAuth();
  const role = user?.role?.toLowerCase();
  const isOnlyManager = !isAdmin && (role === 'manager');
  const canManageUsers = isAdmin || role === 'manager';
  
  const [activeTab, setActiveTab] = useState(isOnlyManager ? 'users' : 'health');

  return {
    activeTab,
    setActiveTab,
    isAdmin,
    isOnlyManager,
    canManageUsers,
    user
  };
};
