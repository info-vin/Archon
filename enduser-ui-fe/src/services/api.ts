/**
 * Archon API Bridge (Facade Pattern)
 * This file remains for backward compatibility but the actual implementation 
 * has been moved to the ./api modular package to achieve L2 Hardening.
 */

export { api, supabase } from './api/index';
export * from './api/types';
