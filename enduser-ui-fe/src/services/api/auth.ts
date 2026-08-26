import { supabase } from './client';
import { userState } from './base';
import { Employee, EmployeeRole, AssignableUser } from '../../types.ts';
import { LoginCredentials, RegistrationData, AdminNewUserData } from './types';
import { callAPI } from './apiClient';

export const authApi = {
  async login(credentials: LoginCredentials): Promise<Employee | null> {
    userState.cache = null;
    const { data, error } = await supabase!.auth.signInWithPassword({
      email: credentials.email,
      password: credentials.password!,
    });
    if (error) throw new Error(error.message);
    if (data.user && data.session) {
      // --- Physical Parity: Ensure token is ready BEFORE the next API call ---
      if (typeof localStorage !== 'undefined') localStorage.setItem('archon_token', data.session.access_token);
      return this.getCurrentUser();
    }
    throw new Error("Login failed. Please check your credentials.");
  },

  async register(credentials: RegistrationData): Promise<Employee | null> {
    userState.cache = null; 
    await callAPI('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(credentials)
    });

    return this.login({ email: credentials.email, password: credentials.password });
  },

  async adminCreateUser(userData: AdminNewUserData): Promise<Employee> {
    const data = await callAPI<{ profile: Employee }>('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify(userData)
    });

    return data.profile;
  },

  async logout(): Promise<void> {
    userState.cache = null;
    const { error } = await supabase!.auth.signOut();
    if (error) throw new Error(error.message);
  },

  async getCurrentUser(): Promise<Employee | null> {
    if (!supabase) return null;
    if (userState.cache) return userState.cache;

    let sessionUser: any = null;

    // Fast-path for Playwright/E2E environments to avoid 5-second Web Lock hangs
    try {
      const isTestEnv = typeof window !== 'undefined' && (window.navigator as any).webdriver;
      if (isTestEnv) {
        const keys = Object.keys(localStorage);
        const sbKey = keys.find(k => k.startsWith('sb-') && k.endsWith('-auth-token'));
        if (sbKey) {
          const sessionData = JSON.parse(localStorage.getItem(sbKey) || '{}');
          if (sessionData && sessionData.user) {
             sessionUser = sessionData.user;
          }
        }
      }
    } catch (e) {
      // Ignore fast-path errors
    }

    if (!sessionUser) {
      try {
        const sessionResult: any = await Promise.race([
          supabase.auth.getSession(),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Auth timeout')), 5000))
        ]);

        const { data: { session }, error: sessionError } = sessionResult;
        if (sessionError) throw new Error(sessionError.message);
        if (!session?.user) throw new Error("No user in session");
        sessionUser = session.user;
      } catch (e) {
        console.warn("[api/auth.ts] Auth check failed:", e);
        // Resilient Fallback: Manually parse localStorage
        try {
          const keys = Object.keys(localStorage);
          const sbKey = keys.find(k => k.startsWith('sb-') && k.endsWith('-auth-token'));
          if (sbKey) {
            const sessionData = JSON.parse(localStorage.getItem(sbKey) || '{}');
            if (sessionData && sessionData.user) {
               console.log("[api/auth.ts] Resilient fallback: Loaded session from localStorage");
               sessionUser = sessionData.user;
            }
          }
        } catch (parseError) {
           console.error("Resilient fallback failed:", parseError);
        }
        
        if (!sessionUser) return null;
      }
    }

    try {
      const { data: profile, error } = await supabase.from('profiles').select('*').eq('id', sessionUser.id).maybeSingle();
      if (error) throw error;
      if (!profile) throw new Error("Profile missing");
      
      userState.cache = profile as Employee;
      return userState.cache;
    } catch (e: any) {
      const metadataRole = sessionUser.user_metadata?.role || EmployeeRole.MEMBER;
      userState.cache = { 
        id: sessionUser.id, 
        email: sessionUser.email!, 
        name: sessionUser.user_metadata.name || sessionUser.email?.split('@')[0] || 'Authenticated User', 
        role: metadataRole as EmployeeRole, 
        avatar: sessionUser.user_metadata.avatar_url || `https://i.pravatar.cc/150?u=${sessionUser.id}`,
        employeeId: 'TEMP-' + sessionUser.id.substring(0, 5),
        department: 'Unknown', status: 'active' 
      } as Employee;
      return userState.cache;
    }
  },

  async getSystemPermissions(): Promise<string[]> {
    const data = await callAPI<{ permissions: string[] }>('/api/auth/permissions');
    return data.permissions;
  },

  async updateUserEmail(newEmail: string): Promise<void> {
    await callAPI('/api/auth/email', {
        method: 'PUT',
        body: JSON.stringify({ new_email: newEmail })
    });
  },

  async updateUserPassword(newPassword: string): Promise<void> {
    const { error } = await supabase!.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
  },

  async updateEmployee(id: string, updates: Partial<Employee>): Promise<Employee> {
    const data = await callAPI<{ profile: Employee }>(`/api/admin/users/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(updates)
    });
    return data.profile;
  },

  async getEmployees(): Promise<Employee[]> {
    const data = await callAPI<any>('/api/admin/users');
    if (Array.isArray(data)) return data;
    return data.profiles || data.users || [];
  },

  async getAssignableUsers(): Promise<AssignableUser[]> {
    return await callAPI<AssignableUser[]>('/api/assignable-users');
  },

  async getAssignableAgents(): Promise<any[]> {
    return await callAPI<any[]>('/api/agents/assignable');
  },

  async resetPassword(userId: string, newPassword: string): Promise<void> {
    await callAPI(`/api/admin/users/${userId}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ password: newPassword })
    });
  },

  async getRBACMatrix(): Promise<any[]> {
    return await callAPI<any[]>('/api/admin/rbac/matrix');
  },

  async updateRBACRole(role: string, permissions: string[], description?: string): Promise<any> {
    return await callAPI<any>('/api/admin/rbac/role', {
        method: 'POST',
        body: JSON.stringify({ role, permissions, description })
    });
  }
};
