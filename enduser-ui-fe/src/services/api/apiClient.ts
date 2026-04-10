/**
 * enduser-ui-fe/src/services/api/apiClient.ts
 * 
 * Unified API Client for End-User UI (Port 5173).
 * Hardened with automatic JWT injection and RBAC (X-User-Role) header support.
 * Protects Alice, Bob, Charlie, and David's access rights.
 */

import { supabase } from './client';

export class APIServiceError extends Error {
  constructor(
    public message: string,
    public code: string = 'API_ERROR',
    public status: number = 500
  ) {
    super(message);
    this.name = 'APIServiceError';
  }
}

/**
 * Call the backend API with automatic authentication and Persona-based RBAC headers.
 * 
 * @param endpoint The API endpoint (e.g., '/api/stats/overview')
 * @param options Fetch options (method, body, etc.)
 */
export async function callAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // --- Physical Network Alignment (Pattern 7: Internal/External Isolation) ---
  // In Docker/Scout, relative paths don't work. We need a solid Base URL.
  let envBase = import.meta.env.VITE_API_URL || '';
  
  // 🟢 Physical Correction: If in browser and env points to internal Docker service, rewrite to localhost
  if (typeof window !== 'undefined' && envBase.includes('archon-server')) {
    envBase = envBase.replace('archon-server', 'localhost');
  }

  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Construct full URL with BaseURL logic
  const fullUrl = normalizedEndpoint.startsWith('http') 
    ? normalizedEndpoint 
    : `${envBase}${normalizedEndpoint}`;
  
  const headers: Record<string, string> = {
    ...((options.body instanceof FormData) ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as Record<string, string>),
  };

  try {
    // 1. JWT Injection (Authorization)
    // Primary: archon_token (Admin UI pattern), Fallback: Supabase session
    let token = localStorage.getItem('archon_token');
    
    if (!token && supabase) {
      const { data: { session } } = await supabase.auth.getSession();
      token = session?.access_token || null;
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // 2. Persona Protection (RBAC / X-User-Role Injection)
    // This is CRITICAL for Alice (sales), Bob (marketing), Charlie (manager) functionality.
    const savedRole = localStorage.getItem('user_role');
    if (savedRole) {
      headers['X-User-Role'] = savedRole;
    }

    const response = await fetch(fullUrl, {
      ...options,
      headers,
    });

    // 3. 429 Retry Logic (Persona Resiliency)
    if (response.status === 429) {
       console.warn(`⏳ [API 429][${normalizedEndpoint}]: Rate limited. Retrying in 2s...`);
       await new Promise(r => setTimeout(r, 2000));
       return callAPI<T>(endpoint, options);
    }

    if (!response.ok) {
      let message = `API Error ${response.status}`;
      let code = 'HTTP_ERROR';
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json().catch(() => ({}));
        message = errorData.detail || errorData.message || message;
        code = errorData.code || code;
      }
      
      throw new APIServiceError(message, code, response.status);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json() as T;
    }
    
    return await response.text() as unknown as T;

  } catch (error) {
    if (error instanceof APIServiceError) throw error;
    
    throw new APIServiceError(
      `Failed to call API ${normalizedEndpoint}: ${error instanceof Error ? error.message : 'Unknown error'}`,
      'NETWORK_ERROR',
      500
    );
  }
}
