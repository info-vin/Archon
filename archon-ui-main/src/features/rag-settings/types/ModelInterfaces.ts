export interface ContextInfo {
  current?: number;
  max?: number;
  min?: number;
}

export interface ModelInfo {
  name: string;
  host: string;
  model_type: 'chat' | 'embedding' | 'multimodal';
  size_mb?: number;
  context_length?: number;
  context_info?: ContextInfo;
  embedding_dimensions?: number;
  parameters?: string | {
    family?: string;
    parameter_size?: string;
    quantization?: string;
    format?: string;
  };
  capabilities: string[];
  archon_compatibility: 'full' | 'partial' | 'limited';
  compatibility_features: string[];
  limitations: string[];
  performance_rating?: 'high' | 'medium' | 'low';
  description?: string;
  last_updated: string;
  // Real API data from /api/show endpoint
  context_window?: number;
  max_context_length?: number;
  base_context_length?: number;
  custom_context_length?: number;
  architecture?: string;
  format?: string;
  parent_model?: string;
  instance_url?: string;
  block_count?: number;
  attention_heads?: number;
}
