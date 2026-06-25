import React, { RefObject, useEffect } from 'react';
import { User } from 'lucide-react';
import { ArchonLoadingSpinner } from '../../animations/Animations';
import { ChatMessage } from '@/services/agentChatService';

interface ChatMessageListProps {
  messages: ChatMessage[];
  isTyping: boolean;
  isStreaming: boolean;
  streamingMessage: string;
  messagesEndRef: RefObject<HTMLDivElement>;
}

// PERFORMANCE: Hoisted Intl.DateTimeFormat outside the component to prevent expensive re-instantiations
const timeFormatter = new Intl.DateTimeFormat(undefined, {
  hour: '2-digit',
  minute: '2-digit'
});

export const ChatMessageList: React.FC<ChatMessageListProps> = ({
  messages,
  isTyping,
  isStreaming,
  streamingMessage,
  messagesEndRef
}) => {
  /**
   * Format timestamp for display in messages
   */
  const formatTime = (date: Date) => {
    return timeFormatter.format(date);
  };

  /**
   * Auto-scroll to the bottom when messages change
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [messages, isTyping, streamingMessage, messagesEndRef]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50 dark:bg-transparent">
      {messages.map(message => (
        <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className={`
            max-w-[80%] rounded-lg p-3 
            ${message.sender === 'user' 
              ? 'bg-purple-100/80 dark:bg-purple-500/20 border border-purple-200 dark:border-purple-500/30 ml-auto' 
              : 'bg-blue-100/80 dark:bg-blue-500/20 border border-blue-200 dark:border-blue-500/30 mr-auto'}
          `}>
            <div className="flex items-center mb-1">
              {message.sender === 'agent' ? (
                <div className="w-4 h-4 mr-1 flex items-center justify-center">
                  <img src="/logo-neon.png" alt="Archon" className="w-full h-full" />
                </div>
              ) : (
                <User className="w-4 h-4 text-purple-500 mr-1" />
              )}
              <span className="text-xs text-gray-500 dark:text-zinc-400">
                {formatTime(message.timestamp)}
              </span>
            </div>
            <div className="text-gray-800 dark:text-white text-sm whitespace-pre-wrap">
              {/* For RAG responses, handle markdown-style formatting */}
              {message.agent_type === 'rag' && message.sender === 'agent' ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {message.content.split('\n').map((line, idx) => {
                    // Handle bold text
                    const boldRegex = /\*\*(.*?)\*\*/g;
                    const parts = line.split(boldRegex);
                    
                    return (
                      <div key={idx}>
                        {parts.map((part, partIdx) => 
                          partIdx % 2 === 1 ? (
                            <strong key={partIdx}>{part}</strong>
                          ) : (
                            <span key={partIdx}>{part}</span>
                          )
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                message.content
              )}
            </div>
          </div>
        </div>
      ))}
      
      {/* Streaming message */}
      {isStreaming && streamingMessage && (
        <div className="flex justify-start">
          <div className="max-w-[80%] bg-blue-100/80 dark:bg-blue-500/20 border border-blue-200 dark:border-blue-500/30 mr-auto rounded-lg p-3">
            <div className="flex items-center mb-1">
              <div className="w-4 h-4 mr-1 flex items-center justify-center">
                <img src="/logo-neon.png" alt="Archon" className="w-full h-full" />
              </div>
              <span className="text-xs text-gray-500 dark:text-zinc-400">
                {formatTime(new Date())}
              </span>
              <div className="ml-2 w-1 h-1 bg-blue-500 rounded-full animate-pulse" />
            </div>
            <p className="text-gray-800 dark:text-white text-sm whitespace-pre-wrap">
              {streamingMessage}
            </p>
          </div>
        </div>
      )}
      
      {/* Typing indicator */}
      {(isTyping && !isStreaming) && (
        <div className="flex justify-start">
          <div className="max-w-[80%] mr-auto flex items-center justify-center py-4">
            <ArchonLoadingSpinner size="md" />
            <span className="ml-2 text-sm text-gray-500 dark:text-zinc-400">
              Agent is typing...
            </span>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
