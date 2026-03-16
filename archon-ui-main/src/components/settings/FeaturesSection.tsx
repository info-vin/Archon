import { useState, useEffect } from 'react';
import { Moon, Sun, FileText, Palette, Flame, Monitor } from 'lucide-react';
import { Switch } from '@/features/ui/primitives/switch';
import { useTheme } from '@/contexts/useTheme';
import { credentialsService } from '@/services/credentialsService';
import { useToast } from '@/features/shared/hooks/useToast';
import { serverHealthService } from '@/services/serverHealthService';
import { useSettings } from '@/contexts/useSettings';
import { callAPIWithETag } from '@/features/shared/api/apiClient';

export const FeaturesSection = () => {
  const { theme, setTheme } = useTheme();
  const { showToast } = useToast();
  const { styleGuideEnabled, setStyleGuideEnabled: setStyleGuideContext } = useSettings();
  const isDarkMode = theme === 'dark';
  const [projectsEnabled, setProjectsEnabled] = useState(true);
  const [styleGuideEnabledLocal, setStyleGuideEnabledLocal] = useState(styleGuideEnabled);
  const [logfireEnabled, setLogfireEnabled] = useState(false);
  const [disconnectScreenEnabled, setDisconnectScreenEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [projectsSchemaValid, setProjectsSchemaValid] = useState(true);
  const [projectsSchemaError, setProjectsSchemaError] = useState<string | null>(null);

  useEffect(() => { loadSettings(); }, []);
  useEffect(() => { setStyleGuideEnabledLocal(styleGuideEnabled); }, [styleGuideEnabled]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const [logfireResponse, projectsResponse, healthData, disconnectScreenRes] = await Promise.all([
        credentialsService.getCredential('LOGFIRE_ENABLED').catch(() => ({ value: 'false' })),
        credentialsService.getCredential('PROJECTS_ENABLED').catch(() => ({ value: 'true' })),
        callAPIWithETag<any>('/health').catch(() => null),
        credentialsService.getCredential('DISCONNECT_SCREEN_ENABLED').catch(() => ({ value: 'true' }))
      ]);
      
      setLogfireEnabled(logfireResponse.value === 'true');
      setDisconnectScreenEnabled(disconnectScreenRes.value === 'true');
      
      if (healthData) {
        const schemaValid = healthData.schema_valid === true;
        setProjectsSchemaValid(schemaValid);
        if (!schemaValid) setProjectsSchemaError('Projects table not detected.');
      }
      
      setProjectsEnabled(projectsResponse.value === 'true');
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectsToggle = async (checked: boolean) => {
    if (loading) return;
    try {
      setLoading(true);
      setProjectsEnabled(checked);
      await credentialsService.createCredential({ key: 'PROJECTS_ENABLED', value: checked.toString(), is_encrypted: false, category: 'features' });
      showToast(checked ? 'Projects Enabled' : 'Projects Disabled', 'success');
    } catch {
      setProjectsEnabled(!checked);
      showToast('Failed to update Projects setting', 'error');
    } finally { setLoading(false); }
  };

  const handleLogfireToggle = async (checked: boolean) => {
    if (loading) return;
    try {
      setLoading(true);
      setLogfireEnabled(checked);
      await credentialsService.createCredential({ key: 'LOGFIRE_ENABLED', value: checked.toString(), is_encrypted: false, category: 'monitoring' });
      showToast(checked ? 'Logfire Enabled' : 'Logfire Disabled', 'success');
    } catch {
      setLogfireEnabled(!checked);
      showToast('Failed to update Logfire setting', 'error');
    } finally { setLoading(false); }
  };

  const handleDisconnectScreenToggle = async (checked: boolean) => {
    if (loading) return;
    try {
      setLoading(true);
      setDisconnectScreenEnabled(checked);
      await serverHealthService.updateSettings({ enabled: checked });
      showToast(checked ? 'Disconnect Screen Updated' : 'Update Failed', 'success');
    } catch {
      setDisconnectScreenEnabled(!checked);
    } finally { setLoading(false); }
  };

  const handleStyleGuideToggle = async (checked: boolean) => {
    if (loading) return;
    try {
      setLoading(true);
      setStyleGuideEnabledLocal(checked);
      await setStyleGuideContext(checked);
      showToast(checked ? 'Style Guide Enabled' : 'Style Guide Disabled', 'success');
    } catch {
      setStyleGuideEnabledLocal(!checked);
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Theme Toggle */}
      <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-purple-600/5 border border-purple-500/20 shadow-lg">
        <div className="flex-1 min-w-0">
          <p className="font-medium">Dark Mode</p>
          <p className="text-sm opacity-70">Switch between themes</p>
        </div>
        <Switch checked={isDarkMode} onCheckedChange={(c) => setTheme(c ? 'dark' : 'light')} color="purple" iconOn={<Moon className="w-5 h-5" />} iconOff={<Sun className="w-5 h-5" />} />
      </div>

      {/* Projects Toggle */}
      <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20 shadow-lg">
        <div className="flex-1 min-w-0">
          <p className="font-medium">Projects</p>
          <p className="text-sm opacity-70">Tasks functionality</p>
          {projectsSchemaError && <p className="text-xs text-red-500 mt-1">⚠️ {projectsSchemaError}</p>}
        </div>
        <Switch checked={projectsEnabled} onCheckedChange={handleProjectsToggle} disabled={loading || !projectsSchemaValid} color="blue" icon={<FileText className="w-5 h-5" />} />
      </div>

      {/* Style Guide Toggle */}
      <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-cyan-500/10 to-cyan-600/5 border border-cyan-500/20 shadow-lg">
        <div className="flex-1 min-w-0">
          <p className="font-medium">Style Guide</p>
          <p className="text-sm opacity-70">Show UI components</p>
        </div>
        <Switch checked={styleGuideEnabledLocal} onCheckedChange={handleStyleGuideToggle} disabled={loading} color="cyan" icon={<Palette className="w-5 h-5" />} />
      </div>

      {/* Logfire Toggle */}
      <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-orange-500/10 to-orange-600/5 border border-orange-500/20 shadow-lg">
        <div className="flex-1 min-w-0">
          <p className="font-medium">Logfire</p>
          <p className="text-sm opacity-70">Observability platform</p>
        </div>
        <Switch checked={logfireEnabled} onCheckedChange={handleLogfireToggle} disabled={loading} color="orange" icon={<Flame className="w-5 h-5" />} />
      </div>

      {/* Disconnect Screen Toggle */}
      <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-green-500/10 to-green-600/5 border border-green-500/20 shadow-lg">
        <div className="flex-1 min-w-0">
          <p className="font-medium">Disconnect Screen</p>
          <p className="text-sm opacity-70">Show overlay on disconnect</p>
        </div>
        <Switch checked={disconnectScreenEnabled} onCheckedChange={handleDisconnectScreenToggle} disabled={loading} color="green" icon={<Monitor className="w-5 h-5" />} />
      </div>
    </div>
  );
};
