export type ProviderKey = 'openai' | 'google' | 'ollama' | 'anthropic' | 'grok' | 'openrouter';

export interface ProviderModels {
  chatModel: string;
  embeddingModel: string;
}

export type ProviderModelMap = Record<ProviderKey, ProviderModels>;

export const PROVIDER_CREDENTIAL_KEYS = [
  'OPENAI_API_KEY',
  'GOOGLE_API_KEY',
  'GEMINI_API_KEY',
  'ANTHROPIC_API_KEY',
  'OPENROUTER_API_KEY',
  'GROK_API_KEY',
] as const;

export type ProviderCredentialKey = typeof PROVIDER_CREDENTIAL_KEYS[number];

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
  CRAWL_BATCH_SIZE?: number;
  CRAWL_MAX_CONCURRENT?: number;
  CRAWL_WAIT_STRATEGY?: string;
  CRAWL_PAGE_TIMEOUT?: number;
  CRAWL_DELAY_BEFORE_HTML?: number;
  DOCUMENT_STORAGE_BATCH_SIZE?: number;
  EMBEDDING_BATCH_SIZE?: number;
  DELETE_BATCH_SIZE?: number;
  ENABLE_PARALLEL_BATCHES?: boolean;
  MEMORY_THRESHOLD_PERCENT?: number;
  DISPATCHER_CHECK_INTERVAL?: number;
  CODE_EXTRACTION_BATCH_SIZE?: number;
  CODE_SUMMARY_MAX_WORKERS?: number;
};
