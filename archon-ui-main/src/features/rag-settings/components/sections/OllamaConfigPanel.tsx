import { Loader } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface InstanceConfig {
  name: string;
  url: string;
}

interface InstanceStatus {
  online: boolean;
  checking: boolean;
  responseTime?: number | null;
}

interface OllamaConfigPanelProps {
  activeSelection: "chat" | "embedding";
  llmInstanceConfig: InstanceConfig;
  embeddingInstanceConfig: InstanceConfig;
  llmStatus: InstanceStatus;
  embeddingStatus: InstanceStatus;
  displayedChatModel: string;
  displayedEmbeddingModel: string;
  ollamaMetrics: {
    loading?: boolean;
    llmInstanceModels?: { chat?: number };
    embeddingInstanceModels?: { embedding?: number };
  };
  onEditLLM: () => void;
  onEditEmbedding: () => void;
  onTestLLM: () => Promise<void>;
  onTestEmbedding: () => Promise<void>;
  onSelectLLMModel: () => void;
  onSelectEmbeddingModel: () => void;
}

const BUTTON_STYLES = {
  chat: "text-white border-emerald-400 hover:bg-emerald-500/10",
  embedding: "text-purple-300 border-purple-400 hover:bg-purple-500/10",
} as const;

const EMPTY_BUTTON_STYLES = {
  chat: "text-green-400 border-green-400 hover:bg-green-400/10",
  embedding: "text-purple-300 border-purple-400 hover:bg-purple-500/10",
} as const;

export const OllamaConfigPanel = ({
  activeSelection,
  llmInstanceConfig,
  embeddingInstanceConfig,
  llmStatus,
  embeddingStatus,
  displayedChatModel,
  displayedEmbeddingModel,
  ollamaMetrics,
  onEditLLM,
  onEditEmbedding,
  onTestLLM,
  onTestEmbedding,
  onSelectLLMModel,
  onSelectEmbeddingModel,
}: OllamaConfigPanelProps) => {
  const isChat = activeSelection === "chat";
  const currentConfig = isChat ? llmInstanceConfig : embeddingInstanceConfig;
  const currentStatus = isChat ? llmStatus : embeddingStatus;
  const displayedModel = isChat ? displayedChatModel : displayedEmbeddingModel;
  const modelCount = isChat
    ? ollamaMetrics.llmInstanceModels?.chat || 0
    : ollamaMetrics.embeddingInstanceModels?.embedding || 0;
  const onEdit = isChat ? onEditLLM : onEditEmbedding;
  const onTest = isChat ? onTestLLM : onTestEmbedding;
  const onSelectModel = isChat ? onSelectLLMModel : onSelectEmbeddingModel;
  const btnStyle = BUTTON_STYLES[activeSelection];
  const emptyBtnStyle = EMPTY_BUTTON_STYLES[activeSelection];

  return (
    <div className="mt-4 p-4 bg-gradient-to-r from-green-500/5 to-green-600/5 border border-green-500/20 rounded-lg shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-white text-lg font-semibold">
            {isChat ? "LLM Chat Configuration" : "Embedding Configuration"}
          </h3>
          <p className="text-gray-400 text-sm">
            {isChat
              ? "Configure Ollama instance for chat completions"
              : "Configure Ollama instance for text embeddings"}
          </p>
        </div>
        <div className={`text-sm font-medium ${currentStatus.online ? "text-teal-400" : "text-red-400"}`}>
          {currentStatus.online ? "Online" : "Offline"}
        </div>
      </div>

      <div className="bg-black/40 rounded-lg p-4 shadow-[0_2px_8px_rgba(34,197,94,0.1)]">
        {currentConfig.name && currentConfig.url ? (
          <>
            <div className="mb-3">
              <div className="text-white font-medium mb-1">{currentConfig.name}</div>
              <div className="text-gray-400 text-sm font-mono">{currentConfig.url}</div>
            </div>
            <div className="mb-4">
              <div className="text-gray-300 text-sm mb-1">Model:</div>
              <div className="text-white">{displayedModel}</div>
            </div>
            <div className="text-gray-400 text-sm mb-4">
              {currentStatus.checking && <Loader className="w-4 h-4 animate-spin inline mr-1" />}
              {ollamaMetrics.loading ? "Loading..." : `${modelCount} ${isChat ? "chat" : "embedding"} models available`}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className={btnStyle} onClick={onEdit}>
                Edit Settings
              </Button>
              <Button
                variant="outline"
                size="sm"
                className={btnStyle}
                disabled={currentStatus.checking}
                onClick={onTest}
              >
                {currentStatus.checking ? "Testing..." : "Test Connection"}
              </Button>
              <Button variant="outline" size="sm" className={btnStyle} onClick={onSelectModel}>
                Select Model
              </Button>
            </div>
          </>
        ) : (
          <div className="text-center py-8">
            <div className="text-gray-400 text-sm mb-2">
              {isChat ? "No LLM instance configured" : "No Embedding instance configured"}
            </div>
            <Button variant="outline" size="sm" className={emptyBtnStyle} onClick={onEdit}>
              {isChat ? "Add LLM Instance" : "Add Embedding Instance"}
            </Button>
          </div>
        )}
      </div>

      <div className="bg-black/40 rounded-lg p-4 mt-4 shadow-[0_2px_8px_rgba(34,197,94,0.1)] overflow-x-auto">
        <h4 className="text-white font-medium mb-3">
          {isChat ? "LLM Instance Summary" : "Embedding Instance Summary"}
        </h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-600">
              <th className="text-left py-2 text-gray-300 font-medium">Configuration</th>
              <th className="text-left py-2 text-gray-300 font-medium">
                {isChat ? "LLM Instance" : "Embedding Instance"}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-600">
            <tr>
              <td className="py-2 text-gray-400">Instance Name</td>
              <td className="py-2 text-white">{currentConfig.name || "Not configured"}</td>
            </tr>
            <tr>
              <td className="py-2 text-gray-400">Instance URL</td>
              <td className="py-2 text-white font-mono text-xs">{currentConfig.url || "Not configured"}</td>
            </tr>
            <tr>
              <td className="py-2 text-gray-400">Status</td>
              <td className="py-2">
                <span
                  className={
                    currentStatus.checking ? "text-yellow-400" : currentStatus.online ? "text-teal-400" : "text-red-400"
                  }
                >
                  {currentStatus.checking
                    ? "Checking..."
                    : currentStatus.online
                      ? `Online (${currentStatus.responseTime}ms)`
                      : "Offline"}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
