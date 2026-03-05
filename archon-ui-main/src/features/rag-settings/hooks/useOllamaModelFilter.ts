import { useMemo } from 'react';
import { ModelInfo } from '../types/ModelInterfaces';

export const useOllamaModelFilter = (
  models: ModelInfo[],
  searchTerm: string,
  compatibilityFilter: 'all' | 'full' | 'partial' | 'limited',
  sortBy: 'name' | 'context' | 'performance',
  modelType: 'chat' | 'embedding',
  selectedInstanceUrl: string
) => {
  const filteredModels = useMemo(() => {
    const filtered = models.filter(model => {
      if (selectedInstanceUrl && model.host !== selectedInstanceUrl) return false;
      if (modelType === 'chat' && model.model_type !== 'chat') return false;
      if (modelType === 'embedding' && model.model_type !== 'embedding') return false;
      if (searchTerm && !model.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      if (compatibilityFilter !== 'all' && model.archon_compatibility !== compatibilityFilter) return false;
      return true;
    });

    filtered.sort((a, b) => {
      const supportOrder = { 'full': 3, 'partial': 2, 'limited': 1 };
      const aSupportLevel = supportOrder[a.archon_compatibility] || 1;
      const bSupportLevel = supportOrder[b.archon_compatibility] || 1;
      
      if (aSupportLevel !== bSupportLevel) return bSupportLevel - aSupportLevel;

      if (sortBy === 'context') {
        const contextDiff = (b.context_length || 0) - (a.context_length || 0);
        if (contextDiff !== 0) return contextDiff;
      }
      return a.name.localeCompare(b.name);
    });
    return filtered;
  }, [models, searchTerm, compatibilityFilter, sortBy, modelType, selectedInstanceUrl]);

  return { filteredModels };
};
