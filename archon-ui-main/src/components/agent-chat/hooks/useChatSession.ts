import { useState, useEffect, useRef, useCallback } from 'react';
import { agentChatService, ChatMessage } from '@/services/agentChatService';

export function useChatSession() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'online' | 'offline' | 'connecting'>('connecting');
  const [isReconnecting, setIsReconnecting] = useState(false);

  const sessionIdRef = useRef<string | null>(null);

  const initializeChat = useCallback(async () => {
    try {
      setConnectionStatus('connecting');
      
      // Yield to next frame to avoid initialization race conditions
      await new Promise(resolve => requestAnimationFrame(resolve));
      
      try {
        const { session_id } = await agentChatService.createSession('rag', undefined);
        setSessionId(session_id);
        sessionIdRef.current = session_id;
        
        try {
          const history = await agentChatService.getChatHistory(session_id);
          setMessages(history || []);
        } catch (error) {
          console.error('Failed to load chat history:', error);
          setMessages([]);
        }
        
        try {
          await agentChatService.streamMessages(
            session_id,
            (message: ChatMessage) => {
              setMessages(prev => [...prev, message]);
              setConnectionError(null);
              setConnectionStatus('online');
            },
            (error: Error) => {
              console.error('Message streaming error:', error);
              setConnectionStatus('offline');
              setConnectionError('Chat service is offline. Messages will not be received.');
            }
          );
        } catch (error) {
          console.error('Failed to start message streaming:', error);
        }
        
        setIsInitialized(true);
        setConnectionStatus('online');
        setConnectionError(null);
      } catch (error) {
        console.error('Failed to initialize chat session:', error);
        if (error instanceof Error && error.message.includes('not available')) {
          setConnectionError('Agent chat service is disabled. Enable it in docker-compose to use this feature.');
        } else {
          setConnectionError('Failed to initialize chat. Server may be offline.');
        }
        setConnectionStatus('offline');
      }
    } catch (error) {
      console.error('Failed to initialize chat:', error);
      if (error instanceof Error && error.message.includes('not available')) {
        setConnectionError('Agent chat service is disabled. Enable it in docker-compose to use this feature.');
      } else {
        setConnectionError('Failed to connect to agent. Server may be offline.');
      }
      setConnectionStatus('offline');
    }
  }, []);

  useEffect(() => {
    if (!isInitialized) {
      initializeChat();
    }
  }, [isInitialized, initializeChat]);

  useEffect(() => {
    return () => {
      if (sessionIdRef.current) {
        agentChatService.stopStreaming(sessionIdRef.current);
      }
    };
  }, []);

  const handleReconnect = async () => {
    if (!sessionId || isReconnecting) return;
    
    setIsReconnecting(true);
    setConnectionStatus('connecting');
    setConnectionError('Attempting to reconnect...');
    
    try {
      const success = await agentChatService.validateSession(sessionId);
      if (success) {
        setConnectionError(null);
        setConnectionStatus('online');
      } else {
        setConnectionError('Reconnection failed. Session may have expired.');
        setConnectionStatus('offline');
      }
    } catch (error) {
      console.error('Manual reconnection failed:', error);
      setConnectionError('Reconnection failed. Please try again later.');
      setConnectionStatus('offline');
    } finally {
      setIsReconnecting(false);
    }
  };

  const handleSendMessage = async (inputValue: string) => {
    if (!inputValue.trim() || !sessionId) return;

    try {
      const context = { match_count: 5 };
      await agentChatService.sendMessage(sessionId, { 
        message: inputValue.trim(),
        context
      });
      setConnectionError(null);
    } catch (error) {
      console.error('Failed to send message:', error);
      setConnectionError('Failed to send message. Please try again.');
      throw error; // Rethrow to let the UI component handle clearing the input or showing local error
    }
  };

  return {
    messages,
    sessionId,
    connectionError,
    connectionStatus,
    isReconnecting,
    handleReconnect,
    handleSendMessage
  };
}
