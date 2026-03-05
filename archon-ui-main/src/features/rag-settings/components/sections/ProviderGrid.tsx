import React from 'react';
import { LuBrainCircuit } from 'react-icons/lu';
import { PiDatabaseThin } from 'react-icons/pi';
import { Check } from 'lucide-react';
import { Button as GlowButton } from '@/features/ui/primitives/button';
import { ProviderKey, RagSettingsType, colorStyles, EMBEDDING_CAPABLE_PROVIDERS, getDefaultModels } from '../../hooks/useRagSettingsData';

interface ProviderGridProps {
  activeSelection: 'chat' | 'embedding';
  setActiveSelection: (val: 'chat' | 'embedding') => void;
  chatProvider: ProviderKey;
  setChatProvider: (val: ProviderKey) => void;
  embeddingProvider: ProviderKey;
  setEmbeddingProvider: (val: ProviderKey) => void;
  providerModels: any;
  setRagSettings: (fn: (prev: RagSettingsType) => RagSettingsType) => void;
  getProviderStatus: (provider: string) => 'configured' | 'partial' | 'missing';
}

export const ProviderGrid: React.FC<ProviderGridProps> = ({
  activeSelection, setActiveSelection,
  chatProvider, setChatProvider,
  embeddingProvider, setEmbeddingProvider,
  providerModels, setRagSettings,
  getProviderStatus
}) => {
  return (
    <>
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
        <div className={`grid gap-3 mb-4 ${activeSelection === 'chat' ? 'grid-cols-6' : 'grid-cols-3'}`}>
          {[
            { key: 'openai', name: 'OpenAI', logo: '/img/OpenAI.png' },
            { key: 'google', name: 'Google', logo: '/img/google-logo.svg' },
            { key: 'openrouter', name: 'OpenRouter', logo: '/img/OpenRouter.png' },
            { key: 'ollama', name: 'Ollama', logo: '/img/Ollama.png' },
            { key: 'anthropic', name: 'Anthropic', logo: '/img/claude-logo.svg' },
            { key: 'grok', name: 'Grok', logo: '/img/Grok.png' }
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
                  const savedModels = providerModels[providerKey] || getDefaultModels(providerKey);
                  setRagSettings(prev => ({ ...prev, MODEL_CHOICE: savedModels.chatModel }));
                } else {
                  setEmbeddingProvider(providerKey);
                  const savedModels = providerModels[providerKey] || getDefaultModels(providerKey);
                  setRagSettings(prev => ({ ...prev, EMBEDDING_MODEL: savedModels.embeddingModel }));
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
                className={`w-8 h-8 mb-1 mx-auto ${provider.key === 'openai' || provider.key === 'grok' ? 'bg-white rounded p-1' : ''}`}
              />
              <div className={`font-medium text-gray-700 dark:text-gray-300 text-center ${provider.key === 'openrouter' ? 'text-xs' : 'text-sm'}`}>
                {provider.name}
              </div>
              {(() => {
                const status = getProviderStatus(provider.key);
                if (status === 'configured') return <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center"><Check className="w-2.5 h-2.5 text-white" /></div>;
                if (status === 'partial') return <div className="absolute -top-1 -right-1 w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center"><div className="w-2 h-2 bg-white rounded-full" /></div>;
                return <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center"><div className="w-1.5 h-1.5 bg-white rounded-full" /></div>;
              })()}
            </button>
          ))}
        </div>
      </div>
    </>
  );
};
