/**
 * Ollama Service Client
 * 
 * Provides frontend API client for Ollama model discovery, validation, and health monitoring.
 * Integrates with the enhanced backend Ollama endpoints for multi-instance configurations.
 */

import { callAPIWithETag } from "../features/shared/api/apiClient";

// Type definitions for Ollama API responses imported from ollamaTypes
import type {
  ModelDiscoveryOptions,
  ModelDiscoveryResponse,
  InstanceHealthResponse,
  InstanceValidationOptions,
  InstanceValidationResponse,
  EmbeddingRouteOptions,
  EmbeddingRouteResponse,
  EmbeddingRoutesResponse,
} from "./ollamaTypes";

export * from "./ollamaTypes";


class OllamaService {
  private handleApiError(error: unknown, context: string): Error {
    const errorMessage = error instanceof Error ? error.message : String(error);

    // Check for network errors
    if (
      errorMessage.toLowerCase().includes("network") ||
      errorMessage.includes("fetch") ||
      errorMessage.includes("Failed to fetch")
    ) {
      return new Error(
        `Network error while ${context.toLowerCase()}: ${errorMessage}. ` +
          `Please check your connection and Ollama server status.`,
      );
    }

    // Check for timeout errors
    if (errorMessage.includes("timeout") || errorMessage.includes("AbortError")) {
      return new Error(
        `Timeout error while ${context.toLowerCase()}: The Ollama instance may be slow to respond or unavailable.`
      );
    }

    // Return original error with context
    return new Error(`${context} failed: ${errorMessage}`);
  }

  /**
   * Discover models from multiple Ollama instances
   */
  async discoverModels(options: ModelDiscoveryOptions): Promise<ModelDiscoveryResponse> {
    try {
      if (!options.instanceUrls || options.instanceUrls.length === 0) {
        throw new Error("At least one instance URL is required for model discovery");
      }

      // Build query parameters
      const params = new URLSearchParams();
      options.instanceUrls.forEach(url => {
        params.append('instance_urls', url);
      });
      
      if (options.includeCapabilities !== undefined) {
        params.append('include_capabilities', options.includeCapabilities.toString());
      }

      return await callAPIWithETag<ModelDiscoveryResponse>(`/ollama/models?${params.toString()}`);
    } catch (error) {
      throw this.handleApiError(error, "Model discovery");
    }
  }

  /**
   * Check health status of multiple Ollama instances
   */
  async checkInstanceHealth(instanceUrls: string[], includeModels: boolean = false): Promise<InstanceHealthResponse> {
    try {
      if (!instanceUrls || instanceUrls.length === 0) {
        throw new Error("At least one instance URL is required for health checking");
      }

      // Build query parameters
      const params = new URLSearchParams();
      instanceUrls.forEach(url => {
        params.append('instance_urls', url);
      });
      
      if (includeModels) {
        params.append('include_models', 'true');
      }

      return await callAPIWithETag<InstanceHealthResponse>(`/ollama/instances/health?${params.toString()}`);
    } catch (error) {
      throw this.handleApiError(error, "Instance health checking");
    }
  }

  /**
   * Validate a specific Ollama instance with comprehensive testing
   */
  async validateInstance(options: InstanceValidationOptions): Promise<InstanceValidationResponse> {
    try {
      const requestBody = {
        instance_url: options.instanceUrl,
        instance_type: options.instanceType,
        timeout_seconds: options.timeoutSeconds || 30,
      };

      return await callAPIWithETag<InstanceValidationResponse>("/ollama/validate", {
        method: 'POST',
        body: JSON.stringify(requestBody),
      });
    } catch (error) {
      throw this.handleApiError(error, "Instance validation");
    }
  }

  /**
   * Analyze embedding routing for a specific model and instance
   */
  async analyzeEmbeddingRoute(options: EmbeddingRouteOptions): Promise<EmbeddingRouteResponse> {
    try {
      const requestBody = {
        model_name: options.modelName,
        instance_url: options.instanceUrl,
        text_sample: options.textSample,
      };

      return await callAPIWithETag<EmbeddingRouteResponse>("/ollama/embedding/route", {
        method: 'POST',
        body: JSON.stringify(requestBody),
      });
    } catch (error) {
      throw this.handleApiError(error, "Embedding route analysis");
    }
  }

