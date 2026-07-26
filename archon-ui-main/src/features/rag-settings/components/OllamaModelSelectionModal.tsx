import { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { X, Search, RotateCcw, Zap } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/features/shared/hooks/useToast';
import { callAPIWithETag } from '@/features/shared/api/apiClient';
import { OllamaModelCard } from './shared/OllamaModelCard';
import { ModelInfo } from '../types/ModelInterfaces';
import { useOllamaModelFilter } from '../hooks/useOllamaModelFilter';

type ApiOllamaModel = {
  name: string;
  size: number;
  parameters?: string | {
    family?: string;
    parameter_size?: string;
    quantization?: string;
    format?: string;
  };
  capabilities?: string[];
  context_window?: number;
  custom_context_length?: number;
  base_context_length?: number;
  max_context_length?: number;
  architecture?: string;
  format?: string;
  parent_model?: string;
  dimensions?: number;
  embedding_dimensions?: number;
  block_count?: number;
  attention_heads?: number;
  instance_url?: string;
};

interface OllamaModelSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  instances: Array<{ name: string; url: string }>;
  currentModel?: string;
  modelType: 'chat' | 'embedding';
  onSelectModel: (modelName: string) => void;
  selectedInstanceUrl: string;
}

export const OllamaModelSelectionModal: React.FC<OllamaModelSelectionModalProps> = ({
  isOpen, onClose, instances, currentModel, modelType, onSelectModel, selectedInstanceUrl
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModel, setSelectedModel] = useState<string>(currentModel || '');
  const [compatibilityFilter, setCompatibilityFilter] = useState<'all' | 'full' | 'partial' | 'limited'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'context' | 'performance'>('name');
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [loadedFromCache, setLoadedFromCache] = useState(false);
  const [cacheTimestamp, setCacheTimestamp] = useState<string | null>(null);
  const { showToast } = useToast();

  const cacheKey = `ollama_models_${selectedInstanceUrl}_${modelType}`;
  const { filteredModels } = useOllamaModelFilter(models, searchTerm, compatibilityFilter, sortBy, modelType, selectedInstanceUrl);

  const getCompatibilityFeatures = (compatibility: 'full' | 'partial' | 'limited'): string[] => {
    switch (compatibility) {
      case 'full': return ['Real-time streaming', 'Function calling', 'JSON mode', 'Tool integration', 'Advanced prompting'];
      case 'partial': return ['Basic streaming', 'Standard prompting', 'Text generation'];
      case 'limited': return ['Basic functionality only'];
      default: return [];
    }
  };

  const getCompatibilityLimitations = (compatibility: 'full' | 'partial' | 'limited'): string[] => {
    switch (compatibility) {
      case 'full': return [];
      case 'partial': return ['Limited advanced features', 'May require specific prompting'];
      case 'limited': return ['Basic functionality only', 'Limited feature support', 'May have performance constraints'];
      default: return [];
    }
  };

  const loadModels = useCallback(async (forceRefresh: boolean = false) => {
    try {
      setLoading(true);
      if (forceRefresh) sessionStorage.removeItem(cacheKey);
      const cachedData = sessionStorage.getItem(cacheKey);
      if (cachedData && !forceRefresh) {
        const parsed = JSON.parse(cachedData);
        if (Date.now() - parsed.timestamp < 300000) {
          setModels(parsed.models);
          setLoadedFromCache(true);
                    // TECH_DEBT: 採用原生 toLocaleTimeString 以維持顯示需求，暫不遷移至 date-fns 以維持效能基線。
          // eslint-disable-next-line no-restricted-syntax
          setCacheTimestamp(new Date(parsed.timestamp).toLocaleTimeString());
          setLoading(false);
          return;
        }
      }
      const instanceUrl = instances.find(i => i.url.replace('/v1', '') === selectedInstanceUrl)?.url || selectedInstanceUrl + '/v1';
      const data = await callAPIWithETag<any>(`/ollama/models?instance_urls=${encodeURIComponent(instanceUrl)}&include_capabilities=true&fetch_details=true`);
      if (data) {
        const getArchonCompatibility = (model: ApiOllamaModel, mType: string): 'full' | 'partial' | 'limited' => {
          if (mType === 'chat') {
            const n = model.name.toLowerCase();
            if (n.includes('llama') || n.includes('mistral') || n.includes('phi') || n.includes('qwen') || n.includes('gemma')) return 'full';
            if (n.includes('codestral') || n.includes('deepseek') || n.includes('aya') || model.size > 53687091200) return 'partial';
            if (model.size < 1073741824) return 'limited';
            return 'partial';
          } else {
            const d = model.dimensions;
            return (d === 768 || d === 1536 || d === 384) ? 'full' : (d && d >= 256 && d <= 4096) ? 'partial' : 'limited';
          }
        };
        const allModels: ModelInfo[] = [];
        (data.chat_models || []).forEach((model: ApiOllamaModel) => {
          const comp = getArchonCompatibility(model, 'chat');
          allModels.push({
            name: model.name, host: selectedInstanceUrl, model_type: 'chat',
            size_mb: model.size ? Math.round(model.size / 1048576) : undefined,
            parameters: model.parameters, capabilities: model.capabilities || ['chat'],
            archon_compatibility: comp, compatibility_features: getCompatibilityFeatures(comp),
            limitations: getCompatibilityLimitations(comp), last_updated: new Date().toISOString(),
            context_window: model.context_window, max_context_length: model.max_context_length,
            base_context_length: model.base_context_length, custom_context_length: model.custom_context_length,
            context_length: model.context_window || model.custom_context_length || model.base_context_length,
            context_info: { current: model.context_window || model.custom_context_length || model.base_context_length, max: model.max_context_length, min: model.base_context_length },
            architecture: model.architecture, format: model.format, parent_model: model.parent_model
          });
        });
        (data.embedding_models || []).forEach((model: ApiOllamaModel) => {
          const comp = getArchonCompatibility(model, 'embedding');
          allModels.push({
            name: model.name, host: selectedInstanceUrl, model_type: 'embedding',
            size_mb: model.size ? Math.round(model.size / 1048576) : undefined,
            embedding_dimensions: model.dimensions, capabilities: model.capabilities || ['embedding'],
            archon_compatibility: comp, compatibility_features: getCompatibilityFeatures(comp),
            limitations: getCompatibilityLimitations(comp), last_updated: new Date().toISOString(),
            context_window: model.context_window, context_length: model.context_window || model.custom_context_length || model.base_context_length,
            context_info: { current: model.context_window || model.custom_context_length || model.base_context_length, max: model.max_context_length, min: model.base_context_length },
            architecture: model.architecture, block_count: model.block_count, attention_heads: model.attention_heads,
            format: model.format, parent_model: model.parent_model, instance_url: selectedInstanceUrl
          });
        });
        setModels(allModels);
        sessionStorage.setItem(cacheKey, JSON.stringify({ models: allModels, timestamp: Date.now() }));
      }
    } catch (_e) {
      showToast('Failed to load models', 'error');
    } finally {
      setLoading(false);
    }
  }, [selectedInstanceUrl, instances, showToast, cacheKey]);

  const refreshModels = async () => {
    sessionStorage.removeItem(cacheKey);
    setLoadedFromCache(false);
    try {
      setRefreshing(true);
      await loadModels(true);
      showToast(`Refreshed models from ${selectedInstanceUrl}`, 'success');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => { if (isOpen) loadModels(); }, [isOpen, loadModels]);

  if (!isOpen) return null;

  return ReactDOM.createPortal(
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-gray-900/95 border border-gray-800 rounded-xl w-full max-w-7xl h-[90vh] flex flex-col overflow-hidden shadow-2xl relative" onClick={e => e.stopPropagation()}>
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-green-500 via-blue-500 to-purple-500"></div>
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div><h2 className="text-xl font-semibold text-white flex items-center"><Zap className="w-5 h-5 text-blue-400 mr-2" />Select Ollama Model</h2><p className="text-sm text-gray-400 mt-1">Choose model for {modelType} from {selectedInstanceUrl}</p></div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={refreshModels} disabled={refreshing} className="text-blue-400 border-blue-400"><RotateCcw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />Refresh</Button>
            <button onClick={onClose} aria-label="Close modal" className="text-gray-400 hover:text-white"><X className="w-6 h-6" /></button>
          </div>
        </div>
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex-1 relative"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" /><input type="text" placeholder="Search models..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white" /></div>
            <div className="flex gap-2"><Button variant={sortBy === 'name' ? 'primary' : 'outline'} size="sm" onClick={() => setSortBy('name')} className="text-white">Name</Button><Button variant={sortBy === 'context' ? 'primary' : 'outline'} size="sm" onClick={() => setSortBy('context')} className="text-white">Context ↓</Button></div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-300 font-bold uppercase tracking-widest text-[10px]">Archon Compatibility:</span>
            <div className="flex gap-2">
              <Button variant={compatibilityFilter === 'all' ? 'primary' : 'outline'} size="sm" onClick={() => setCompatibilityFilter('all')} className="text-white text-[10px]">All</Button>
              <Button variant={compatibilityFilter === 'full' ? 'primary' : 'outline'} size="sm" onClick={() => setCompatibilityFilter('full')} className="text-green-500 border-green-500 text-[10px]">● Full</Button>
              <Button variant={compatibilityFilter === 'partial' ? 'primary' : 'outline'} size="sm" onClick={() => setCompatibilityFilter('partial')} className="text-orange-500 border-orange-500 text-[10px]">◐ Partial</Button>
              <Button variant={compatibilityFilter === 'limited' ? 'primary' : 'outline'} size="sm" onClick={() => setCompatibilityFilter('limited')} className="text-red-500 border-red-500 text-[10px]">◯ Limited</Button>
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? <div className="flex items-center justify-center h-64 text-gray-400">Loading models...</div> : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredModels.map(model => (
                <OllamaModelCard key={`${model.name}-${model.host}`} model={model} isSelected={selectedModel === model.name} onSelect={() => setSelectedModel(model.name)} />
              ))}
            </div>
          )}
        </div>
        <div className="p-6 border-t border-gray-700 flex justify-between items-center bg-gray-900">
          <div className="text-xs text-gray-400">{loadedFromCache && cacheTimestamp && `💾 Cached at ${cacheTimestamp}`}</div>
          <div className="flex gap-2"><Button variant="outline" onClick={onClose}>Cancel</Button><Button onClick={() => { if (selectedModel) { onSelectModel(selectedModel); onClose(); } }} disabled={!selectedModel} className="bg-blue-500 hover:bg-blue-600 px-8">Select Model</Button></div>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default OllamaModelSelectionModal;
