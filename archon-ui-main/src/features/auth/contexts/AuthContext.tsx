// archon-ui-main/src/features/auth/contexts/AuthContext.tsx

import type React from "react";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { API_BASE_URL } from "@/config/api";
import type { EmployeeRole, UserProfile } from "@/features/auth/types";

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  role: EmployeeRole | undefined;
  isLoading: boolean;
  error: string | null;
  loginWithSecret: (secret: string) => Promise<void>;
}

class AuthStatusError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
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

  const requestDevToken = useCallback(async (secret: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/auth/dev-token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Secret": secret,
      },
    });

    if (!response.ok) {
      throw new AuthStatusError(`Auto-login failed: ${response.statusText || response.status}`, response.status);
    }

    const data = await response.json();
    if (data.access_token && data.user) {
      setToken(data.access_token);
      localStorage.setItem("archon_token", data.access_token);
      setUser({
        id: data.user.id,
        email: data.user.email,
        name: "System Admin",
        role: "system_admin",
      });
    }
  }, []);

  useEffect(() => {
    const initAuth = async (retries = 3): Promise<void> => {
      try {
        setIsLoading(true);
        setError(null);
        await requestDevToken((import.meta.env.VITE_ADMIN_SECRET as string) || "");
        setIsLoading(false);
      } catch (err) {
        const status = err instanceof AuthStatusError ? err.status : undefined;
        if (status !== 401 && status !== 403 && retries > 0) {
          console.warn(`Auto-login attempt failed, retrying... (${retries} left)`);
          await new Promise((resolve) => setTimeout(resolve, 2000));
          return initAuth(retries - 1);
        }
        console.error("Auth initialization failed:", err);
        setError(err instanceof Error ? err.message : "Unknown auth error");
        setIsLoading(false);
      }
    };

    initAuth();
  }, [requestDevToken]);

  const loginWithSecret = async (secret: string): Promise<void> => {
    setError(null);
    await requestDevToken(secret);
  };

  return (
    <AuthContext.Provider value={{ user, token, role: user?.role, isLoading, error, loginWithSecret }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