  /**
   * Get all available embedding routes across multiple instances
   */
  async getEmbeddingRoutes(instanceUrls: string[], sortByPerformance: boolean = true): Promise<EmbeddingRoutesResponse> {
    try {
      if (!instanceUrls || instanceUrls.length === 0) {
        throw new Error("At least one instance URL is required for embedding routes");
      }

      // Build query parameters
      const params = new URLSearchParams();
      instanceUrls.forEach(url => {
        params.append('instance_urls', url);
      });
      
      if (sortByPerformance) {
        params.append('sort_by_performance', 'true');
      }

      return await callAPIWithETag<EmbeddingRoutesResponse>(`/ollama/embedding/routes?${params.toString()}`);
    } catch (error) {
      throw this.handleApiError(error, "Getting embedding routes");
    }
  }

  /**
   * Clear all Ollama-related caches
   */
  async clearCaches(): Promise<{ message: string }> {
    try {
      return await callAPIWithETag<{ message: string }>("/ollama/cache", {
        method: 'DELETE',
      });
    } catch (error) {
      throw this.handleApiError(error, "Cache clearing");
    }
  }

  /**
   * Test connectivity to a single Ollama instance (quick health check) with retry logic
   */
  async testConnection(instanceUrl: string, retryCount = 3): Promise<{ isHealthy: boolean; responseTime?: number; error?: string }> {
    const maxRetries = retryCount;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const startTime = Date.now();
        
        const healthResponse = await this.checkInstanceHealth([instanceUrl], false);
        const responseTime = Date.now() - startTime;
        
        const instanceStatus = healthResponse.instance_status[instanceUrl];
        
        const result = {
          isHealthy: instanceStatus?.is_healthy || false,
          responseTime: instanceStatus?.response_time_ms || responseTime,
          error: instanceStatus?.error_message,
        };

        // If successful, return immediately
        if (result.isHealthy) {
          return result;
        }

        // If not healthy but we got a valid response, store error for potential retry
        lastError = new Error(result.error || 'Instance not available');
        
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
      }

      // If this wasn't the last attempt, wait before retrying
      if (attempt < maxRetries) {
        const delayMs = Math.pow(2, attempt - 1) * 1000; // Exponential backoff: 1s, 2s, 4s
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }

    // All retries failed, return error result
    return {
      isHealthy: false,
      error: lastError?.message || 'Connection failed after retries',
    };
  }

  /**
   * Get model capabilities for a specific model
   */
  async getModelCapabilities(modelName: string, instanceUrl: string): Promise<{
    supports_chat: boolean;
    supports_embedding: boolean;
    embedding_dimensions?: number;
    error?: string;
  }> {
    try {
      // Use the validation endpoint to get capabilities
      const validation = await this.validateInstance({
        instanceUrl,
        instanceType: 'both',
      });

      const capabilities = validation.capabilities;
      const chatModels = capabilities.chat_models || [];
      const embeddingModels = capabilities.embedding_models || [];

      // Find the model in the lists
      const supportsChat = chatModels.includes(modelName);
      const supportsEmbedding = embeddingModels.includes(modelName);

      // For embedding dimensions, we need to use the embedding route analysis
      let embeddingDimensions: number | undefined;
      if (supportsEmbedding) {
        try {
          const route = await this.analyzeEmbeddingRoute({
            modelName,
            instanceUrl,
          });
          embeddingDimensions = route.dimensions;
        } catch {
          // Ignore routing errors, just report basic capability
        }
      }

      return {
        supports_chat: supportsChat,
        supports_embedding: supportsEmbedding,
        embedding_dimensions: embeddingDimensions,
      };
    } catch (error) {
      return {
        supports_chat: false,
        supports_embedding: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }
}

// Export singleton instance
export const ollamaService = new OllamaService();
