import React, { useState, useEffect } from 'react';
import { Moon, Sun, FileText, Palette, Flame, Monitor } from 'lucide-react';
import { Switch } from '@/features/ui/primitives/switch';
import { useTheme } from '../../contexts/useTheme';
import { credentialsService } from '../../services/credentialsService';
import { useToast } from '../../features/shared/hooks/useToast';
import { serverHealthService } from '../../services/serverHealthService';
import { useSettings } from '../../contexts/useSettings';

export const FeaturesSection = () => {
  const {
    theme,
    setTheme
  } = useTheme();
  const { showToast } = useToast();
  const { styleGuideEnabled, setStyleGuideEnabled: setStyleGuideContext } = useSettings();
  const isDarkMode = theme === 'dark';
  const [projectsEnabled, setProjectsEnabled] = useState(true);
  const [styleGuideEnabledLocal, setStyleGuideEnabledLocal] = useState(styleGuideEnabled);

  // Commented out for future release

  const [logfireEnabled, setLogfireEnabled] = useState(false);
  const [disconnectScreenEnabled, setDisconnectScreenEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [projectsSchemaValid, setProjectsSchemaValid] = useState(true);
  const [projectsSchemaError, setProjectsSchemaError] = useState<string | null>(null);

  // Load settings on mount and sync with context
  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    setStyleGuideEnabledLocal(styleGuideEnabled);
  }, [styleGuideEnabled]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // Load both Logfire and Projects settings, plus check projects schema
      const [logfireResponse, projectsResponse, projectsHealthResponse, disconnectScreenRes] = await Promise.all([
        credentialsService.getCredential('LOGFIRE_ENABLED').catch(() => ({ value: undefined })),
        credentialsService.getCredential('PROJECTS_ENABLED').catch(() => ({ value: undefined })),
        fetch(`${credentialsService['baseUrl']}/api/health`).catch(() => null),
        credentialsService.getCredential('DISCONNECT_SCREEN_ENABLED').catch(() => ({ value: 'true' }))
      ]);
      
      // Set Logfire setting
      if (logfireResponse.value !== undefined) {
        setLogfireEnabled(logfireResponse.value === 'true');
      } else {
        setLogfireEnabled(false);
      }
      
      // Set Disconnect Screen setting
      setDisconnectScreenEnabled(disconnectScreenRes.value === 'true');
      
      // Check projects schema health
      if (projectsHealthResponse && projectsHealthResponse.ok) {
                        const healthData = await projectsHealthResponse.json();
                
                        const schemaValid = healthData.schema_valid === true;
                        setProjectsSchemaValid(schemaValid);        if (!schemaValid) {
          setProjectsSchemaError(
            'Projects table not detected. Please ensure you have installed the archon_tasks.sql structure to your database and restart the server.'
          );
        } else {
          setProjectsSchemaError(null);
        }
      } else {
        // If health check fails, assume schema is invalid
        setProjectsSchemaValid(false);
        setProjectsSchemaError(
          'Unable to verify projects schema. Please ensure the backend is running and database is accessible.'
        );
      }
      
      // Set Projects setting (but only if schema is valid)
      if (projectsResponse.value !== undefined) {
        setProjectsEnabled(projectsResponse.value === 'true');
      } else {
        setProjectsEnabled(true); // Default to true
      }
      
    } catch (error) {
      console.error('Failed to load settings:', error);
      // Default values on error
      setLogfireEnabled(false);
      setProjectsEnabled(true);
      setDisconnectScreenEnabled(true);
      setProjectsSchemaValid(false);
      setProjectsSchemaError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleProjectsToggle = async (checked: boolean) => {
    // Prevent duplicate calls while one is already in progress
    if (loading) return;
    
    try {
      setLoading(true);
      // Update local state immediately for responsive UI
      setProjectsEnabled(checked);

      // Save to backend
      await credentialsService.createCredential({
        key: 'PROJECTS_ENABLED',
        value: checked.toString(),
        is_encrypted: false,
        category: 'features',
        description: 'Enable or disable Projects and Tasks functionality'
      });

      showToast(
        checked ? 'Projects Enabled Successfully!' : 'Projects Now Disabled', 
        checked ? 'success' : 'warning'
      );
    } catch (error) {
      console.error('Failed to update projects setting:', error);
      // Revert local state on error
      setProjectsEnabled(!checked);
      showToast('Failed to update Projects setting', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleLogfireToggle = async (checked: boolean) => {
    // Prevent duplicate calls while one is already in progress
    if (loading) return;
    
    try {
      setLoading(true);
      // Update local state immediately for responsive UI
      setLogfireEnabled(checked);

      // Save to backend
      await credentialsService.createCredential({
        key: 'LOGFIRE_ENABLED',
        value: checked.toString(),
        is_encrypted: false,
        category: 'monitoring',
        description: 'Enable or disable Pydantic Logfire logging and observability'
      });

      showToast(
        checked ? 'Logfire Enabled Successfully!' : 'Logfire Now Disabled', 
        checked ? 'success' : 'warning'
      );
    } catch (error) {
      console.error('Failed to update logfire setting:', error);
      // Revert local state on error
      setLogfireEnabled(!checked);
      showToast('Failed to update Logfire setting', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleThemeToggle = (checked: boolean) => {
    setTheme(checked ? 'dark' : 'light');
  };

  const handleDisconnectScreenToggle = async (checked: boolean) => {
    if (loading) return;

    try {
      setLoading(true);
      setDisconnectScreenEnabled(checked);

      await serverHealthService.updateSettings(checked);

      showToast(
        checked ? 'Disconnect Screen Enabled' : 'Disconnect Screen Disabled',
        checked ? 'success' : 'warning'
      );
    } catch (error) {
      console.error('Failed to update disconnect screen setting:', error);
      setDisconnectScreenEnabled(!checked);
      showToast('Failed to update disconnect screen setting', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStyleGuideToggle = async (checked: boolean) => {
    if (loading) return;

    try {
      setLoading(true);
      setStyleGuideEnabledLocal(checked);

      // Update context which will save to backend
      await setStyleGuideContext(checked);

      showToast(
        checked ? 'Style Guide Enabled' : 'Style Guide Disabled',
        checked ? 'success' : 'warning'
      );
    } catch (error) {
      console.error('Failed to update style guide setting:', error);
      setStyleGuideEnabledLocal(!checked);
      showToast('Failed to update style guide setting', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="grid grid-cols-2 gap-4">
          {/* Theme Toggle */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-purple-600/5 backdrop-blur-sm border border-purple-500/20 shadow-lg">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 dark:text-white">
                Dark Mode
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Switch between light and dark themes
              </p>
            </div>
            <div className="flex-shrink-0">
              <Switch
                size="lg"
                checked={isDarkMode}
                onCheckedChange={handleThemeToggle}
                color="purple"
                iconOn={<Moon className="w-5 h-5" />}
                iconOff={<Sun className="w-5 h-5" />}
              />
            </div>
          </div>

          {/* Projects Toggle */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-600/5 backdrop-blur-sm border border-blue-500/20 shadow-lg">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 dark:text-white">
                Projects
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Enable Projects and Tasks functionality
              </p>
              {!projectsSchemaValid && projectsSchemaError && (
                <p className="text-xs text-red-500 dark:text-red-400 mt-1">
                  ⚠️ {projectsSchemaError}
                </p>
              )}
            </div>
            <div className="flex-shrink-0">
              <Switch
                size="lg"
                checked={projectsEnabled}
                onCheckedChange={handleProjectsToggle}
                color="blue"
                icon={<FileText className="w-5 h-5" />}
                disabled={loading || !projectsSchemaValid}
              />
            </div>
          </div>

          {/* Style Guide Toggle */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 backdrop-blur-sm border border-cyan-500/20 shadow-lg">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 dark:text-white">
                Style Guide
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Show UI style guide and components in navigation
              </p>
            </div>
            <div className="flex-shrink-0">
              <Switch
                size="lg"
                checked={styleGuideEnabledLocal}
                onCheckedChange={handleStyleGuideToggle}
                color="cyan"
                icon={<Palette className="w-5 h-5" />}
                disabled={loading}
              />
            </div>
          </div>

          {/* Pydantic Logfire Toggle */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-orange-500/10 to-orange-600/5 backdrop-blur-sm border border-orange-500/20 shadow-lg">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 dark:text-white">
                Pydantic Logfire
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Structured logging and observability platform
              </p>
            </div>
            <div className="flex-shrink-0">
              <Switch
                size="lg"
                checked={logfireEnabled}
                onCheckedChange={handleLogfireToggle}
                color="orange"
                icon={<Flame className="w-5 h-5" />}
                disabled={loading}
              />
            </div>
          </div>

          {/* Disconnect Screen Toggle */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-green-500/10 to-green-600/5 backdrop-blur-sm border border-green-500/20 shadow-lg">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800 dark:text-white">
                Disconnect Screen
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Show disconnect screen when server disconnects
              </p>
            </div>
            <div className="flex-shrink-0">
              <Switch
                size="lg"
                checked={disconnectScreenEnabled}
                onCheckedChange={handleDisconnectScreenToggle}
                color="green"
                icon={<Monitor className="w-5 h-5" />}
                disabled={loading}
              />
            </div>
          </div>
        </div>
    </>
  );
};