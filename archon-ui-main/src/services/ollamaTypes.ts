// Type definitions for Ollama API responses

export interface OllamaModel {
  name: string;
  tag: string;
  size: number;
  digest: string;
  capabilities: ('chat' | 'embedding')[];
  embedding_dimensions?: number;
  parameters?: {
    family?: string;
    parameter_size?: string;
    quantization?: string;
    parameter_count?: string;
    format?: string;
  };
  instance_url: string;
  last_updated?: string;
  // Real API data from /api/show endpoint
  context_window?: number;
  architecture?: string;
  block_count?: number;
  attention_heads?: number;
  format?: string;
  parent_model?: string;
}

export interface ModelDiscoveryResponse {
  total_models: number;
  chat_models: Array<{
    name: string;
    instance_url: string;
    size: number;
    parameters?: {
      family?: string;
      parameter_size?: string;
      quantization?: string;
      parameter_count?: string;
      format?: string;
    };
    // Real API data from /api/show
    context_window?: number;
    architecture?: string;
    block_count?: number;
    attention_heads?: number;
    format?: string;
    parent_model?: string;
    capabilities?: string[];
  }>;
  embedding_models: Array<{
    name: string;
    instance_url: string;
    dimensions?: number;
    size: number;
    parameters?: {
      family?: string;
      parameter_size?: string;
      quantization?: string;
      parameter_count?: string;
      format?: string;
    };
    // Real API data from /api/show
    architecture?: string;
    format?: string;
    parent_model?: string;
    capabilities?: string[];
  }>;
  host_status: Record<string, {
    status: 'online' | 'error';
    error?: string;
    models_count?: number;
    instance_url?: string;
  }>;
  discovery_errors: string[];
  unique_model_names: string[];
}

export interface InstanceHealthResponse {
  summary: {
    total_instances: number;
    healthy_instances: number;
    unhealthy_instances: number;
    average_response_time_ms?: number;
  };
  instance_status: Record<string, {
    is_healthy: boolean;
    response_time_ms?: number;
    models_available?: number;
    error_message?: string;
    last_checked?: string;
  }>;
  timestamp: string;
}

export interface InstanceValidationResponse {
  is_valid: boolean;
  instance_url: string;
  response_time_ms?: number;
  models_available: number;
  error_message?: string;
  capabilities: {
    total_models?: number;
    chat_models?: string[];
    embedding_models?: string[];
    supported_dimensions?: number[];
    error?: string;
  };
  health_status: Record<string, HealthStatus>;
}

export interface HealthStatus {
  is_healthy: boolean;
  response_time_ms?: number;
  models_available?: number;
  error_message?: string;
  last_checked?: string;
}

export interface EmbeddingRouteResponse {
  target_column: string;
  model_name: string;
  instance_url: string;
  dimensions: number;
  confidence: number;
  fallback_applied: boolean;
  routing_strategy: string;
  performance_score?: number;
}

export interface EmbeddingRoutesResponse {
  total_routes: number;
  routes: Array<{
    model_name: string;
    instance_url: string;
    dimensions: number;
    column_name: string;
    performance_score: number;
    index_type: string;
  }>;
  dimension_analysis: Record<string, {
    count: number;
    models: string[];
    avg_performance: number;
  }>;
  routing_statistics: Record<string, RoutingStatistics>;
}

export interface RoutingStatistics {
  [key: string]: number | string | string[];
}

// Request interfaces
export interface ModelDiscoveryOptions {
  instanceUrls: string[];
  includeCapabilities?: boolean;
}

export interface InstanceValidationOptions {
  instanceUrl: string;
  instanceType?: 'chat' | 'embedding' | 'both';
  timeoutSeconds?: number;
}

export interface EmbeddingRouteOptions {
  modelName: string;
  instanceUrl: string;
  textSample?: string;
}
