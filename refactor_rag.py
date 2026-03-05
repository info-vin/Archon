import re

with open('archon-ui-main/src/features/rag-settings/index.tsx', 'r') as f:
    original = f.read()

lines = original.split("\n")

# Find boundaries
start_const = next(i for i, line in enumerate(lines) if line.startswith('type ProviderKey ='))
start_comp = next(i for i, line in enumerate(lines) if line.startswith('export const RAGSettings ='))
comp_open_brace = next(i for i in range(start_comp, len(lines)) if '{' in lines[i])
end_hook = next(i for i, line in enumerate(lines) if line.strip().startswith('return <Card'))

imports_for_hook = """import { useState, useEffect, useRef, useCallback } from 'react';
import { useToast } from '@/features/shared/hooks/useToast';
import { credentialsService } from '@/services/credentialsService';

"""

constants = "\n".join(lines[start_const:start_comp]).replace('type ProviderKey', 'export type ProviderKey')
constants = constants.replace('type RagSettingsType', 'export type RagSettingsType')
constants = constants.replace('type ProviderCredentialKey', 'export type ProviderCredentialKey')
constants = constants.replace('const colorStyles', 'export const colorStyles')
constants = constants.replace('const providerDisplayNames', 'export const providerDisplayNames')
constants = constants.replace('const providerWarningAlertStyle', 'export const providerWarningAlertStyle')
constants = constants.replace('const providerErrorAlertStyle', 'export const providerErrorAlertStyle')
constants = constants.replace('const providerMissingAlertStyle', 'export const providerMissingAlertStyle')
constants = constants.replace('const EMBEDDING_CAPABLE_PROVIDERS', 'export const EMBEDDING_CAPABLE_PROVIDERS')
constants = constants.replace('const getDefaultModels', 'export const getDefaultModels')
constants = constants.replace('const normalizeBaseUrl', 'export const normalizeBaseUrl')

hook_start = """export const useRagSettingsData = (
  ragSettings: RagSettingsType,
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void
) => {
"""
hook_body = "\n".join(lines[comp_open_brace+1:end_hook])

return_stmt = """
  return {
    saving, setSaving,
    showCrawlingSettings, setShowCrawlingSettings,
    showStorageSettings, setShowStorageSettings,
    showModelDiscoveryModal, setShowModelDiscoveryModal,
    showOllamaConfig, setShowOllamaConfig,
    llmStatus, setLLMStatus,
    embeddingStatus, setEmbeddingStatus,
    apiCredentials, providerConnectionStatus,
    ollamaServerStatus, ollamaManualConfirmed, setOllamaManualConfirmed,
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
    manualTestConnection, getProviderStatus, hasApiCredential,
    crawlingSettingsFields, storageSettingsFields, coreModelFields
  };
}
"""

with open('archon-ui-main/src/features/rag-settings/hooks/useRagSettingsData.ts', 'w') as f:
    f.write(imports_for_hook + constants + hook_start + hook_body + return_stmt)

# Now rewrite index.tsx
new_index_imports = """import React from 'react';
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
import { 
  useRagSettingsData, ProviderKey, RagSettingsType, colorStyles, 
  providerDisplayNames, providerWarningAlertStyle, providerErrorAlertStyle, 
  providerMissingAlertStyle, EMBEDDING_CAPABLE_PROVIDERS, getDefaultModels, normalizeBaseUrl
} from './hooks/useRagSettingsData';

interface RAGSettingsProps {
  ragSettings: RagSettingsType;
  setRagSettings: (settings: RagSettingsType | ((prev: RagSettingsType) => RagSettingsType)) => void;
}
"""

comp_start = """
export const RAGSettings = ({ ragSettings, setRagSettings }: RAGSettingsProps) => {
  const {
    saving, setSaving,
    showCrawlingSettings, setShowCrawlingSettings,
    showStorageSettings, setShowStorageSettings,
    showModelDiscoveryModal, setShowModelDiscoveryModal,
    showOllamaConfig, setShowOllamaConfig,
    llmStatus, setLLMStatus,
    embeddingStatus, setEmbeddingStatus,
    apiCredentials, providerConnectionStatus,
    ollamaServerStatus, ollamaManualConfirmed, setOllamaManualConfirmed,
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
    manualTestConnection, getProviderStatus, hasApiCredential,
    crawlingSettingsFields, storageSettingsFields, coreModelFields
  } = useRagSettingsData(ragSettings, setRagSettings);
"""

comp_rest = "\n".join(lines[end_hook:])

with open('archon-ui-main/src/features/rag-settings/index.tsx', 'w') as f:
    f.write(new_index_imports + comp_start + "\n" + comp_rest)

print("Refactoring done.")
