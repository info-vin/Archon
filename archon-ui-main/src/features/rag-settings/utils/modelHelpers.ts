import { ProviderModelMap, ProviderKey, RagSettingsType } from '../types';
import { PROVIDER_MODELS_KEY, getDefaultModels } from '../constants';

export const saveProviderModels = (providerModels: ProviderModelMap): void => {
  try {
    localStorage.setItem(PROVIDER_MODELS_KEY, JSON.stringify(providerModels));
  } catch { /* Ignore */ }
};

export const loadProviderModels = (): ProviderModelMap => {
  try {
    const saved = localStorage.getItem(PROVIDER_MODELS_KEY);
    if (saved) return JSON.parse(saved);
  } catch { /* Ignore */ }

  const providers: ProviderKey[] = ['openai', 'google', 'openrouter', 'ollama', 'anthropic', 'grok'];
  const defaultModels: ProviderModelMap = {} as ProviderModelMap;
  providers.forEach(p => { defaultModels[p] = getDefaultModels(p); });
  return defaultModels;
};

export const normalizeBaseUrl = (url?: string | null): string | null => {
  if (!url) return null;
  const trimmed = url.trim();
  if (!trimmed) return null;
  let normalized = trimmed.replace(/\/+$/, '');
  normalized = normalized.replace(/\/v1$/i, '');
  return normalized || null;
};

export const isProviderKey = (value: unknown): value is ProviderKey =>
  typeof value === 'string' && ['openai', 'google', 'openrouter', 'ollama', 'anthropic', 'grok'].includes(value);

// UI Formatting Helpers (Restored with correct logic matching original giant Hook)
export const getDisplayedChatModel = (provider: ProviderKey | RagSettingsType, settings?: RagSettingsType, models?: ProviderModelMap) => {
  // Overload: handle (settings) or (provider, settings, models)
  const isSettings = (val: any): val is RagSettingsType => typeof val === 'object' && 'MODEL_CHOICE' in val;
  
  if (isSettings(provider)) {
    return provider.MODEL_CHOICE || 'Not set';
  }
  
  const pKey = provider as ProviderKey;
  if (settings && pKey === settings.LLM_PROVIDER) return settings.MODEL_CHOICE || 'Not set';
  return models?.[pKey]?.chatModel || getDefaultModels(pKey).chatModel;
};

export const getDisplayedEmbeddingModel = (provider: ProviderKey | RagSettingsType, settings?: RagSettingsType, models?: ProviderModelMap) => {
  const isSettings = (val: any): val is RagSettingsType => typeof val === 'object' && 'EMBEDDING_MODEL' in val;
  
  if (isSettings(provider)) {
    return provider.EMBEDDING_MODEL || 'Not set';
  }
  
  const pKey = provider as ProviderKey;
  if (settings && pKey === settings.EMBEDDING_PROVIDER) return settings.EMBEDDING_MODEL || 'Not set';
  return models?.[pKey]?.embeddingModel || getDefaultModels(pKey).embeddingModel;
};

export const getModelPlaceholder = (provider: ProviderKey) => `e.g. ${getDefaultModels(provider).chatModel}`;
export const getEmbeddingPlaceholder = (provider: ProviderKey) => `e.g. ${getDefaultModels(provider).embeddingModel}`;
