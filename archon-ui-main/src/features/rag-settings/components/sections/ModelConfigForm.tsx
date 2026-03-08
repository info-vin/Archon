import React from 'react';
import { Cog } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { ProviderKey, RagSettingsType } from '../../types';

interface ModelConfigFormProps {
  activeSelection: 'chat' | 'embedding';
  chatProvider: ProviderKey;
  embeddingProvider: ProviderKey;
  coreModelFields: any[];
  ragSettings: RagSettingsType;
  setRagSettings: (settings: any) => void;
  showOllamaConfig: boolean;
  setShowOllamaConfig: (val: boolean) => void;
  getDisplayedChatModel: (s: any) => string;
  getDisplayedEmbeddingModel: (s: any) => string;
  getModelPlaceholder: (p: any) => string;
  getEmbeddingPlaceholder: (p: any) => string;
}

export const ModelConfigForm: React.FC<ModelConfigFormProps> = ({
  activeSelection, chatProvider, embeddingProvider,
  coreModelFields, ragSettings, setRagSettings,
  showOllamaConfig, setShowOllamaConfig,
  getDisplayedChatModel, getDisplayedEmbeddingModel,
  getModelPlaceholder, getEmbeddingPlaceholder
}) => {
  return (
    <div className="flex justify-between items-end">
      {/* Context-Aware Model Input */}
      <div className="flex-1 max-w-md grid grid-cols-2 gap-4">
        {coreModelFields.filter(f => 
          activeSelection === 'chat' ? (f.key === 'MODEL_CHOICE') : (f.key === 'EMBEDDING_MODEL')
        ).map(field => {
          const isOllama = activeSelection === 'chat' ? chatProvider === 'ollama' : embeddingProvider === 'ollama';
          if (!isOllama) {
            return (
              <Input
                key={field.key}
                label={field.label}
                value={activeSelection === 'chat' ? getDisplayedChatModel(ragSettings) : getDisplayedEmbeddingModel(ragSettings)}
                onChange={e => setRagSettings({
                  ...ragSettings,
                  [field.key]: e.target.value
                })}
                placeholder={activeSelection === 'chat' ? getModelPlaceholder(chatProvider) : getEmbeddingPlaceholder(embeddingProvider)}
                accentColor={activeSelection === 'chat' ? "green" : "purple"}
              />
            );
          } else {
            const currentModel = activeSelection === 'chat' ? (getDisplayedChatModel(ragSettings) || 'Not selected') : (getDisplayedEmbeddingModel(ragSettings) || 'Not selected');
            return (
              <div key={field.key} className={`p-3 border rounded-lg bg-${activeSelection === 'chat' ? 'green' : 'purple'}-500/5 border-${activeSelection === 'chat' ? 'green' : 'purple'}-500/30`}>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {field.label}
                </label>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Configured via Ollama instance
                </div>
                <div className={`text-xs text-${activeSelection === 'chat' ? 'green' : 'purple'}-400 mt-1`}>
                  Current: {currentModel}
                </div>
              </div>
            );
          }
        })}
      </div>

      {/* Ollama Configuration Gear Icon */}
      {((activeSelection === 'chat' && chatProvider === 'ollama') ||
        (activeSelection === 'embedding' && embeddingProvider === 'ollama')) && (
        <Button
          variant="outline"
          accentColor="green"
          icon={<Cog className={`w-4 h-4 mr-1 transition-transform ${showOllamaConfig ? 'rotate-90' : ''}`} />}
          onClick={() => setShowOllamaConfig(!showOllamaConfig)}
          className="ml-4 h-10 px-4 text-emerald-400 border-emerald-400/30 hover:bg-emerald-500/10"
        >
          {showOllamaConfig ? 'Hide Config' : 'Instance Config'}
        </Button>
      )}
    </div>
  );
};
