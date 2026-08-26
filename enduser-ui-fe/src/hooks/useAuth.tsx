import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { Employee, EmployeeRole } from '../types';
import { api } from '../services/api';
import { supabase } from '../services/api';

interface AuthContextType {
  user: Employee | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: any) => Promise<void>;
  register: (credentials: any) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<Employee | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const syncIdentity = useCallback(async () => {
    try {
        const currentUser = await api.getCurrentUser();
        setUser(currentUser);
    } catch (error) {
        console.error("[AuthProvider] Identity sync failed:", error);
        setUser(null);
    } finally {
        setLoading(false);
    }
  }, []);

  useEffect(() => {
    const initializeAuth = async () => {
        try {
            // 1. Race to check if session exists
            const sessionPromise = supabase ? supabase.auth.getSession() : Promise.resolve({ data: { session: null } });
            const result: any = await Promise.race([
                sessionPromise,
                new Promise(resolve => setTimeout(() => resolve({ data: { session: null }, error: 'timeout' }), 2000))
            ]);

            const session = result?.data?.session;
            if (session?.access_token) {
                if (typeof localStorage !== 'undefined') localStorage.setItem('archon_token', session.access_token);
                await syncIdentity();
            } else {
                // Check if we have a legacy token or it's a headless state
                if (localStorage.getItem('archon_token')) {
                    await syncIdentity();
                } else {
                    setLoading(false);
                }
            }
        } catch (e) {
            setLoading(false);
        }
    };

    initializeAuth();

    if (supabase) {
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            if (event === 'SIGNED_IN' && session?.access_token) {
                if (typeof localStorage !== 'undefined') localStorage.setItem('archon_token', session.access_token);
                syncIdentity();
            } else if (event === 'SIGNED_OUT') {
                if (typeof localStorage !== 'undefined') localStorage.removeItem('archon_token');
                if (typeof localStorage !== 'undefined') localStorage.removeItem('user_role');
                setUser(null);
            }
        });
        return () => subscription.unsubscribe();
    }
  }, [syncIdentity]);

  const login = async (credentials: any) => {
    setLoading(true);
    try {
      const loggedInUser = await api.login(credentials);
      setUser(loggedInUser);
    } finally {
      setLoading(false);
    }
  };

  const register = async (credentials: any) => {
    setLoading(true);
    try {
      const newUser = await api.register(credentials);
      setUser(newUser);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
        await api.logout();
        setUser(null);
    } catch(e) {}
  };

  const isAuthenticated = !!user;
  const role = user?.role?.toLowerCase();
  const isAdmin = role === 'admin' || role === 'system_admin' || role === EmployeeRole.ADMIN || role === EmployeeRole.SYSTEM_ADMIN;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isAdmin, login, register, logout, loading }}>
      {loading ? (
        <div className="flex items-center justify-center min-h-screen bg-slate-950 text-white font-sans">
             <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                <div className="text-xl font-black tracking-tighter uppercase animate-pulse">Syncing HUD...</div>
             </div>
        </div>
      ) : children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) throw new Error('useAuth missing provider');
  return context;
};
