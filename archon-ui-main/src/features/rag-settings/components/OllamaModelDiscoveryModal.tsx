import React from 'react';
import { 
  X, Search, Activity, Database, Server,
  Loader, MessageCircle, Layers, HardDrive
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPortal } from 'react-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import type { OllamaInstance } from '@/features/rag-settings/types/OllamaTypes';
import { useOllamaDiscovery, EnrichedModel } from '../hooks/useOllamaDiscovery';

interface OllamaModelDiscoveryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectModels: (selection: { chatModel?: string; embeddingModel?: string }) => void;
  instances: OllamaInstance[];
  initialChatModel?: string;
  initialEmbeddingModel?: string;
}

const OllamaModelDiscoveryModal: React.FC<OllamaModelDiscoveryModalProps> = ({
  isOpen, onClose, onSelectModels, instances, initialChatModel, initialEmbeddingModel
}) => {
  const {
    loading, hasCache, testingModels,
    selectionState, setSelectionState,
    filteredAndSortedModels,
    discoverModels, testModelCapabilities
  } = useOllamaDiscovery(isOpen, instances, initialChatModel, initialEmbeddingModel);

  if (!isOpen) return null;

  const handleModelSelect = (model: EnrichedModel, type: 'chat' | 'embedding') => {
    setSelectionState(prev => ({ ...prev, [type === 'chat' ? 'selectedChatModel' : 'selectedEmbeddingModel']: model.name }));
  };

  const handleApplySelection = () => {
    onSelectModels({ 
      chatModel: selectionState.selectedChatModel || undefined, 
      embeddingModel: selectionState.selectedEmbeddingModel || undefined 
    });
    onClose();
  };

  const modalContent = (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={(e) => e.target === e.currentTarget && onClose()}>
        <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="w-full max-w-4xl max-h-[85vh] mx-4 bg-white dark:bg-gray-900 rounded-xl shadow-2xl overflow-hidden flex flex-col">
          <div className="border-b border-gray-200 dark:border-gray-700 p-6 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2"><Database className="w-6 h-6 text-green-500" />Ollama Model Discovery</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Discover models across instances {hasCache && <span className="text-green-600">(Cached)</span>}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}><X className="w-5 h-5" /></Button>
          </div>
          <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex flex-col md:flex-row gap-4">
            <Input type="text" placeholder="Search..." value={selectionState.filterText} onChange={e => setSelectionState(p => ({ ...p, filterText: e.target.value }))} icon={<Search className="w-4 h-4" />} className="flex-1" />
            <div className="flex gap-2">
              <Button variant={selectionState.showOnlyChat ? "primary" : "outline"} size="sm" onClick={() => setSelectionState(p => ({ ...p, showOnlyChat: !p.showOnlyChat, showOnlyEmbedding: false }))}><MessageCircle className="w-4 h-4 mr-1" />Chat</Button>
              <Button variant={selectionState.showOnlyEmbedding ? "primary" : "outline"} size="sm" onClick={() => setSelectionState(p => ({ ...p, showOnlyEmbedding: !p.showOnlyEmbedding, showOnlyChat: false }))}><Layers className="w-4 h-4 mr-1" />Embedding</Button>
              <Button variant="outline" size="sm" onClick={() => discoverModels(true)} disabled={loading}>{loading ? <Loader className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}Refresh</Button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            {loading ? <div className="text-center py-12"><Loader className="w-12 h-12 animate-spin mx-auto text-green-500" /></div> : (
              <div className="grid gap-4">
                {filteredAndSortedModels.map(model => (
                  <Card key={`${model.name}@${model.instance_url}`} className={`p-4 ${selectionState.selectedChatModel === model.name || selectionState.selectedEmbeddingModel === model.name ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : ''}`}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="font-semibold text-gray-900 dark:text-white">{model.name}</h4>
                          <div className="flex gap-1">
                            {model.capabilities.includes('chat') && <Badge variant="solid" className="bg-blue-100 text-blue-800 text-xs">Chat</Badge>}
                            {model.capabilities.includes('embedding') && <Badge variant="solid" className="bg-purple-100 text-purple-800 text-xs">{model.embedding_dimensions}D</Badge>}
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-500 uppercase font-black">
                          <span className="flex items-center gap-1"><Server className="w-3 h-3" />{model.instanceName}</span>
                          <span className="flex items-center gap-1"><HardDrive className="w-3 h-3" />{(model.size / (1024 ** 3)).toFixed(1)} GB</span>
                        </div>
                      </div>
                      <div className="flex flex-col gap-2">
                        <div className="flex gap-2">
                          {model.capabilities.includes('chat') && <Button size="sm" variant={selectionState.selectedChatModel === model.name ? "primary" : "outline"} onClick={() => handleModelSelect(model, 'chat')} className="text-[10px] h-8 px-3">Chat</Button>}
                          {model.capabilities.includes('embedding') && <Button size="sm" variant={selectionState.selectedEmbeddingModel === model.name ? "primary" : "outline"} onClick={() => handleModelSelect(model, 'embedding')} className="text-[10px] h-8 px-3">Embed</Button>}
                        </div>
                        <Button size="sm" variant="ghost" onClick={() => testModelCapabilities(model)} disabled={testingModels.has(`${model.name}@${model.instance_url}`)} className="text-[10px] h-8">Test Model</Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
          <div className="border-t border-gray-200 dark:border-gray-700 p-6 flex justify-between items-center bg-gray-50 dark:bg-slate-950/50">
            <div className="text-xs font-bold text-gray-500 uppercase tracking-tighter">
              {selectionState.selectedChatModel && <span className="mr-4 text-indigo-600">LLM: {selectionState.selectedChatModel}</span>}
              {selectionState.selectedEmbeddingModel && <span className="text-purple-600">EMB: {selectionState.selectedEmbeddingModel}</span>}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>Cancel</Button>
              <Button onClick={handleApplySelection} disabled={!selectionState.selectedChatModel && !selectionState.selectedEmbeddingModel} className="bg-indigo-600 text-white font-black px-8">Apply Selection</Button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
  return createPortal(modalContent, document.body);
};

export default OllamaModelDiscoveryModal;
