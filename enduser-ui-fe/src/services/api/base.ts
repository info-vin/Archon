import { supabase } from './client';
import { Employee } from '../../types.ts';

/**
 * Shared state for user cache to reduce redundant profile fetches
 */
export const userState = {
  cache: null as Employee | null
};

/**
 * Internal helper to build headers with user role for RBAC
 */
export async function getHeaders(extraHeaders: Record<string, string> = {}): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  };

  try {
    // We'll need a circular dependency safe way to get currentUser, 
    // for now we use the exported cache or rely on the caller to provide it.
    if (userState.cache?.role) {
      headers['X-User-Role'] = userState.cache.role;
    }
    
    if (supabase) {
        // Physically retrieve session without race condition to avoid 401s in Docker
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (!sessionError && session?.access_token) {
            headers['Authorization'] = `Bearer ${session.access_token}`;
        }
    }
  } catch (e) {
    console.warn("Could not attach auth headers", e);
  }
  return headers;
}

/**
 * Safe response handler to prevent SyntaxErrors from non-JSON (HTML) error pages.
 * Includes 429 Retry logic to handle AI quota limits.
 */
export async function handleResponse(response: Response, errorContext: string, retryCount = 0): Promise<any> {
  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');

  if (response.status === 429 && retryCount < 2) {
      const delay = 2000 * (retryCount + 1);
      console.warn(`⏳ [API 429][${errorContext}]: Retrying in ${delay}ms... (Attempt ${retryCount + 1}/2)`);
      await new Promise(r => setTimeout(r, delay));
      
      const newResponse = await fetch(response.url, {
          method: 'GET', 
          headers: response.headers
      });
      return handleResponse(newResponse, errorContext, retryCount + 1);
  }

  if (!response.ok) {
      let errorMessage = errorContext;
      if (isJson) {
          const errorData = await response.json().catch(() => ({}));
          errorMessage = errorData.detail || errorData.message || errorContext;
      } else {
          const text = await response.text().catch(() => '');
          console.error(`🚨 [API ERROR][${errorContext}]: Server returned non-JSON response (${response.status}). Body snippet: ${text.slice(0, 300)}`);
          errorMessage = `Backend error (${response.status}): Unexpected response format (Expected JSON, got ${contentType || 'unknown'}).`;
      }
      throw new Error(errorMessage);
  }

  if (isJson) {
      return response.json();
  }
  return response.text();
}
