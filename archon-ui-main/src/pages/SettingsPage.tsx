import React, { useState } from "react";
import { Settings, Shield, Cpu, Sparkles, Globe, BrainCircuit } from "lucide-react";
import { APIKeysSection } from "@/features/rag-settings/components/APIKeysSection";
import { RAGSettings } from "@/features/rag-settings";
import { CodeExtractionSettings } from "@/features/rag-settings/components/CodeExtractionSettings";
import { IDEGlobalRules } from "@/features/rag-settings/components/IDEGlobalRules";
import { FeaturesSection } from "@/components/settings/FeaturesSection";

// GROUNDED: Real type alignment from source file
type RagSettingsType = {
  MODEL_CHOICE: string;
  USE_CONTEXTUAL_EMBEDDINGS: boolean;
  CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: number;
  USE_HYBRID_SEARCH: boolean;
  USE_AGENTIC_RAG: boolean;
  USE_RERANKING: boolean;
  LLM_PROVIDER?: string;
  LLM_BASE_URL?: string;
  LLM_INSTANCE_NAME?: string;
  EMBEDDING_MODEL?: string;
  EMBEDDING_PROVIDER?: string;
  OLLAMA_EMBEDDING_URL?: string;
  OLLAMA_EMBEDDING_INSTANCE_NAME?: string;
  CRAWL_BATCH_SIZE?: number;
  CRAWL_MAX_CONCURRENT?: number;
  CRAWL_WAIT_STRATEGY?: string;
  CRAWL_PAGE_TIMEOUT?: number;
  CRAWL_DELAY_BEFORE_HTML?: number;
};

type CodeExtractionSettingsType = {
  MIN_CODE_BLOCK_LENGTH: number;
  MAX_CODE_BLOCK_LENGTH: number;
  ENABLE_COMPLETE_BLOCK_DETECTION: boolean;
  ENABLE_LANGUAGE_SPECIFIC_PATTERNS: boolean;
  ENABLE_PROSE_FILTERING: boolean;
  MAX_PROSE_RATIO: number;
  MIN_CODE_INDICATORS: number;
  ENABLE_DIAGRAM_FILTERING: boolean;
  ENABLE_CONTEXTUAL_LENGTH: boolean;
  CODE_EXTRACTION_MAX_WORKERS: number;
  CONTEXT_WINDOW_SIZE: number;
  ENABLE_CODE_SUMMARIES: boolean;
};

const SettingsPage: React.FC = () => {
  // RAG Settings State
  const [ragSettings, setRagSettings] = useState<RagSettingsType>({
    MODEL_CHOICE: 'gpt-4o-mini',
    USE_CONTEXTUAL_EMBEDDINGS: true,
    CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: 5,
    USE_HYBRID_SEARCH: true,
    USE_AGENTIC_RAG: false,
    USE_RERANKING: false
  });

  // Code Extraction Settings State - GROUNDED with 12 real fields
  const [codeExtractionSettings, setCodeExtractionSettings] = useState<CodeExtractionSettingsType>({
    MIN_CODE_BLOCK_LENGTH: 10,
    MAX_CODE_BLOCK_LENGTH: 50000,
    ENABLE_COMPLETE_BLOCK_DETECTION: true,
    ENABLE_LANGUAGE_SPECIFIC_PATTERNS: true,
    ENABLE_PROSE_FILTERING: true,
    MAX_PROSE_RATIO: 0.5,
    MIN_CODE_INDICATORS: 2,
    ENABLE_DIAGRAM_FILTERING: false,
    ENABLE_CONTEXTUAL_LENGTH: true,
    CODE_EXTRACTION_MAX_WORKERS: 4,
    CONTEXT_WINDOW_SIZE: 128000,
    ENABLE_CODE_SUMMARIES: true
  });

  return (
    <div className="container mx-auto py-8 px-4 space-y-8 max-w-7xl animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Settings className="h-8 w-8 text-indigo-400" />
            System Settings
          </h1>
          <p className="text-slate-400 mt-1">Configure AI models, API keys, and system preferences</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* RAG & Model Configuration */}
        <section id="rag-settings" className="scroll-mt-20">
          <div className="flex items-center gap-2 mb-4 text-indigo-300">
            <BrainCircuit className="h-5 w-5" />
            <h2 className="text-xl font-semibold uppercase tracking-wider">AI Intelligence</h2>
          </div>
          <RAGSettings 
            ragSettings={ragSettings} 
            setRagSettings={setRagSettings} 
          />
        </section>

        {/* Security & Credentials */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section id="api-keys" className="scroll-mt-20">
            <div className="flex items-center gap-2 mb-4 text-emerald-300">
              <Shield className="h-5 w-5" />
              <h2 className="text-xl font-semibold uppercase tracking-wider">Authentication</h2>
            </div>
            <APIKeysSection />
          </section>

          <section id="features" className="scroll-mt-20">
            <div className="flex items-center gap-2 mb-4 text-amber-300">
              <Sparkles className="h-5 w-5" />
              <h2 className="text-xl font-semibold uppercase tracking-wider">Platform Features</h2>
            </div>
            <FeaturesSection />
          </section>
        </div>

        {/* Development & Rules */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section id="global-rules" className="scroll-mt-20">
            <div className="flex items-center gap-2 mb-4 text-blue-300">
              <Cpu className="h-5 w-5" />
              <h2 className="text-xl font-semibold uppercase tracking-wider">System Rules</h2>
            </div>
            <IDEGlobalRules />
          </section>

          <section id="crawling" className="scroll-mt-20">
            <div className="flex items-center gap-2 mb-4 text-purple-300">
              <Globe className="h-5 w-5" />
              <h2 className="text-xl font-semibold uppercase tracking-wider">Ingestion & Crawling</h2>
            </div>
            <CodeExtractionSettings 
              codeExtractionSettings={codeExtractionSettings}
              setCodeExtractionSettings={setCodeExtractionSettings}
            />
          </section>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
