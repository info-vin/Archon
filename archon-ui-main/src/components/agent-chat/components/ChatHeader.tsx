import React from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

interface ChatHeaderProps {
  connectionStatus: 'online' | 'offline' | 'connecting';
  connectionError: string | null;
  isReconnecting: boolean;
  onReconnect: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  connectionStatus,
  connectionError,
  isReconnecting,
  onReconnect
}) => {
  return (
    <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-zinc-800/80">
      <div className="flex flex-col gap-2">
        <div className="flex items-center">
          {/* Archon Logo - No animation in header */}
          <div className="relative w-8 h-8 mr-3 flex items-center justify-center">
            <img src="/logo-neon.png" alt="Archon" className="w-6 h-6 z-10 relative" />
          </div>
          <h2 className="text-gray-800 dark:text-white font-medium z-10 relative">
            Knowledge Base Assistant
          </h2>
        </div>
      </div>
      
      {/* Connection status and controls */}
      <div className="flex items-center gap-2">
        {/* Connection status indicator */}
        {connectionStatus === 'offline' && (
          <div className="flex items-center gap-2">
            <div className="flex items-center text-xs text-red-500 bg-red-100/80 dark:bg-red-900/30 px-2 py-1 rounded">
              <WifiOff className="w-3 h-3 mr-1" />
              Chat Offline
            </div>
            <button
              onClick={onReconnect}
              disabled={isReconnecting}
              aria-label={isReconnecting ? 'Reconnecting to chat server' : 'Reconnect to chat server'}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 bg-blue-100/80 hover:bg-blue-200/80 dark:bg-blue-900/30 dark:hover:bg-blue-800/40 px-2 py-1 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-3 h-3 ${isReconnecting ? 'animate-spin' : ''}`} />
              {isReconnecting ? 'Connecting...' : 'Reconnect'}
            </button>
          </div>
        )}
        
        {connectionStatus === 'connecting' && (
          <div className="text-xs text-blue-500 bg-blue-100/80 dark:bg-blue-900/30 px-2 py-1 rounded">
            <div className="flex items-center">
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
              Connecting...
            </div>
          </div>
        )}
        
        {connectionStatus === 'online' && !connectionError && (
          <div className="text-xs text-green-600 bg-green-100/80 dark:bg-green-900/30 px-2 py-1 rounded">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-1" />
              Online
            </div>
          </div>
        )}
        
        {/* Error message overlay */}
        {connectionError && connectionStatus !== 'offline' && (
          <div className="text-xs text-orange-600 bg-orange-100/80 dark:bg-orange-900/30 px-2 py-1 rounded">
            {connectionError}
          </div>
        )}
      </div>
    </div>
  );
};
