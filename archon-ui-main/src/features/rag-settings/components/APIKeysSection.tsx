import { useState, useEffect, useCallback } from 'react';
import { Plus, Save, Lock } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { credentialsService } from '@/services/credentialsService';
import { useToast } from '@/features/shared/hooks/useToast';

import { CustomCredential } from '../types';
import { APIKeyRow } from './APIKeyRow';

export const APIKeysSection = () => {
  const [customCredentials, setCustomCredentials] = useState<CustomCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const { showToast } = useToast();

  const loadCredentials = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load all credentials
      const allCredentials = await credentialsService.getAllCredentials();
      
      // Filter strictly by the 'api_keys' category to prevent false positives (e.g., LAST_RUN_API_DEPRECATION_SCAN)
      const apiKeys = allCredentials.filter(cred => cred.category === 'api_keys');
      
      // Convert to UI format
      const uiCredentials = apiKeys.map(cred => {
        
        return {
          key: cred.key,
          value: cred.value || '',
          description: cred.description || '',
          originalValue: cred.value || '',
          originalKey: cred.key, // Track original key for updates
          hasChanges: false,
          is_encrypted: cred.is_encrypted || false,
          showValue: false,
          isNew: false,
          isFromBackend: true, // It's from backend, so it's not new
        };
      });
      
      setCustomCredentials(uiCredentials);
    } catch (err) {
      console.error('Failed to load credentials:', err);
      showToast('Failed to load credentials', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Load credentials on mount
  useEffect(() => {
    loadCredentials();
  }, [loadCredentials]);

  // Track unsaved changes
  useEffect(() => {
    const hasChanges = customCredentials.some(cred => cred.hasChanges || cred.isNew);
    setHasUnsavedChanges(hasChanges);
  }, [customCredentials]);

  const handleAddNewRow = () => {
    const newCred: CustomCredential = {
      key: '',
      value: '',
      description: '',
      originalValue: '',
      hasChanges: true,
      is_encrypted: true, // Default to encrypted
      showValue: true, // Show value for new entries
      isNew: true,
      isFromBackend: false // New credentials are not from backend
    };
    
    setCustomCredentials([...customCredentials, newCred]);
  };

  const updateCredential = (index: number, field: keyof CustomCredential, value: string | boolean) => {
    setCustomCredentials(customCredentials.map((cred, i) => {
      if (i === index) {
        const updated = { ...cred, [field]: value };
        // Mark as changed if value differs from original
        if (field === 'key' || field === 'value' || field === 'is_encrypted') {
          updated.hasChanges = true;
        }
        // If user is editing the value of an encrypted credential from backend, make it editable
        if (field === 'value' && cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]') {
          updated.isFromBackend = false; // Now it's being edited, treat like new credential
          updated.showValue = false; // Keep it hidden by default since it was encrypted
          updated.value = ''; // Clear the [ENCRYPTED] placeholder so they can enter new value
        }
        return updated;
      }
      return cred;
    }));
  };

  const toggleValueVisibility = (index: number) => {
    const cred = customCredentials[index];
    if (cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]') {
      showToast('Encrypted credentials cannot be viewed. Edit to make changes.', 'warning');
      return;
    }
    updateCredential(index, 'showValue', !cred.showValue);
  };

  const toggleEncryption = (index: number) => {
    const cred = customCredentials[index];
    if (cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]') {
      showToast('Edit the credential value to make changes.', 'warning');
      return;
    }
    updateCredential(index, 'is_encrypted', !cred.is_encrypted);
  };

  const deleteCredential = async (index: number) => {
    const cred = customCredentials[index];
    
    if (cred.isNew) {
      // Just remove from UI if it's not saved yet
      setCustomCredentials(customCredentials.filter((_, i) => i !== index));
    } else {
      try {
        await credentialsService.deleteCredential(cred.key);
        setCustomCredentials(customCredentials.filter((_, i) => i !== index));
        showToast(`Deleted ${cred.key}`, 'success');
      } catch (err) {
        console.error('Failed to delete credential:', err);
        showToast('Failed to delete credential', 'error');
      }
    }
  };

  const saveAllChanges = async () => {
    setSaving(true);
    let hasErrors = false;
    
    for (const cred of customCredentials) {
      if (cred.hasChanges || cred.isNew) {
        if (!cred.key) {
          showToast('Key name cannot be empty', 'error');
          hasErrors = true;
          continue;
        }
        
        try {
          if (cred.isNew) {
            await credentialsService.createCredential({
              key: cred.key,
              value: cred.value,
              description: cred.description,
              is_encrypted: cred.is_encrypted || false,
              category: 'api_keys'
            });
          } else {
            // If key has changed, delete old and create new
            if (cred.originalKey && cred.originalKey !== cred.key) {
              await credentialsService.deleteCredential(cred.originalKey);
              await credentialsService.createCredential({
                key: cred.key,
                value: cred.value,
                description: cred.description,
                is_encrypted: cred.is_encrypted || false,
                category: 'api_keys'
              });
            } else {
              // Just update the value
              await credentialsService.updateCredential({
                key: cred.key,
                value: cred.value,
                description: cred.description,
                is_encrypted: cred.is_encrypted || false,
                category: 'api_keys'
              });
            }
          }
        } catch (err) {
          console.error(`Failed to save ${cred.key}:`, err);
          showToast(`Failed to save ${cred.key}`, 'error');
          hasErrors = true;
        }
      }
    }
    
    if (!hasErrors) {
      showToast('All changes saved successfully!', 'success');
      await loadCredentials(); // Reload to get fresh data
    }
    
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="space-y-5">
        <Card accentColor="pink" className="space-y-5">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <Card accentColor="pink" className="p-8">
        <div className="space-y-4">
          {/* Description text */}
          <p className="text-sm text-gray-600 dark:text-zinc-400 mb-4">
            Manage your API keys and credentials for various services used by Archon.
          </p>

          {/* Credentials list */}
          <div className="space-y-3">
            {/* Header row */}
            <div className="grid grid-cols-[240px_1fr_40px] gap-4 px-2 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              <div>Key Name</div>
              <div>Value</div>
              <div></div>
            </div>

            {/* Credential rows */}
            {customCredentials.map((cred, index) => (
              <APIKeyRow
                key={index}
                cred={cred}
                index={index}
                onUpdate={updateCredential}
                onToggleVisibility={toggleValueVisibility}
                onToggleEncryption={toggleEncryption}
                onDelete={deleteCredential}
              />
            ))}
          </div>

          {/* Add credential button */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              variant="outline"
              onClick={handleAddNewRow}
              accentColor="pink"
              size="sm"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Add Credential
            </Button>
          </div>

          {/* Save all changes button */}
          {hasUnsavedChanges && (
            <div className="pt-4 flex justify-center gap-2">
              <Button
                variant="ghost"
                onClick={loadCredentials}
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={saveAllChanges}
                accentColor="green"
                disabled={saving}
                className="shadow-emerald-500/20 shadow-sm"
              >
                {saving ? (
                  <>
                    <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save All Changes
                  </>
                )}
              </Button>
            </div>
          )}

          {/* Security Notice */}
          <div className="p-3 mt-6 mb-2 bg-gray-50 dark:bg-black/40 rounded-md flex items-start gap-3">
            <div className="w-5 h-5 text-pink-500 mt-0.5 flex-shrink-0">
              <Lock className="w-5 h-5" />
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p>
                Encrypted credentials are masked after saving. Click on a masked credential to edit it - this allows you to change the value and encryption settings.
              </p>
            </div>
          </div>
        </div>
      </Card>
  );
};