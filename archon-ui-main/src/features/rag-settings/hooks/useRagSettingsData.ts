import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/features/shared/hooks/useToast';
import { credentialsService } from '@/services/credentialsService';

export type ProviderKey = 'openai' | 'google' | 'ollama' | 'anthropic' | 'grok' | 'openrouter';

// Providers that support embedding models
export const EMBEDDING_CAPABLE_PROVIDERS: ProviderKey[] = ['openai', 'google', 'ollama'];

export interface ProviderModels {
  chatModel: string;
  embeddingModel: string;
}

export type ProviderModelMap = Record<ProviderKey, ProviderModels>;

// Provider model persistence helpers
const PROVIDER_MODELS_KEY = 'archon_provider_models';

export const getDefaultModels = (provider: ProviderKey): ProviderModels => {
  const chatDefaults: Record<ProviderKey, string> = {
    openai: 'gpt-4o-mini',
    anthropic: 'claude-3-5-sonnet-20241022',
    google: 'gemini-1.5-flash',
    grok: 'grok-3-mini', // Updated to use grok-3-mini as default
    openrouter: 'openai/gpt-4o-mini',
    ollama: 'llama3:8b'
  };

  const embeddingDefaults: Record<ProviderKey, string> = {
    openai: 'text-embedding-3-small',
    anthropic: 'text-embedding-3-small', // Fallback to OpenAI
    google: 'gemini-embedding-001',
    grok: 'text-embedding-3-small', // Fallback to OpenAI
    openrouter: 'text-embedding-3-small',
    ollama: 'nomic-embed-text'
  };

  return {
    chatModel: chatDefaults[provider],
    embeddingModel: embeddingDefaults[provider]
  };
};

const saveProviderModels = (providerModels: ProviderModelMap): void => {
  try {
    localStorage.setItem(PROVIDER_MODELS_KEY, JSON.stringify(providerModels));
  } catch (_error) {
    // console.error('Failed to save provider models:', error);
  }
};

