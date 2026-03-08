import { useState, useCallback, useRef, useEffect } from 'react';
import { RagSettingsType } from '../types';
import { DEFAULT_OLLAMA_URL } from '../constants';
import { normalizeBaseUrl } from '../utils/modelHelpers';

interface OllamaStatus {
  online: boolean;
  responseTime: number | null;
  checking: boolean;
}

export const useOllamaLogic = (
  ragSettings: RagSettingsType,
  showToast: (msg: string, type: 'success' | 'error' | 'info') => void
) => {
  const [llmStatus, setLLMStatus] = useState<OllamaStatus>({ online: false, responseTime: null, checking: false });
  const [embeddingStatus, setEmbeddingStatus] = useState<OllamaStatus>({ online: false, responseTime: null, checking: false });
  const [ollamaServerStatus, setOllamaServerStatus] = useState<'unknown' | 'online' | 'offline'>('unknown');
  const [ollamaManualConfirmed, setOllamaManualConfirmed] = useState(false);

  const [ollamaMetrics, setOllamaMetrics] = useState({
    totalModels: 0,
    chatModels: 0,
    embeddingModels: 0,
    activeHosts: 0,
    loading: true,
    llmInstanceModels: { chat: 0, embedding: 0, total: 0 },
    embeddingInstanceModels: { chat: 0, embedding: 0, total: 0 }
  });

  const ollamaMetricsRef = useRef(ollamaMetrics);
  const lastMetricsFetchRef = useRef({ provider: '', embProvider: '', llmUrl: '', embUrl: '', llmOnline: false, embOnline: false });

  useEffect(() => {
    ollamaMetricsRef.current = ollamaMetrics;
  }, [ollamaMetrics]);

  const fetchOllamaMetrics = useCallback(async (currentLlmUrl?: string, currentEmbUrl?: string) => {
    try {
      setOllamaMetrics(prev => ({ ...prev, loading: true }));
      const llmUrlBase = normalizeBaseUrl(currentLlmUrl || ragSettings.LLM_BASE_URL || DEFAULT_OLLAMA_URL);
      const embUrlBase = normalizeBaseUrl(currentEmbUrl || ragSettings.OLLAMA_EMBEDDING_URL || DEFAULT_OLLAMA_URL);

      const instanceUrls: string[] = [];
      if (llmUrlBase) instanceUrls.push(llmUrlBase);
      if (embUrlBase && embUrlBase !== llmUrlBase) instanceUrls.push(embUrlBase);

      if (instanceUrls.length === 0) {
        setOllamaMetrics(prev => ({ ...prev, loading: false }));
        return;
      }

      const params = new URLSearchParams();
      instanceUrls.forEach(url => params.append('instance_urls', url));
      params.append('include_capabilities', 'true');

      const response = await fetch(`/api/ollama/models?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        const allChat = data.chat_models || [];
        const allEmb = data.embedding_models || [];

        const llmChat = allChat.filter((m: any) => normalizeBaseUrl(m.instance_url) === llmUrlBase);
        const llmEmb = allEmb.filter((m: any) => normalizeBaseUrl(m.instance_url) === llmUrlBase);
        const embChat = allChat.filter((m: any) => normalizeBaseUrl(m.instance_url) === embUrlBase);
        const embEmb = allEmb.filter((m: any) => normalizeBaseUrl(m.instance_url) === embUrlBase);

        setOllamaMetrics({
          totalModels: data.total_models || 0,
          chatModels: allChat.length,
          embeddingModels: allEmb.length,
          activeHosts: (llmStatus.online ? 1 : 0) + (embeddingStatus.online ? 1 : 0),
          loading: false,
          llmInstanceModels: { chat: llmChat.length, embedding: llmEmb.length, total: llmChat.length + llmEmb.length },
          embeddingInstanceModels: { chat: embChat.length, embedding: embEmb.length, total: embChat.length + embEmb.length }
        });
      } else {
        setOllamaMetrics(prev => ({ ...prev, loading: false }));
      }
    } catch {
      setOllamaMetrics(prev => ({ ...prev, loading: false }));
    }
  }, [ragSettings.LLM_BASE_URL, ragSettings.OLLAMA_EMBEDDING_URL, llmStatus.online, embeddingStatus.online]);

  const manualTestConnection = useCallback(async (
    url: string,
    setStatus: React.Dispatch<React.SetStateAction<OllamaStatus>>,
    instanceName: string,
    context?: 'chat' | 'embedding',
    options?: { suppressToast?: boolean }
  ): Promise<boolean> => {
    const suppressToast = options?.suppressToast ?? false;
    setStatus(prev => ({ ...prev, checking: true }));
    const startTime = Date.now();

    try {
      const baseUrl = url.replace('/v1', '').replace(/\/$/, '');
      const backendHealthUrl = `/api/ollama/instances/health?instance_urls=${encodeURIComponent(baseUrl)}&include_models=true`;

      const response = await fetch(backendHealthUrl, { signal: AbortSignal.timeout(15000) });
      if (response.ok) {
        const data = await response.json();
        const statusData = data.instance_status?.[baseUrl];

        if (statusData?.is_healthy) {
          const responseTime = Math.round(statusData.response_time_ms || (Date.now() - startTime));
          setStatus({ online: true, responseTime, checking: false });

          if (!suppressToast) {
            const count = context === 'chat' ? ollamaMetricsRef.current.llmInstanceModels.chat : 
                          context === 'embedding' ? ollamaMetricsRef.current.embeddingInstanceModels.embedding :
                          statusData.models_available;
            showToast(`${instanceName} connected: ${count} models (${responseTime}ms)`, 'success');
          }
          // Scenario 2: Auto-refresh metrics after manual success
          if (ragSettings.LLM_PROVIDER === 'ollama' || context === 'embedding') {
            void fetchOllamaMetrics();
          }
          return true;
        }
      }
      setStatus({ online: false, responseTime: null, checking: false });
      if (!suppressToast) showToast(`${instanceName} connection failed`, 'error');
      return false;
    } catch {
      setStatus({ online: false, responseTime: null, checking: false });
      if (!suppressToast) showToast(`${instanceName} connection error`, 'error');
      return false;
    }
  }, [showToast, fetchOllamaMetrics, ragSettings.LLM_PROVIDER]);

  // Server auto-detection effect
  useEffect(() => {
    const needsDetection = ragSettings.LLM_PROVIDER === 'ollama' || ragSettings.EMBEDDING_PROVIDER === 'ollama';
    if (!needsDetection) {
      setOllamaServerStatus('unknown');
      return;
    }
    const baseUrl = (ragSettings.LLM_BASE_URL || DEFAULT_OLLAMA_URL).replace('/v1', '').replace(/\/$/, '');
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(`/api/ollama/instances/health?instance_urls=${encodeURIComponent(baseUrl)}`, { signal: AbortSignal.timeout(10000) });
        if (cancelled) return;
        if (response.ok) {
          const data = await response.json();
          setOllamaServerStatus(data.instance_status?.[baseUrl]?.is_healthy ? 'online' : 'offline');
        } else setOllamaServerStatus('offline');
      } catch { if (!cancelled) setOllamaServerStatus('offline'); }
    })();
    return () => { cancelled = true; };
  }, [ragSettings.LLM_PROVIDER, ragSettings.EMBEDDING_PROVIDER, ragSettings.LLM_BASE_URL]);

  return {
    llmStatus, setLLMStatus,
    embeddingStatus, setEmbeddingStatus,
    ollamaServerStatus, setOllamaServerStatus,
    ollamaManualConfirmed, setOllamaManualConfirmed,
    ollamaMetrics, fetchOllamaMetrics,
    manualTestConnection,
    lastMetricsFetchRef
  };
};
