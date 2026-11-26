import { ChevronDown, ChevronUp, Database, ShieldAlert, Zap } from "lucide-react";
import type React from "react";
import { useId } from "react";
import { ConfigDrivenInput, type FieldConfig } from "@/features/admin/components/ConfigDrivenInput";
import type { RagSettingsType } from "../../hooks/useRagSettingsData";
import { RagCheckboxField } from "./RagCheckboxes";

interface AccordionSectionProps {
  title: string;
  icon: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const AccordionSection = ({ title, icon, isOpen, onToggle, children }: AccordionSectionProps) => (
  <div>
    <button
      type="button"
      aria-expanded={isOpen}
      className="w-full flex items-center justify-between cursor-pointer p-3 rounded-lg border border-green-500/20 bg-green-500/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500"
      onClick={onToggle}
    >
      <div className="flex items-center">
        {icon}
        <h3 className="font-semibold text-gray-800 dark:text-white">{title}</h3>
      </div>
      {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
    </button>
    {isOpen && children}
  </div>
);

interface AdvancedSettingsAccordionProps {
  ragSettings: RagSettingsType;
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void;
  crawlingSettingsFields: FieldConfig[];
  storageSettingsFields: FieldConfig[];
  fallbackSettingsFields: FieldConfig[];
  showCrawlingSettings: boolean;
  setShowCrawlingSettings: (v: boolean) => void;
  showStorageSettings: boolean;
  setShowStorageSettings: (v: boolean) => void;
  showFallbackSettings: boolean;
  setShowFallbackSettings: (v: boolean) => void;
}

export const AdvancedSettingsAccordion = ({
  ragSettings,
  setRagSettings,
  crawlingSettingsFields,
  storageSettingsFields,
  fallbackSettingsFields,
  showCrawlingSettings,
  setShowCrawlingSettings,
  showStorageSettings,
  setShowStorageSettings,
  showFallbackSettings,
  setShowFallbackSettings,
}: AdvancedSettingsAccordionProps) => {
  const parallelBatchesId = useId();
  const renderFieldGrid = (fields: FieldConfig[], colsClass: "grid-cols-2" | "grid-cols-3") => (
    <div className={`grid ${colsClass} gap-x-6 gap-y-4`}>
      {fields.map((field) => (
        <div key={field.key} className="space-y-1">
          <span className="block text-xs font-medium text-gray-500 dark:text-zinc-400 uppercase tracking-wider">
            {field.label || field.key}
          </span>
          <ConfigDrivenInput
            field={field}
            value={ragSettings[field.key as keyof typeof ragSettings]}
            onChange={(val, key) => key && setRagSettings({ ...ragSettings, [key]: val })}
          />
        </div>
      ))}
    </div>
  );

  return (
    <div className="mt-6 space-y-4">
      <AccordionSection
        title="Crawling Settings"
        icon={<Zap className="mr-2 text-green-500" size={18} />}
        isOpen={showCrawlingSettings}
        onToggle={() => setShowCrawlingSettings(!showCrawlingSettings)}
      >
        <div className="mt-4 p-4 border border-green-500/10 rounded-lg bg-green-500/5">
          {renderFieldGrid(crawlingSettingsFields, "grid-cols-2")}
        </div>
      </AccordionSection>

      <AccordionSection
        title="Storage Settings"
        icon={<Database className="mr-2 text-green-500" size={18} />}
        isOpen={showStorageSettings}
        onToggle={() => setShowStorageSettings(!showStorageSettings)}
      >
        <div className="mt-4 p-4 border border-green-500/10 rounded-lg bg-green-500/5 space-y-4">
          {renderFieldGrid(storageSettingsFields, "grid-cols-3")}
          <RagCheckboxField
            id={parallelBatchesId}
            checked={ragSettings.ENABLE_PARALLEL_BATCHES !== false}
            onChange={(e) => setRagSettings({ ...ragSettings, ENABLE_PARALLEL_BATCHES: e.target.checked })}
            label="Enable Parallel Processing"
            description="Process multiple batches simultaneously"
          />
        </div>
      </AccordionSection>

      <AccordionSection
        title="3-Tier Fallback Settings"
        icon={<ShieldAlert className="mr-2 text-green-500" size={18} />}
        isOpen={showFallbackSettings}
        onToggle={() => setShowFallbackSettings(!showFallbackSettings)}
      >
        <div className="mt-4 p-4 border border-green-500/10 rounded-lg bg-green-500/5 space-y-4">
          {renderFieldGrid(fallbackSettingsFields, "grid-cols-2")}
          <div className="text-xs text-gray-500 dark:text-gray-400 border-t border-green-500/10 pt-3 leading-relaxed">
            <p className="font-semibold text-gray-700 dark:text-zinc-300 mb-1">
              💡 3-Tier Multi-Agent Fallback Architecture Notes:
            </p>
            <ul className="list-disc pl-4 space-y-1">
              <li>
                <strong>Tier 1 (主要雲端)</strong>: Google Gemini 等高精度雲端模型。正常運行時，將自動執行
                <strong>自我癒合 (Self-Healing)</strong> 重設為 Tier 1。
              </li>
              <li>
                <strong>Tier 2 (HF 雲端備援)</strong>: 當主要雲端遭遇 429 頻率限制或 401 憑證失效時，自動切換至 Hugging
                Face 免費 API。需提供 HF Access Token (Read 權限即可)。
              </li>
              <li>
                <strong>Tier 3 (本地 Ollama)</strong>: 當主要網路斷線或 Tier 2 連線失敗時，自動優雅降階至本地
                Ollama，啟動 OFFLINE_MODE 運作。
              </li>
            </ul>
          </div>
        </div>
      </AccordionSection>
    </div>
  );
};
