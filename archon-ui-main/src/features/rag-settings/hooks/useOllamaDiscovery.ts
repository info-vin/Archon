import { useState, useMemo, useCallback, useEffect } from 'react';
import { ollamaService, type OllamaModel } from '@/services/ollamaService';
import type { OllamaInstance, ModelSelectionState } from '@/features/rag-settings/types/OllamaTypes';
import { useToast } from '@/features/shared/hooks/useToast';

export interface EnrichedModel extends OllamaModel {
  instanceName?: string;
  status: 'available' | 'testing' | 'error';
  testResult?: {
    chatWorks: boolean;
    embeddingWorks: boolean;
    dimensions?: number;
  };
}

export const useOllamaDiscovery = (
  isOpen: boolean,
  instances: OllamaInstance[],
  initialChatModel?: string | null,
  initialEmbeddingModel?: string | null
) => {
  const [models, setModels] = useState<EnrichedModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [discoveryComplete, setDiscoveryComplete] = useState(false);
  const [hasCache, setHasCache] = useState(false);
  const [testingModels, setTestingModels] = useState<Set<string>>(new Set());
  const { showToast } = useToast();

  const [selectionState, setSelectionState] = useState<ModelSelectionState>({
    selectedChatModel: initialChatModel || null,
    selectedEmbeddingModel: initialEmbeddingModel || null,
    filterText: '',
    showOnlyEmbedding: false,
    showOnlyChat: false,
    sortBy: 'name'
  });

  const enabledInstanceUrls = useMemo(() => 
    instances.filter(instance => instance.isEnabled).map(instance => instance.baseUrl), 
  [instances]);

  const instanceLookup = useMemo(() => {
    const lookup: Record<string, OllamaInstance> = {};
    instances.forEach(instance => { lookup[instance.baseUrl] = instance; });
    return lookup;
  }, [instances]);

  const cacheKey = useMemo(() => {
    const sortedUrls = [...enabledInstanceUrls].sort();
    return `ollama-models-${sortedUrls.join('|')}`;
  }, [enabledInstanceUrls]);

  const saveModelsToCache = useCallback((modelsToCache: EnrichedModel[]) => {
    try {
      const cacheData = { models: modelsToCache, timestamp: Date.now(), instanceUrls: enabledInstanceUrls };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
      setHasCache(true);
    } catch (e) {
      console.warn('Ollama cache save failed:', e);
    }
  }, [cacheKey, enabledInstanceUrls]);

  const loadModelsFromCache = useCallback(() => {
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const cacheData = JSON.parse(cached);
        const cacheAge = Date.now() - cacheData.timestamp;
        const instanceUrlsMatch = JSON.stringify(cacheData.instanceUrls?.sort()) === JSON.stringify([...enabledInstanceUrls].sort());
        if (cacheAge < 10 * 60 * 1000 && instanceUrlsMatch) {
          setModels(cacheData.models);
          setDiscoveryComplete(true);
          setHasCache(true);
          return true;
        }
      }
    } catch (e) {
      console.warn('Ollama cache load failed:', e);
    }
    return false;
  }, [cacheKey, enabledInstanceUrls]);

  const discoverModels = useCallback(async (forceRefresh: boolean = false) => {
    if (enabledInstanceUrls.length === 0) {
      showToast('No enabled Ollama instances configured', 'error');
      return;
    }
    if (!forceRefresh && loadModelsFromCache()) return;

    setLoading(true);
    try {
      const discoveryResult = await ollamaService.discoverModels({
        instanceUrls: enabledInstanceUrls,
        includeCapabilities: true
      });
      
      const enrichedModels: EnrichedModel[] = [];
      discoveryResult.chat_models.forEach(chatModel => {
        const instance = instanceLookup[chatModel.instance_url];
        enrichedModels.push({
          name: chatModel.name,
          tag: chatModel.name,
          size: chatModel.size,
          digest: '',
          capabilities: ['chat'],
          instance_url: chatModel.instance_url,
          instanceName: instance?.name || 'Unknown',
          status: 'available',
          parameters: chatModel.parameters
        });
      });

      discoveryResult.embedding_models.forEach(embeddingModel => {
        const instance = instanceLookup[embeddingModel.instance_url];
        const existingModel = enrichedModels.find(m => m.name === embeddingModel.name && m.instance_url === embeddingModel.instance_url);
        if (existingModel) {
          existingModel.capabilities.push('embedding');
          existingModel.embedding_dimensions = embeddingModel.dimensions;
        } else {
          enrichedModels.push({
            name: embeddingModel.name,
            tag: embeddingModel.name,
            size: embeddingModel.size,
            digest: '',
            capabilities: ['embedding'],
            embedding_dimensions: embeddingModel.dimensions,
            instance_url: embeddingModel.instance_url,
            instanceName: instance?.name || 'Unknown',
            status: 'available'
          });
        }
      });

      setModels(enrichedModels);
      setDiscoveryComplete(true);
      saveModelsToCache(enrichedModels);
      showToast(`Discovery complete: Found ${discoveryResult.total_models} models`, 'success');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error occurred';
      showToast(`Model discovery failed: ${errorMsg}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [enabledInstanceUrls, instanceLookup, showToast, loadModelsFromCache, saveModelsToCache]);

  const testModelCapabilities = useCallback(async (model: EnrichedModel) => {
    const modelKey = `${model.name}@${model.instance_url}`;
    setTestingModels(prev => new Set(prev).add(modelKey));
    try {
      const capabilities = await ollamaService.getModelCapabilities(model.name, model.instance_url);
      const testResult = {
        chatWorks: capabilities.supports_chat,
        embeddingWorks: capabilities.supports_embedding,
        dimensions: capabilities.embedding_dimensions
      };
      setModels(prev => prev.map(m => m.name === model.name && m.instance_url === model.instance_url ? { ...m, testResult, status: 'available' } : m));
      showToast(`Model ${model.name} tested successfully`, 'success');
    } catch (_err) {
      setModels(prev => prev.map(m => m.name === model.name && m.instance_url === model.instance_url ? { ...m, status: 'error' } : m));
      showToast(`Failed to test ${model.name}`, 'error');
    } finally {
      setTestingModels(prev => { const n = new Set(prev); n.delete(modelKey); return n; });
    }
  }, [showToast]);

  const filteredAndSortedModels = useMemo(() => {
    const filtered = models.filter(model => {
      if (selectionState.filterText && !model.name.toLowerCase().includes(selectionState.filterText.toLowerCase())) return false;
      if (selectionState.showOnlyChat && !model.capabilities.includes('chat')) return false;
      if (selectionState.showOnlyEmbedding && !model.capabilities.includes('embedding')) return false;
      return true;
    });
    filtered.sort((a, b) => {
      switch (selectionState.sortBy) {
        case 'name': return a.name.localeCompare(b.name);
        case 'size': return b.size - a.size;
        case 'instance': return (a.instanceName || '').localeCompare(b.instanceName || '');
        default: return 0;
      }
    });
    return filtered;
  }, [models, selectionState]);

  useEffect(() => {
    if (isOpen && !discoveryComplete && !loading && !hasCache) discoverModels();
  }, [isOpen, discoveryComplete, loading, hasCache, discoverModels]);

  return {
    models, loading, discoveryComplete, hasCache, testingModels,
    selectionState, setSelectionState,
    filteredAndSortedModels,
    discoverModels, testModelCapabilities
  };
};
