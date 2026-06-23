import { Trash2, Lock, Unlock, Eye, EyeOff } from 'lucide-react';
import { CustomCredential } from '../types';

interface APIKeyRowProps {
  cred: CustomCredential;
  index: number;
  onUpdate: (index: number, field: keyof CustomCredential, value: string | boolean) => void;
  onToggleVisibility: (index: number) => void;
  onToggleEncryption: (index: number) => void;
  onDelete: (index: number) => void;
}

export const APIKeyRow = ({
  cred,
  index,
  onUpdate,
  onToggleVisibility,
  onToggleEncryption,
  onDelete,
}: APIKeyRowProps) => {
  return (
    <div className="grid grid-cols-[240px_1fr_40px] gap-4 items-center">
      {/* Key name column */}
      <div className="flex items-center">
        <input
          type="text"
          value={cred.key}
          onChange={(e) => onUpdate(index, 'key', e.target.value)}
          placeholder="Enter key name"
          className="w-full px-3 py-2 rounded-md bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-sm font-mono"
        />
      </div>

      {/* Value column with encryption toggle */}
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          <input
            type={cred.showValue ? 'text' : 'password'}
            value={cred.value}
            onChange={(e) => onUpdate(index, 'value', e.target.value)}
            placeholder={cred.is_encrypted && !cred.value ? 'Enter new value (encrypted)' : 'Enter value'}
            className={`w-full px-3 py-2 pr-20 rounded-md border text-sm ${
              cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]'
                ? 'bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400'
                : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700'
            }`}
            title={cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]' 
              ? 'Click to edit this encrypted credential' 
              : undefined}
          />
          
          {/* Show/Hide value button */}
          <button
            type="button"
            onClick={() => onToggleVisibility(index)}
            disabled={cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]'}
            aria-label="Toggle value visibility"
            aria-pressed={!!cred.showValue}
            className={`absolute right-10 top-1/2 -translate-y-1/2 p-1.5 rounded transition-colors ${
              cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]'
                ? 'cursor-not-allowed opacity-50'
                : 'hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
            title={
              cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]'
                ? 'Edit credential to view and modify'
                : cred.showValue ? 'Hide value' : 'Show value'
            }
          >
            {cred.showValue ? (
              <EyeOff className="w-4 h-4 text-gray-500" />
            ) : (
              <Eye className="w-4 h-4 text-gray-500" />
            )}
          </button>
          
          {/* Encryption toggle */}
          <button
            type="button"
            onClick={() => onToggleEncryption(index)}
            disabled={cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]'}
            aria-label="Toggle encryption"
            aria-pressed={!!cred.is_encrypted}
            className={`
              absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded transition-colors
              ${
                cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]'
                  ? 'cursor-not-allowed opacity-50 text-pink-400'
                  : cred.is_encrypted 
                    ? 'text-pink-600 dark:text-pink-400 hover:bg-pink-100 dark:hover:bg-pink-900/20' 
                    : 'text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              }
            `}
            title={
              cred.isFromBackend && cred.is_encrypted && cred.value === '[ENCRYPTED]'
                ? 'Edit credential to modify encryption'
                : cred.is_encrypted ? 'Encrypted - click to decrypt' : 'Not encrypted - click to encrypt'
            }
          >
            {cred.is_encrypted ? (
              <Lock className="w-4 h-4" />
            ) : (
              <Unlock className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Actions column */}
      <div className="flex items-center justify-center">
        <button
          onClick={() => onDelete(index)}
          className="p-1 rounded text-gray-400 hover:text-red-600 transition-colors"
          title="Delete credential"
          aria-label="Delete credential"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
