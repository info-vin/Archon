import React, { useState, useEffect } from 'react';
import { HashRouter, Routes, Route, Navigate, Link, useLocation, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth.tsx';
import LandingPage from './pages/LandingPage.tsx';
import AuthPage from './pages/AuthPage.tsx';
import DashboardPage from './pages/DashboardPage.tsx';
import AdminPage from './pages/AdminPage.tsx';
import BlogPage from './pages/BlogPage.tsx';
import SettingsPage from './pages/SettingsPage.tsx';
import { LogOutIcon, SettingsIcon, UserIcon, MenuIcon, XIcon } from './components/Icons.tsx';
import ThemeToggle from './components/ThemeToggle.tsx';
import UserAvatar from './components/UserAvatar.tsx';
import LiveClock from './components/LiveClock.tsx';

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

const PublicLayout: React.FC = () => {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isMobileMenuOpen]);

  const navLinks = [
    { name: 'Home', path: '/landing' },
    { name: 'Blog', path: '/blog' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-14 max-w-screen-2xl items-center justify-between px-4">
          <Link to="/landing" className="mr-6 flex items-center space-x-2">
            <span className="font-bold text-lg">Archon</span>
          </Link>
          <nav className="hidden md:flex items-center space-x-6 text-sm font-medium">
            {navLinks.map(link => (
              <Link
                key={link.name}
                to={link.path}
                className={`transition-colors hover:text-primary ${location.pathname === link.path ? 'text-primary' : 'text-muted-foreground'}`}
              >
                {link.name}
              </Link>
            ))}
          </nav>
          <div className="flex items-center justify-end space-x-2">
            <ThemeToggle />
            <Link
              to="/auth"
              className="hidden md:inline-flex px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-semibold hover:bg-primary/90 transition-colors"
            >
              Login
            </Link>
            <button 
              className="md:hidden p-2"
              onClick={() => setIsMobileMenuOpen(true)}
              aria-label="Open menu"
            >
                <MenuIcon className="h-6 w-6" />
            </button>
          </div>
        </div>
      </header>
      
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
          role="dialog"
          aria-modal="true"
        >
          <div 
            className="fixed top-0 right-0 h-full w-full max-w-xs bg-card p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <span className="font-bold text-lg">Archon</span>
              <button onClick={() => setIsMobileMenuOpen(false)} className="p-1 -mr-1" aria-label="Close menu">
                <XIcon className="h-6 w-6" />
              </button>
            </div>
            <nav className="mt-6 flex flex-col space-y-1">
              {navLinks.map(link => (
                <Link
                  key={link.name}
                  to={link.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`block px-3 py-2 rounded-md text-lg font-medium transition-colors hover:text-primary ${location.pathname === link.path ? 'text-primary' : 'text-foreground'}`}
                >
                  {link.name}
                </Link>
              ))}
            </nav>
            <div className="mt-6 pt-6 border-t border-border">
                <Link
                    to="/auth"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex items-center justify-center w-full px-4 py-2 bg-primary text-primary-foreground rounded-md font-semibold hover:bg-primary/90 transition-colors"
                >
                    Login
                </Link>
            </div>
          </div>
        </div>
      )}

      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="py-6 md:px-8 md:py-0 border-t border-border">
          <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row py-4 mx-auto">
              <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                  Built for efficiency. Inspired by Vik and Arc.
              </p>
          </div>
      </footer>
    </div>
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

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user, logout, isAdmin } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const location = useLocation();

    return (
        <div className="flex h-screen bg-background text-foreground">
             <nav className={`fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out md:relative md:translate-x-0`}>
                <div className="p-4 border-b border-border flex justify-between items-center gap-2">
                    <Link to="/dashboard" className="text-2xl font-bold">Archon</Link>
                     <div className="hidden md:block">
                        <LiveClock />
                     </div>
                     <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-1">
                        <XIcon className="w-6 h-6" />
                    </button>
                </div>
                <ul className="flex-grow p-2">
                    <li className="mb-2">
                        <Link to="/dashboard" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/dashboard') ? 'bg-secondary' : ''}`}>
                            <UserIcon className="w-5 h-5 mr-3" />
                            My Tasks
                        </Link>
                    </li>
                    <li className="mb-2">
                        <Link to="/settings" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/settings') ? 'bg-secondary' : ''}`}>
                            <SettingsIcon className="w-5 h-5 mr-3" />
                            Settings
                        </Link>
                    </li>
                    {isAdmin && (
                         <li className="mb-2">
                            <Link to="/admin" className={`flex items-center p-2 rounded-md hover:bg-secondary ${location.pathname.startsWith('/admin') ? 'bg-secondary' : ''}`}>
                                <SettingsIcon className="w-5 h-5 mr-3" />
                                Admin Panel
                            </Link>
                        </li>
                    )}
                </ul>
                <div className="p-4 border-t border-border">
                   <div className="flex items-center mb-4">
                       <UserAvatar name={user?.name || ''} className="w-10 h-10 mr-3" />
                       <div>
                           <p className="font-semibold">{user?.name}</p>
                           <p className="text-sm text-muted-foreground">{user?.email}</p>
                       </div>
                   </div>
                   <button onClick={logout} className="w-full flex items-center justify-center p-2 rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90">
                       <LogOutIcon className="w-5 h-5 mr-2" />
                       Logout
                   </button>
                </div>
            </nav>
            {isSidebarOpen && <div className="fixed inset-0 bg-black/50 z-40 md:hidden" onClick={() => setIsSidebarOpen(false)}></div>}
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="md:hidden flex items-center justify-between p-4 border-b border-border bg-background/80 backdrop-blur">
                    <button onClick={() => setIsSidebarOpen(true)} aria-label="Open sidebar">
                        <MenuIcon className="w-6 h-6" />
                    </button>
                    <LiveClock />
                </header>
                {children}
            </main>
        </div>
    );
}

export default App;