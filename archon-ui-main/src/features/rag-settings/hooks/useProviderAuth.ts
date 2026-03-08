import { useState, useCallback, useEffect, useRef } from 'react';
import { credentialsService } from '@/services/credentialsService';
import { PROVIDER_CREDENTIAL_KEYS, CREDENTIAL_PROVIDER_MAP } from '../constants';
import { ProviderCredentialKey, RagSettingsType } from '../types';

export const useProviderAuth = (ragSettings: RagSettingsType) => {
  const [apiCredentials, setApiCredentials] = useState<{[key: string]: boolean}>({});
  const [providerConnectionStatus, setProviderConnectionStatus] = useState<{
    [key: string]: { connected: boolean; checking: boolean; lastChecked?: Date }
  }>({});
  
  const providerConnectionStatusRef = useRef(providerConnectionStatus);
  const hasLoadedCredentialsRef = useRef(false);

  useEffect(() => {
    providerConnectionStatusRef.current = providerConnectionStatus;
  }, [providerConnectionStatus]);

  const reloadApiCredentials = useCallback(async () => {
    try {
      const statusResults = await credentialsService.checkCredentialStatus(
        Array.from(PROVIDER_CREDENTIAL_KEYS),
      );
      const credentials: { [key: string]: boolean } = {};
      for (const key of PROVIDER_CREDENTIAL_KEYS) {
        credentials[key] = !!statusResults[key]?.has_value;
      }
      setApiCredentials(credentials);
      hasLoadedCredentialsRef.current = true;
    } catch { /* Silent fail */ }
  }, []);

  const testProviderConnection = useCallback(async (provider: string): Promise<boolean> => {
    setProviderConnectionStatus(prev => ({ ...prev, [provider]: { ...prev[provider], checking: true } }));
    try {
      const response = await fetch(`/api/providers/${provider}/status`);
      const result = await response.json();
      const isConnected = result.ok && result.reason === 'connected';
      setProviderConnectionStatus(prev => ({
        ...prev,
        [provider]: { connected: isConnected, checking: false, lastChecked: new Date() }
      }));
      return isConnected;
    } catch {
      setProviderConnectionStatus(prev => ({ ...prev, [provider]: { connected: false, checking: false, lastChecked: new Date() } }));
      return false;
    }
  }, []);

  // --- Physical Restoration of Side Effects ---
  
  // Initial load
  useEffect(() => {
    void reloadApiCredentials();
  }, [reloadApiCredentials]);

  // Reload when provider changes (Uses ragSettings argument)
  useEffect(() => {
    if (hasLoadedCredentialsRef.current && ragSettings.LLM_PROVIDER) {
      void reloadApiCredentials();
    }
  }, [ragSettings.LLM_PROVIDER, reloadApiCredentials]);

  // 30s Automatic Refresh
  useEffect(() => {
    const interval = setInterval(() => {
      if (Object.keys(ragSettings).length > 0) {
        void reloadApiCredentials();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [ragSettings, reloadApiCredentials]);

  // Periodic Connection Testing (60s)
  useEffect(() => {
    const testAll = async () => {
      const providers = ['openai', 'google', 'anthropic', 'openrouter', 'grok'];
      for (const p of providers) {
        const last = providerConnectionStatusRef.current[p]?.lastChecked;
        if (!last || (new Date().getTime() - last.getTime() > 30000)) {
          await testProviderConnection(p);
        }
      }
    };
    testAll();
    const interval = setInterval(testAll, 60000);
    return () => clearInterval(interval);
  }, [apiCredentials, testProviderConnection]);

  // Event listener for external updates
  useEffect(() => {
    const handleUpdate = (event: Event) => {
      const detail = (event as CustomEvent<{ keys?: string[] }>).detail;
      const keys = (detail?.keys ?? []).map(k => k.toUpperCase());
      void reloadApiCredentials();
      keys.forEach(k => {
        const p = CREDENTIAL_PROVIDER_MAP[k as ProviderCredentialKey];
        if (p) void testProviderConnection(p);
      });
    };
    window.addEventListener('archon:credentials-updated', handleUpdate);
    return () => window.removeEventListener('archon:credentials-updated', handleUpdate);
  }, [reloadApiCredentials, testProviderConnection]);

  return { apiCredentials, providerConnectionStatus, reloadApiCredentials, testProviderConnection, hasLoadedCredentialsRef };
};
