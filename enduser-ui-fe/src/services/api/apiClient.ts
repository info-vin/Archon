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

export function getBaseUrl(): string {
  let envBase = import.meta.env.VITE_API_URL || '';
  if (typeof window !== 'undefined' && envBase.includes('archon-server')) {
    envBase = envBase.replace('archon-server', 'localhost');
  }
  return envBase;
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
  // In Docker environments, VITE_API_URL might point to internal DNS (archon-server).
  // We MUST rewrite this to localhost for browser-side execution.
  const envBase = getBaseUrl();
  
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
      // Resilient check: check localStorage directly to avoid Web Lock hangs in E2E
      const keys = Object.keys(localStorage);
      const sbKey = keys.find(k => k.startsWith('sb-') && k.endsWith('-auth-token'));
      if (sbKey) {
        try {
          const sessionData = JSON.parse(localStorage.getItem(sbKey) || '{}');
          token = sessionData?.access_token || null;
        } catch (e) {
          console.warn("apiClient: Failed to parse localStorage token", e);
        }
      }

      // If still no token, try getSession but with a race to avoid permanent hang
      if (!token) {
        try {
          const sessionResult: any = await Promise.race([
            supabase.auth.getSession(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Auth timeout')), 3000))
          ]);
          token = sessionResult?.data?.session?.access_token || null;
        } catch (e) {
          console.warn("apiClient: Auth session retrieval failed/timed out", e);
        }
      }
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

    // 3. Timeout Logic (Resiliency against hangs)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    let response;
    try {
        response = await fetch(fullUrl, {
            ...options,
            headers,
            signal: controller.signal
        });
    } finally {
        clearTimeout(timeoutId);
    }

    // 4. 429 Retry Logic (Persona Resiliency)
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
