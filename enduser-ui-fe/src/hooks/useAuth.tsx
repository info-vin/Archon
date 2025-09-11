import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Employee, EmployeeRole } from '../types.ts';
import { api, LoginCredentials, RegistrationData } from '../services/api.ts';
import { supabase } from '../services/api.ts';

interface AuthContextType {
  user: Employee | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegistrationData) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<Employee | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchUser = async () => {
        try {
            const currentUser = await api.getCurrentUser();
            setUser(currentUser);
        } catch (error) {
            console.error("Failed to fetch current user:", error);
            // Could clear localstorage/sessionstorage here if auth is invalid
        } finally {
            setLoading(false);
        }
    };
    
    fetchUser();

    // Only set up the real-time listener if Supabase is configured
    if (supabase) {
        const { data: authListener } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            if (event === 'SIGNED_IN' || event === 'USER_UPDATED' || event === 'TOKEN_REFRESHED') {
              const currentUser = await api.getCurrentUser();
              setUser(currentUser);
            }
            if (event === 'SIGNED_OUT') {
              setUser(null);
            }
          }
        );

        return () => {
          authListener?.subscription.unsubscribe();
        };
    }
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setLoading(true);
    try {
      const loggedInUser = await api.login(credentials);
      setUser(loggedInUser);
    } catch (error) {
      console.error("Login failed", error);
      throw error; // Re-throw for the UI component
    } finally {
      setLoading(false);
    }
  };

  const register = async (credentials: RegistrationData) => {
    setLoading(true);
    try {
      const newUser = await api.register(credentials);
      setUser(newUser);
    } catch (error) {
      console.error("Registration failed", error);
      throw error; // Re-throw for the UI component
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
        await api.logout();
        setUser(null);
    } catch(error: any) {
        alert(`Logout failed: ${error.message}`);
    }
  };

  const isAuthenticated = !!user;
  const isAdmin = user?.role === EmployeeRole.SYSTEM_ADMIN;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isAdmin, login, register, logout, loading }}>
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
