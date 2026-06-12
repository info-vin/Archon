import React, { useEffect } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/hooks/useAuth';
import { useSSE } from '@/hooks/useSSE';
import { EmployeeRole } from './types';
import LandingPage from './pages/LandingPage.tsx';
import AuthPage from './pages/AuthPage.tsx';
import DashboardPage from './pages/DashboardPage.tsx';
import AdminPage from './pages/AdminPage.tsx';
import BlogPage from './pages/BlogPage.tsx';
import BlogDetailPage from './pages/BlogDetailPage.tsx';
import SettingsPage from './pages/SettingsPage.tsx';
import StatsPage from './pages/StatsPage.tsx';
import MarketingPage from './pages/MarketingPage.tsx';
import TeamManagementPage from './pages/TeamManagementPage.tsx';
import BrandPage from './pages/BrandPage.tsx';
import { ManagerNexus } from './pages/ManagerNexus.tsx';
import ApprovalsPage from './pages/ApprovalsPage.tsx';
import PublicLayout from './components/layout/PublicLayout.tsx';
import MainLayout from './components/layout/MainLayout.tsx';
import SolutionsPage from './features/marketing/SolutionsPage.tsx';
import SalesCartPage from './pages/SalesCartPage.tsx';
import BlogEditor from './pages/BlogEditor.tsx';
import GamePage from './pages/GamePage.tsx';
import { ROUTES } from '@/lib/routes';

const App: React.FC = () => {
  return (
    <HashRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </HashRouter>
  );
};

export const AppRoutes: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  // Initialize SSE for real-time updates (Phase 5.1.1)
  useSSE();

  useEffect(() => {
    // Initialize theme on app load
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia?.('(prefers-color-scheme: dark)')?.matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen bg-background">Loading...</div>;
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<PublicLayout />}>
        <Route path={ROUTES.LANDING} element={<LandingPage />} />
        <Route path={ROUTES.BLOG} element={<BlogPage />} />
        <Route path={ROUTES.BLOG_DETAIL} element={<BlogDetailPage />} />
        <Route path={ROUTES.SOLUTIONS} element={<SolutionsPage />} />
        <Route path={ROUTES.AUTH} element={<AuthPage />} />
        <Route path={ROUTES.GAME_CARD_BATTLER} element={<GamePage />} />
      </Route>

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <MainLayout>
              <DashboardPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/stats"
        element={
          <ProtectedRoute>
            <MainLayout>
              <StatsPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/marketing"
        element={
          <ProtectedRoute>
            <MainLayout>
              <MarketingPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/brand"
        element={
          <ProtectedRoute>
            <MainLayout>
              <BrandPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/sales-cart"
        element={
          <ProtectedRoute>
            <MainLayout>
              <SalesCartPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/team"
        element={
          <ProtectedRoute>
            <MainLayout>
              <TeamManagementPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/approvals"
        element={
          <ManagerRoute>
            <MainLayout>
              <ApprovalsPage />
            </MainLayout>
          </ManagerRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <MainLayout>
              <AdminPage />
            </MainLayout>
          </AdminRoute>
        }
      />
      {/* Standalone Route for the Pro Blog Editor (Belongs to Brand Hub / Marketing) */}
      <Route
        path="/brand/editor/:id"
        element={
          <ProtectedRoute>
            <MainLayout>
              <BlogEditor />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager"
        element={<Navigate to="/nexus" replace />}
      />
      <Route
        path="/nexus"
        element={
          <ManagerRoute>
            <MainLayout>
              <ManagerNexus />
            </MainLayout>
          </ManagerRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <MainLayout>
              <SettingsPage />
            </MainLayout>
          </ProtectedRoute>
        }
      />
      
      {/* Redirects */}
      <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/landing"} />} />
      <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/landing"} />} />
    </Routes>
  );
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth" />;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAdmin, user } = useAuth();
    const role = user?.role?.toLowerCase();
    const isAuthorized = isAdmin || role === 'admin' || role === 'system_admin';
    return isAuthorized ? <>{children}</> : <Navigate to="/dashboard" />;
};

const ManagerRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAdmin, user } = useAuth();
    const role = user?.role?.toLowerCase();
    const isManager = isAdmin || role === 'manager' || role === 'admin' || role === 'system_admin' || role === EmployeeRole.MANAGER;
    return isManager ? <>{children}</> : <Navigate to="/dashboard" />;
};

export default App;