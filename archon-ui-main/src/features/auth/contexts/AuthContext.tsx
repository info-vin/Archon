// archon-ui-main/src/features/auth/contexts/AuthContext.tsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, EmployeeRole } from '@/features/auth/types';
import { API_BASE_URL } from '@/config/api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  role: EmployeeRole | undefined;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * SSOT for Auth State in Archon Admin UI.
 * Automatically logs in as System Admin in development mode.
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Attempt Dev Auto-Login
        // NOTE: In production, this would check for existing session or redirect to /login
        const response = await fetch(`${API_BASE_URL}/auth/dev-token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
          throw new Error(`Auto-login failed: ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data.access_token && data.user) {
          setToken(data.access_token);
          // Store token for apiClient to pick up
          localStorage.setItem('archon_token', data.access_token);
          
          setUser({
            id: data.user.id,
            email: data.user.email,
            name: "System Admin",
            role: "system_admin" // Enforced role for Admin UI
          });
        }
      } catch (err) {
        console.error("Auth initialization failed:", err);
        setError(err instanceof Error ? err.message : "Unknown auth error");
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, role: user?.role, isLoading, error }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
