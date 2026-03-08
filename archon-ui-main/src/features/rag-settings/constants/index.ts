import { ProviderKey, ProviderModels } from '../types';

export const EMBEDDING_CAPABLE_PROVIDERS: ProviderKey[] = ['openai', 'google', 'ollama'];

export const PROVIDER_MODELS_KEY = 'archon_provider_models';

export const getDefaultModels = (provider: ProviderKey): ProviderModels => {
  const chatDefaults: Record<ProviderKey, string> = {
    openai: 'gpt-4o-mini',
    anthropic: 'claude-3-5-sonnet-20241022',
    google: 'gemini-1.5-flash',
    grok: 'grok-3-mini',
    openrouter: 'openai/gpt-4o-mini',
    ollama: 'llama3:8b'
  };

  const embeddingDefaults: Record<ProviderKey, string> = {
    openai: 'text-embedding-3-small',
    anthropic: 'text-embedding-3-small',
    google: 'gemini-embedding-001',
    grok: 'text-embedding-3-small',
    openrouter: 'text-embedding-3-small',
    ollama: 'nomic-embed-text'
  };

  return {
    chatModel: chatDefaults[provider],
    embeddingModel: embeddingDefaults[provider]
  };
};

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

export const DEFAULT_OLLAMA_URL = 'http://host.docker.internal:11434/v1';

export const PROVIDER_CREDENTIAL_KEYS = [
  'OPENAI_API_KEY',
  'GOOGLE_API_KEY',
  'GEMINI_API_KEY',
  'ANTHROPIC_API_KEY',
  'OPENROUTER_API_KEY',
  'GROK_API_KEY',
] as const;

export const CREDENTIAL_PROVIDER_MAP: Record<string, ProviderKey> = {
  OPENAI_API_KEY: 'openai',
  GOOGLE_API_KEY: 'google',
  GEMINI_API_KEY: 'google',
  ANTHROPIC_API_KEY: 'anthropic',
  OPENROUTER_API_KEY: 'openrouter',
  GROK_API_KEY: 'grok',
};
