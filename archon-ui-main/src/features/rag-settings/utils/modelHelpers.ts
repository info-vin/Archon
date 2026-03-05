import { ProviderKey } from '../hooks/useRagSettingsData';

export function getDisplayedChatModel(ragSettings: any): string {
  if (ragSettings.MODEL_CHOICE) return ragSettings.MODEL_CHOICE;
  switch (ragSettings.LLM_PROVIDER) {
    case 'openai': return 'gpt-4o-mini';
    case 'anthropic': return 'claude-3-5-sonnet-20241022';
    case 'google': return 'gemini-1.5-flash';
    default: return 'gpt-4o-mini';
  }
}

export function getDisplayedEmbeddingModel(ragSettings: any): string {
  if (ragSettings.EMBEDDING_MODEL) return ragSettings.EMBEDDING_MODEL;
  return 'text-embedding-3-small';
}

export function getModelPlaceholder(provider: ProviderKey): string {
  switch (provider) {
    case 'openai': return 'e.g., gpt-4o-mini';
    case 'anthropic': return 'e.g., claude-3-5-sonnet-20241022';
    case 'google': return 'e.g., gemini-1.5-flash';
    case 'ollama': return 'e.g., llama3';
    default: return 'e.g., model-name';
  }
}

export function getEmbeddingPlaceholder(_provider: ProviderKey): string {
  return 'Default: text-embedding-3-small';
}
