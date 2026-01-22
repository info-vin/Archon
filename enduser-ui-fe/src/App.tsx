import React, { useEffect } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth.tsx';
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
import PublicLayout from './components/layout/PublicLayout.tsx';
import MainLayout from './components/layout/MainLayout.tsx';
import SolutionsPage from './features/marketing/SolutionsPage.tsx';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <HashRouter>
        <AppRoutes />
      </HashRouter>
    </AuthProvider>
  );
};

export const AppRoutes: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    // Initialize theme on app load
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
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
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/blog" element={<BlogPage />} />
        <Route path="/blog/:id" element={<BlogDetailPage />} />
        <Route path="/solutions" element={<SolutionsPage />} />
        <Route path="/auth" element={<AuthPage />} />
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
        path="/admin"
        element={
          <AdminRoute>
            <MainLayout>
              <AdminPage />
            </MainLayout>
          </AdminRoute>
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
    const { isAdmin } = useAuth();
    return isAdmin ? <>{children}</> : <Navigate to="/dashboard" />;
};

export default App;