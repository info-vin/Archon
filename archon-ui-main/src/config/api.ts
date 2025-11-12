/**
 * Unified API Configuration
 * 
 * This module provides centralized configuration for API endpoints
 * and handles different environments (development, Docker, production)
 */

// Get the API URL from environment or use relative URLs for proxy
export function getApiUrl(): string {
  const viteApiUrl = import.meta.env.VITE_API_URL;

  // In production, VITE_API_URL MUST be set and non-empty
  if (import.meta.env.PROD) {
    if (!viteApiUrl || viteApiUrl.length === 0) {
      console.error(
        "CRITICAL ERROR: VITE_API_URL is not set in production environment. API calls will fail.",
      );
      // Return empty string to allow app to load, but API calls will fail visibly
      return "";
    }
    return viteApiUrl;
  }

  // In development, if VITE_API_URL is provided, use it.
  // Otherwise, return empty string to use Vite's proxy.
  return viteApiUrl || "";
}

// Get the base path for API endpoints
export function getApiBasePath(): string {
  const apiUrl = getApiUrl();
  
  // If using relative URLs (empty string), just return /api
  if (!apiUrl) {
    return '/api';
  }
  
  // Otherwise, append /api to the base URL
  return `${apiUrl}/api`;
}

// Export commonly used values
export const API_BASE_URL = '/api';  // Always use relative URL for API calls
export const API_FULL_URL = getApiUrl();
