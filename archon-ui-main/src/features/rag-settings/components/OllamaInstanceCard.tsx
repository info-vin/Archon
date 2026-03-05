import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { OllamaInstance } from '@/services/credentialsService';

interface OllamaInstanceCardProps {
  instance: OllamaInstance;
  tempUrl?: string;
  isTesting: boolean;
  instancesCount: number;
  separateHosts: boolean;
  onUrlChange: (id: string, url: string) => void;
  onUrlBlur: (id: string) => void;
  onTest: (id: string) => void;
  onSetPrimary: (id: string) => void;
  onToggle: (id: string) => void;
  onRemove: (id: string) => void;
}

export const OllamaInstanceCard: React.FC<OllamaInstanceCardProps> = ({
  instance, tempUrl, isTesting, instancesCount, separateHosts,
  onUrlChange, onUrlBlur, onTest, onSetPrimary, onToggle, onRemove
}) => {
  const getConnectionStatusBadge = () => {
    if (isTesting) {
      return <Badge variant="outline" color="gray" className="animate-pulse">Testing...</Badge>;
    }
    
    if (instance.isHealthy === true) {
      return (
        <Badge variant="solid" color="green" className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Online
          {instance.responseTimeMs && (
            <span className="text-xs opacity-75">
              ({instance.responseTimeMs.toFixed(0)}ms)
            </span>
          )}
        </Badge>
      );
    }
    
    if (instance.isHealthy === false) {
      return (
        <Badge variant="solid" color="pink" className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-red-500" />
          Offline
        </Badge>
      );
    }
    
    return (
      <Badge variant="outline" color="blue" className="animate-pulse">
        <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping mr-1" />
        Checking...
      </Badge>
    );
  };

  return (
    <Card className="p-4 bg-gray-50 dark:bg-gray-800/50">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-white">
              {instance.name}
            </span>
            {instance.isPrimary && (
              <Badge variant="outline" color="gray" className="text-xs">Primary</Badge>
            )}
            {instance.instanceType && instance.instanceType !== 'both' && (
              <Badge 
                variant="solid" 
                color={instance.instanceType === 'chat' ? 'blue' : 'purple'}
                className="text-xs"
              >
                {instance.instanceType === 'chat' ? 'Chat' : 'Embedding'}
              </Badge>
            )}
            {(!instance.instanceType || instance.instanceType === 'both') && separateHosts && (
              <Badge variant="outline" color="gray" className="text-xs">Both</Badge>
            )}
            {getConnectionStatusBadge()}
          </div>
          
          <div className="relative">
            <Input
              type="url"
              value={tempUrl !== undefined ? tempUrl : instance.baseUrl}
              onChange={(e) => onUrlChange(instance.id, e.target.value)}
              onBlur={() => onUrlBlur(instance.id)}
              placeholder="http://host.docker.internal:11434"
              className={cn(
                "text-sm",
                tempUrl !== undefined && tempUrl !== instance.baseUrl 
                  ? "border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20" 
                  : ""
              )}
            />
            {tempUrl !== undefined && tempUrl !== instance.baseUrl && (
              <div className="absolute right-2 top-1/2 -translate-y-1/2">
                <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" title="Changes will be saved after you stop typing" />
              </div>
            )}
          </div>
          
          {instance.modelsAvailable !== undefined && (
            <div className="text-xs text-gray-600 dark:text-gray-400">
              {instance.modelsAvailable} models available
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onTest(instance.id)}
            disabled={isTesting}
            className="text-xs"
          >
            {isTesting ? 'Testing...' : 'Test'}
          </Button>
          
          {!instance.isPrimary && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSetPrimary(instance.id)}
              className="text-xs"
            >
              Set Primary
            </Button>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onToggle(instance.id)}
            className={cn(
              "text-xs",
              instance.isEnabled 
                ? "text-green-600 hover:text-green-700" 
                : "text-gray-500 hover:text-gray-600"
            )}
          >
            {instance.isEnabled ? 'Enabled' : 'Disabled'}
          </Button>
          
          {instancesCount > 1 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(instance.id)}
              className="text-xs text-red-600 hover:text-red-700"
            >
              Remove
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};
