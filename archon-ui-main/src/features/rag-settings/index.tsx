import { Loader, Save } from "lucide-react";
import { useId } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { credentialsService } from "@/services/credentialsService";
import { AdvancedSettingsAccordion } from "./components/sections/AdvancedSettingsAccordion";
import { ModelConfigForm } from "./components/sections/ModelConfigForm";
import { OllamaConfigPanel } from "./components/sections/OllamaConfigPanel";
import { ProviderGrid } from "./components/sections/ProviderGrid";
import { RagCheckboxField } from "./components/sections/RagCheckboxes";
import { RagModalsContainer } from "./components/sections/RagModalsContainer";
import { StatusAlerts } from "./components/sections/StatusAlerts";
import { type RagSettingsType, useRagSettingsData } from "./hooks/useRagSettingsData";

interface RAGSettingsProps {
  ragSettings: RagSettingsType;
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void;
}

export const RAGSettings = ({ ragSettings, setRagSettings }: RAGSettingsProps) => {
  const contextualId = useId();
  const maxWorkersId = useId();
  const hybridId = useId();
  const agenticId = useId();
  const data = useRagSettingsData(ragSettings, setRagSettings);
  const {
    saving,
    setSaving,
    showCrawlingSettings,
    setShowCrawlingSettings,
    showStorageSettings,
    setShowStorageSettings,
    showModelDiscoveryModal,
    setShowModelDiscoveryModal,
    showOllamaConfig,
    setShowOllamaConfig,
    llmStatus,
    setLLMStatus,
    embeddingStatus,
    setEmbeddingStatus,
    setOllamaManualConfirmed,
    showEditLLMModal,
    setShowEditLLMModal,
    showEditEmbeddingModal,
    setShowEditEmbeddingModal,
    showLLMModelSelectionModal,
    setShowLLMModelSelectionModal,
    showEmbeddingModelSelectionModal,
    setShowEmbeddingModelSelectionModal,
    providerModels,
    chatProvider,
    setChatProvider,
    embeddingProvider,
    setEmbeddingProvider,
    activeSelection,
    setActiveSelection,
    llmInstanceConfig,
    setLLMInstanceConfig,
    embeddingInstanceConfig,
    setEmbeddingInstanceConfig,
    ollamaMetrics,
    fetchOllamaMetrics,
    showToast,
    setOllamaServerStatus,
    manualTestConnection,
    getProviderStatus,
    shouldShowProviderAlert,
    providerAlertClassName,
    providerAlertMessage,
    crawlingSettingsFields,
    storageSettingsFields,
    coreModelFields,
    fallbackSettingsFields,
    showFallbackSettings,
    setShowFallbackSettings,
    getDisplayedChatModel,
    getDisplayedEmbeddingModel,
    getModelPlaceholder,
    getEmbeddingPlaceholder,
  } = data;

  const showOllamaSection =
    showOllamaConfig &&
    ((activeSelection === "chat" && chatProvider === "ollama") ||
      (activeSelection === "embedding" && embeddingProvider === "ollama"));

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
                OLLAMA_EMBEDDING_INSTANCE_NAME: embeddingInstanceConfig.name,
              };
              await credentialsService.updateRagSettings(updatedSettings);
              setRagSettings(updatedSettings);
              showToast("RAG settings saved successfully!", "success");
            } catch (_err) {
              showToast("Failed to save settings", "error");
            } finally {
              setSaving(false);
            }
          }}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save Settings"}
        </Button>
      </div>

      {showOllamaSection && (
        <OllamaConfigPanel
          activeSelection={activeSelection}
          llmInstanceConfig={llmInstanceConfig}
          embeddingInstanceConfig={embeddingInstanceConfig}
          llmStatus={llmStatus}
          embeddingStatus={embeddingStatus}
          displayedChatModel={getDisplayedChatModel(ragSettings)}
          displayedEmbeddingModel={getDisplayedEmbeddingModel(ragSettings)}
          ollamaMetrics={ollamaMetrics}
          onEditLLM={() => setShowEditLLMModal(true)}
          onEditEmbedding={() => setShowEditEmbeddingModal(true)}
          onTestLLM={async () => {
            const ok = await manualTestConnection(llmInstanceConfig.url, setLLMStatus, llmInstanceConfig.name, "chat");
            setOllamaManualConfirmed(ok);
            setOllamaServerStatus(ok ? "online" : "offline");
          }}
          onTestEmbedding={async () => {
            const ok = await manualTestConnection(
              embeddingInstanceConfig.url,
              setEmbeddingStatus,
              embeddingInstanceConfig.name,
              "embedding",
            );
            setOllamaManualConfirmed(ok);
            setOllamaServerStatus(ok ? "online" : "offline");
          }}
          onSelectLLMModel={() => setShowLLMModelSelectionModal(true)}
          onSelectEmbeddingModel={() => setShowEmbeddingModelSelectionModal(true)}
        />
      )}

      <div className="grid grid-cols-8 gap-4 mb-4 p-4 rounded-lg border border-green-500/20 shadow-[0_2px_8px_rgba(34,197,94,0.1)] mt-6">
        <div className="col-span-4">
          <RagCheckboxField
            id={contextualId}
            checked={ragSettings.USE_CONTEXTUAL_EMBEDDINGS}
            onChange={(e) => setRagSettings({ ...ragSettings, USE_CONTEXTUAL_EMBEDDINGS: e.target.checked })}
            label="Use Contextual Embeddings"
            description="Enhances embeddings with contextual information for better retrieval"
          />
        </div>
        <div className="col-span-1">
          {ragSettings.USE_CONTEXTUAL_EMBEDDINGS && (
            <div className="flex flex-col items-center">
              <input
                id={maxWorkersId}
                type="number"
                min="1"
                max="10"
                value={ragSettings.CONTEXTUAL_EMBEDDINGS_MAX_WORKERS}
                onChange={(e) =>
                  setRagSettings({
                    ...ragSettings,
                    CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: parseInt(e.target.value, 10) || 3,
                  })
                }
                className="w-14 h-10 text-center rounded-md bg-gray-900 border border-green-500/30 text-white"
              />
              <label htmlFor={maxWorkersId} className="text-xs text-gray-500 mt-1">
                Max
              </label>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <RagCheckboxField
          id={hybridId}
          checked={ragSettings.USE_HYBRID_SEARCH}
          onChange={(e) => setRagSettings({ ...ragSettings, USE_HYBRID_SEARCH: e.target.checked })}
          label="Use Hybrid Search"
          description="Combines vector similarity search with keyword search"
        />
        <RagCheckboxField
          id={agenticId}
          checked={ragSettings.USE_AGENTIC_RAG}
          onChange={(e) => setRagSettings({ ...ragSettings, USE_AGENTIC_RAG: e.target.checked })}
          label="Use Agentic RAG"
          description="Enables code extraction and specialized search"
        />
      </div>

      <AdvancedSettingsAccordion
        ragSettings={ragSettings}
        setRagSettings={setRagSettings}
        crawlingSettingsFields={crawlingSettingsFields}
        storageSettingsFields={storageSettingsFields}
        fallbackSettingsFields={fallbackSettingsFields}
        showCrawlingSettings={showCrawlingSettings}
        setShowCrawlingSettings={setShowCrawlingSettings}
        showStorageSettings={showStorageSettings}
        setShowStorageSettings={setShowStorageSettings}
        showFallbackSettings={showFallbackSettings}
        setShowFallbackSettings={setShowFallbackSettings}
      />

      <RagModalsContainer
        ragSettings={ragSettings}
        setRagSettings={setRagSettings}
        llmInstanceConfig={llmInstanceConfig}
        setLLMInstanceConfig={setLLMInstanceConfig}
        embeddingInstanceConfig={embeddingInstanceConfig}
        setEmbeddingInstanceConfig={setEmbeddingInstanceConfig}
        showEditLLMModal={showEditLLMModal}
        setShowEditLLMModal={setShowEditLLMModal}
        showEditEmbeddingModal={showEditEmbeddingModal}
        setShowEditEmbeddingModal={setShowEditEmbeddingModal}
        showLLMModelSelectionModal={showLLMModelSelectionModal}
        setShowLLMModelSelectionModal={setShowLLMModelSelectionModal}
        showEmbeddingModelSelectionModal={showEmbeddingModelSelectionModal}
        setShowEmbeddingModelSelectionModal={setShowEmbeddingModelSelectionModal}
        showModelDiscoveryModal={showModelDiscoveryModal}
        setShowModelDiscoveryModal={setShowModelDiscoveryModal}
        onSaveLLMInstance={async () => {
          setRagSettings({ ...ragSettings, LLM_BASE_URL: llmInstanceConfig.url });
          setShowEditLLMModal(false);
          showToast("LLM updated", "success");
          setTimeout(() => {
            manualTestConnection(llmInstanceConfig.url, setLLMStatus, llmInstanceConfig.name, "chat", {
              suppressToast: true,
            }).then((s) => {
              setOllamaManualConfirmed(s);
              setOllamaServerStatus(s ? "online" : "offline");
            });
            fetchOllamaMetrics();
          }, 1000);
        }}
        onSaveEmbeddingInstance={async () => {
          setRagSettings({ ...ragSettings, OLLAMA_EMBEDDING_URL: embeddingInstanceConfig.url });
          setShowEditEmbeddingModal(false);
          showToast("Embedding updated", "success");
          setTimeout(() => {
            manualTestConnection(
              embeddingInstanceConfig.url,
              setEmbeddingStatus,
              embeddingInstanceConfig.name,
              "embedding",
              { suppressToast: true },
            ).then((s) => {
              setOllamaManualConfirmed(s);
              setOllamaServerStatus(s ? "online" : "offline");
            });
            fetchOllamaMetrics();
          }, 1000);
        }}
        onModelsDiscovered={(s) => {
          const upd = { ...ragSettings };
          if (s.chatModel) upd.MODEL_CHOICE = s.chatModel;
          if (s.embeddingModel) upd.EMBEDDING_MODEL = s.embeddingModel;
          setRagSettings(upd);
          setShowModelDiscoveryModal(false);
          fetchOllamaMetrics();
          showToast("Models updated", "success");
        }}
        showToast={showToast}
      />
    </Card>
  );
};
