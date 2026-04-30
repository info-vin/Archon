import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Employee, EmployeeRole } from '../types';
import { api, LoginCredentials, RegistrationData } from '../services/api';
import { supabase } from '../services/api';

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
    const initializeAuth = async () => {
        try {
            // 1. Ensure we have a valid session before fetching user identity
            const { data: { session }, error } = supabase ? await supabase.auth.getSession() : { data: { session: null }, error: null };
            
            if (error || !session?.access_token) {
                // Clear potentially corrupted tokens
                localStorage.removeItem('archon_token');
                localStorage.removeItem('user_role');
                setUser(null);
                return;
            }

            localStorage.setItem('archon_token', session.access_token);
            const currentUser = await api.getCurrentUser();
            setUser(currentUser);
        } catch (error) {
            console.error("Failed to initialize user session, forcing cleanup:", error);
            localStorage.removeItem('archon_token');
            localStorage.removeItem('user_role');
            setUser(null);
        } finally {
            setLoading(false);
        }
    };
    
    initializeAuth();

    if (supabase) {
        const { data: authListener } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            if (event === 'SIGNED_IN') {
              if (session?.access_token) {
                localStorage.setItem('archon_token', session.access_token);
              }
              setLoading(true);
              try {
                const currentUser = await api.getCurrentUser();
                setUser(currentUser);
              } finally {
                setLoading(false);
              }
            } else if (event === 'SIGNED_OUT') {
              setUser(null);
              localStorage.removeItem('archon_token');
              localStorage.removeItem('user_role');
            }
          }
        );

        return () => {
          authListener?.subscription.unsubscribe();
        };
    }
  }, []);

  useEffect(() => {
    if (user?.role) {
      localStorage.setItem('user_role', user.role);
    } else if (!user) {
      localStorage.removeItem('user_role');
    }
  }, [user]);

  const login = async (credentials: LoginCredentials) => {
    setLoading(true);
    try {
      const loggedInUser = await api.login(credentials);
      setUser(loggedInUser);
    } catch (error) {
      console.error("Login failed", error);
      throw error;
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
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
        await api.logout();
        setUser(null);
    } catch(error: any) {
        console.error(`Logout failed: ${error.message}`);
    }
  };

  const isAuthenticated = !!user;
  const role = user?.role?.toLowerCase();
  const isAdmin = role === 'admin' || role === 'system_admin' || role === EmployeeRole.ADMIN || role === EmployeeRole.SYSTEM_ADMIN;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isAdmin, login, register, logout, loading }}>
      {!loading ? children : (
        <div className="flex items-center justify-center min-h-screen bg-slate-900 text-white">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-lg font-medium animate-pulse">Syncing Identity Matrix...</p>
          </div>
        </div>
      )}
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
