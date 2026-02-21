import React from "react";
import { Card } from "@/components/ui/Card";
import { Settings, Shield, Cpu, Sparkles, Globe, BrainCircuit } from "lucide-react";
import { APIKeysSection } from "@/features/rag-settings/components/APIKeysSection";
import { RAGSettings } from "@/features/rag-settings";
import { CodeExtractionSettings } from "@/features/rag-settings/components/CodeExtractionSettings";
import { IDEGlobalRules } from "@/features/rag-settings/components/IDEGlobalRules";
import { FeaturesSection } from "@/components/settings/FeaturesSection";

const SettingsPage: React.FC = () => {
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
          <RAGSettings />
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
            <CodeExtractionSettings />
          </section>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
