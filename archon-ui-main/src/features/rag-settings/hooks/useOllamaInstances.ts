import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/features/shared/hooks/useToast';
import { credentialsService, OllamaInstance } from '@/services/credentialsService';

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
      const migrationResult = await credentialsService.migrateOllamaFromLocalStorage();
      if (migrationResult.migrated) {
        showToast(`Migrated ${migrationResult.instanceCount} Ollama instances to database`, 'success');
      }
      
      const databaseInstances = await credentialsService.getOllamaInstances();
      setInstances(databaseInstances);
      onConfigChange(databaseInstances);
    } catch (_error) {
      console.error('Failed to load Ollama instances from database:', _error);
      showToast('Failed to load Ollama configuration from database', 'error');
      
      try {
        const saved = localStorage.getItem('ollama-instances');
        if (saved) {
          const localInstances = JSON.parse(saved);
          setInstances(localInstances);
          onConfigChange(localInstances);
          showToast('Loaded Ollama configuration from local backup', 'warning');
        }
      } catch (localError) {
        console.error('Failed to load from localStorage as fallback:', localError);
      }
    } finally {
      setLoading(false);
    }
  }, [showToast, onConfigChange]);

  useEffect(() => {
    loadInstances();
  }, [loadInstances]);

  const saveInstances = async (newInstances: OllamaInstance[]) => {
    try {
      setLoading(true);
      await credentialsService.setOllamaInstances(newInstances);
      setInstances(newInstances);
      onConfigChange(newInstances);
      localStorage.setItem('ollama-instances', JSON.stringify(newInstances));
    } catch (_error) {
      console.error('Failed to save Ollama instances to database:', _error);
      showToast('Failed to save Ollama configuration to database', 'error');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (baseUrl: string, retryCount = 3): Promise<ConnectionTestResult> => {
    const maxRetries = retryCount;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch('/api/providers/validate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ provider: 'ollama', base_url: baseUrl })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

        const data = await response.json();
        const result = {
          isHealthy: data.health_status?.is_available || false,
          responseTimeMs: data.health_status?.response_time_ms,
          modelsAvailable: data.health_status?.models_available,
          error: data.health_status?.error_message
        };

        if (result.isHealthy) return result;
        lastError = new Error(result.error || 'Instance not available');
      } catch (_error) {
        lastError = _error instanceof Error ? _error : new Error('Unknown error');
      }

      if (attempt < maxRetries) {
        const delayMs = Math.pow(2, attempt - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }

    return { isHealthy: false, error: lastError?.message || 'Connection failed after retries' };
  };

  const handleTestConnection = async (instanceId: string) => {
    const instance = instances.find(inst => inst.id === instanceId);
    if (!instance) return;

    setTestingConnections(prev => new Set(prev).add(instanceId));

    try {
      const result = await testConnection(instance.baseUrl);
      const updatedInstances = instances.map(inst => 
        inst.id === instanceId 
          ? {
              ...inst,
              isHealthy: result.isHealthy,
              responseTimeMs: result.responseTimeMs,
              modelsAvailable: result.modelsAvailable,
              lastHealthCheck: new Date().toISOString()
            }
          : inst
      );
      await saveInstances(updatedInstances);

      if (result.isHealthy) {
        showToast(`Connected to ${instance.name} (${result.responseTimeMs?.toFixed(0)}ms, ${result.modelsAvailable} models)`, 'success');
      } else {
        showToast(result.error || 'Unable to connect to Ollama instance', 'error');
      }
    } catch (_error) {
      showToast(`Connection test failed`, 'error');
    } finally {
      setTestingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(instanceId);
        return newSet;
      });
    }
  };

  const handleAddInstance = async () => {
    if (!newInstanceUrl.trim() || !newInstanceName.trim()) {
      showToast('Please provide both URL and name for the new instance', 'error');
      return;
    }

    try {
      const url = new URL(newInstanceUrl);
      if (!url.protocol.startsWith('http')) throw new Error('URL must use HTTP or HTTPS protocol');
    } catch (_error) {
      showToast('Please provide a valid HTTP/HTTPS URL', 'error');
      return;
    }

    if (instances.some(inst => inst.baseUrl === newInstanceUrl.trim())) {
      showToast('An instance with this URL already exists', 'error');
      return;
    }

    const newInstance: OllamaInstance = {
      id: `instance-${Date.now()}`,
      name: newInstanceName.trim(),
      baseUrl: newInstanceUrl.trim(),
      isEnabled: true,
      isPrimary: false,
      loadBalancingWeight: 100,
      instanceType: separateHosts ? newInstanceType : 'both'
    };

    try {
      setLoading(true);
      await credentialsService.addOllamaInstance(newInstance);
      await loadInstances();
      setNewInstanceUrl('');
      setNewInstanceName('');
      setNewInstanceType('chat');
      setShowAddInstance(false);
      showToast(`Added new Ollama instance: ${newInstance.name}`, 'success');
    } catch (_error) {
      showToast(`Failed to add Ollama instance`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveInstance = async (instanceId: string) => {
    if (instances.length <= 1) {
      showToast('At least one Ollama instance must be configured', 'error');
      return;
    }

    const instance = instances.find(inst => inst.id === instanceId);
    if (!instance) return;

    try {
      setLoading(true);
      await credentialsService.removeOllamaInstance(instanceId);
      await loadInstances();
      showToast(`Removed Ollama instance: ${instance.name}`, 'success');
    } catch (_error) {
      showToast(`Failed to remove Ollama instance`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const debouncedUpdateInstanceUrl = useCallback(async (instanceId: string, newUrl: string) => {
    if (updateTimeouts.current[instanceId]) clearTimeout(updateTimeouts.current[instanceId]);

    updateTimeouts.current[instanceId] = setTimeout(async () => {
      try {
        await credentialsService.updateOllamaInstance(instanceId, { baseUrl: newUrl });
        await loadInstances();
        setTempUrls(prev => {
          const updated = { ...prev };
          delete updated[instanceId];
          return updated;
        });
      } catch (_error) {
        showToast('Failed to update instance URL', 'error');
      }
    }, 1000);
  }, [showToast, loadInstances]);

  const handleUrlChange = (instanceId: string, newUrl: string) => {
    setTempUrls(prev => ({ ...prev, [instanceId]: newUrl }));
    debouncedUpdateInstanceUrl(instanceId, newUrl);
  };

  const handleUrlBlur = async (instanceId: string) => {
    const tempUrl = tempUrls[instanceId];
    const instance = instances.find(inst => inst.id === instanceId);
    
    if (tempUrl && instance && tempUrl !== instance.baseUrl) {
      if (updateTimeouts.current[instanceId]) {
        clearTimeout(updateTimeouts.current[instanceId]);
        delete updateTimeouts.current[instanceId];
      }

      try {
        await credentialsService.updateOllamaInstance(instanceId, { baseUrl: tempUrl });
        await loadInstances();
        setTempUrls(prev => {
          const updated = { ...prev };
          delete updated[instanceId];
          return updated;
        });
      } catch (_error) {
        showToast('Failed to update instance URL', 'error');
      }
    }
  };

  const handleUpdateInstance = async (instanceId: string, updates: Partial<OllamaInstance>) => {
    try {
      await credentialsService.updateOllamaInstance(instanceId, updates);
      await loadInstances();
    } catch (_error) {
      showToast(`Failed to update instance`, 'error');
    }
  };

  return {
    instances, loading, testingConnections,
    showAddInstance, setShowAddInstance,
    newInstanceUrl, setNewInstanceUrl,
    newInstanceName, setNewInstanceName,
    newInstanceType, setNewInstanceType,
    tempUrls,
    handleTestConnection, handleAddInstance, handleRemoveInstance,
    handleUrlChange, handleUrlBlur, handleUpdateInstance,
    loadInstances
  };
};
