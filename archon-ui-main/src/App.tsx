import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './features/shared/config/queryClient';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import SettingsPage from './pages/SettingsPage';
import { MCPPage } from './pages/MCPPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { MainLayout } from './components/layout/MainLayout';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './features/ui/components/ToastProvider';
import { SettingsProvider } from './contexts/SettingsContext';
import { useSettings } from './contexts/useSettings';
import { TooltipProvider } from './features/ui/primitives/tooltip';
import { AuthProvider, useAuth } from './features/auth/contexts/AuthContext';
import { AdminAuthGate } from './features/auth/components/AdminAuthGate';
import { ProjectPage } from './pages/ProjectPage';
import StyleGuidePage from './pages/StyleGuidePage';
import { DisconnectScreenOverlay } from './components/DisconnectScreenOverlay';
import { ErrorBoundaryWithBugReport } from './components/bug-report/ErrorBoundaryWithBugReport';
import { MigrationBanner } from './components/ui/MigrationBanner';
import { serverHealthService } from './services/serverHealthService';
import { useMigrationStatus } from './hooks/useMigrationStatus';
import { AdminPage } from './pages/AdminPage';


const NotFoundView = (): JSX.Element => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
    <h1 className="text-4xl font-bold text-white mb-2">404</h1>
    <p className="text-sm text-slate-400 mb-6">The requested route does not exist.</p>
    <Link
      to="/"
      className="px-4 py-2 rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 text-sm"
    >
      Back to Knowledge Base
    </Link>
  </div>
);

const AppRoutes = (): JSX.Element => {
  const { projectsEnabled, styleGuideEnabled } = useSettings();

  return (
    <Routes>
      <Route path="/" element={<KnowledgeBasePage />} />
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/mcp" element={<MCPPage />} />
      <Route path="/admin" element={<AdminPage />} />
      {styleGuideEnabled ? (
        <Route path="/style-guide" element={<StyleGuidePage />} />
      ) : (
        <Route path="/style-guide" element={<Navigate to="/" replace />} />
      )}
      {projectsEnabled ? (
        <>
          <Route path="/projects" element={<ProjectPage />} />
          <Route path="/projects/:projectId" element={<ProjectPage />} />
        </>
      ) : (
        <Route path="/projects" element={<Navigate to="/" replace />} />
      )}
      <Route path="*" element={<NotFoundView />} />
    </Routes>
  );
};

const AuthenticatedApp = (): JSX.Element => {
  const [disconnectScreenActive, setDisconnectScreenActive] = useState(false);
  const [disconnectScreenDismissed, setDisconnectScreenDismissed] = useState(false);
  const [disconnectScreenSettings, setDisconnectScreenSettings] = useState({
    enabled: true,
    delay: 10000
  });
  const [migrationBannerDismissed, setMigrationBannerDismissed] = useState(false);
  const migrationStatus = useMigrationStatus();

  useEffect(() => {
    const settings = serverHealthService.getSettings();
    setDisconnectScreenSettings(settings);
    serverHealthService.stopMonitoring();
    serverHealthService.startMonitoring({
      onDisconnected: () => {
        if (!disconnectScreenDismissed) {
          setDisconnectScreenActive(true);
        }
      },
      onReconnected: () => {
        setDisconnectScreenActive(false);
        setDisconnectScreenDismissed(false);
        window.location.reload();
      }
    });

    return () => {
      serverHealthService.stopMonitoring();
    };
  }, [disconnectScreenDismissed]);

  const handleDismissDisconnectScreen = (): void => {
    setDisconnectScreenActive(false);
    setDisconnectScreenDismissed(true);
  };

  return (
    <SettingsProvider>
      <Router>
        <ErrorBoundaryWithBugReport>
          <MainLayout>
            {/* Migration Banner - shows when backend is up but DB schema needs work */}
            {migrationStatus.migrationRequired && !migrationBannerDismissed && (
              <MigrationBanner
                message={migrationStatus.message || "Database migration required"}
                onDismiss={() => setMigrationBannerDismissed(true)}
              />
            )}
            <AppRoutes />
          </MainLayout>
        </ErrorBoundaryWithBugReport>
      </Router>
      <DisconnectScreenOverlay
        isActive={disconnectScreenActive && disconnectScreenSettings.enabled}
        onDismiss={handleDismissDisconnectScreen}
      />
    </SettingsProvider>
  );
};

const AppContent = (): JSX.Element => {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-300 flex items-center justify-center text-sm">
        Verifying Admin Session...
      </div>
    );
  }

  if (!token) {
    return <AdminAuthGate />;
  }

  return <AuthenticatedApp />;
};

export function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <TooltipProvider>
            <AuthProvider>
              <AppContent />
            </AuthProvider>
          </TooltipProvider>
        </ToastProvider>
      </ThemeProvider>
      {import.meta.env.VITE_SHOW_DEVTOOLS === 'true' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}