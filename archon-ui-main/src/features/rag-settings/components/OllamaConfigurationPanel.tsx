import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { OllamaInstance } from '@/services/credentialsService';
import OllamaModelDiscoveryModal from './OllamaModelDiscoveryModal';
import { useOllamaInstances } from '../hooks/useOllamaInstances';
import { OllamaInstanceCard } from './OllamaInstanceCard';

interface OllamaConfigurationPanelProps {
  isVisible: boolean;
  onConfigChange: (instances: OllamaInstance[]) => void;
  className?: string;
  separateHosts?: boolean;
}

const OllamaConfigurationPanel: React.FC<OllamaConfigurationPanelProps> = ({
  isVisible,
  onConfigChange,
  className = '',
  separateHosts = false
}) => {
  const {
    instances, testingConnections,
    showAddInstance, setShowAddInstance,
    newInstanceUrl, setNewInstanceUrl,
    newInstanceName, setNewInstanceName,
    newInstanceType, setNewInstanceType,
    tempUrls,
    handleTestConnection, handleAddInstance, handleRemoveInstance,
    handleUrlChange, handleUrlBlur, handleUpdateInstance,
    loadInstances
  } = useOllamaInstances(onConfigChange, separateHosts);

  const [showModelDiscoveryModal, setShowModelDiscoveryModal] = useState(false);
  const [selectedChatModel, setSelectedChatModel] = useState<string | null>(null);
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState<string | null>(null);

  // Load saved models on mount
  useEffect(() => {
    try {
      const savedChat = localStorage.getItem('rag_llm_model');
      const savedEmbedding = localStorage.getItem('rag_embedding_model');
      if (savedChat) setSelectedChatModel(savedChat);
      if (savedEmbedding) setSelectedEmbeddingModel(savedEmbedding);
    } catch (e) {
      console.warn('Failed to load saved model preferences:', e);
    }
  }, []);

  if (!isVisible) return null;

  return (
    <Card accentColor="green" className={cn("mt-4 space-y-4", className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Ollama Configuration</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">Configure Ollama instances for distributed processing</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowModelDiscoveryModal(true)}
            disabled={instances.filter(inst => inst.isEnabled).length === 0}
            className="text-xs"
          >
            {selectedChatModel || selectedEmbeddingModel ? 'Change Models' : 'Select Models'}
          </Button>
          <Badge variant="outline" color="gray" className="text-xs">
            {instances.filter(inst => inst.isEnabled).length} Active
          </Badge>
          {(selectedChatModel || selectedEmbeddingModel) && (
            <div className="flex gap-1">
              {selectedChatModel && <Badge variant="solid" color="blue" className="text-xs">Chat: {selectedChatModel.split(':')[0]}</Badge>}
              {selectedEmbeddingModel && <Badge variant="solid" color="purple" className="text-xs">Embed: {selectedEmbeddingModel.split(':')[0]}</Badge>}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {instances.map((instance) => (
          <OllamaInstanceCard
            key={instance.id}
            instance={instance}
            tempUrl={tempUrls[instance.id]}
            isTesting={testingConnections.has(instance.id)}
            instancesCount={instances.length}
            separateHosts={separateHosts}
            onUrlChange={handleUrlChange}
            onUrlBlur={handleUrlBlur}
            onTest={handleTestConnection}
            onSetPrimary={(id) => handleUpdateInstance(id, { isPrimary: true })}
            onToggle={(id) => handleUpdateInstance(id, { isEnabled: !instance.isEnabled })}
            onRemove={handleRemoveInstance}
          />
        ))}
      </div>

      {showAddInstance ? (
        <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div className="space-y-3">
            <h4 className="font-medium text-blue-900 dark:text-blue-100">Add New Ollama Instance</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input placeholder="Instance Name" value={newInstanceName} onChange={e => setNewInstanceName(e.target.value)} />
              <Input placeholder="http://host.docker.internal:11434" value={newInstanceUrl} onChange={e => setNewInstanceUrl(e.target.value)} />
            </div>
            {separateHosts && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-blue-900 dark:text-blue-100">Instance Type</label>
                <div className="flex gap-2">
                  <Button variant={newInstanceType === 'chat' ? 'primary' : 'outline'} size="sm" onClick={() => setNewInstanceType('chat')} className={newInstanceType === 'chat' ? 'bg-blue-600 text-white' : 'text-blue-600 border-blue-600'}>LLM Chat</Button>
                  <Button variant={newInstanceType === 'embedding' ? 'primary' : 'outline'} size="sm" onClick={() => setNewInstanceType('embedding')} className={newInstanceType === 'embedding' ? 'bg-blue-600 text-white' : 'text-blue-600 border-blue-600'}>Embedding</Button>
                </div>
              </div>
            )}
            <div className="flex gap-2">
              <Button size="sm" onClick={handleAddInstance} className="bg-blue-600 hover:bg-blue-700">Add Instance</Button>
              <Button variant="outline" size="sm" onClick={() => { setShowAddInstance(false); setNewInstanceUrl(''); setNewInstanceName(''); }}>Cancel</Button>
            </div>
          </div>
        </Card>
      ) : (
        <Button variant="outline" size="sm" onClick={() => setShowAddInstance(true)} className="w-full border-dashed">Add Ollama Instance</Button>
      )}

      {showModelDiscoveryModal && (
        <OllamaModelDiscoveryModal
          isOpen={showModelDiscoveryModal}
          onClose={() => setShowModelDiscoveryModal(false)}
          instances={instances.map(inst => ({
            ...inst,
            instanceType: inst.instanceType || 'both',
            healthStatus: {
              isHealthy: inst.isHealthy ?? false,
              lastChecked: inst.lastHealthCheck ? new Date(inst.lastHealthCheck) : new Date(),
              responseTimeMs: inst.responseTimeMs
            }
          }))}
          initialChatModel={selectedChatModel || undefined}
          initialEmbeddingModel={selectedEmbeddingModel || undefined}
          onSelectModels={(selection) => {
            if (selection.chatModel) setSelectedChatModel(selection.chatModel);
            if (selection.embeddingModel) setSelectedEmbeddingModel(selection.embeddingModel);
            setShowModelDiscoveryModal(false);
            loadInstances();
          }}
        />
      )}
    </Card>
  );
};

export default OllamaConfigurationPanel;
