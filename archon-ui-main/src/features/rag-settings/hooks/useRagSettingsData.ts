import { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/features/shared/hooks/useToast';
import { 
  ProviderKey, ProviderModelMap, RagSettingsType 
} from '../types';
import { 
  DEFAULT_OLLAMA_URL, 
  providerErrorAlertStyle, 
  providerWarningAlertStyle,
  providerMissingAlertStyle,
  providerDisplayNames
} from '../constants';
import { 
  loadProviderModels, saveProviderModels, normalizeBaseUrl,
  getDisplayedChatModel as _getChat,
  getDisplayedEmbeddingModel as _getEmb,
  getModelPlaceholder,
  getEmbeddingPlaceholder
} from '../utils/modelHelpers';
import { useOllamaLogic } from './useOllamaLogic';
import { useProviderAuth } from './useProviderAuth';

export { normalizeBaseUrl, type RagSettingsType };

export const useRagSettingsData = (
  ragSettings: RagSettingsType,
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void
) => {
  const { showToast } = useToast();
  const [saving, setSaving] = useState(false);
  const [showCrawlingSettings, setShowCrawlingSettings] = useState(false);
  const [showStorageSettings, setShowStorageSettings] = useState(false);
  const [showModelDiscoveryModal, setShowModelDiscoveryModal] = useState(false);
  const [showOllamaConfig, setShowOllamaConfig] = useState(false);
  
  // Sub-hooks integration
  const ollama = useOllamaLogic(ragSettings, showToast);
  const auth = useProviderAuth(ragSettings);

  // Component local states
  const [showEditLLMModal, setShowEditLLMModal] = useState(false);
  const [showEditEmbeddingModal, setShowEditEmbeddingModal] = useState(false);
  const [showLLMModelSelectionModal, setShowLLMModelSelectionModal] = useState(false);
  const [showEmbeddingModelSelectionModal, setShowEmbeddingModelSelectionModal] = useState(false);
  const [providerModels, setProviderModels] = useState<ProviderModelMap>(() => loadProviderModels());
  const [chatProvider, setChatProvider] = useState<ProviderKey>(() => (ragSettings.LLM_PROVIDER as ProviderKey) || 'openai');
  const [embeddingProvider, setEmbeddingProvider] = useState<ProviderKey>(() => (ragSettings.EMBEDDING_PROVIDER as ProviderKey) || 'openai');
  const [activeSelection, setActiveSelection] = useState<'chat' | 'embedding'>('chat');
  const [llmInstanceConfig, setLLMInstanceConfig] = useState({ name: '', url: ragSettings.LLM_BASE_URL || DEFAULT_OLLAMA_URL });
  const [embeddingInstanceConfig, setEmbeddingInstanceConfig] = useState({ name: '', url: ragSettings.OLLAMA_EMBEDDING_URL || DEFAULT_OLLAMA_URL });

  // Refs for stability (Physical History preserved)
  const lastLLMConfigRef = useRef({ url: '', name: '' });
  const lastEmbeddingConfigRef = useRef({ url: '', name: '' });
  const hasRunInitialTestRef = useRef(false);
  const updateChatRagSettingsRef = useRef(true);
  const updateEmbeddingRagSettingsRef = useRef(true);

  // --- Wrap Utils to match original overload signature ---
  const getDisplayedChatModel = useCallback((p: ProviderKey | RagSettingsType) => 
    _getChat(p, ragSettings, providerModels), [ragSettings, providerModels]);

  const getDisplayedEmbeddingModel = useCallback((p: ProviderKey | RagSettingsType) => 
    _getEmb(p, ragSettings, providerModels), [ragSettings, providerModels]);

  // Sync state with ragSettings (One-way: ragSettings -> local)
  useEffect(() => {
    const newUrl = ragSettings.LLM_BASE_URL || '';
    const newName = ragSettings.LLM_INSTANCE_NAME || '';
    if (newUrl !== lastLLMConfigRef.current.url || newName !== lastLLMConfigRef.current.name) {
      lastLLMConfigRef.current = { url: newUrl, name: newName };
      setLLMInstanceConfig(prev => (newUrl === prev.url && newName === prev.name ? prev : { url: newUrl || prev.url, name: newName || prev.name }));
    }
  }, [ragSettings.LLM_BASE_URL, ragSettings.LLM_INSTANCE_NAME]);

  useEffect(() => {
    const newUrl = ragSettings.OLLAMA_EMBEDDING_URL || '';
    const newName = ragSettings.OLLAMA_EMBEDDING_INSTANCE_NAME || '';
    if (newUrl !== lastEmbeddingConfigRef.current.url || newName !== lastEmbeddingConfigRef.current.name) {
      lastEmbeddingConfigRef.current = { url: newUrl, name: newName };
      setEmbeddingInstanceConfig(prev => (newUrl === prev.url && newName === prev.name ? prev : { url: newUrl || prev.url, name: newName || prev.name }));
    }
  }, [ragSettings.OLLAMA_EMBEDDING_URL, ragSettings.OLLAMA_EMBEDDING_INSTANCE_NAME]);

  useEffect(() => {
    if (ragSettings.LLM_PROVIDER) setChatProvider(ragSettings.LLM_PROVIDER as ProviderKey);
  }, [ragSettings.LLM_PROVIDER]);

  useEffect(() => {
    if (ragSettings.EMBEDDING_PROVIDER) setEmbeddingProvider(ragSettings.EMBEDDING_PROVIDER as ProviderKey);
  }, [ragSettings.EMBEDDING_PROVIDER]);

  // Update ragSettings when local providers change (One-way: local -> ragSettings)
  useEffect(() => {
    if (updateChatRagSettingsRef.current && chatProvider !== ragSettings.LLM_PROVIDER) {
      setRagSettings(prev => ({ ...prev, LLM_PROVIDER: chatProvider }));
    }
    updateChatRagSettingsRef.current = true;
  }, [chatProvider, ragSettings.LLM_PROVIDER, setRagSettings]);

  useEffect(() => {
    if (updateEmbeddingRagSettingsRef.current && embeddingProvider && embeddingProvider !== ragSettings.EMBEDDING_PROVIDER) {
      setRagSettings(prev => ({ ...prev, EMBEDDING_PROVIDER: embeddingProvider }));
    }
    updateEmbeddingRagSettingsRef.current = true;
  }, [embeddingProvider, ragSettings.EMBEDDING_PROVIDER, setRagSettings]);

  // Provider model persistence
  useEffect(() => {
    if (chatProvider && ragSettings.MODEL_CHOICE) {
      setProviderModels(prev => {
        const updated = { ...prev, [chatProvider]: { ...prev[chatProvider], chatModel: ragSettings.MODEL_CHOICE } };
        saveProviderModels(updated);
        return updated;
      });
    }
  }, [ragSettings.MODEL_CHOICE, chatProvider]);

  useEffect(() => {
    if (embeddingProvider && ragSettings.EMBEDDING_MODEL) {
      setProviderModels(prev => {
        const updated = { ...prev, [embeddingProvider]: { ...prev[embeddingProvider], embeddingModel: ragSettings.EMBEDDING_MODEL } };
        saveProviderModels(updated);
        return updated;
      });
    }
  }, [ragSettings.EMBEDDING_MODEL, embeddingProvider]);

  // Connection testing on page load
  useEffect(() => {
    if (!hasRunInitialTestRef.current && (ragSettings.LLM_PROVIDER === 'ollama' || embeddingProvider === 'ollama') && Object.keys(ragSettings).length > 0) {
      hasRunInitialTestRef.current = true;
      if (llmInstanceConfig.url) {
        setTimeout(() => ollama.manualTestConnection(llmInstanceConfig.url, ollama.setLLMStatus, llmInstanceConfig.name || 'LLM Instance', 'chat', { suppressToast: true }), 1000);
      }
      if (embeddingInstanceConfig.url && embeddingInstanceConfig.url !== llmInstanceConfig.url) {
        setTimeout(() => ollama.manualTestConnection(embeddingInstanceConfig.url, ollama.setEmbeddingStatus, embeddingInstanceConfig.name || 'Embedding Instance', 'embedding', { suppressToast: true }), 1500);
      }
      setTimeout(() => ollama.fetchOllamaMetrics(), 2000);
    }
  }, [ragSettings.LLM_PROVIDER, embeddingProvider, llmInstanceConfig, embeddingInstanceConfig, ollama, ragSettings]);

  // Alert Resolution Logic
  const getProviderStatus = (pKey: string) => {
    if (pKey === 'ollama') {
      if (ollama.ollamaManualConfirmed || ollama.llmStatus.online || ollama.embeddingStatus.online) return 'configured';
      return ollama.ollamaServerStatus === 'online' ? 'partial' : 'missing';
    }
    const hasKey = auth.apiCredentials[pKey.toUpperCase() + '_API_KEY'];
    if (!hasKey) return 'missing';
    return auth.providerConnectionStatus[pKey]?.connected ? 'configured' : 'missing';
  };

  const activeP = activeSelection === 'chat' ? chatProvider : embeddingProvider;
  const status = getProviderStatus(activeP);
  let providerAlertMessage = null;
  let providerAlertClassName = '';

  if (activeP === 'ollama') {
    if (ollama.ollamaServerStatus === 'offline') {
      providerAlertMessage = 'Local Ollama service is not running.';
      providerAlertClassName = providerErrorAlertStyle;
    } else if (status === 'partial') {
      providerAlertMessage = 'Detected local Ollama. Test connection to confirm models.';
      providerAlertClassName = providerWarningAlertStyle;
    }
  } else if (status === 'missing') {
    providerAlertMessage = `${providerDisplayNames[activeP] || activeP} API key not configured.`;
    providerAlertClassName = providerMissingAlertStyle;
  }

  // Field definitions (Config-Driven)
  const crawlingSettingsFields = [
    { key: 'CRAWL_BATCH_SIZE', type: 'number', label: 'Batch Size', min: 10, max: 100, default: 50 },
    { key: 'CRAWL_MAX_CONCURRENT', type: 'number', label: 'Max Concurrent', min: 1, max: 20, default: 10 },
    { key: 'CRAWL_PAGE_TIMEOUT', type: 'number', label: 'Page Timeout (ms)', min: 5000, max: 120000, default: 60000 },
    { key: 'CRAWL_DELAY_BEFORE_HTML', type: 'number', label: 'Render Delay (s)', min: 0.1, max: 5, default: 0.5, step: 0.1 },
    { key: 'CRAWL_WAIT_STRATEGY', label: 'Wait Strategy', type: 'select', options: [{ value: 'domcontentloaded', label: 'DOM Loaded' }, { value: 'networkidle', label: 'Network Idle' }, { value: 'load', label: 'Full Load' }] },
    { key: 'RAG_CONTEXTUAL_WINDOW', type: 'number', label: 'Context Window (chars)', min: 1000, max: 100000, default: 20000 },
    { key: 'RAG_CONTEXTUAL_PROMPT', type: 'textarea', label: 'Context Prompt' }
  ];

  const storageSettingsFields = [
    { key: 'DOCUMENT_STORAGE_BATCH_SIZE', type: 'number', label: 'Doc Batch Size', min: 10, max: 100, default: 50 },
    { key: 'EMBEDDING_BATCH_SIZE', type: 'number', label: 'Embedding Batch Size', min: 20, max: 200, default: 100 },
    { key: 'CODE_SUMMARY_MAX_WORKERS', type: 'number', label: 'Code Workers', min: 1, max: 10, default: 3 },
    { key: 'MEMORY_THRESHOLD_PERCENT', type: 'number', label: 'Memory Threshold (%)', min: 50, max: 95, default: 85 },
    { key: 'DISPATCHER_CHECK_INTERVAL', type: 'number', label: 'Check Interval (ms)', min: 100, max: 5000, default: 1000 }
  ];

  const coreModelFields = [
    { key: 'MODEL_CHOICE', label: 'Chat Model', type: 'text' },
    { key: 'EMBEDDING_MODEL', label: 'Embedding Model', type: 'text' },
    { key: 'LLM_BASE_URL', label: 'LLM Base URL', type: 'text' },
    { key: 'OLLAMA_EMBEDDING_URL', label: 'Embedding URL', type: 'text' }
  ];

  return {
    saving, setSaving,
    showCrawlingSettings, setShowCrawlingSettings,
    showStorageSettings, setShowStorageSettings,
    showModelDiscoveryModal, setShowModelDiscoveryModal,
    showOllamaConfig, setShowOllamaConfig,
    ...ollama,
    ...auth,
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
    shouldShowProviderAlert: !!providerAlertMessage,
    providerAlertClassName,
    providerAlertMessage,
    crawlingSettingsFields, storageSettingsFields, coreModelFields,
    getProviderStatus,
    showToast,
    getDisplayedChatModel,
    getDisplayedEmbeddingModel,
    getModelPlaceholder,
    getEmbeddingPlaceholder
  };
};
