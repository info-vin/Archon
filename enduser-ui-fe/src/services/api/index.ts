import { authApi } from './auth';
import { tasksApi } from './tasks';
import { statsApi } from './stats';
import { opsApi } from './ops';

/**
 * Modularized API Service for Archon End-User UI.
 * Achieves L2 Hardening by domain separation.
 */
export const api = {
  ...authApi,
  ...tasksApi,
  ...statsApi,
  ...opsApi,
  // Backward compatibility for unit tests
  getAssignableAgents: authApi.getAssignableAgents,
  getAttendanceStatus: opsApi.getAttendanceStatus,
};

// Re-export core dependencies and types for backward compatibility
export { supabase } from './client';
export * from './types';