const loadProviderModels = (): ProviderModelMap => {
  try {
    const saved = localStorage.getItem(PROVIDER_MODELS_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (_error) {
    // console.error('Failed to load provider models:', error);
  }

  // Return defaults for all providers if nothing saved
  const providers: ProviderKey[] = ['openai', 'google', 'openrouter', 'ollama', 'anthropic', 'grok'];
  const defaultModels: ProviderModelMap = {} as ProviderModelMap;

  providers.forEach(provider => {
    defaultModels[provider] = getDefaultModels(provider);
  });

  return defaultModels;
};

// Static color styles mapping (prevents Tailwind JIT purging)
export const colorStyles: Record<ProviderKey, string> = {
  openai: 'border-green-500 bg-green-500/10',
  google: 'border-blue-500 bg-blue-500/10',
  openrouter: 'border-cyan-500 bg-cyan-500/10',
  ollama: 'border-purple-500 bg-purple-500/10',
  anthropic: 'border-orange-500 bg-orange-500/10',
  grok: 'border-yellow-500 bg-yellow-500/10',
};

export const providerWarningAlertStyle = 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300';
export const providerErrorAlertStyle = 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-300';
export const providerMissingAlertStyle = providerErrorAlertStyle;

export const providerDisplayNames: Record<ProviderKey, string> = {
  openai: 'OpenAI',
  google: 'Google',
  openrouter: 'OpenRouter',
  ollama: 'Ollama',
  anthropic: 'Anthropic',
  grok: 'Grok',
};

const isProviderKey = (value: unknown): value is ProviderKey =>
  typeof value === 'string' && ['openai', 'google', 'openrouter', 'ollama', 'anthropic', 'grok'].includes(value);

// Default base URL for Ollama instances when not explicitly configured
const DEFAULT_OLLAMA_URL = 'http://host.docker.internal:11434/v1';

const PROVIDER_CREDENTIAL_KEYS = [
  'OPENAI_API_KEY',
  'GOOGLE_API_KEY',
  'GEMINI_API_KEY',
  'ANTHROPIC_API_KEY',
  'OPENROUTER_API_KEY',
  'GROK_API_KEY',
] as const;

export type ProviderCredentialKey = typeof PROVIDER_CREDENTIAL_KEYS[number];

const CREDENTIAL_PROVIDER_MAP: Record<ProviderCredentialKey, ProviderKey> = {
  OPENAI_API_KEY: 'openai',
  GOOGLE_API_KEY: 'google',
  GEMINI_API_KEY: 'google',
  ANTHROPIC_API_KEY: 'anthropic',
  OPENROUTER_API_KEY: 'openrouter',
  GROK_API_KEY: 'grok',
};

export const normalizeBaseUrl = (url?: string | null): string | null => {
  if (!url) return null;
  const trimmed = url.trim();
  if (!trimmed) return null;

  let normalized = trimmed.replace(/\/+$/, '');
  normalized = normalized.replace(/\/v1$/i, '');
  return normalized || null;
};

export type RagSettingsType = {
  MODEL_CHOICE: string;
  USE_CONTEXTUAL_EMBEDDINGS: boolean;
  CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: number;
  USE_HYBRID_SEARCH: boolean;
  USE_AGENTIC_RAG: boolean;
  USE_RERANKING: boolean;
  LLM_PROVIDER?: string;
  LLM_BASE_URL?: string;
  LLM_INSTANCE_NAME?: string;
  EMBEDDING_MODEL?: string;
  EMBEDDING_PROVIDER?: string;
  OLLAMA_EMBEDDING_URL?: string;
  OLLAMA_EMBEDDING_INSTANCE_NAME?: string;
  // Crawling Performance Settings
  CRAWL_BATCH_SIZE?: number;
  CRAWL_MAX_CONCURRENT?: number;
  CRAWL_WAIT_STRATEGY?: string;
  CRAWL_PAGE_TIMEOUT?: number;
  CRAWL_DELAY_BEFORE_HTML?: number;
  // Storage Performance Settings
  DOCUMENT_STORAGE_BATCH_SIZE?: number;
  EMBEDDING_BATCH_SIZE?: number;
  DELETE_BATCH_SIZE?: number;
  ENABLE_PARALLEL_BATCHES?: boolean;
  // Advanced Settings
  MEMORY_THRESHOLD_PERCENT?: number;
  DISPATCHER_CHECK_INTERVAL?: number;
  CODE_EXTRACTION_BATCH_SIZE?: number;
  CODE_SUMMARY_MAX_WORKERS?: number;
};

export const useRagSettingsData = (
  ragSettings: RagSettingsType,
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void
) => {
  const [saving, setSaving] = useState(false);
  const [showCrawlingSettings, setShowCrawlingSettings] = useState(false);
  const [showStorageSettings, setShowStorageSettings] = useState(false);
  const [showModelDiscoveryModal, setShowModelDiscoveryModal] = useState(false);
  const [showOllamaConfig, setShowOllamaConfig] = useState(false);
  
  // Status tracking
  const [llmStatus, setLLMStatus] = useState<{
    online: boolean;
    responseTime: number | null;
    checking: boolean;
  }>({ online: false, responseTime: null, checking: false });
  const [embeddingStatus, setEmbeddingStatus] = useState<{
    online: boolean;
    responseTime: number | null;
    checking: boolean;
  }>({ online: false, responseTime: null, checking: false });

  // API key credentials for status checking
  const [apiCredentials, setApiCredentials] = useState<{[key: string]: boolean}>({});
  // Provider connection status tracking
  const [providerConnectionStatus, setProviderConnectionStatus] = useState<{
    [key: string]: { connected: boolean; checking: boolean; lastChecked?: Date }
  }>({});
  const providerConnectionStatusRef = useRef(providerConnectionStatus);
  useEffect(() => {
    providerConnectionStatusRef.current = providerConnectionStatus;
  }, [providerConnectionStatus]);
  const [ollamaServerStatus, setOllamaServerStatus] = useState<'unknown' | 'online' | 'offline'>('unknown');
  const [ollamaManualConfirmed, setOllamaManualConfirmed] = useState(false);

  // Edit modals state
  const [showEditLLMModal, setShowEditLLMModal] = useState(false);
  const [showEditEmbeddingModal, setShowEditEmbeddingModal] = useState(false);
  
  // Model selection modals state
  const [showLLMModelSelectionModal, setShowLLMModelSelectionModal] = useState(false);
  const [showEmbeddingModelSelectionModal, setShowEmbeddingModelSelectionModal] = useState(false);

  // Provider-specific model persistence state
  const [providerModels, setProviderModels] = useState<ProviderModelMap>(() => loadProviderModels());

  // Independent provider selection state
  const [chatProvider, setChatProvider] = useState<ProviderKey>(() =>
    (ragSettings.LLM_PROVIDER as ProviderKey) || 'openai'
  );
  const [embeddingProvider, setEmbeddingProvider] = useState<ProviderKey>(() =>
    // Default to openai if no specific embedding provider is set
    (ragSettings.EMBEDDING_PROVIDER as ProviderKey) || 'openai'
  );
  const [activeSelection, setActiveSelection] = useState<'chat' | 'embedding'>('chat');

  // Instance configurations
  const [llmInstanceConfig, setLLMInstanceConfig] = useState({
    name: '',
    url: ragSettings.LLM_BASE_URL || 'http://host.docker.internal:11434/v1'
  });
  const [embeddingInstanceConfig, setEmbeddingInstanceConfig] = useState({
    name: '', 
    url: ragSettings.OLLAMA_EMBEDDING_URL || 'http://host.docker.internal:11434/v1'
  });

  // --- Refs for managing component state and side effects ---
  // Refs to prevent infinite loops in useEffect hooks when syncing with ragSettings
  const lastLLMConfigRef = useRef({ url: '', name: '' });
  const lastEmbeddingConfigRef = useRef({ url: '', name: '' });
  // Ref to track if the initial credential load has completed
  const hasLoadedCredentialsRef = useRef(false);
  // Refs to manage effect re-runs for provider changes
  const updateChatRagSettingsRef = useRef(true);
  const updateEmbeddingRagSettingsRef = useRef(true);
  // Refs for managing polling timeouts for Ollama connection tests
  const llmRetryTimeoutRef = useRef<number | null>(null);
  const embeddingRetryTimeoutRef = useRef<number | null>(null);
  // Ref to track whether the initial on-load connection test has been performed
  const hasRunInitialTestRef = useRef(false);
  // Ref to track the last state that triggered a metrics fetch, preventing redundant calls
  const lastMetricsFetchRef = useRef({
    provider: '',
    embProvider: '',
    llmUrl: '',
    embUrl: '',
    llmOnline: false,
    embOnline: false
  });

  const [ollamaMetrics, setOllamaMetrics] = useState({
    totalModels: 0,
    chatModels: 0,
    embeddingModels: 0,
    activeHosts: 0,
    loading: true,
    // Per-instance model counts
    llmInstanceModels: { chat: 0, embedding: 0, total: 0 },
    embeddingInstanceModels: { chat: 0, embedding: 0, total: 0 }
  });

  const { showToast } = useToast();

  // Config-driven arrays for Performance settings
  const crawlingSettingsFields = [
    { key: 'CRAWL_BATCH_SIZE', type: 'number', label: 'Batch Size', min: 10, max: 100, default: 50, description: 'URLs to crawl in parallel (10-100)' },
    { key: 'CRAWL_MAX_CONCURRENT', type: 'number', label: 'Max Concurrent', min: 1, max: 20, default: 10, description: 'Pages to crawl in parallel per operation (1-20)' },
    { key: 'CRAWL_PAGE_TIMEOUT', type: 'number', label: 'Page Timeout (ms)', min: 5000, max: 120000, default: 60000, description: 'Timeout per page' },
    { key: 'CRAWL_DELAY_BEFORE_HTML', type: 'number', label: 'Render Delay (s)', min: 0.1, max: 5, default: 0.5, step: 0.1, description: 'Wait for JS execution' },
    { key: 'CRAWL_WAIT_STRATEGY', label: 'Wait Strategy', type: 'select', options: [
      { value: 'domcontentloaded', label: 'DOM Loaded' },
      { value: 'networkidle', label: 'Network Idle' },
      { value: 'load', label: 'Full Load' }
    ]}
  ];

  const storageSettingsFields = [
    { key: 'DOCUMENT_STORAGE_BATCH_SIZE', type: 'number', label: 'Document Batch Size', min: 10, max: 100, default: 50, description: 'Chunks per batch (10-100)' },
    { key: 'EMBEDDING_BATCH_SIZE', type: 'number', label: 'Embedding Batch Size', min: 20, max: 200, default: 100, description: 'Per API call (20-200)' },
    { key: 'CODE_SUMMARY_MAX_WORKERS', type: 'number', label: 'Code Extraction Workers', min: 1, max: 10, default: 3, description: 'Parallel workers (1-10)' },
    { key: 'MEMORY_THRESHOLD_PERCENT', type: 'number', label: 'Memory Threshold (%)', min: 50, max: 95, default: 85, description: 'Pause if usage exceeds this' },
    { key: 'DISPATCHER_CHECK_INTERVAL', type: 'number', label: 'Check Interval (ms)', min: 100, max: 5000, default: 1000, description: 'Queue polling frequency' }
  ];

  const coreModelFields = [
    { key: 'MODEL_CHOICE', label: 'Chat Model', type: 'text', placeholder: 'e.g. gpt-4o-mini' },
    { key: 'EMBEDDING_MODEL', label: 'Embedding Model', type: 'text', placeholder: 'e.g. text-embedding-3-small' },
    { key: 'LLM_INSTANCE_NAME', label: 'LLM Instance Name', type: 'text' },
    { key: 'LLM_BASE_URL', label: 'LLM Base URL', type: 'text' },
    { key: 'OLLAMA_EMBEDDING_URL', label: 'Embedding URL', type: 'text' },
    { key: 'OLLAMA_EMBEDDING_INSTANCE_NAME', label: 'Embedding Name', type: 'text' },
    { key: 'CONTEXTUAL_EMBEDDINGS_MAX_WORKERS', label: 'Contextual Workers', type: 'number', min: 1, max: 10 },
    { key: 'CODE_EXTRACTION_BATCH_SIZE', label: 'Extraction Batch Size', type: 'number', min: 1, max: 50 }
  ];


  const fetchOllamaMetrics = useCallback(async () => {
    try {
      setOllamaMetrics(prev => ({ ...prev, loading: true }));

      // Prepare normalized instance URLs for the API call
      const instanceUrls: string[] = [];
      const llmUrlBase = normalizeBaseUrl(llmInstanceConfig.url);
      const embUrlBase = normalizeBaseUrl(embeddingInstanceConfig.url);

      if (llmUrlBase) instanceUrls.push(llmUrlBase);
      if (embUrlBase && embUrlBase !== llmUrlBase) {
        instanceUrls.push(embUrlBase);
      }

      if (instanceUrls.length === 0) {
        setOllamaMetrics(prev => ({ ...prev, loading: false }));
        return;
      }

      // Build query parameters
      const params = new URLSearchParams();
      instanceUrls.forEach(url => params.append('instance_urls', url));
      params.append('include_capabilities', 'true');

      // Fetch models from configured instances
      const modelsResponse = await fetch(`/api/ollama/models?${params.toString()}`);
      const modelsData = await modelsResponse.json();

      if (modelsResponse.ok) {
        // Extract models from the response
        const allChatModels = modelsData.chat_models || [];
        const allEmbeddingModels = modelsData.embedding_models || [];

        // Count models for LLM instance
        const llmChatModels = allChatModels.filter((model: { instance_url: string }) =>
          normalizeBaseUrl(model.instance_url) === llmUrlBase
        );
        const llmEmbeddingModels = allEmbeddingModels.filter((model: { instance_url: string }) =>
          normalizeBaseUrl(model.instance_url) === llmUrlBase
        );

        // Count models for Embedding instance
        const embChatModels = allChatModels.filter((model: { instance_url: string }) =>
          normalizeBaseUrl(model.instance_url) === embUrlBase
        );
        const embEmbeddingModels = allEmbeddingModels.filter((model: { instance_url: string }) =>
          normalizeBaseUrl(model.instance_url) === embUrlBase
        );

        // Calculate totals
        const totalModels = modelsData.total_models || 0;
        const activeHosts = (llmStatus.online ? 1 : 0) + (embeddingStatus.online ? 1 : 0);

        setOllamaMetrics({
          totalModels: totalModels,
          chatModels: allChatModels.length,
          embeddingModels: allEmbeddingModels.length,
          activeHosts,
          loading: false,
          // Per-instance model counts
          llmInstanceModels: {
            chat: llmChatModels.length,
            embedding: llmEmbeddingModels.length,
            total: llmChatModels.length + llmEmbeddingModels.length
          },
          embeddingInstanceModels: {
            chat: embChatModels.length,
            embedding: embEmbeddingModels.length,
            total: embChatModels.length + embEmbeddingModels.length
          }
        });
      } else {
        // console.error('Failed to fetch models:', modelsData);
        setOllamaMetrics(prev => ({ ...prev, loading: false }));
      }
    } catch (_error) {
      // console.error('Error fetching Ollama metrics:', error);
      setOllamaMetrics(prev => ({ ...prev, loading: false }));
    }
  }, [embeddingInstanceConfig.url, llmInstanceConfig.url, llmStatus.online, embeddingStatus.online]);

  // Refs to stabilize manualTestConnection dependencies and prevent loops
  const ollamaMetricsRef = useRef(ollamaMetrics);
  const fetchOllamaMetricsRef = useRef(fetchOllamaMetrics);

  useEffect(() => {
    ollamaMetricsRef.current = ollamaMetrics;
  }, [ollamaMetrics]);

  useEffect(() => {
    fetchOllamaMetricsRef.current = fetchOllamaMetrics;
  }, [fetchOllamaMetrics]);

  // Manual test function with user feedback using backend proxy
const manualTestConnection = useCallback(async (
    url: string,
    setStatus: React.Dispatch<React.SetStateAction<{ online: boolean; responseTime: number | null; checking: boolean }>>,
    instanceName: string,
    context?: 'chat' | 'embedding',
    options?: { suppressToast?: boolean }
  ): Promise<boolean> => {
    const suppressToast = options?.suppressToast ?? false;
    setStatus(prev => ({ ...prev, checking: true }));
    const startTime = Date.now();

    try {
      // Strip /v1 suffix for backend health check (backend expects base Ollama URL)
      const baseUrl = url.replace('/v1', '').replace(/\/$/, '');

      // Use the backend health check endpoint to avoid CORS issues
      const backendHealthUrl = `/api/ollama/instances/health?instance_urls=${encodeURIComponent(baseUrl)}&include_models=true`;

      const response = await fetch(backendHealthUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(15000)
      });

      if (response.ok) {
        const data = await response.json();
        const instanceStatus = data.instance_status?.[baseUrl];

        if (instanceStatus?.is_healthy) {
          const responseTime = Math.round(instanceStatus.response_time_ms || (Date.now() - startTime));
          setStatus({ online: true, responseTime, checking: false });

          // Context-aware model count display
          let modelCount = instanceStatus.models_available || 0;
          let modelType = 'models';

          if (context === 'chat') {
            modelCount = ollamaMetricsRef.current.llmInstanceModels?.chat || 0;
            modelType = 'chat models';
          } else if (context === 'embedding') {
            modelCount = ollamaMetricsRef.current.embeddingInstanceModels?.embedding || 0;
            modelType = 'embedding models';
          }

          if (!suppressToast) {
            showToast(`${instanceName} connection successful: ${modelCount} ${modelType} available (${responseTime}ms)`, 'success');
          }

          // Scenario 2: Manual "Test Connection" button - refresh Ollama metrics if Ollama provider is selected
          if (ragSettings.LLM_PROVIDER === 'ollama' || embeddingProvider === 'ollama' || context === 'embedding') {
            // console.log('🔄 Fetching Ollama metrics - Test Connection button clicked');
            fetchOllamaMetricsRef.current();
          }

          return true;
        } else {
          setStatus({ online: false, responseTime: null, checking: false });
          if (!suppressToast) {
            showToast(`${instanceName} connection failed: ${instanceStatus?.error_message || 'Instance is not healthy'}`, 'error');
          }
          return false;
        }
      } else {
        setStatus({ online: false, responseTime: null, checking: false });
        if (!suppressToast) {
          showToast(`${instanceName} connection failed: Backend proxy error (HTTP ${response.status})`, 'error');
        }
        return false;
      }
    } catch (error) {
      setStatus({ online: false, responseTime: null, checking: false });

      if (!suppressToast) {
        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            showToast(`${instanceName} connection failed: Request timeout (>15s)`, 'error');
          } else {
            showToast(`${instanceName} connection failed: ${error.message || 'Unknown error'}`, 'error');
          }
        } else {
          showToast(`${instanceName} connection failed: Unknown error`, 'error');
        }
      }

      return false;
    }
  }, [embeddingProvider, ragSettings.LLM_PROVIDER, showToast]);

  useEffect(() => {
    const newLLMUrl = ragSettings.LLM_BASE_URL || '';
    const newLLMName = ragSettings.LLM_INSTANCE_NAME || '';
    
    if (newLLMUrl !== lastLLMConfigRef.current.url || newLLMName !== lastLLMConfigRef.current.name) {
      lastLLMConfigRef.current = { url: newLLMUrl, name: newLLMName };
      setLLMInstanceConfig(prev => {
        const newConfig = {
          url: newLLMUrl || prev.url,
          name: newLLMName || prev.name
        };
        // Only update if actually different to prevent loops
        if (newConfig.url !== prev.url || newConfig.name !== prev.name) {
          return newConfig;
        }
        return prev;
      });
    }
  }, [ragSettings.LLM_BASE_URL, ragSettings.LLM_INSTANCE_NAME]);

  useEffect(() => {
    const newEmbeddingUrl = ragSettings.OLLAMA_EMBEDDING_URL || '';
    const newEmbeddingName = ragSettings.OLLAMA_EMBEDDING_INSTANCE_NAME || '';
    
    if (newEmbeddingUrl !== lastEmbeddingConfigRef.current.url || newEmbeddingName !== lastEmbeddingConfigRef.current.name) {
      lastEmbeddingConfigRef.current = { url: newEmbeddingUrl, name: newEmbeddingName };
      setEmbeddingInstanceConfig(prev => {
        const newConfig = {
          url: newEmbeddingUrl || prev.url,
          name: newEmbeddingName || prev.name
        };
        // Only update if actually different to prevent loops
        if (newConfig.url !== prev.url || newConfig.name !== prev.name) {
          return newConfig;
        }
        return prev;
      });
    }
  }, [ragSettings.OLLAMA_EMBEDDING_URL, ragSettings.OLLAMA_EMBEDDING_INSTANCE_NAME]);

  // Provider model persistence effects - separate for chat and embedding
  useEffect(() => {
    // Update chat provider models when chat model changes
    if (chatProvider && ragSettings.MODEL_CHOICE) {
      setProviderModels(prev => {
        const updated = {
          ...prev,
          [chatProvider]: {
            ...prev[chatProvider],
            chatModel: ragSettings.MODEL_CHOICE
          }
        };
        saveProviderModels(updated);
        return updated;
      });
    }
  }, [ragSettings.MODEL_CHOICE, chatProvider]);

  useEffect(() => {
    // Update embedding provider models when embedding model changes
    if (embeddingProvider && ragSettings.EMBEDDING_MODEL) {
      setProviderModels(prev => {
        const updated = {
          ...prev,
          [embeddingProvider]: {
            ...prev[embeddingProvider],
            embeddingModel: ragSettings.EMBEDDING_MODEL
          }
        };
        saveProviderModels(updated);
        return updated;
      });
    }
  }, [ragSettings.EMBEDDING_MODEL, embeddingProvider]);

  const reloadApiCredentials = useCallback(async () => {
    try {
      const statusResults = await credentialsService.checkCredentialStatus(
        Array.from(PROVIDER_CREDENTIAL_KEYS),
      );

      const credentials: { [key: string]: boolean } = {};

      for (const key of PROVIDER_CREDENTIAL_KEYS) {
        const result = statusResults[key];
        credentials[key] = !!result?.has_value;
      }

      // console.log(
      //   '🔑 Updated API credential status snapshot:',
      //   Object.keys(credentials),
      // );
      setApiCredentials(credentials);
      hasLoadedCredentialsRef.current = true;
    } catch (_error) {
      // console.error('Failed to load API credentials for status checking:', error);
    }
  }, []);

  useEffect(() => {
    void reloadApiCredentials();
  }, [reloadApiCredentials]);

  useEffect(() => {
    if (!hasLoadedCredentialsRef.current) {
      return;
    }

    void reloadApiCredentials();
  }, [ragSettings.LLM_PROVIDER, reloadApiCredentials]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (Object.keys(ragSettings).length > 0) {
        void reloadApiCredentials();
      }
    }, 30000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ragSettings.LLM_PROVIDER, reloadApiCredentials]);

  useEffect(() => {
    const needsDetection = chatProvider === 'ollama' || embeddingProvider === 'ollama';

    if (!needsDetection) {
      setOllamaServerStatus('unknown');
      return;
    }

    const baseUrl = (
      ragSettings.LLM_BASE_URL?.trim() ||
      llmInstanceConfig.url?.trim() ||
      ragSettings.OLLAMA_EMBEDDING_URL?.trim() ||
      embeddingInstanceConfig.url?.trim() ||
      DEFAULT_OLLAMA_URL
    );

    const normalizedUrl = baseUrl.replace('/v1', '').replace(/\/$/, '');

    let cancelled = false;

    (async () => {
      try {
        const response = await fetch(
          `/api/ollama/instances/health?instance_urls=${encodeURIComponent(normalizedUrl)}`,
          { method: 'GET', headers: { Accept: 'application/json' }, signal: AbortSignal.timeout(10000) }
        );

        if (cancelled) return;

        if (!response.ok) {
          setOllamaServerStatus('offline');
          return;
        }

        const data = await response.json();
        const instanceStatus = data.instance_status?.[normalizedUrl];
        setOllamaServerStatus(instanceStatus?.is_healthy ? 'online' : 'offline');
      } catch (_error) {
        if (!cancelled) {
          setOllamaServerStatus('offline');
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [chatProvider, embeddingProvider, ragSettings.LLM_BASE_URL, ragSettings.OLLAMA_EMBEDDING_URL, llmInstanceConfig.url, embeddingInstanceConfig.url]);

  // Sync independent provider states with ragSettings (one-way: ragSettings -> local state)
  useEffect(() => {
    if (ragSettings.LLM_PROVIDER) {
      setChatProvider(ragSettings.LLM_PROVIDER as ProviderKey);
    }
  }, [ragSettings.LLM_PROVIDER]);

  useEffect(() => {
    if (ragSettings.EMBEDDING_PROVIDER) {
      setEmbeddingProvider(ragSettings.EMBEDDING_PROVIDER as ProviderKey);
    }
  }, [ragSettings.EMBEDDING_PROVIDER]);

  useEffect(() => {
    setOllamaManualConfirmed(false);
    setOllamaServerStatus('unknown');
  }, [ragSettings.LLM_BASE_URL, ragSettings.OLLAMA_EMBEDDING_URL, chatProvider, embeddingProvider]);

  // Update ragSettings when independent providers change (one-way: local state -> ragSettings)
  // Split the “first‐run” guard into two refs so chat and embedding effects don’t interfere.

  useEffect(() => {
    // Only update if this is a user‐initiated change, not a sync from ragSettings
    if (updateChatRagSettingsRef.current && chatProvider !== ragSettings.LLM_PROVIDER) {
      setRagSettings(prev => ({
        ...prev,
        LLM_PROVIDER: chatProvider
      }));
    }
    updateChatRagSettingsRef.current = true;
  }, [chatProvider, ragSettings.LLM_PROVIDER, setRagSettings]);

  useEffect(() => {
    // Only update if this is a user‐initiated change, not a sync from ragSettings
    if (updateEmbeddingRagSettingsRef.current && embeddingProvider && embeddingProvider !== ragSettings.EMBEDDING_PROVIDER) {
      setRagSettings(prev => ({
        ...prev,
        EMBEDDING_PROVIDER: embeddingProvider
      }));
    }
    updateEmbeddingRagSettingsRef.current = true;
  }, [embeddingProvider, ragSettings.EMBEDDING_PROVIDER, setRagSettings]);

  useEffect(() => {
    return () => {
      if (llmRetryTimeoutRef.current) {
        clearTimeout(llmRetryTimeoutRef.current);
        llmRetryTimeoutRef.current = null;
      }
      if (embeddingRetryTimeoutRef.current) {
        clearTimeout(embeddingRetryTimeoutRef.current);
        embeddingRetryTimeoutRef.current = null;
      }
    };
  }, []);

  // Test connection to external providers
  const testProviderConnection = useCallback(async (provider: string): Promise<boolean> => {
    setProviderConnectionStatus(prev => ({
      ...prev,
      [provider]: { ...prev[provider], checking: true }
    }));

    try {
      // Use server-side API endpoint for secure connectivity testing
      const response = await fetch(`/api/providers/${provider}/status`);
      const result = await response.json();

      const isConnected = result.ok && result.reason === 'connected';

      setProviderConnectionStatus(prev => ({
        ...prev,
        [provider]: { connected: isConnected, checking: false, lastChecked: new Date() }
      }));

      return isConnected;
    } catch (_error) {
      // console.error(`Error testing ${provider} connection:`, error);
      setProviderConnectionStatus(prev => ({
        ...prev,
        [provider]: { connected: false, checking: false, lastChecked: new Date() }
      }));
      return false;
    }
  }, []);

  // Test provider connections when API credentials change
  useEffect(() => {
    const testConnections = async () => {
      // Test all supported providers
      const providers = ['openai', 'google', 'anthropic', 'openrouter', 'grok'];

      for (const provider of providers) {
        // Don't test if we've already checked recently (within last 30 seconds)
        const lastChecked = providerConnectionStatusRef.current[provider]?.lastChecked;
        const now = new Date();
        const timeSinceLastCheck = lastChecked ? now.getTime() - lastChecked.getTime() : Infinity;

        if (timeSinceLastCheck > 30000) { // 30 seconds
          // console.log(`🔄 Testing ${provider} connection...`);
          await testProviderConnection(provider);
        }
      }
    };

    // Test connections periodically (every 60 seconds)
    testConnections();
    const interval = setInterval(testConnections, 60000);

    return () => clearInterval(interval);
  }, [apiCredentials, testProviderConnection]); // Test when credentials change

  useEffect(() => {
    const handleCredentialUpdate = (event: Event) => {
      const detail = (event as CustomEvent<{ keys?: string[] }>).detail;
      const updatedKeys = (detail?.keys ?? []).map(key => key.toUpperCase());

      if (updatedKeys.length === 0) {
        void reloadApiCredentials();
        return;
      }

      const touchedProviderKeys = updatedKeys.filter(key => key in CREDENTIAL_PROVIDER_MAP);
      if (touchedProviderKeys.length === 0) {
        return;
      }

      void reloadApiCredentials();

      touchedProviderKeys.forEach(key => {
        const provider = CREDENTIAL_PROVIDER_MAP[key as ProviderCredentialKey];
        if (provider) {
          void testProviderConnection(provider);
        }
      });
    };

    window.addEventListener('archon:credentials-updated', handleCredentialUpdate);

    return () => {
      window.removeEventListener('archon:credentials-updated', handleCredentialUpdate);
    };
  }, [reloadApiCredentials, testProviderConnection]);



  React.useEffect(() => {
    const current = {
      provider: ragSettings.LLM_PROVIDER ?? '',
      embProvider: embeddingProvider,
      llmUrl: llmInstanceConfig.url,
      embUrl: embeddingInstanceConfig.url,
      llmOnline: llmStatus.online,
      embOnline: embeddingStatus.online
    };
    const last = lastMetricsFetchRef.current;

    const meaningfulChange =
      current.provider !== last.provider ||
      current.embProvider !== last.embProvider ||
      current.llmUrl !== last.llmUrl ||
      current.embUrl !== last.embUrl ||
      current.llmOnline !== last.llmOnline ||
      current.embOnline !== last.embOnline;

    if ((current.provider === 'ollama' || current.embProvider === 'ollama') && meaningfulChange) {
      lastMetricsFetchRef.current = current;
      // console.log('🔄 Fetching Ollama metrics - state changed');
      fetchOllamaMetrics();
    }
  }, [ragSettings.LLM_PROVIDER, embeddingProvider, llmStatus.online, embeddingStatus.online, llmInstanceConfig.url, embeddingInstanceConfig.url, fetchOllamaMetrics]);

  const hasApiCredential = (credentialKey: ProviderCredentialKey): boolean => {
    if (credentialKey in apiCredentials) {
      return Boolean(apiCredentials[credentialKey]);
    }

    const fallbackKey = Object.keys(apiCredentials).find(
      key => key.toUpperCase() === credentialKey,
    );

    return fallbackKey ? Boolean(apiCredentials[fallbackKey]) : false;
  };

  // Function to check if a provider is properly configured
  const getProviderStatus = (providerKey: string): 'configured' | 'missing' | 'partial' => {
    switch (providerKey) {
      case 'openai': {
        const hasOpenAIKey = hasApiCredential('OPENAI_API_KEY');

        // Only show configured if we have both API key AND confirmed connection
        const openAIConnected = providerConnectionStatus['openai']?.connected || false;
        const isChecking = providerConnectionStatus['openai']?.checking || false;

        // Intentionally avoid logging API key material.

        if (!hasOpenAIKey) return 'missing';
        if (isChecking) return 'partial';
        return openAIConnected ? 'configured' : 'missing';
      }
      case 'google': {
        const hasGoogleKey = hasApiCredential('GOOGLE_API_KEY') || hasApiCredential('GEMINI_API_KEY');
        
        // Only show configured if we have both API key AND confirmed connection
        const googleConnected = providerConnectionStatus['google']?.connected || false;
        const googleChecking = providerConnectionStatus['google']?.checking || false;

        if (!hasGoogleKey) return 'missing';
        if (googleChecking) return 'partial';
        return googleConnected ? 'configured' : 'missing';
      }
      case 'ollama':
        {
          if (ollamaManualConfirmed || llmStatus.online || embeddingStatus.online) {
            return 'configured';
          }

          if (ollamaServerStatus === 'online') {
            return 'partial';
          }

          if (ollamaServerStatus === 'offline') {
            return 'missing';
          }

          return 'missing';
        }
      case 'anthropic': {
        const hasAnthropicKey = hasApiCredential('ANTHROPIC_API_KEY');
        const anthropicConnected = providerConnectionStatus['anthropic']?.connected || false;
        const anthropicChecking = providerConnectionStatus['anthropic']?.checking || false;
        if (!hasAnthropicKey) return 'missing';
        if (anthropicChecking) return 'partial';
        return anthropicConnected ? 'configured' : 'missing';
      }
      case 'grok': {
        const hasGrokKey = hasApiCredential('GROK_API_KEY');
        const grokConnected = providerConnectionStatus['grok']?.connected || false;
        const grokChecking = providerConnectionStatus['grok']?.checking || false;
        if (!hasGrokKey) return 'missing';
        if (grokChecking) return 'partial';
        return grokConnected ? 'configured' : 'missing';
      }
      case 'openrouter': {
        const hasOpenRouterKey = hasApiCredential('OPENROUTER_API_KEY');
        const openRouterConnected = providerConnectionStatus['openrouter']?.connected || false;
        const openRouterChecking = providerConnectionStatus['openrouter']?.checking || false;
        if (!hasOpenRouterKey) return 'missing';
        if (openRouterChecking) return 'partial';
        return openRouterConnected ? 'configured' : 'missing';
      }
      default:
        return 'missing';
    }
  };

  const resolvedProviderForAlert = activeSelection === 'chat' ? chatProvider : embeddingProvider;
  const activeProviderKey = isProviderKey(resolvedProviderForAlert)
    ? (resolvedProviderForAlert as ProviderKey)
    : undefined;
  const selectedProviderStatus = activeProviderKey ? getProviderStatus(activeProviderKey) : undefined;

  let providerAlertMessage: string | null = null;
  let providerAlertClassName = '';

  if (activeProviderKey === 'ollama') {
    if (ollamaServerStatus === 'offline') {
      providerAlertMessage = 'Local Ollama service is not running. Start the Ollama server and ensure it is reachable at the configured URL.';
      providerAlertClassName = providerErrorAlertStyle;
    } else if (selectedProviderStatus === 'partial' && ollamaServerStatus === 'online') {
      providerAlertMessage = 'Local Ollama service detected. Click "Test Connection" to confirm model availability.';
      providerAlertClassName = providerWarningAlertStyle;
    }
  } else if (activeProviderKey && selectedProviderStatus === 'missing') {
    const providerName = providerDisplayNames[activeProviderKey] ?? activeProviderKey;
    providerAlertMessage = `${providerName} API key is not configured. Add it in Settings > API Keys.`;
    providerAlertClassName = providerMissingAlertStyle;
  }

  const shouldShowProviderAlert = Boolean(providerAlertMessage);
  
  useEffect(() => {
    if (chatProvider !== 'ollama') {
      if (llmRetryTimeoutRef.current) {
        clearTimeout(llmRetryTimeoutRef.current);
        llmRetryTimeoutRef.current = null;
      }
      return;
    }

    const baseUrl = (
      ragSettings.LLM_BASE_URL?.trim() ||
      llmInstanceConfig.url?.trim() ||
      DEFAULT_OLLAMA_URL
    );

    if (!baseUrl) {
      return;
    }

    const instanceName = llmInstanceConfig.name?.trim().length
      ? llmInstanceConfig.name
      : 'LLM Instance';

    let cancelled = false;

    const runTest = async () => {
      if (cancelled) return;

      const success = await manualTestConnection(
        baseUrl,
        setLLMStatus,
        instanceName,
        'chat',
        { suppressToast: true }
      );

      if (!success && chatProvider === 'ollama' && !cancelled) {
        llmRetryTimeoutRef.current = window.setTimeout(runTest, 5000);
      }
    };

    if (llmRetryTimeoutRef.current) {
      clearTimeout(llmRetryTimeoutRef.current);
      llmRetryTimeoutRef.current = null;
    }

    setLLMStatus(prev => ({ ...prev, checking: true }));
    runTest();

    return () => {
      cancelled = true;
      if (llmRetryTimeoutRef.current) {
        clearTimeout(llmRetryTimeoutRef.current);
        llmRetryTimeoutRef.current = null;
      }
    };
  }, [chatProvider, ragSettings.LLM_BASE_URL, ragSettings.LLM_INSTANCE_NAME, llmInstanceConfig.url, llmInstanceConfig.name, manualTestConnection]);

  useEffect(() => {
    if (embeddingProvider !== 'ollama') {
      if (embeddingRetryTimeoutRef.current) {
        clearTimeout(embeddingRetryTimeoutRef.current);
        embeddingRetryTimeoutRef.current = null;
      }
      return;
    }

    const baseUrl = (
      ragSettings.OLLAMA_EMBEDDING_URL?.trim() ||
      embeddingInstanceConfig.url?.trim() ||
      DEFAULT_OLLAMA_URL
    );

    if (!baseUrl) {
      return;
    }

    const instanceName = embeddingInstanceConfig.name?.trim().length
      ? embeddingInstanceConfig.name
      : 'Embedding Instance';

    let cancelled = false;

    const runTest = async () => {
      if (cancelled) return;

      const success = await manualTestConnection(
        baseUrl,
        setEmbeddingStatus,
        instanceName,
        'embedding',
        { suppressToast: true }
      );

      if (!success && embeddingProvider === 'ollama' && !cancelled) {
        embeddingRetryTimeoutRef.current = window.setTimeout(runTest, 5000);
      }
    };

    if (embeddingRetryTimeoutRef.current) {
      clearTimeout(embeddingRetryTimeoutRef.current);
      embeddingRetryTimeoutRef.current = null;
    }

    setEmbeddingStatus(prev => ({ ...prev, checking: true }));
    runTest();

    return () => {
      cancelled = true;
      if (embeddingRetryTimeoutRef.current) {
        clearTimeout(embeddingRetryTimeoutRef.current);
        embeddingRetryTimeoutRef.current = null;
      }
    };
  }, [embeddingProvider, ragSettings.OLLAMA_EMBEDDING_URL, ragSettings.OLLAMA_EMBEDDING_INSTANCE_NAME, embeddingInstanceConfig.url, embeddingInstanceConfig.name, manualTestConnection]);

  // Test Ollama connectivity when Settings page loads (scenario 4: page load)
  // This useEffect is placed after function definitions to ensure access to manualTestConnection
  useEffect(() => {
    // console.log('🔍 Page load check:', {
    //   hasRunInitialTest: hasRunInitialTestRef.current,
    //   provider: ragSettings.LLM_PROVIDER,
    //   ragSettingsCount: Object.keys(ragSettings).length,
    //   llmUrl: llmInstanceConfig.url,
    //   llmName: llmInstanceConfig.name,
    //   embUrl: embeddingInstanceConfig.url,
    //   embName: embeddingInstanceConfig.name
    // });
    
    // Only run once when data is properly loaded and not run before
    if (
      !hasRunInitialTestRef.current &&
      (ragSettings.LLM_PROVIDER === 'ollama' || embeddingProvider === 'ollama') &&
      Object.keys(ragSettings).length > 0
    ) {
      
      hasRunInitialTestRef.current = true;
      // console.log('🔄 Settings page loaded with Ollama - Testing connectivity');

      // Test LLM instance if a URL is available (either saved or default)
      if (llmInstanceConfig.url) {
        setTimeout(() => {
          const instanceName = llmInstanceConfig.name || 'LLM Instance';
          // console.log('🔍 Testing LLM instance on page load:', instanceName, llmInstanceConfig.url);
          manualTestConnection(
            llmInstanceConfig.url,
            setLLMStatus,
            instanceName,
            'chat',
            { suppressToast: true }
          );
        }, 1000); // Increased delay to ensure component is fully ready
      }
      // If no saved URL, run tests against default endpoint
      else {
        setTimeout(() => {
          const defaultInstanceName = 'Local Ollama (Default)';
          // console.log('🔍 Testing default Ollama chat instance on page load:', DEFAULT_OLLAMA_URL);
          manualTestConnection(
            DEFAULT_OLLAMA_URL,
            setLLMStatus,
            defaultInstanceName,
            'chat',
            { suppressToast: true }
          );
        }, 1000);
      }

      // Test Embedding instance if configured and different from LLM instance
      if (embeddingInstanceConfig.url &&
          embeddingInstanceConfig.url !== llmInstanceConfig.url) {
        setTimeout(() => {
          const instanceName = embeddingInstanceConfig.name || 'Embedding Instance';
          // console.log('🔍 Testing Embedding instance on page load:', instanceName, embeddingInstanceConfig.url);
          manualTestConnection(
            embeddingInstanceConfig.url,
            setEmbeddingStatus,
            instanceName,
            'embedding',
            { suppressToast: true }
          );
        }, 1500); // Stagger the tests
      }
      // If embedding provider is also Ollama but no specific URL is set, test default as fallback
      else if (embeddingProvider === 'ollama' && !embeddingInstanceConfig.url) {
        setTimeout(() => {
          const defaultEmbeddingName = 'Local Ollama (Default)';
          // console.log('🔍 Testing default Ollama embedding instance on page load:', DEFAULT_OLLAMA_URL);
          manualTestConnection(
            DEFAULT_OLLAMA_URL,
            setEmbeddingStatus,
            defaultEmbeddingName,
            'embedding',
            { suppressToast: true }
          );
        }, 1500);
      }

      // Fetch Ollama metrics after testing connections
      setTimeout(() => {
        // console.log('📊 Fetching Ollama metrics on page load');
        fetchOllamaMetrics();
      }, 2000);
    }
  }, [
    ragSettings.LLM_PROVIDER,
    embeddingProvider,
    llmInstanceConfig.url,
    llmInstanceConfig.name,
    embeddingInstanceConfig.url,
    embeddingInstanceConfig.name,
    manualTestConnection,
    fetchOllamaMetrics,
    ragSettings
    // eslint-disable-next-line react-hooks/exhaustive-deps
  ]);
  
  return {
    saving, setSaving,
    showCrawlingSettings, setShowCrawlingSettings,
    showStorageSettings, setShowStorageSettings,
    showModelDiscoveryModal, setShowModelDiscoveryModal,
    showOllamaConfig, setShowOllamaConfig,
    llmStatus, setLLMStatus,
    embeddingStatus, setEmbeddingStatus,
    apiCredentials, providerConnectionStatus,
    ollamaServerStatus, ollamaManualConfirmed, setOllamaManualConfirmed,
    showEditLLMModal, setShowEditLLMModal,
    showEditEmbeddingModal, setShowEditEmbeddingModal,
    showLLMModelSelectionModal, setShowLLMModelSelectionModal,
    showEmbeddingModelSelectionModal, setShowEmbeddingModelSelectionModal,
    providerModels,
    chatProvider, setChatProvider,
    embeddingProvider, setEmbeddingProvider,
    activeSelection, setActiveSelection,
    llmInstanceConfig, setLLMInstanceConfig,
    embeddingInstanceConfig, setEmbeddingInstanceConfig,
    ollamaMetrics, fetchOllamaMetrics,
    showToast, setOllamaServerStatus,
    manualTestConnection, getProviderStatus,
    shouldShowProviderAlert, providerAlertClassName, providerAlertMessage,
    crawlingSettingsFields, storageSettingsFields, coreModelFields
  };
}
