import { supabase } from './client';
import { getHeaders, handleResponse, userState } from './base';
import { Employee, EmployeeRole, AssignableUser } from '../../types.ts';
import { LoginCredentials, RegistrationData, AdminNewUserData } from './types';

export const authApi = {
  async login(credentials: LoginCredentials): Promise<Employee | null> {
    userState.cache = null;
    const { data, error } = await supabase!.auth.signInWithPassword({
      email: credentials.email,
      password: credentials.password!,
    });
    if (error) throw new Error(error.message);
    if (data.user) return this.getCurrentUser();
    throw new Error("Login failed. Please check your credentials.");
  },

  async register(credentials: RegistrationData): Promise<Employee | null> {
    userState.cache = null; 
    const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
    });

    await handleResponse(response, 'Registration failed');
    return this.login({ email: credentials.email, password: credentials.password });
  },

  async adminCreateUser(userData: AdminNewUserData): Promise<Employee> {
    const response = await fetch('/api/admin/users', {
        method: 'POST',
        headers: await getHeaders(), 
        body: JSON.stringify(userData)
    });

    const data = await handleResponse(response, 'Failed to create user');
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
    try {
      const sessionResult: any = await Promise.race([
        supabase.auth.getSession(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Auth timeout')), 5000))
      ]);

      const { data: { session }, error: sessionError } = sessionResult;
      if (sessionError) throw new Error(sessionError.message);
      if (!session?.user) return null;
      sessionUser = session.user;
    } catch (e) {
      console.warn("[api/auth.ts] Auth check failed:", e);
      return null;
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
    const response = await fetch('/api/auth/permissions', { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch permissions');
    return data.permissions;
  },

  async updateUserEmail(newEmail: string): Promise<void> {
    const response = await fetch('/api/auth/email', {
        method: 'PUT',
        headers: await getHeaders(),
        body: JSON.stringify({ new_email: newEmail })
    });
    await handleResponse(response, 'Failed to update email');
  },

  async updateUserPassword(newPassword: string): Promise<void> {
    const { error } = await supabase!.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
  },

  async updateEmployee(id: string, updates: Partial<Employee>): Promise<Employee> {
    const response = await fetch(`/api/admin/users/${id}`, {
        method: 'PATCH',
        headers: await getHeaders(),
        body: JSON.stringify(updates)
    });
    const data = await handleResponse(response, 'Failed to update employee');
    return data.profile;
  },

  async getEmployees(): Promise<Employee[]> {
    const response = await fetch('/api/admin/users', { headers: await getHeaders() });
    const data = await handleResponse(response, 'Failed to fetch employees');
    return data.profiles;
  },

  async getAssignableUsers(): Promise<AssignableUser[]> {
    const response = await fetch('/api/tasks/assignable-users', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch assignable users');
  },

  async getAssignableAgents(): Promise<any[]> {
    const response = await fetch('/api/tasks/assignable-agents', { headers: await getHeaders() });
    return handleResponse(response, 'Failed to fetch assignable agents');
  },

  async resetPassword(userId: string, newPassword: string): Promise<void> {
    const response = await fetch(`/api/admin/users/${userId}/reset-password`, {
        method: 'POST',
        headers: await getHeaders(),
        body: JSON.stringify({ password: newPassword })
    });
    await handleResponse(response, 'Failed to reset password');
  }
};
