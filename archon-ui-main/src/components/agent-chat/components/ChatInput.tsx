import React, { useState } from 'react';
import { Send, WifiOff } from 'lucide-react';

interface ChatInputProps {
  connectionStatus: 'online' | 'offline' | 'connecting';
  isTyping: boolean;
  onSendMessage: (message: string) => Promise<void>;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  connectionStatus,
  isTyping,
  onSendMessage
}) => {
  const [inputValue, setInputValue] = useState('');

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    try {
      await onSendMessage(inputValue);
      setInputValue(''); // Clear on success
    } catch (_error) {
      // Error is handled by parent, we keep input value if failed
    }
  };

  return (
    <div className="p-4 border-t border-gray-200 dark:border-zinc-800/80 bg-white/60 dark:bg-transparent">
      {connectionStatus === 'offline' && (
        <div className="mb-3 p-3 bg-red-50/80 dark:bg-red-900/20 border border-red-200 dark:border-red-800/40 rounded-md">
          <div className="flex items-center text-sm text-red-700 dark:text-red-300">
            <WifiOff className="w-4 h-4 mr-2" />
            Chat is currently offline. Please use the reconnect button above to try again.
          </div>
        </div>
      )}
      
      <div className="flex items-center gap-2">
        {/* Text input field */}
        <div className="flex-1 backdrop-blur-md bg-gradient-to-b from-white/80 to-white/60 dark:from-white/10 dark:to-black/30 border border-gray-200 dark:border-zinc-800/80 rounded-md px-3 py-2 focus-within:border-blue-500 focus-within:shadow-[0_0_15px_rgba(59,130,246,0.5)] transition-all duration-200">
          <input 
            type="text" 
            value={inputValue} 
            onChange={e => setInputValue(e.target.value)} 
            placeholder={
              connectionStatus === 'offline' ? "Chat is offline..." :
              connectionStatus === 'connecting' ? "Connecting..." :
              "Search the knowledge base..."
            }
            aria-label="Chat input message"
            disabled={connectionStatus !== 'online'} 
            className="w-full bg-transparent text-gray-800 dark:text-white placeholder:text-gray-500 dark:placeholder:text-zinc-600 focus:outline-none disabled:opacity-50" 
            onKeyDown={e => {
              if (e.key === 'Enter') handleSend();
            }} 
          />
        </div>
        {/* Send button */}
        <button 
          onClick={handleSend} 
          disabled={connectionStatus !== 'online' || isTyping || !inputValue.trim()} 
          className="relative flex items-center justify-center p-2 rounded-md overflow-hidden group disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Send message"
          title="Send message"
        >
          {/* Glass background */}
          <div className="absolute inset-0 backdrop-blur-md bg-gradient-to-b from-blue-100/80 to-blue-50/60 dark:from-white/5 dark:to-black/20 rounded-md"></div>
          {/* Neon border glow */}
          <div className={`absolute inset-0 rounded-md border-2 border-blue-400 ${
            isTyping || connectionStatus !== 'online' ? 'opacity-30' : 'opacity-60 group-hover:opacity-100'
          } shadow-[0_0_10px_rgba(59,130,246,0.3),inset_0_0_6px_rgba(59,130,246,0.2)] dark:shadow-[0_0_10px_rgba(59,130,246,0.6),inset_0_0_6px_rgba(59,130,246,0.4)] transition-all duration-300`}></div>
          {/* Inner glow effect */}
          <div className={`absolute inset-[1px] rounded-sm bg-blue-100/30 dark:bg-blue-500/10 ${
            isTyping || connectionStatus !== 'online' ? 'opacity-20' : 'opacity-30 group-hover:opacity-40'
          } transition-all duration-200`}></div>
          {/* Send icon with neon glow */}
          <Send className={`w-4 h-4 text-blue-500 dark:text-blue-400 relative z-10 ${
            isTyping || connectionStatus !== 'online' ? 'opacity-50' : 'opacity-90 group-hover:opacity-100'
          } drop-shadow-[0_0_3px_rgba(59,130,246,0.5)] dark:drop-shadow-[0_0_3px_rgba(59,130,246,0.8)] transition-all duration-200`} />
          {/* Shine effect */}
          <div className="absolute top-0 left-0 w-full h-[1px] bg-white/40 rounded-t-md"></div>
        </button>
      </div>
    </div>
  );
};
