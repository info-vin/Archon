export interface Credential {
  id?: string;
  key: string;
  value?: string;
  encrypted_value?: string;
  is_encrypted: boolean;
  category: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RagSettings {
  USE_CONTEXTUAL_EMBEDDINGS: boolean;
  CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: number;
  USE_HYBRID_SEARCH: boolean;
  USE_AGENTIC_RAG: boolean;
  USE_RERANKING: boolean;
  MODEL_CHOICE: string;
  LLM_PROVIDER?: string;
  LLM_BASE_URL?: string;
  LLM_INSTANCE_NAME?: string;
  OLLAMA_EMBEDDING_URL?: string;
  OLLAMA_EMBEDDING_INSTANCE_NAME?: string;
  EMBEDDING_MODEL?: string;
  EMBEDDING_PROVIDER?: string;
  CRAWL_BATCH_SIZE?: number;
  CRAWL_MAX_CONCURRENT?: number;
  CRAWL_WAIT_STRATEGY?: string;
  CRAWL_PAGE_TIMEOUT?: number;
  CRAWL_DELAY_BEFORE_HTML?: number;
  DOCUMENT_STORAGE_BATCH_SIZE?: number;
  EMBEDDING_BATCH_SIZE?: number;
  DELETE_BATCH_SIZE?: number;
  ENABLE_PARALLEL_BATCHES?: boolean;
  MEMORY_THRESHOLD_PERCENT?: number;
  DISPATCHER_CHECK_INTERVAL?: number;
  CODE_EXTRACTION_BATCH_SIZE?: number;
  CODE_SUMMARY_MAX_WORKERS?: number;
  RAG_CONTEXTUAL_WINDOW?: number;
  RAG_CONTEXTUAL_PROMPT?: string;
  forced_fallback_tier?: string;
  HF_TOKEN?: string;
}

export interface CodeExtractionSettings {
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
}

export interface OllamaInstance {
  id: string;
  name: string;
  baseUrl: string;
  isEnabled: boolean;
  isPrimary: boolean;
  instanceType?: 'chat' | 'embedding' | 'both';
  loadBalancingWeight?: number;
  isHealthy?: boolean;
  responseTimeMs?: number;
  modelsAvailable?: number;
  lastHealthCheck?: string;
}

import { callAPIWithETag } from "../features/shared/api/apiClient";

class CredentialsService {
  private notifyCredentialUpdate(keys: string[]): void {
    if (typeof window === "undefined") return;
    window.dispatchEvent(new CustomEvent("archon:credentials-updated", { detail: { keys } }));
  }

  async getAllCredentials(): Promise<Credential[]> {
    return callAPIWithETag<Credential[]>('/credentials');
  }

  async getCredentialsByCategory(category: string): Promise<Credential[]> {
    const result = await callAPIWithETag<any>(`/credentials/categories/${category}`);
    if (result && result.credentials && typeof result.credentials === "object") {
      return Object.entries(result.credentials).map(([key, val]: [string, any]) => ({
        key,
        value: val && typeof val === "object" ? (val.value || "") : String(val),
        is_encrypted: val && typeof val === "object" ? val.is_encrypted : false,
        category,
        description: (val && typeof val === "object" && val.description) || "",
      }));
    }
    return Array.isArray(result) ? result : [];
  }

  async getCredential(key: string): Promise<{ key: string; value?: string; is_encrypted?: boolean }> {
    try {
      return await callAPIWithETag<any>(`/credentials/${key}`);
    } catch (error: any) {
      if (error.message?.includes('404')) return { key, value: undefined };
      throw error;
    }
  }

  async checkCredentialStatus(keys: string[]): Promise<any> {
    return callAPIWithETag('/credentials/status-check', {
      method: 'POST',
      body: JSON.stringify({ keys }),
    });
  }

  async getRagSettings(): Promise<RagSettings> {
    const ragCredentials = await this.getCredentialsByCategory("rag_strategy");
    const apiKeysCredentials = await this.getCredentialsByCategory("api_keys");
    const settings: RagSettings = {
      USE_CONTEXTUAL_EMBEDDINGS: false,
      CONTEXTUAL_EMBEDDINGS_MAX_WORKERS: 3,
      USE_HYBRID_SEARCH: true,
      USE_AGENTIC_RAG: true,
      USE_RERANKING: true,
      MODEL_CHOICE: "gemini-2.5-flash",
      LLM_PROVIDER: "google",
      EMBEDDING_PROVIDER: "google",
      EMBEDDING_MODEL: "gemini-embedding-001",
      CRAWL_BATCH_SIZE: 50,
      CRAWL_MAX_CONCURRENT: 10,
      CRAWL_WAIT_STRATEGY: "domcontentloaded",
      CRAWL_PAGE_TIMEOUT: 60000,
      CRAWL_DELAY_BEFORE_HTML: 0.5,
      DOCUMENT_STORAGE_BATCH_SIZE: 50,
      EMBEDDING_BATCH_SIZE: 100,
      DELETE_BATCH_SIZE: 100,
      ENABLE_PARALLEL_BATCHES: true,
      MEMORY_THRESHOLD_PERCENT: 80,
      DISPATCHER_CHECK_INTERVAL: 30,
      CODE_EXTRACTION_BATCH_SIZE: 50,
      CODE_SUMMARY_MAX_WORKERS: 3,
      RAG_CONTEXTUAL_WINDOW: 20000,
      RAG_CONTEXTUAL_PROMPT: "Please give a short succinct context to situate this chunk within the overall document.",
      forced_fallback_tier: "0",
      HF_TOKEN: "",
    };
    [...ragCredentials, ...apiKeysCredentials].forEach((cred) => {
      if (cred.key in settings) {
        const key = cred.key as keyof RagSettings;
        if (typeof settings[key] === "boolean") (settings as any)[key] = cred.value === "true";
        else if (["CRAWL_DELAY_BEFORE_HTML"].includes(key)) (settings as any)[key] = parseFloat(cred.value || "0.5");
        else if (typeof settings[key] === "number") (settings as any)[key] = parseInt(cred.value || "0", 10);
        else (settings as any)[key] = cred.value || "";
      }
    });
    return settings;
  }

  async updateCredential(credential: Credential): Promise<Credential> {
    const updated = await callAPIWithETag<Credential>(`/credentials/${credential.key}`, {
      method: "PUT",
      body: JSON.stringify(credential),
    });
    this.notifyCredentialUpdate([credential.key]);
    return updated;
  }

  async createCredential(credential: Credential): Promise<Credential> {
    const created = await callAPIWithETag<Credential>('/credentials', {
      method: "POST",
      body: JSON.stringify(credential),
    });
    this.notifyCredentialUpdate([credential.key]);
    return created;
  }

  async deleteCredential(key: string): Promise<void> {
    await callAPIWithETag(`/credentials/${key}`, { method: "DELETE" });
    this.notifyCredentialUpdate([key]);
  }

  async updateRagSettings(settings: RagSettings): Promise<void> {
    const promises = Object.entries(settings)
      .filter(([_, value]) => value !== undefined)
      .map(([key, value]) => {
        const isHF = key === "HF_TOKEN";
        return this.updateCredential({
          key,
          value: value.toString(),
          is_encrypted: isHF,
          category: isHF ? "api_keys" : "rag_strategy",
        });
      });
    await Promise.all(promises);
  }

  async getCodeExtractionSettings(): Promise<CodeExtractionSettings> {
    const codeExtractionCredentials = await this.getCredentialsByCategory("code_extraction");
    const settings: CodeExtractionSettings = {
      MIN_CODE_BLOCK_LENGTH: 250,
      MAX_CODE_BLOCK_LENGTH: 5000,
      ENABLE_COMPLETE_BLOCK_DETECTION: true,
      ENABLE_LANGUAGE_SPECIFIC_PATTERNS: true,
      ENABLE_PROSE_FILTERING: true,
      MAX_PROSE_RATIO: 0.15,
      MIN_CODE_INDICATORS: 3,
      ENABLE_DIAGRAM_FILTERING: true,
      ENABLE_CONTEXTUAL_LENGTH: true,
      CODE_EXTRACTION_MAX_WORKERS: 3,
      CONTEXT_WINDOW_SIZE: 1000,
      ENABLE_CODE_SUMMARIES: true,
    };
    codeExtractionCredentials.forEach((cred) => {
      if (cred.key in settings) {
        const key = cred.key as keyof CodeExtractionSettings;
        if (key === "MAX_PROSE_RATIO") (settings as any)[key] = parseFloat(cred.value || "0.15");
        else if (typeof settings[key] === "number") (settings as any)[key] = parseInt(cred.value || "0", 10);
        else if (typeof settings[key] === "boolean") (settings as any)[key] = cred.value === "true";
      }
    });
    return settings;
  }

  async updateCodeExtractionSettings(settings: CodeExtractionSettings): Promise<void> {
    const promises = Object.entries(settings).map(([key, value]) => this.updateCredential({
      key,
      value: value.toString(),
      is_encrypted: false,
      category: "code_extraction",
    }));
    await Promise.all(promises);
  }

  async getOllamaInstances(): Promise<OllamaInstance[]> {
    const ollamaCredentials = await this.getCredentialsByCategory('ollama_instances');
    const instanceMap: Record<string, Partial<OllamaInstance>> = {};
    ollamaCredentials.forEach(cred => {
      const parts = cred.key.split('_');
      if (parts.length >= 3 && parts[0] === 'ollama' && parts[1] === 'instance') {
        const id = parts[2];
        const field = parts.slice(3).join('_') as keyof OllamaInstance;
        if (!instanceMap[id]) instanceMap[id] = { id };
        let value: any = cred.value || "";
        if (['isEnabled', 'isPrimary', 'isHealthy'].includes(field)) value = cred.value === 'true';
        else if (['responseTimeMs', 'modelsAvailable', 'loadBalancingWeight'].includes(field)) value = parseInt(cred.value || '0', 10);
        (instanceMap[id] as any)[field] = value;
      }
    });
    return Object.values(instanceMap).filter(i => i.id && i.name && i.baseUrl) as OllamaInstance[];
  }

  async setOllamaInstances(instances: OllamaInstance[]): Promise<void> {
    const existing = await this.getCredentialsByCategory('ollama_instances');
    await Promise.all(existing.map(c => this.deleteCredential(c.key)));
    const promises: Promise<any>[] = [];
    instances.forEach(inst => {
      const fields = { name: inst.name, baseUrl: inst.baseUrl, isEnabled: inst.isEnabled, isPrimary: inst.isPrimary, instanceType: inst.instanceType || 'both', loadBalancingWeight: inst.loadBalancingWeight || 100 };
      Object.entries(fields).forEach(([f, v]) => promises.push(this.createCredential({ key: `ollama_instance_${inst.id}_${f}`, value: v.toString(), is_encrypted: false, category: 'ollama_instances' })));
    });
    await Promise.all(promises);
  }

  async addOllamaInstance(instance: OllamaInstance): Promise<void> {
    const instances = await this.getOllamaInstances();
    instances.push(instance);
    await this.setOllamaInstances(instances);
  }

  async updateOllamaInstance(instanceId: string, updates: Partial<OllamaInstance>): Promise<void> {
    const instances = await this.getOllamaInstances();
    const index = instances.findIndex(inst => inst.id === instanceId);
    if (index !== -1) {
      instances[index] = { ...instances[index], ...updates };
      await this.setOllamaInstances(instances);
    }
  }

  async removeOllamaInstance(instanceId: string): Promise<void> {
    const instances = await this.getOllamaInstances();
    await this.setOllamaInstances(instances.filter(inst => inst.id !== instanceId));
  }

  async migrateOllamaFromLocalStorage(): Promise<any> {
    const saved = localStorage.getItem('ollama-instances');
    if (!saved) return { migrated: false, instanceCount: 0 };
    try {
      const instances = JSON.parse(saved);
      if (Array.isArray(instances) && instances.length > 0) {
        await this.setOllamaInstances(instances);
        localStorage.removeItem('ollama-instances');
        return { migrated: true, instanceCount: instances.length };
      }
    } catch (err) {
      console.warn('Failed to migrate Ollama instances from local storage:', err);
    }
    return { migrated: false, instanceCount: 0 };
  }
}

export const credentialsService = new CredentialsService();
