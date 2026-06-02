import React, { useRef, useState } from 'react';
import { EdgeLitEffect } from '../animations/Animations';
import { useChatSession } from './hooks/useChatSession';
import { usePanelResize } from './hooks/usePanelResize';
import { ChatHeader } from './components/ChatHeader';
import { ChatMessageList } from './components/ChatMessageList';
import { ChatInput } from './components/ChatInput';

/**
 * Props for the ArchonChatPanel component
 */
interface ArchonChatPanelProps {
  'data-id'?: string;
}

/**
 * ArchonChatPanel - A chat interface for the Archon AI assistant
 *
 * This component provides a resizable chat panel with message history,
 * loading states, and input functionality connected to real AI agents.
 */
export const ArchonChatPanel: React.FC<ArchonChatPanelProps> = props => {
  const chatPanelRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Custom hook for resize logic
  const { width, isDragging, handleDragStart } = usePanelResize(chatPanelRef);
  
  // Custom hook for session and chat logic
  const {
    messages,
    connectionError,
    connectionStatus,
    isReconnecting,
    handleReconnect,
    handleSendMessage
  } = useChatSession();

  // These states are kept here for UI simulation if needed, 
  // currently we don't have typing/streaming state exposed from the backend service directly
  // but they are kept to maintain the exact same UI as before.
  const [isTyping] = useState(false);
  const [isStreaming] = useState(false);
  const [streamingMessage] = useState('');

  return (
    <div ref={chatPanelRef} className="h-full flex flex-col relative" style={{
      width: `${width}px`
    }} data-id={props['data-id']}>
      {/* Drag handle for resizing */}
      <div 
        className={`absolute left-0 top-0 w-1.5 h-full cursor-ew-resize z-20 ${isDragging ? 'bg-blue-500/50' : 'bg-transparent hover:bg-blue-500/30'} transition-colors duration-200`} 
        onMouseDown={handleDragStart} 
      />
      
      {/* Main panel with glassmorphism */}
      <div className="h-full flex flex-col relative backdrop-blur-md bg-gradient-to-b from-white/80 to-white/60 dark:from-white/10 dark:to-black/30 border-l border-blue-200 dark:border-blue-500/30">
        {/* Edgelit glow effect */}
        <EdgeLitEffect color="blue" />
        
        {/* Header gradient background */}
        <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-b from-blue-100 to-white dark:from-blue-500/20 dark:to-blue-500/5 rounded-t-md pointer-events-none"></div>
        
        {/* Extracted Header Component */}
        <ChatHeader 
          connectionStatus={connectionStatus}
          connectionError={connectionError}
          isReconnecting={isReconnecting}
          onReconnect={handleReconnect}
        />
        
        {/* Extracted Message List Component */}
        <ChatMessageList 
          messages={messages}
          isTyping={isTyping}
          isStreaming={isStreaming}
          streamingMessage={streamingMessage}
          messagesEndRef={messagesEndRef}
        />
        
        {/* Extracted Input Component */}
        <ChatInput 
          connectionStatus={connectionStatus}
          isTyping={isTyping}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
};
