import React from 'react';
import { Check, Save, Loader, ChevronDown, ChevronUp, Zap, Database, Cog } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Button as GlowButton } from '@/features/ui/primitives/button';
import { LuBrainCircuit } from 'react-icons/lu';
import { PiDatabaseThin } from 'react-icons/pi';
import OllamaModelDiscoveryModal from './components/OllamaModelDiscoveryModal';
import OllamaModelSelectionModal from './components/OllamaModelSelectionModal';
import { credentialsService } from '@/services/credentialsService';
import { ConfigDrivenInput } from '@/features/admin/components/ConfigDrivenInput';
import { 
  useRagSettingsData, ProviderKey, RagSettingsType, colorStyles, 
  EMBEDDING_CAPABLE_PROVIDERS, getDefaultModels, normalizeBaseUrl
} from './hooks/useRagSettingsData';

interface RAGSettingsProps {
  ragSettings: RagSettingsType;
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void;
}

export const RAGSettings = ({ ragSettings, setRagSettings }: RAGSettingsProps) => {
  const {
    saving, setSaving,
    showCrawlingSettings, setShowCrawlingSettings,
    showStorageSettings, setShowStorageSettings,
    showModelDiscoveryModal, setShowModelDiscoveryModal,
    showOllamaConfig, setShowOllamaConfig,
    llmStatus, setLLMStatus,
    embeddingStatus, setEmbeddingStatus,
    setOllamaManualConfirmed,
    showEditLLMModal, setShowEditLLMModal,
    showEditEmbeddingModal, setShowEditEmbeddingModal,
    showLLMModelSelectionModal, setShowLLMModelSelectionModal,
    showEmbeddingModelSelectionModal, setShowEmbeddingModelSelectionModal,
    providerModels,
    chatProvider, setChatProvider,
    embeddingProvider, setEmbeddingProvider,
    activeSelection, setActiveSelection,
    llmInstanceConfig, setLLMInstanceConfig,
    embeddingInstanceConfig, setEmbeddingInstanceConfig,
    ollamaMetrics, fetchOllamaMetrics,
    showToast, setOllamaServerStatus,
    manualTestConnection, getProviderStatus,
    shouldShowProviderAlert, providerAlertClassName, providerAlertMessage,
    crawlingSettingsFields, storageSettingsFields, coreModelFields
  } = useRagSettingsData(ragSettings, setRagSettings);

  return <Card accentColor="green" className="overflow-hidden p-8">
        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-zinc-400 mb-6">
          Configure Retrieval-Augmented Generation (RAG) strategies for optimal
          knowledge retrieval.
        </p>
        
        {/* LLM Provider Settings Header */}
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
            LLM Provider Settings
          </h2>
        </div>

        {/* Provider Selection Buttons */}
        <div className="flex gap-4 mb-6">
          <GlowButton
            onClick={() => setActiveSelection('chat')}
            variant="ghost"
            className={`min-w-[180px] px-5 py-3 font-semibold text-white dark:text-white
              border border-emerald-400/70 dark:border-emerald-400/40
              bg-black/40 backdrop-blur-md
              shadow-[inset_0_0_16px_rgba(15,118,110,0.38)]
              hover:bg-emerald-500/12 dark:hover:bg-emerald-500/20
              hover:border-emerald-300/80 hover:shadow-[0_0_22px_rgba(16,185,129,0.5)]
              ${(activeSelection === 'chat')
                ? 'shadow-[0_0_25px_rgba(16,185,129,0.5)] ring-2 ring-emerald-400/50'
                : 'shadow-[0_0_15px_rgba(16,185,129,0.25)]'}
            `}
          >
            <span className="flex items-center justify-center gap-2">
              <LuBrainCircuit className="w-4 h-4 text-emerald-300" aria-hidden="true" />
              <span>Chat: {chatProvider}</span>
            </span>
          </GlowButton>
          <GlowButton
            onClick={() => setActiveSelection('embedding')}
            variant="ghost"
            className={`min-w-[180px] px-5 py-3 font-semibold text-white dark:text-white
              border border-purple-400/70 dark:border-purple-400/40
              bg-black/40 backdrop-blur-md
              shadow-[inset_0_0_16px_rgba(109,40,217,0.38)]
              hover:bg-purple-500/12 dark:hover:bg-purple-500/20
              hover:border-purple-300/80 hover:shadow-[0_0_24px_rgba(168,85,247,0.52)]
              ${(activeSelection === 'embedding')
                ? 'shadow-[0_0_26px_rgba(168,85,247,0.55)] ring-2 ring-purple-400/60'
                : 'shadow-[0_0_15px_rgba(168,85,247,0.25)]'}
            `}
          >
            <span className="flex items-center justify-center gap-2">
              <PiDatabaseThin className="w-4 h-4 text-purple-300" aria-hidden="true" />
              <span>Embeddings: {embeddingProvider}</span>
            </span>
          </GlowButton>
        </div>

        {/* Context-Aware Provider Grid */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Select {activeSelection === 'chat' ? 'Chat' : 'Embedding'} Provider
          </label>
          <div className={`grid gap-3 mb-4 ${
            activeSelection === 'chat' ? 'grid-cols-6' : 'grid-cols-3'
          }`}>
            {[
              { key: 'openai', name: 'OpenAI', logo: '/img/OpenAI.png', color: 'green' },
              { key: 'google', name: 'Google', logo: '/img/google-logo.svg', color: 'blue' },
              { key: 'openrouter', name: 'OpenRouter', logo: '/img/OpenRouter.png', color: 'cyan' },
              { key: 'ollama', name: 'Ollama', logo: '/img/Ollama.png', color: 'purple' },
              { key: 'anthropic', name: 'Anthropic', logo: '/img/claude-logo.svg', color: 'orange' },
              { key: 'grok', name: 'Grok', logo: '/img/Grok.png', color: 'yellow' }
            ]
              .filter(provider =>
                activeSelection === 'chat' || EMBEDDING_CAPABLE_PROVIDERS.includes(provider.key as ProviderKey)
              )
              .map(provider => (
              <button
                key={provider.key}
                type="button"
                onClick={() => {
                  const providerKey = provider.key as ProviderKey;

                  if (activeSelection === 'chat') {
                    setChatProvider(providerKey);
                    // Update chat model when switching providers
                    const savedModels = providerModels[providerKey] || getDefaultModels(providerKey);
                    setRagSettings(prev => ({
                      ...prev,
                      MODEL_CHOICE: savedModels.chatModel
                    }));
                  } else {
                    setEmbeddingProvider(providerKey);
                    // Update embedding model when switching providers
                    const savedModels = providerModels[providerKey] || getDefaultModels(providerKey);
                    setRagSettings(prev => ({
                      ...prev,
                      EMBEDDING_MODEL: savedModels.embeddingModel
                    }));
                  }
                }}
                className={`
                  relative p-3 rounded-lg border-2 transition-all duration-200 text-center
                  ${(activeSelection === 'chat' ? chatProvider === provider.key : embeddingProvider === provider.key)
                    ? `${colorStyles[provider.key as ProviderKey]} shadow-[0_0_15px_rgba(34,197,94,0.3)]`
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                  }
                  hover:scale-105 active:scale-95
                `}
              >
                <img
                  src={provider.logo}
                  alt={`${provider.name} logo`}
                  className={`w-8 h-8 mb-1 mx-auto ${
                    provider.key === 'openai' || provider.key === 'grok'
                      ? 'bg-white rounded p-1'
                      : ''
                  }`}
                />
                <div className={`font-medium text-gray-700 dark:text-gray-300 text-center ${
                  provider.key === 'openrouter' ? 'text-xs' : 'text-sm'
                }`}>
                  {provider.name}
                </div>
                {(() => {
                  const status = getProviderStatus(provider.key);

                  if (status === 'configured') {
                    return (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                        <Check className="w-2.5 h-2.5 text-white" />
                      </div>
                    );
                  } else if (status === 'partial') {
                    return (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full" />
                      </div>
                    );
                  } else {
                    return (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                        <div className="w-1.5 h-1.5 bg-white rounded-full" />
                      </div>
                    );
                  }
                })()}
              </button>
            ))}
          </div>
          {shouldShowProviderAlert && (
            <div className={`p-4 border rounded-lg mb-4 ${providerAlertClassName}`}>
              <p className="text-sm">{providerAlertMessage}</p>
            </div>
          )}
          
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
                  return (
                    <div key={field.key} className={`p-3 border rounded-lg bg-${activeSelection === 'chat' ? 'green' : 'purple'}-500/5 border-${activeSelection === 'chat' ? 'green' : 'purple'}-500/30`}>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        {field.label}
                      </label>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        Configured via Ollama instance
                      </div>
                      <div className={`text-xs text-${activeSelection === 'chat' ? 'green' : 'purple'}-400 mt-1`}>
                        Current: {activeSelection === 'chat' ? (getDisplayedChatModel(ragSettings) || 'Not selected') : (getDisplayedEmbeddingModel(ragSettings) || 'Not selected')}
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
                className="whitespace-nowrap ml-4 border-green-500 text-green-400 hover:bg-green-500/10"
                onClick={() => setShowOllamaConfig(!showOllamaConfig)}
              >
                {activeSelection === 'chat' ? 'Config' : 'Config'}
              </Button>
            )}

            {/* Save Settings Button */}
            <Button
              variant="outline"
              accentColor="green"
              icon={saving ? <Loader className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />}
              className="whitespace-nowrap ml-4"
              size="md"
              onClick={async () => {
                try {
                  setSaving(true);

                  // Ensure instance configurations are synced with ragSettings before saving
                  const updatedSettings = {
                    ...ragSettings,
                    LLM_BASE_URL: llmInstanceConfig.url,
                    LLM_INSTANCE_NAME: llmInstanceConfig.name,
                    OLLAMA_EMBEDDING_URL: embeddingInstanceConfig.url,
                    OLLAMA_EMBEDDING_INSTANCE_NAME: embeddingInstanceConfig.name
                  };

                  await credentialsService.updateRagSettings(updatedSettings);

                  // Update local ragSettings state to match what was saved
                  setRagSettings(updatedSettings);

                  showToast('RAG settings saved successfully!', 'success');
                } catch (_err) {
                  // console.error('Failed to save RAG settings:', err);
                  showToast('Failed to save settings', 'error');
                } finally {
                  setSaving(false);
                }
              }}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </div>

          {/* Expandable Ollama Configuration Container */}
          {showOllamaConfig && ((activeSelection === 'chat' && chatProvider === 'ollama') ||
                               (activeSelection === 'embedding' && embeddingProvider === 'ollama')) && (
            <div className="mt-4 p-4 bg-gradient-to-r from-green-500/5 to-green-600/5 border border-green-500/20 rounded-lg shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-white text-lg font-semibold">
                    {activeSelection === 'chat' ? 'LLM Chat Configuration' : 'Embedding Configuration'}
                  </h3>
                  <p className="text-gray-400 text-sm">
                    {activeSelection === 'chat'
                      ? 'Configure Ollama instance for chat completions'
                      : 'Configure Ollama instance for text embeddings'}
                  </p>
                </div>
                <div className={`text-sm font-medium ${
                  (activeSelection === 'chat' ? llmStatus.online : embeddingStatus.online)
                    ? "text-teal-400" : "text-red-400"
                }`}>
                  {(activeSelection === 'chat' ? llmStatus.online : embeddingStatus.online)
                    ? "Online" : "Offline"}
                </div>
              </div>

              {/* Configuration Content */}
              <div className="bg-black/40 rounded-lg p-4 shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
                {activeSelection === 'chat' ? (
                  // Chat Model Configuration
                  <div>
                    {llmInstanceConfig.name && llmInstanceConfig.url ? (
                      <>
                        <div className="mb-3">
                          <div className="text-white font-medium mb-1">{llmInstanceConfig.name}</div>
                          <div className="text-gray-400 text-sm font-mono">{llmInstanceConfig.url}</div>
                        </div>

                        <div className="mb-4">
                          <div className="text-gray-300 text-sm mb-1">Model:</div>
                          <div className="text-white">{getDisplayedChatModel(ragSettings)}</div>
                        </div>

                        <div className="text-gray-400 text-sm mb-4">
                          {llmStatus.checking ? (
                            <Loader className="w-4 h-4 animate-spin inline mr-1" />
                          ) : null}
                          {ollamaMetrics.loading ? 'Loading...' : `${ollamaMetrics.llmInstanceModels?.chat || 0} chat models available`}
                        </div>

                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            accentColor="green"
                            className="text-white border-emerald-400 hover:bg-emerald-500/10"
                            onClick={() => setShowEditLLMModal(true)}
                          >
                            Edit Settings
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            accentColor="green"
                            className="text-white border-emerald-400 hover:bg-emerald-500/10"
                            onClick={async () => {
                              const success = await manualTestConnection(
                                llmInstanceConfig.url,
                                setLLMStatus,
                                llmInstanceConfig.name,
                                'chat'
                              );

                              setOllamaManualConfirmed(success);
                              setOllamaServerStatus(success ? 'online' : 'offline');
                            }}
                            disabled={llmStatus.checking}
                          >
                            {llmStatus.checking ? 'Testing...' : 'Test Connection'}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            accentColor="green"
                            className="text-white border-emerald-400 hover:bg-emerald-500/10"
                            onClick={() => setShowLLMModelSelectionModal(true)}
                          >
                            Select Model
                          </Button>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-gray-400 text-sm mb-2">No LLM instance configured</div>
                        <div className="text-gray-500 text-xs mb-4">Configure an instance to use LLM chat features</div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-green-400 border-green-400 hover:bg-green-400/10"
                          onClick={() => setShowEditLLMModal(true)}
                        >
                          Add LLM Instance
                        </Button>
                      </div>
                    )}
                  </div>
                ) : (
                  // Embedding Model Configuration
                  <div>
                    {embeddingInstanceConfig.name && embeddingInstanceConfig.url ? (
                      <>
                        <div className="mb-3">
                          <div className="text-white font-medium mb-1">{embeddingInstanceConfig.name}</div>
                          <div className="text-gray-400 text-sm font-mono">{embeddingInstanceConfig.url}</div>
                        </div>

                        <div className="mb-4">
                          <div className="text-gray-300 text-sm mb-1">Model:</div>
                          <div className="text-white">{getDisplayedEmbeddingModel(ragSettings)}</div>
                        </div>

                        <div className="text-gray-400 text-sm mb-4">
                          {embeddingStatus.checking ? (
                            <Loader className="w-4 h-4 animate-spin inline mr-1" />
                          ) : null}
                          {ollamaMetrics.loading ? 'Loading...' : `${ollamaMetrics.embeddingInstanceModels?.embedding || 0} embedding models available`}
                        </div>

                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-purple-300 border-purple-400 hover:bg-purple-500/10"
                            onClick={() => setShowEditEmbeddingModal(true)}
                          >
                            Edit Settings
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-purple-300 border-purple-400 hover:bg-purple-500/10"
                            onClick={async () => {
                              const success = await manualTestConnection(
                                embeddingInstanceConfig.url,
                                setEmbeddingStatus,
                                embeddingInstanceConfig.name,
                                'embedding'
                              );

                              setOllamaManualConfirmed(success);
                              setOllamaServerStatus(success ? 'online' : 'offline');
                            }}
                            disabled={embeddingStatus.checking}
                          >
                            {embeddingStatus.checking ? 'Testing...' : 'Test Connection'}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-purple-300 border-purple-400 hover:bg-purple-500/10"
                            onClick={() => setShowEmbeddingModelSelectionModal(true)}
                          >
                            Select Model
                          </Button>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-gray-400 text-sm mb-2">No Embedding instance configured</div>
                        <div className="text-gray-500 text-xs mb-4">Configure an instance to use embedding features</div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-purple-300 border-purple-400 hover:bg-purple-500/10"
                          onClick={() => setShowEditEmbeddingModal(true)}
                        >
                          Add Embedding Instance
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Context-Aware Configuration Summary */}
              <div className="bg-black/40 rounded-lg p-4 mt-4 shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
                <h4 className="text-white font-medium mb-3">
                  {activeSelection === 'chat' ? 'LLM Instance Summary' : 'Embedding Instance Summary'}
                </h4>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-600">
                        <th className="text-left py-2 text-gray-300 font-medium">Configuration</th>
                        <th className="text-left py-2 text-gray-300 font-medium">
                          {activeSelection === 'chat' ? 'LLM Instance' : 'Embedding Instance'}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-600">
                      <tr>
                        <td className="py-2 text-gray-400">Instance Name</td>
                        <td className="py-2 text-white">
                          {activeSelection === 'chat'
                            ? (llmInstanceConfig.name || <span className="text-gray-500 italic">Not configured</span>)
                            : (embeddingInstanceConfig.name || <span className="text-gray-500 italic">Not configured</span>)
                          }
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-400">Instance URL</td>
                        <td className="py-2 text-white font-mono text-xs">
                          {activeSelection === 'chat'
                            ? (llmInstanceConfig.url || <span className="text-gray-500 italic">Not configured</span>)
                            : (embeddingInstanceConfig.url || <span className="text-gray-500 italic">Not configured</span>)
                          }
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-400">Status</td>
                        <td className="py-2">
                          {activeSelection === 'chat' ? (
                            <span className={llmStatus.checking ? "text-yellow-400" : llmStatus.online ? "text-teal-400" : "text-red-400"}>
                              {llmStatus.checking ? "Checking..." : llmStatus.online ? `Online (${llmStatus.responseTime}ms)` : "Offline"}
                            </span>
                          ) : (
                            <span className={embeddingStatus.checking ? "text-yellow-400" : embeddingStatus.online ? "text-teal-400" : "text-red-400"}>
                              {embeddingStatus.checking ? "Checking..." : embeddingStatus.online ? `Online (${embeddingStatus.responseTime}ms)` : "Offline"}
                            </span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-400">Selected Model</td>
                        <td className="py-2 text-white">
                          {activeSelection === 'chat'
                            ? (getDisplayedChatModel(ragSettings) || <span className="text-gray-500 italic">No model selected</span>)
                            : (getDisplayedEmbeddingModel(ragSettings) || <span className="text-gray-500 italic">No model selected</span>)
                          }
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 text-gray-400">Available Models</td>
                        <td className="py-2">
                          {ollamaMetrics.loading ? (
                            <Loader className="w-3 h-3 animate-spin inline" />
                          ) : activeSelection === 'chat' ? (
                            <div className="text-white">
                              <span className="text-green-400 font-medium text-lg">{ollamaMetrics.llmInstanceModels?.chat || 0}</span>
                              <span className="text-gray-400 text-sm ml-2">chat models</span>
                            </div>
                          ) : (
                            <div className="text-white">
                              <span className="text-purple-400 font-medium text-lg">{ollamaMetrics.embeddingInstanceModels?.embedding || 0}</span>
                              <span className="text-gray-400 text-sm ml-2">embedding models</span>
                            </div>
                          )}
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  {/* Instance-Specific Readiness */}
                  <div className="mt-4 pt-3 border-t border-gray-600">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-300">
                        {activeSelection === 'chat' ? 'LLM Instance Status:' : 'Embedding Instance Status:'}
                      </span>
                      <span className={
                        activeSelection === 'chat'
                          ? (llmStatus.online ? "text-teal-400 font-medium" : "text-red-400")
                          : (embeddingStatus.online ? "text-teal-400 font-medium" : "text-red-400")
                      }>
                        {activeSelection === 'chat'
                          ? (llmStatus.online ? "✓ Ready" : "✗ Not Ready")
                          : (embeddingStatus.online ? "✓ Ready" : "✗ Not Ready")
                        }
                      </span>
                    </div>

                    {/* Instance-Specific Model Metrics */}
                    <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
                      <div className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                        </svg>
                        <span>Available on this instance:</span>
                        <span className="text-white">
                          {ollamaMetrics.loading ? (
                            <Loader className="w-3 h-3 animate-spin inline" />
                          ) : activeSelection === 'chat' ? (
                            `${ollamaMetrics.llmInstanceModels?.chat || 0} chat models`
                          ) : (
                            `${ollamaMetrics.embeddingInstanceModels?.embedding || 0} embedding models`
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>


        {/* Second row: Contextual Embeddings, Max Workers, and description */}
        <div className="grid grid-cols-8 gap-4 mb-4 p-4 rounded-lg border border-green-500/20 shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
          <div className="col-span-4">
            <CustomCheckbox 
              id="contextualEmbeddings" 
              checked={ragSettings.USE_CONTEXTUAL_EMBEDDINGS} 
              onChange={e => setRagSettings({
                ...ragSettings,
                USE_CONTEXTUAL_EMBEDDINGS: e.target.checked
              })} 
              label="Use Contextual Embeddings" 
              description="Enhances embeddings with contextual information for better retrieval" 
            />
          </div>
                      <div className="col-span-1">
              {ragSettings.USE_CONTEXTUAL_EMBEDDINGS && (
                <div className="flex flex-col items-center">
                  <div className="relative ml-2 mr-6">
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={ragSettings.CONTEXTUAL_EMBEDDINGS_MAX_WORKERS}
                      onChange={e => setRagSettings({
                        ...ragSettings,
                        CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: parseInt(e.target.value, 10) || 3
                      })}
                      className="w-14 h-10 pl-1 pr-7 text-center font-medium rounded-md 
                        bg-gradient-to-b from-gray-100 to-gray-200 dark:from-gray-900 dark:to-black 
                        border border-green-500/30 
                        text-gray-900 dark:text-white
                        focus:border-green-500 focus:shadow-[0_0_15px_rgba(34,197,94,0.4)]
                        transition-all duration-200
                        [appearance:textfield] 
                        [&::-webkit-outer-spin-button]:appearance-none 
                        [&::-webkit-inner-spin-button]:appearance-none"
                    />
                    <div className="absolute right-1 top-1 bottom-1 flex flex-col">
                      <button
                        type="button"
                        onClick={() => setRagSettings({
                          ...ragSettings,
                          CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: Math.min(ragSettings.CONTEXTUAL_EMBEDDINGS_MAX_WORKERS + 1, 10)
                        })}
                        className="flex-1 px-1 rounded-t-sm 
                          bg-gradient-to-b from-green-500/20 to-green-600/10
                          hover:from-green-500/30 hover:to-green-600/20
                          border border-green-500/30 border-b-0
                          transition-all duration-200 group"
                      >
                        <svg className="w-2.5 h-2.5 text-green-500 group-hover:filter group-hover:drop-shadow-[0_0_4px_rgba(34,197,94,0.8)]" 
                          viewBox="0 0 10 6" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M1 5L5 1L9 5" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={() => setRagSettings({
                          ...ragSettings,
                          CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: Math.max(ragSettings.CONTEXTUAL_EMBEDDINGS_MAX_WORKERS - 1, 1)
                        })}
                        className="flex-1 px-1 rounded-b-sm 
                          bg-gradient-to-b from-green-500/20 to-green-600/10
                          hover:from-green-500/30 hover:to-green-600/20
                          border border-green-500/30 border-t-0
                          transition-all duration-200 group"
                      >
                        <svg className="w-2.5 h-2.5 text-green-500 group-hover:filter group-hover:drop-shadow-[0_0_4px_rgba(34,197,94,0.8)]" 
                          viewBox="0 0 10 6" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M1 1L5 5L9 1" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  <label className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Max
                  </label>
                </div>
              )}
            </div>
          <div className="col-span-3">
            {ragSettings.USE_CONTEXTUAL_EMBEDDINGS && (
              <p className="text-xs text-green-900 dark:text-blue-600 mt-2">
                Controls parallel processing for embeddings (1-10)
              </p>
            )}
          </div>
        </div>
        
        {/* Third row: Hybrid Search and Agentic RAG */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <CustomCheckbox 
              id="hybridSearch" 
              checked={ragSettings.USE_HYBRID_SEARCH} 
              onChange={e => setRagSettings({
                ...ragSettings,
                USE_HYBRID_SEARCH: e.target.checked
              })} 
              label="Use Hybrid Search" 
              description="Combines vector similarity search with keyword search for better results" 
            />
          </div>
          <div>
            <CustomCheckbox 
              id="agenticRag" 
              checked={ragSettings.USE_AGENTIC_RAG} 
              onChange={e => setRagSettings({
                ...ragSettings,
                USE_AGENTIC_RAG: e.target.checked
              })} 
              label="Use Agentic RAG" 
              description="Enables code extraction and specialized search for technical content" 
            />
          </div>
        </div>
        
        {/* Fourth row: Use Reranking */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <CustomCheckbox 
              id="reranking" 
              checked={ragSettings.USE_RERANKING} 
              onChange={e => setRagSettings({
                ...ragSettings,
                USE_RERANKING: e.target.checked
              })} 
              label="Use Reranking" 
              description="Applies cross-encoder reranking to improve search result relevance" 
            />
          </div>
          <div>{/* Empty column */}</div>
        </div>

        {/* Crawling Performance Settings */}
        <div className="mt-6">
          <div
            className="flex items-center justify-between cursor-pointer p-3 rounded-lg border border-green-500/20 bg-gradient-to-r from-green-500/5 to-green-600/5 hover:from-green-500/10 hover:to-green-600/10 transition-all duration-200"
            onClick={() => setShowCrawlingSettings(!showCrawlingSettings)}
          >
            <div className="flex items-center">
              <Zap className="mr-2 text-green-500 filter drop-shadow-[0_0_8px_rgba(34,197,94,0.6)]" size={18} />
              <h3 className="font-semibold text-gray-800 dark:text-white">Crawling Performance Settings</h3>
            </div>
            {showCrawlingSettings ? (
              <ChevronUp className="text-gray-500 dark:text-gray-400" size={20} />
            ) : (
              <ChevronDown className="text-gray-500 dark:text-gray-400" size={20} />
            )}
          </div>
          
          {showCrawlingSettings && (
            <div className="mt-4 p-4 border border-green-500/10 rounded-lg bg-green-500/5">
              <div className="grid grid-cols-2 gap-4">
                {crawlingSettingsFields.map(field => (
                  <ConfigDrivenInput
                    key={field.key}
                    field={field}
                    value={ragSettings[field.key as keyof typeof ragSettings]}
                    onChange={(key, val) => setRagSettings({ ...ragSettings, [key]: val })}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Storage Performance Settings */}
        <div className="mt-4">
          <div
            className="flex items-center justify-between cursor-pointer p-3 rounded-lg border border-green-500/20 bg-gradient-to-r from-green-500/5 to-green-600/5 hover:from-green-500/10 hover:to-green-600/10 transition-all duration-200"
            onClick={() => setShowStorageSettings(!showStorageSettings)}
          >
            <div className="flex items-center">
              <Database className="mr-2 text-green-500 filter drop-shadow-[0_0_8px_rgba(34,197,94,0.6)]" size={18} />
              <h3 className="font-semibold text-gray-800 dark:text-white">Storage Performance Settings</h3>
            </div>
            {showStorageSettings ? (
              <ChevronUp className="text-gray-500 dark:text-gray-400" size={20} />
            ) : (
              <ChevronDown className="text-gray-500 dark:text-gray-400" size={20} />
            )}
          </div>
          
          {showStorageSettings && (
            <div className="mt-4 p-4 border border-green-500/10 rounded-lg bg-green-500/5">
              <div className="grid grid-cols-3 gap-4">
                {storageSettingsFields.map(field => (
                  <ConfigDrivenInput
                    key={field.key}
                    field={field}
                    value={ragSettings[field.key as keyof typeof ragSettings]}
                    onChange={(key, val) => setRagSettings({ ...ragSettings, [key]: val })}
                  />
                ))}
              </div>
              
              <div className="mt-4 flex items-center">
                <CustomCheckbox
                  id="parallelBatches"
                  checked={ragSettings.ENABLE_PARALLEL_BATCHES !== false}
                  onChange={e => setRagSettings({
                    ...ragSettings,
                    ENABLE_PARALLEL_BATCHES: e.target.checked
                  })}
                  label="Enable Parallel Processing"
                  description="Process multiple document batches simultaneously for faster storage"
                />
              </div>
            </div>
          )}
        </div>

        {/* Edit LLM Instance Modal */}
        {showEditLLMModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-20 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-md">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Edit LLM Instance</h3>
              
              <div className="space-y-4">
                <Input
                  label="Instance Name"
                  value={llmInstanceConfig.name}
                  onChange={(e) => {
                    const newName = e.target.value;
                    setLLMInstanceConfig({...llmInstanceConfig, name: newName});
                    
                    // Auto-sync embedding instance name if URLs are the same (single host setup)
                    if (llmInstanceConfig.url === embeddingInstanceConfig.url && embeddingInstanceConfig.url !== '') {
                      setEmbeddingInstanceConfig({...embeddingInstanceConfig, name: newName});
                    }
                  }}
                  placeholder="Enter instance name"
                />
                
                <Input
                  label="Instance URL"
                  value={llmInstanceConfig.url}
                  onChange={(e) => {
                    const newUrl = e.target.value;
                    setLLMInstanceConfig({...llmInstanceConfig, url: newUrl});
                    
                    // Auto-populate embedding instance if it's empty (convenience for single-host users)
                    if (!embeddingInstanceConfig.url || !embeddingInstanceConfig.name) {
                      setEmbeddingInstanceConfig({
                        name: llmInstanceConfig.name || 'Default Ollama',
                        url: newUrl
                      });
                    }
                  }}
                  placeholder="http://host.docker.internal:11434/v1"
                />
                
                {/* Convenience checkbox for single host setup */}
                <div className="flex items-center gap-2 mt-3">
                  <input
                    type="checkbox"
                    id="use-same-host"
                    checked={llmInstanceConfig.url === embeddingInstanceConfig.url && llmInstanceConfig.url !== ''}
                    onChange={(e) => {
                      if (e.target.checked) {
                        // Sync embedding instance with LLM instance
                        setEmbeddingInstanceConfig({
                          name: llmInstanceConfig.name || 'Default Ollama',
                          url: llmInstanceConfig.url
                        });
                      }
                    }}
                    className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 dark:focus:ring-purple-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                  />
                  <label htmlFor="use-same-host" className="text-sm text-gray-600 dark:text-gray-400">
                    Use same host for embedding instance
                  </label>
                </div>
              </div>
              
              <div className="flex gap-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setShowEditLLMModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    setRagSettings({...ragSettings, LLM_BASE_URL: llmInstanceConfig.url});
                    setShowEditLLMModal(false);
                    showToast('LLM instance updated successfully', 'success');
                    // Wait 1 second then automatically test connection and refresh models
                    setTimeout(() => {
                      manualTestConnection(
                        llmInstanceConfig.url,
                        setLLMStatus,
                        llmInstanceConfig.name,
                        'chat',
                        { suppressToast: true }
                      ).then((success) => {
                        setOllamaManualConfirmed(success);
                        setOllamaServerStatus(success ? 'online' : 'offline');
                      });
                      fetchOllamaMetrics(); // Refresh model metrics after saving
                    }, 1000);
                  }}
                  className="flex-1"
                  accentColor="green"
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Embedding Instance Modal */}
        {showEditEmbeddingModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-20 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-md">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Edit Embedding Instance</h3>
              
              <div className="space-y-4">
                <Input
                  label="Instance Name"
                  value={embeddingInstanceConfig.name}
                  onChange={(e) => setEmbeddingInstanceConfig({...embeddingInstanceConfig, name: e.target.value})}
                  placeholder="Enter instance name"
                />
                
                <Input
                  label="Instance URL"
                  value={embeddingInstanceConfig.url}
                  onChange={(e) => setEmbeddingInstanceConfig({...embeddingInstanceConfig, url: e.target.value})}
                  placeholder="http://host.docker.internal:11434/v1"
                />
              </div>
              
              <div className="flex gap-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => setShowEditEmbeddingModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    setRagSettings({...ragSettings, OLLAMA_EMBEDDING_URL: embeddingInstanceConfig.url});
                    setShowEditEmbeddingModal(false);
                    showToast('Embedding instance updated successfully', 'success');
                    // Wait 1 second then automatically test connection and refresh models
                    setTimeout(() => {
                      manualTestConnection(
                        embeddingInstanceConfig.url,
                        setEmbeddingStatus,
                        embeddingInstanceConfig.name,
                        'embedding',
                        { suppressToast: true }
                      ).then((success) => {
                        setOllamaManualConfirmed(success);
                        setOllamaServerStatus(success ? 'online' : 'offline');
                      });
                      fetchOllamaMetrics(); // Refresh model metrics after saving
                    }, 1000);
                  }}
                  className="flex-1"
                  accentColor="green"
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* LLM Model Selection Modal */}
        {showLLMModelSelectionModal && (
          <OllamaModelSelectionModal
            isOpen={showLLMModelSelectionModal}
            onClose={() => setShowLLMModelSelectionModal(false)}
            instances={[
              { name: llmInstanceConfig.name, url: llmInstanceConfig.url },
              { name: embeddingInstanceConfig.name, url: embeddingInstanceConfig.url }
            ]}
            currentModel={ragSettings.MODEL_CHOICE}
            modelType="chat"
            selectedInstanceUrl={normalizeBaseUrl(llmInstanceConfig.url) ?? ''}
            onSelectModel={(modelName: string) => {
              setRagSettings({ ...ragSettings, MODEL_CHOICE: modelName });
              showToast(`Selected LLM model: ${modelName}`, 'success');
            }}
          />
        )}

        {/* Embedding Model Selection Modal */}
        {showEmbeddingModelSelectionModal && (
          <OllamaModelSelectionModal
            isOpen={showEmbeddingModelSelectionModal}
            onClose={() => setShowEmbeddingModelSelectionModal(false)}
            instances={[
              { name: llmInstanceConfig.name, url: llmInstanceConfig.url },
              { name: embeddingInstanceConfig.name, url: embeddingInstanceConfig.url }
            ]}
            currentModel={ragSettings.EMBEDDING_MODEL}
            modelType="embedding"
            selectedInstanceUrl={normalizeBaseUrl(embeddingInstanceConfig.url) ?? ''}
            onSelectModel={(modelName: string) => {
              setRagSettings({ ...ragSettings, EMBEDDING_MODEL: modelName });
              showToast(`Selected embedding model: ${modelName}`, 'success');
            }}
          />
        )}

        {/* Ollama Model Discovery Modal */}
        {showModelDiscoveryModal && (
          <OllamaModelDiscoveryModal
            isOpen={showModelDiscoveryModal}
            onClose={() => setShowModelDiscoveryModal(false)}
            instances={[]}
            onSelectModels={(selection: { chatModel?: string; embeddingModel?: string }) => {
              const updatedSettings = { ...ragSettings };
              if (selection.chatModel) {
                updatedSettings.MODEL_CHOICE = selection.chatModel;
              }
              if (selection.embeddingModel) {
                updatedSettings.EMBEDDING_MODEL = selection.embeddingModel;
              }
              setRagSettings(updatedSettings);
              setShowModelDiscoveryModal(false);
              // Refresh metrics after model discovery
              fetchOllamaMetrics();
              showToast(`Selected models: ${selection.chatModel || 'none'} (chat), ${selection.embeddingModel || 'none'} (embedding)`, 'success');
            }}
          />
        )}
    </Card>;
};

// Helper functions to get provider-specific model display
function getDisplayedChatModel(ragSettings: RAGSettingsProps["ragSettings"]): string {
  const provider = ragSettings.LLM_PROVIDER || 'openai';
  const modelChoice = ragSettings.MODEL_CHOICE;

  // Always prioritize user input to allow editing
  if (modelChoice !== undefined && modelChoice !== null) {
    return modelChoice;
  }

  // Only use defaults when there's no stored value
  switch (provider) {
    case 'openai':
      return 'gpt-4o-mini';
    case 'anthropic':
      return 'claude-3-5-sonnet-20241022';
    case 'google':
      return 'gemini-1.5-flash';
    case 'grok':
      return 'grok-3-mini';
    case 'ollama':
      return '';
    case 'openrouter':
      return 'anthropic/claude-3.5-sonnet';
    default:
      return 'gpt-4o-mini';
  }
}

function getDisplayedEmbeddingModel(ragSettings: RAGSettingsProps["ragSettings"]): string {
  const provider = ragSettings.EMBEDDING_PROVIDER || ragSettings.LLM_PROVIDER || 'openai';
  const embeddingModel = ragSettings.EMBEDDING_MODEL;

  // Always prioritize user input to allow editing
  if (embeddingModel !== undefined && embeddingModel !== null && embeddingModel !== '') {
    return embeddingModel;
  }

  // Provide appropriate defaults based on LLM provider
  switch (provider) {
    case 'openai':
      return 'text-embedding-3-small';
    case 'google':
      return 'text-embedding-004';
    case 'ollama':
      return '';
    case 'openrouter':
      return 'text-embedding-3-small';  // Default to OpenAI embedding for OpenRouter
    case 'anthropic':
      return 'text-embedding-3-small';  // Use OpenAI embeddings with Claude
    case 'grok':
      return 'text-embedding-3-small';  // Use OpenAI embeddings with Grok
    default:
      return 'text-embedding-3-small';
  }
}

// Helper functions for model placeholders
function getModelPlaceholder(provider: ProviderKey): string {
  switch (provider) {
    case 'openai':
      return 'e.g., gpt-4o-mini';
    case 'anthropic':
      return 'e.g., claude-3-5-sonnet-20241022';
    case 'google':
      return 'e.g., gemini-1.5-flash';
    case 'grok':
      return 'e.g., grok-2-latest';
    case 'ollama':
      return 'e.g., llama2, mistral';
    case 'openrouter':
      return 'e.g., anthropic/claude-3.5-sonnet';
    default:
      return 'e.g., gpt-4o-mini';
  }
}

function getEmbeddingPlaceholder(provider: ProviderKey): string {
  switch (provider) {
    case 'openai':
      return 'Default: text-embedding-3-small';
    case 'anthropic':
      return 'Claude does not provide embedding models';
    case 'google':
      return 'e.g., text-embedding-004';
    case 'grok':
      return 'Grok does not provide embedding models';
    case 'ollama':
      return 'e.g., nomic-embed-text';
    case 'openrouter':
      return 'e.g., text-embedding-3-small';
    default:
      return 'Default: text-embedding-3-small';
  }
}

interface CustomCheckboxProps {
  id: string;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  label: string;
  description: string;
}

const CustomCheckbox = ({
  id,
  checked,
  onChange,
  label,
  description
}: CustomCheckboxProps) => {
  return (
    <div className="flex items-start group">
      <div className="relative flex items-center h-5 mt-1">
        <input 
          type="checkbox" 
          id={id} 
          checked={checked} 
          onChange={onChange} 
          className="sr-only peer" 
        />
        <label 
          htmlFor={id}
          className="relative w-5 h-5 rounded-md transition-all duration-200 cursor-pointer
            bg-gradient-to-b from-white/80 to-white/60 dark:from-white/5 dark:to-black/40
            border border-gray-300 dark:border-gray-700
            peer-checked:border-green-500 dark:peer-checked:border-green-500/50
            peer-checked:bg-gradient-to-b peer-checked:from-green-500/20 peer-checked:to-green-600/20
            group-hover:border-green-500/50 dark:group-hover:border-green-500/30
            peer-checked:shadow-[0_0_10px_rgba(34,197,94,0.2)] dark:peer-checked:shadow-[0_0_15px_rgba(34,197,94,0.3)]"
        >
          <Check className={`
              w-3.5 h-3.5 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
              transition-all duration-200 text-green-500 pointer-events-none
              ${checked ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}
            `} />
        </label>
      </div>
      <div className="ml-3 flex-1">
        <label htmlFor={id} className="text-gray-700 dark:text-zinc-300 font-medium cursor-pointer block text-sm">
          {label}
        </label>
        <p className="text-xs text-gray-600 dark:text-zinc-400 mt-0.5 leading-tight">
          {description}
        </p>
      </div>
    </div>
  );
};
