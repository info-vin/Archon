import { useId } from "react";
import { Button } from "@/components/ui/Button";
import { normalizeBaseUrl, type RagSettingsType } from "../../hooks/useRagSettingsData";
import type { InstanceConfig } from "../../types";
import OllamaModelDiscoveryModal from "../OllamaModelDiscoveryModal";
import OllamaModelSelectionModal from "../OllamaModelSelectionModal";

interface EditInstanceModalProps {
  title: string;
  config: InstanceConfig;
  setConfig: (cfg: InstanceConfig) => void;
  onClose: () => void;
  onSave: () => Promise<void>;
}

const EditInstanceModal = ({ title, config, setConfig, onClose, onSave }: EditInstanceModalProps) => {
  const nameId = useId();
  const urlId = useId();
  return (
    <div className="fixed inset-0 bg-black/50 flex items-start justify-center pt-20 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-96 max-w-md shadow-2xl">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
        <div className="space-y-4">
          <div className="space-y-1">
            <label htmlFor={nameId} className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Name
            </label>
            <input
              id={nameId}
              value={config.name}
              onChange={(e) => setConfig({ ...config, name: e.target.value })}
              className="w-full p-2 rounded-md bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 text-sm"
              placeholder="Instance Name"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor={urlId} className="text-sm font-medium text-gray-700 dark:text-gray-300">
              URL
            </label>
            <input
              id={urlId}
              value={config.url}
              onChange={(e) => setConfig({ ...config, url: e.target.value })}
              className="w-full p-2 rounded-md bg-gray-50 dark:bg-gray-900 border dark:border-gray-700 text-sm"
              placeholder="http://..."
            />
          </div>
        </div>
        <div className="flex gap-2 mt-6">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button onClick={onSave} className="flex-1" accentColor="green">
            Save
          </Button>
        </div>
      </div>
    </div>
  );
};

interface RagModalsContainerProps {
  ragSettings: RagSettingsType;
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void;
  llmInstanceConfig: InstanceConfig;
  setLLMInstanceConfig: (cfg: InstanceConfig) => void;
  embeddingInstanceConfig: InstanceConfig;
  setEmbeddingInstanceConfig: (cfg: InstanceConfig) => void;
  showEditLLMModal: boolean;
  setShowEditLLMModal: (v: boolean) => void;
  showEditEmbeddingModal: boolean;
  setShowEditEmbeddingModal: (v: boolean) => void;
  showLLMModelSelectionModal: boolean;
  setShowLLMModelSelectionModal: (v: boolean) => void;
  showEmbeddingModelSelectionModal: boolean;
  setShowEmbeddingModelSelectionModal: (v: boolean) => void;
  showModelDiscoveryModal: boolean;
  setShowModelDiscoveryModal: (v: boolean) => void;
  onSaveLLMInstance: () => Promise<void>;
  onSaveEmbeddingInstance: () => Promise<void>;
  onModelsDiscovered: (selected: { chatModel?: string; embeddingModel?: string }) => void;
  showToast: (msg: string, type: "success" | "error" | "info") => void;
}

export const RagModalsContainer = ({
  ragSettings,
  setRagSettings,
  llmInstanceConfig,
  setLLMInstanceConfig,
  embeddingInstanceConfig,
  setEmbeddingInstanceConfig,
  showEditLLMModal,
  setShowEditLLMModal,
  showEditEmbeddingModal,
  setShowEditEmbeddingModal,
  showLLMModelSelectionModal,
  setShowLLMModelSelectionModal,
  showEmbeddingModelSelectionModal,
  setShowEmbeddingModelSelectionModal,
  showModelDiscoveryModal,
  setShowModelDiscoveryModal,
  onSaveLLMInstance,
  onSaveEmbeddingInstance,
  onModelsDiscovered,
  showToast,
}: RagModalsContainerProps) => {
  const instances = [
    { name: llmInstanceConfig.name, url: llmInstanceConfig.url },
    { name: embeddingInstanceConfig.name, url: embeddingInstanceConfig.url },
  ];

  return (
    <>
      {showEditLLMModal && (
        <EditInstanceModal
          title="Edit LLM Instance"
          config={llmInstanceConfig}
          setConfig={setLLMInstanceConfig}
          onClose={() => setShowEditLLMModal(false)}
          onSave={onSaveLLMInstance}
        />
      )}

      {showEditEmbeddingModal && (
        <EditInstanceModal
          title="Edit Embedding Instance"
          config={embeddingInstanceConfig}
          setConfig={setEmbeddingInstanceConfig}
          onClose={() => setShowEditEmbeddingModal(false)}
          onSave={onSaveEmbeddingInstance}
        />
      )}

      {showLLMModelSelectionModal && (
        <OllamaModelSelectionModal
          isOpen={showLLMModelSelectionModal}
          onClose={() => setShowLLMModelSelectionModal(false)}
          instances={instances}
          currentModel={ragSettings.MODEL_CHOICE}
          modelType="chat"
          selectedInstanceUrl={normalizeBaseUrl(llmInstanceConfig.url) ?? ""}
          onSelectModel={(m) => {
            setRagSettings({ ...ragSettings, MODEL_CHOICE: m });
            showToast(`LLM selected: ${m}`, "success");
          }}
        />
      )}

      {showEmbeddingModelSelectionModal && (
        <OllamaModelSelectionModal
          isOpen={showEmbeddingModelSelectionModal}
          onClose={() => setShowEmbeddingModelSelectionModal(false)}
          instances={instances}
          currentModel={ragSettings.EMBEDDING_MODEL}
          modelType="embedding"
          selectedInstanceUrl={normalizeBaseUrl(embeddingInstanceConfig.url) ?? ""}
          onSelectModel={(m) => {
            setRagSettings({ ...ragSettings, EMBEDDING_MODEL: m });
            showToast(`Embedding selected: ${m}`, "success");
          }}
        />
      )}

      {showModelDiscoveryModal && (
        <OllamaModelDiscoveryModal
          isOpen={showModelDiscoveryModal}
          onClose={() => setShowModelDiscoveryModal(false)}
          instances={[]}
          onSelectModels={onModelsDiscovered}
        />
      )}
    </>
  );
};
