import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/features/shared/hooks/useToast';
import { credentialsService, OllamaInstance } from '@/services/credentialsService';
import { callAPIWithETag } from '@/features/shared/api/apiClient';

export interface ConnectionTestResult {
  isHealthy: boolean;
  responseTimeMs?: number;
  modelsAvailable?: number;
  error?: string;
}

export const useOllamaInstances = (
  onConfigChange: (instances: OllamaInstance[]) => void,
  separateHosts: boolean = false
) => {
  const [instances, setInstances] = useState<OllamaInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingConnections, setTestingConnections] = useState<Set<string>>(new Set());
  const [showAddInstance, setShowAddInstance] = useState(false);
  const [newInstanceUrl, setNewInstanceUrl] = useState('');
  const [newInstanceName, setNewInstanceName] = useState('');
  const [newInstanceType, setNewInstanceType] = useState<'chat' | 'embedding' | 'both'>('chat');
  const [tempUrls, setTempUrls] = useState<Record<string, string>>({});
  const updateTimeouts = useRef<Record<string, any>>({});
  const { showToast } = useToast();

  const loadInstances = useCallback(async () => {
    try {
      setLoading(true);
      await credentialsService.migrateOllamaFromLocalStorage();
      const databaseInstances = await credentialsService.getOllamaInstances();
      setInstances(databaseInstances);
      onConfigChange(databaseInstances);
    } catch (_error) {
      console.error('Failed to load Ollama instances:', _error);
      const saved = localStorage.getItem('ollama-instances');
      if (saved) {
        const local = JSON.parse(saved);
        setInstances(local);
        onConfigChange(local);
      }
    } finally {
      setLoading(false);
    }
  }, [onConfigChange]);

  useEffect(() => { loadInstances(); }, [loadInstances]);

  const saveInstances = async (newInstances: OllamaInstance[]) => {
    try {
      await credentialsService.setOllamaInstances(newInstances);
      setInstances(newInstances);
      onConfigChange(newInstances);
      localStorage.setItem('ollama-instances', JSON.stringify(newInstances));
    } catch (_error) {
      showToast('Failed to save configuration', 'error');
    }
  };

  const testConnection = async (baseUrl: string): Promise<ConnectionTestResult> => {
    try {
      const data = await callAPIWithETag<any>('/providers/validate', {
        method: 'POST',
        body: JSON.stringify({ provider: 'ollama', base_url: baseUrl })
      });
      return {
        isHealthy: data.health_status?.is_available || false,
        responseTimeMs: data.health_status?.response_time_ms,
        modelsAvailable: data.health_status?.models_available,
        error: data.health_status?.error_message
      };
    } catch (e: any) {
      return { isHealthy: false, error: e.message };
    }
  };

  const handleTestConnection = async (instanceId: string) => {
    const instance = instances.find(inst => inst.id === instanceId);
    if (!instance) return;
    setTestingConnections(prev => new Set(prev).add(instanceId));
    try {
      const result = await testConnection(instance.baseUrl);
      const updated = instances.map(inst => inst.id === instanceId ? { ...inst, isHealthy: result.isHealthy, lastHealthCheck: new Date().toISOString() } : inst);
      await saveInstances(updated);
      if (result.isHealthy) showToast(`Connected to ${instance.name}`, 'success');
      else showToast(result.error || 'Connection failed', 'error');
    } finally {
      setTestingConnections(prev => {
        const n = new Set(prev);
        n.delete(instanceId);
        return n;
      });
    }
  };

  const handleAddInstance = async () => {
    const newInstance: OllamaInstance = {
      id: `instance-${Date.now()}`,
      name: newInstanceName.trim(),
      baseUrl: newInstanceUrl.trim(),
      isEnabled: true,
      isPrimary: false,
      loadBalancingWeight: 100,
      instanceType: separateHosts ? newInstanceType : 'both'
    };
    await credentialsService.addOllamaInstance(newInstance);
    await loadInstances();
    setNewInstanceUrl('');
    setNewInstanceName('');
    setShowAddInstance(false);
  };

  const handleRemoveInstance = async (id: string) => {
    await credentialsService.removeOllamaInstance(id);
    await loadInstances();
  };

  const handleUpdateInstance = async (id: string, updates: Partial<OllamaInstance>) => {
    await credentialsService.updateOllamaInstance(id, updates);
    await loadInstances();
  };

  const handleUrlChange = (id: string, url: string) => {
    setTempUrls(prev => ({ ...prev, [id]: url }));
    if (updateTimeouts.current[id]) clearTimeout(updateTimeouts.current[id]);
    updateTimeouts.current[id] = setTimeout(async () => {
      await handleUpdateInstance(id, { baseUrl: url });
      setTempUrls(prev => { const n = { ...prev }; delete n[id]; return n; });
    }, 1000);
  };

  return {
    instances, loading, testingConnections, showAddInstance, setShowAddInstance,
    newInstanceUrl, setNewInstanceUrl, newInstanceName, setNewInstanceName,
    newInstanceType, setNewInstanceType, tempUrls,
    handleTestConnection, handleAddInstance, handleRemoveInstance,
    handleUrlChange, handleUrlBlur: () => {}, handleUpdateInstance,
    loadInstances
  };
};
