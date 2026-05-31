import { useCallback, useEffect, useRef, useState } from "react";
import { callAPIWithETag } from "@/features/shared/api/apiClient";
import { credentialsService } from "@/services/credentialsService";
import { CREDENTIAL_PROVIDER_MAP, PROVIDER_CREDENTIAL_KEYS } from "../constants";
import type { ProviderCredentialKey, RagSettingsType } from "../types";

export const useProviderAuth = (ragSettings: RagSettingsType) => {
  const [apiCredentials, setApiCredentials] = useState<{ [key: string]: boolean }>({});
  const [providerConnectionStatus, setProviderConnectionStatus] = useState<{
    [key: string]: { connected: boolean; checking: boolean; lastChecked?: Date };
  }>({});

  const providerConnectionStatusRef = useRef(providerConnectionStatus);
  const hasLoadedCredentialsRef = useRef(false);

  useEffect(() => {
    providerConnectionStatusRef.current = providerConnectionStatus;
  }, [providerConnectionStatus]);

  const reloadApiCredentials = useCallback(async () => {
    try {
      const statusResults = await credentialsService.checkCredentialStatus(Array.from(PROVIDER_CREDENTIAL_KEYS));
      const credentials: { [key: string]: boolean } = {};
      for (const key of PROVIDER_CREDENTIAL_KEYS) {
        credentials[key] = !!statusResults[key]?.has_value;
      }
      setApiCredentials(credentials);
      hasLoadedCredentialsRef.current = true;
    } catch {
      /* Silent fail */
    }
  }, []);

  const testProviderConnection = useCallback(async (provider: string): Promise<boolean> => {
    setProviderConnectionStatus((prev) => ({ ...prev, [provider]: { ...prev[provider], checking: true } }));
    try {
      const result = await callAPIWithETag<any>(`/providers/${provider}/status`);
      const isConnected = result.ok && result.reason === "connected";
      setProviderConnectionStatus((prev) => ({
        ...prev,
        [provider]: { connected: isConnected, checking: false, lastChecked: new Date() },
      }));
      return isConnected;
    } catch {
      setProviderConnectionStatus((prev) => ({
        ...prev,
        [provider]: { connected: false, checking: false, lastChecked: new Date() },
      }));
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
      if (ragSettings.LLM_PROVIDER) {
        void reloadApiCredentials();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [ragSettings.LLM_PROVIDER, reloadApiCredentials]);

  // Periodic Connection Testing (60s)
  useEffect(() => {
    const testAll = async () => {
      const providers = ["openai", "google", "anthropic", "openrouter", "grok"];
      // PERFORMANCE: Replaced sequential for...of loop with Promise.all to fetch provider
      // connection statuses concurrently, eliminating the network waterfall.
      await Promise.all(
        providers.map((p) => {
          const last = providerConnectionStatusRef.current[p]?.lastChecked;
          if (!last || Date.now() - last.getTime() > 30000) {
            return testProviderConnection(p);
          }
          return Promise.resolve(true);
        }),
      );
    };
    testAll();
    const interval = setInterval(testAll, 60000);
    return () => clearInterval(interval);
  }, [testProviderConnection]);

  // Event listener for external updates
  useEffect(() => {
    const handleUpdate = (event: Event) => {
      const detail = (event as CustomEvent<{ keys?: string[] }>).detail;
      const keys = (detail?.keys ?? []).map((k) => k.toUpperCase());
      void reloadApiCredentials();
      keys.forEach((k) => {
        const p = CREDENTIAL_PROVIDER_MAP[k as ProviderCredentialKey];
        if (p) void testProviderConnection(p);
      });
    };
    window.addEventListener("archon:credentials-updated", handleUpdate);
    return () => window.removeEventListener("archon:credentials-updated", handleUpdate);
  }, [reloadApiCredentials, testProviderConnection]);

  return {
    apiCredentials,
    providerConnectionStatus,
    reloadApiCredentials,
    testProviderConnection,
    hasLoadedCredentialsRef,
  };
};
