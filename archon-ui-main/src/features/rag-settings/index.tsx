import { Check, Save, Loader, ChevronDown, ChevronUp, Zap, Database } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import OllamaModelDiscoveryModal from './components/OllamaModelDiscoveryModal';
import OllamaModelSelectionModal from './components/OllamaModelSelectionModal';
import { ProviderGrid } from './components/sections/ProviderGrid';
import { StatusAlerts } from './components/sections/StatusAlerts';
import { ModelConfigForm } from './components/sections/ModelConfigForm';
import { credentialsService } from '@/services/credentialsService';
import { ConfigDrivenInput } from '@/features/admin/components/ConfigDrivenInput';
import { 
  useRagSettingsData, RagSettingsType,
  normalizeBaseUrl
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
    crawlingSettingsFields, storageSettingsFields, coreModelFields,
    getDisplayedChatModel, getDisplayedEmbeddingModel, 
    getModelPlaceholder, getEmbeddingPlaceholder
  } = useRagSettingsData(ragSettings, setRagSettings);

  return (
    <Card accentColor="green" className="overflow-hidden p-8">
      <p className="text-sm text-gray-600 dark:text-zinc-400 mb-6">
        Configure Retrieval-Augmented Generation (RAG) strategies for optimal knowledge retrieval.
      </p>
      
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-white">LLM Provider Settings</h2>
      </div>

      <ProviderGrid
        activeSelection={activeSelection}
        setActiveSelection={setActiveSelection}
        chatProvider={chatProvider}
        setChatProvider={setChatProvider}
        embeddingProvider={embeddingProvider}
        setEmbeddingProvider={setEmbeddingProvider}
        providerModels={providerModels}
        setRagSettings={setRagSettings}
        getProviderStatus={getProviderStatus}
      />

      <StatusAlerts
        shouldShowProviderAlert={shouldShowProviderAlert}
        providerAlertClassName={providerAlertClassName}
        providerAlertMessage={providerAlertMessage}
      />
      
      <div className="flex justify-between items-end">
        <ModelConfigForm
          activeSelection={activeSelection}
          chatProvider={chatProvider}
          embeddingProvider={embeddingProvider}
          coreModelFields={coreModelFields}
          ragSettings={ragSettings}
          setRagSettings={setRagSettings}
          showOllamaConfig={showOllamaConfig}
          setShowOllamaConfig={setShowOllamaConfig}
          getDisplayedChatModel={getDisplayedChatModel}
          getDisplayedEmbeddingModel={getDisplayedEmbeddingModel}
          getModelPlaceholder={getModelPlaceholder}
          getEmbeddingPlaceholder={getEmbeddingPlaceholder}
        />

        <Button
          variant="outline"
          accentColor="green"
          icon={saving ? <Loader className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />}
          className="whitespace-nowrap ml-4"
          size="md"
          onClick={async () => {
            try {
              setSaving(true);
              const updatedSettings = {
                ...ragSettings,
                LLM_PROVIDER: chatProvider,
                EMBEDDING_PROVIDER: embeddingProvider,
                LLM_BASE_URL: llmInstanceConfig.url,
                LLM_INSTANCE_NAME: llmInstanceConfig.name,
                OLLAMA_EMBEDDING_URL: embeddingInstanceConfig.url,
                OLLAMA_EMBEDDING_INSTANCE_NAME: embeddingInstanceConfig.name
              };
              await credentialsService.updateRagSettings(updatedSettings);
              setRagSettings(updatedSettings);
              showToast('RAG settings saved successfully!', 'success');
            } catch (_err) {
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

      {showOllamaConfig && ((activeSelection === 'chat' && chatProvider === 'ollama') ||
                           (activeSelection === 'embedding' && embeddingProvider === 'ollama')) && (
        <div className="mt-4 p-4 bg-gradient-to-r from-green-500/5 to-green-600/5 border border-green-500/20 rounded-lg shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-white text-lg font-semibold">{activeSelection === 'chat' ? 'LLM Chat Configuration' : 'Embedding Configuration'}</h3>
              <p className="text-gray-400 text-sm">{activeSelection === 'chat' ? 'Configure Ollama instance for chat completions' : 'Configure Ollama instance for text embeddings'}</p>
            </div>
            <div className={`text-sm font-medium ${(activeSelection === 'chat' ? llmStatus.online : embeddingStatus.online) ? "text-teal-400" : "text-red-400"}`}>
              {(activeSelection === 'chat' ? llmStatus.online : embeddingStatus.online) ? "Online" : "Offline"}
            </div>
          </div>

          <div className="bg-black/40 rounded-lg p-4 shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
            {activeSelection === 'chat' ? (
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
                      {llmStatus.checking && <Loader className="w-4 h-4 animate-spin inline mr-1" />}
                      {ollamaMetrics.loading ? 'Loading...' : `${ollamaMetrics.llmInstanceModels?.chat || 0} chat models available`}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" accentColor="green" className="text-white border-emerald-400 hover:bg-emerald-500/10" onClick={() => setShowEditLLMModal(true)}>Edit Settings</Button>
                      <Button variant="outline" size="sm" accentColor="green" className="text-white border-emerald-400 hover:bg-emerald-500/10" disabled={llmStatus.checking} onClick={async () => {
                        const success = await manualTestConnection(llmInstanceConfig.url, setLLMStatus, llmInstanceConfig.name, 'chat');
                        setOllamaManualConfirmed(success);
                        setOllamaServerStatus(success ? 'online' : 'offline');
                      }}>{llmStatus.checking ? 'Testing...' : 'Test Connection'}</Button>
                      <Button variant="outline" size="sm" accentColor="green" className="text-white border-emerald-400 hover:bg-emerald-500/10" onClick={() => setShowLLMModelSelectionModal(true)}>Select Model</Button>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-sm mb-2">No LLM instance configured</div>
                    <Button variant="outline" size="sm" className="text-green-400 border-green-400 hover:bg-green-400/10" onClick={() => setShowEditLLMModal(true)}>Add LLM Instance</Button>
                  </div>
                )}
              </div>
            ) : (
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
                      {embeddingStatus.checking && <Loader className="w-4 h-4 animate-spin inline mr-1" />}
                      {ollamaMetrics.loading ? 'Loading...' : `${ollamaMetrics.embeddingInstanceModels?.embedding || 0} embedding models available`}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="text-purple-300 border-purple-400 hover:bg-purple-500/10" onClick={() => setShowEditEmbeddingModal(true)}>Edit Settings</Button>
                      <Button variant="outline" size="sm" className="text-purple-300 border-purple-400 hover:bg-purple-500/10" disabled={embeddingStatus.checking} onClick={async () => {
                        const success = await manualTestConnection(embeddingInstanceConfig.url, setEmbeddingStatus, embeddingInstanceConfig.name, 'embedding');
                        setOllamaManualConfirmed(success);
                        setOllamaServerStatus(success ? 'online' : 'offline');
                      }}>{embeddingStatus.checking ? 'Testing...' : 'Test Connection'}</Button>
                      <Button variant="outline" size="sm" className="text-purple-300 border-purple-400 hover:bg-purple-500/10" onClick={() => setShowEmbeddingModelSelectionModal(true)}>Select Model</Button>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-sm mb-2">No Embedding instance configured</div>
                    <Button variant="outline" size="sm" className="text-purple-300 border-purple-400 hover:bg-purple-500/10" onClick={() => setShowEditEmbeddingModal(true)}>Add Embedding Instance</Button>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="bg-black/40 rounded-lg p-4 mt-4 shadow-[0_2px_8px_rgba(34,197,94,0.1)] overflow-x-auto">
            <h4 className="text-white font-medium mb-3">{activeSelection === 'chat' ? 'LLM Instance Summary' : 'Embedding Instance Summary'}</h4>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-600">
                  <th className="text-left py-2 text-gray-300 font-medium">Configuration</th>
                  <th className="text-left py-2 text-gray-300 font-medium">{activeSelection === 'chat' ? 'LLM Instance' : 'Embedding Instance'}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-600">
                <tr>
                  <td className="py-2 text-gray-400">Instance Name</td>
                  <td className="py-2 text-white">{activeSelection === 'chat' ? (llmInstanceConfig.name || 'Not configured') : (embeddingInstanceConfig.name || 'Not configured')}</td>
                </tr>
                <tr>
                  <td className="py-2 text-gray-400">Instance URL</td>
                  <td className="py-2 text-white font-mono text-xs">{activeSelection === 'chat' ? (llmInstanceConfig.url || 'Not configured') : (embeddingInstanceConfig.url || 'Not configured')}</td>
                </tr>
                <tr>
                  <td className="py-2 text-gray-400">Status</td>
                  <td className="py-2">
                    <span className={activeSelection === 'chat' ? (llmStatus.checking ? "text-yellow-400" : llmStatus.online ? "text-teal-400" : "text-red-400") : (embeddingStatus.checking ? "text-yellow-400" : embeddingStatus.online ? "text-teal-400" : "text-red-400")}>
                      {activeSelection === 'chat' ? (llmStatus.checking ? "Checking..." : llmStatus.online ? `Online (${llmStatus.responseTime}ms)` : "Offline") : (embeddingStatus.checking ? "Checking..." : embeddingStatus.online ? `Online (${embeddingStatus.responseTime}ms)` : "Offline")}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid grid-cols-8 gap-4 mb-4 p-4 rounded-lg border border-green-500/20 shadow-[0_2px_8px_rgba(34,197,94,0.1)] mt-6">
        <div className="col-span-4">
          <CustomCheckbox 
            id="contextualEmbeddings" 
            checked={ragSettings.USE_CONTEXTUAL_EMBEDDINGS} 
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRagSettings({ ...ragSettings, USE_CONTEXTUAL_EMBEDDINGS: e.target.checked })} 
            label="Use Contextual Embeddings" 
            description="Enhances embeddings with contextual information for better retrieval" 
          />
        </div>
        <div className="col-span-1">
          {ragSettings.USE_CONTEXTUAL_EMBEDDINGS && (
            <div className="flex flex-col items-center">
              <input type="number" min="1" max="10" value={ragSettings.CONTEXTUAL_EMBEDDINGS_MAX_WORKERS} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRagSettings({ ...ragSettings, CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: parseInt(e.target.value, 10) || 3 })} className="w-14 h-10 text-center rounded-md bg-gray-900 border border-green-500/30 text-white" />
              <label className="text-xs text-gray-500 mt-1">Max</label>
            </div>
          )}
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <CustomCheckbox id="hybridSearch" checked={ragSettings.USE_HYBRID_SEARCH} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRagSettings({ ...ragSettings, USE_HYBRID_SEARCH: e.target.checked })} label="Use Hybrid Search" description="Combines vector similarity search with keyword search" />
        <CustomCheckbox id="agenticRag" checked={ragSettings.USE_AGENTIC_RAG} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRagSettings({ ...ragSettings, USE_AGENTIC_RAG: e.target.checked })} label="Use Agentic RAG" description="Enables code extraction and specialized search" />
      </div>

      <div className="mt-6 space-y-4">
        <div>
          <div className="flex items-center justify-between cursor-pointer p-3 rounded-lg border border-green-500/20 bg-green-500/5" onClick={() => setShowCrawlingSettings(!showCrawlingSettings)}>
            <div className="flex items-center"><Zap className="mr-2 text-green-500" size={18} /><h3 className="font-semibold text-gray-800 dark:text-white">Crawling Settings</h3></div>
            {showCrawlingSettings ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
          {showCrawlingSettings && (
            <div className="mt-4 p-4 border border-green-500/10 rounded-lg bg-green-500/5 grid grid-cols-2 gap-x-6 gap-y-4">
              {crawlingSettingsFields.map(field => (
                <div key={field.key} className="space-y-1">
                  <label className="block text-xs font-medium text-gray-500 dark:text-zinc-400 uppercase tracking-wider">
                    {field.label || field.key}
                  </label>
                  <ConfigDrivenInput field={field} value={ragSettings[field.key as keyof typeof ragSettings]} onChange={(val, key) => key && setRagSettings({ ...ragSettings, [key]: val })} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between cursor-pointer p-3 rounded-lg border border-green-500/20 bg-green-500/5" onClick={() => setShowStorageSettings(!showStorageSettings)}>
            <div className="flex items-center"><Database className="mr-2 text-green-500" size={18} /><h3 className="font-semibold text-gray-800 dark:text-white">Storage Settings</h3></div>
            {showStorageSettings ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
          {showStorageSettings && (
            <div className="mt-4 p-4 border border-green-500/10 rounded-lg bg-green-500/5 space-y-4">
              <div className="grid grid-cols-3 gap-x-6 gap-y-4">
                {storageSettingsFields.map(field => (
                  <div key={field.key} className="space-y-1">
                    <label className="block text-xs font-medium text-gray-500 dark:text-zinc-400 uppercase tracking-wider">
                      {field.label || field.key}
                    </label>
                    <ConfigDrivenInput field={field} value={ragSettings[field.key as keyof typeof ragSettings]} onChange={(val, key) => key && setRagSettings({ ...ragSettings, [key]: val })} />
                  </div>
                ))}
              </div>
              <CustomCheckbox id="parallelBatches" checked={ragSettings.ENABLE_PARALLEL_BATCHES !== false} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRagSettings({ ...ragSettings, ENABLE_PARALLEL_BATCHES: e.target.checked })} label="Enable Parallel Processing" description="Process multiple batches simultaneously" />
            </div>
          )}
        </div>
      </div>

      {showEditLLMModal && <EditInstanceModal title="Edit LLM Instance" config={llmInstanceConfig} setConfig={setLLMInstanceConfig} onClose={() => setShowEditLLMModal(false)} onSave={async () => {
        setRagSettings({...ragSettings, LLM_BASE_URL: llmInstanceConfig.url});
        setShowEditLLMModal(false);
        showToast('LLM updated', 'success');
        setTimeout(() => { manualTestConnection(llmInstanceConfig.url, setLLMStatus, llmInstanceConfig.name, 'chat', { suppressToast: true }).then(s => { setOllamaManualConfirmed(s); setOllamaServerStatus(s ? 'online' : 'offline'); }); fetchOllamaMetrics(); }, 1000);
      }} />}

      {showEditEmbeddingModal && <EditInstanceModal title="Edit Embedding Instance" config={embeddingInstanceConfig} setConfig={setEmbeddingInstanceConfig} onClose={() => setShowEditEmbeddingModal(false)} onSave={async () => {
        setRagSettings({...ragSettings, OLLAMA_EMBEDDING_URL: embeddingInstanceConfig.url});
        setShowEditEmbeddingModal(false);
        showToast('Embedding updated', 'success');
        setTimeout(() => { manualTestConnection(embeddingInstanceConfig.url, setEmbeddingStatus, embeddingInstanceConfig.name, 'embedding', { suppressToast: true }).then(s => { setOllamaManualConfirmed(s); setOllamaServerStatus(s ? 'online' : 'offline'); }); fetchOllamaMetrics(); }, 1000);
      }} />}

      {showLLMModelSelectionModal && <OllamaModelSelectionModal isOpen={showLLMModelSelectionModal} onClose={() => setShowLLMModelSelectionModal(false)} instances={[{ name: llmInstanceConfig.name, url: llmInstanceConfig.url }, { name: embeddingInstanceConfig.name, url: embeddingInstanceConfig.url }]} currentModel={ragSettings.MODEL_CHOICE} modelType="chat" selectedInstanceUrl={normalizeBaseUrl(llmInstanceConfig.url) ?? ''} onSelectModel={m => { setRagSettings({ ...ragSettings, MODEL_CHOICE: m }); showToast(`LLM selected: ${m}`, 'success'); }} />}
      {showEmbeddingModelSelectionModal && <OllamaModelSelectionModal isOpen={showEmbeddingModelSelectionModal} onClose={() => setShowEmbeddingModelSelectionModal(false)} instances={[{ name: llmInstanceConfig.name, url: llmInstanceConfig.url }, { name: embeddingInstanceConfig.name, url: embeddingInstanceConfig.url }]} currentModel={ragSettings.EMBEDDING_MODEL} modelType="embedding" selectedInstanceUrl={normalizeBaseUrl(embeddingInstanceConfig.url) ?? ''} onSelectModel={m => { setRagSettings({ ...ragSettings, EMBEDDING_MODEL: m }); showToast(`Embedding selected: ${m}`, 'success'); }} />}
      {showModelDiscoveryModal && <OllamaModelDiscoveryModal isOpen={showModelDiscoveryModal} onClose={() => setShowModelDiscoveryModal(false)} instances={[]} onSelectModels={s => { const upd = { ...ragSettings }; if (s.chatModel) upd.MODEL_CHOICE = s.chatModel; if (s.embeddingModel) upd.EMBEDDING_MODEL = s.embeddingModel; setRagSettings(upd); setShowModelDiscoveryModal(false); fetchOllamaMetrics(); showToast('Models updated', 'success'); }} />}
    </Card>
  );
};

const EditInstanceModal = ({ title, config, setConfig, onClose, onSave }: any) => (
  <div className="fixed inset-0 bg-black/50 flex items-start justify-center pt-20 z-50">
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-md shadow-2xl">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      <div className="space-y-4">
        <div className="space-y-1"><label className="text-sm font-medium text-gray-700 dark:text-gray-300">Name</label><input value={config.name} onChange={e => setConfig({...config, name: e.target.value})} className="w-full p-2 rounded-md bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 text-sm" placeholder="Instance Name" /></div>
        <div className="space-y-1"><label className="text-sm font-medium text-gray-700 dark:text-gray-300">URL</label><input value={config.url} onChange={e => setConfig({...config, url: e.target.value})} className="w-full p-2 rounded-md bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 text-sm" placeholder="http://..." /></div>
      </div>
      <div className="flex gap-2 mt-6">
        <Button variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
        <Button onClick={onSave} className="flex-1" accentColor="green">Save</Button>
      </div>
    </div>
  </div>
);

const CustomCheckbox = ({ id, checked, onChange, label, description }: any) => (
  <div className="flex items-start group">
    <div className="relative flex items-center h-5 mt-1">
      <input type="checkbox" id={id} checked={checked} onChange={onChange} className="sr-only peer" />
      <label htmlFor={id} className="w-5 h-5 rounded-md border border-gray-300 dark:border-gray-700 peer-checked:bg-green-500/20 peer-checked:border-green-500 cursor-pointer flex items-center justify-center">
        <Check className={`w-3.5 h-3.5 text-green-500 transition-all ${checked ? 'opacity-100' : 'opacity-0'}`} />
      </label>
    </div>
    <div className="ml-3"><label htmlFor={id} className="text-sm font-medium text-gray-700 dark:text-zinc-300 cursor-pointer">{label}</label><p className="text-[10px] text-gray-500 leading-tight">{description}</p></div>
  </div>
);
