/**
 * Agent Chat Service
 * Handles communication with AI agents via REST API
 */

import { callAPIWithETag } from '../features/shared/api/apiClient';
import { serverHealthService } from './serverHealthService';

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  agent_type?: string;
}

interface ChatSession {
  session_id: string;
  project_id?: string;
  messages: ChatMessage[];
  agent_type: string;
  created_at: Date;
}

interface ChatRequest {
  message: string;
  project_id?: string;
  context?: Record<string, unknown>;
}

class AgentChatService {
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();
  private messageHandlers: Map<string, (message: ChatMessage) => void> = new Map();
  private errorHandlers: Map<string, (error: Error) => void> = new Map();
  private _serverStatus: 'online' | 'offline' | 'unknown' = 'unknown';

  constructor() {
    // callAPIWithETag handles baseUrl automatically via proxy/config
  }

  /**
   * Clean up polling for a session
   */
  private cleanupConnection(sessionId: string): void {
    const interval = this.pollingIntervals.get(sessionId);
    if (interval) {
      clearInterval(interval);
      this.pollingIntervals.delete(sessionId);
    }
    
    this.messageHandlers.delete(sessionId);
    this.errorHandlers.delete(sessionId);
  }

  /**
   * Check if the chat server is online
   */
  private async checkServerStatus(): Promise<'online' | 'offline'> {
    try {
      await callAPIWithETag("/agent-chat/status");
      this._serverStatus = 'online';
      return 'online';
    } catch (error) {
      console.error('Failed to check chat server status:', error);
      this._serverStatus = 'offline';
      return 'offline';
    }
  }

  /**
   * Validate a session exists
   */
  async validateSession(sessionId: string): Promise<boolean> {
    try {
      await callAPIWithETag(`/agent-chat/sessions/${sessionId}`);
      return true;
    } catch (error) {
      console.error('Failed to validate session:', error);
      return false;
    }
  }

  /**
   * Create or get an existing chat session
   */
  async createSession(agentType: string, projectId?: string): Promise<ChatSession> {
    try {
      const session = await callAPIWithETag<ChatSession>("/agent-chat/sessions", {
        method: 'POST',
        body: JSON.stringify({
          agent_type: agentType,
          project_id: projectId
        }),
      });
      return session;
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        throw new Error('Agent chat service is not available. The service may be disabled.');
      }
      console.error('Failed to create chat session:', error);
      throw error;
    }
  }

  /**
   * Send a message to an existing chat session
   */
  async sendMessage(sessionId: string, request: ChatRequest): Promise<ChatMessage> {
    try {
      const message = await callAPIWithETag<ChatMessage>(`/agent-chat/sessions/${sessionId}/send`, {
        method: 'POST',
        body: JSON.stringify(request),
      });
      return message;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  }

  /**
   * Stream messages from a chat session using polling
   */
  async streamMessages(
    sessionId: string,
    onMessage: (message: ChatMessage) => void,
    onError?: (error: Error) => void
  ): Promise<void> {
    // Store handlers
    this.messageHandlers.set(sessionId, onMessage);
    if (onError) {
      this.errorHandlers.set(sessionId, onError);
    }

    // Start polling for new messages
    let lastMessageId: string | null = null;
    
    const pollInterval = setInterval(async () => {
      try {
        const url = `/agent-chat/sessions/${sessionId}/messages${lastMessageId ? `?after=${lastMessageId}` : ''}`;
        const messages = await callAPIWithETag<ChatMessage[]>(url);
        
        // Process new messages
        for (const message of messages) {
          lastMessageId = message.id;
          const handler = this.messageHandlers.get(sessionId);
          if (handler) {
            handler(message);
          }
        }
      } catch (error) {
        if (error instanceof Error && error.message.includes('404')) {
          clearInterval(pollInterval);
          this.pollingIntervals.delete(sessionId);
          const errorHandler = this.errorHandlers.get(sessionId);
          if (errorHandler) {
            errorHandler(new Error('Agent chat service is not available'));
          }
          return;
        }
        
        console.error('Failed to poll messages:', error);
        const errorHandler = this.errorHandlers.get(sessionId);
        if (errorHandler) {
          errorHandler(error instanceof Error ? error : new Error('Unknown error'));
        }
      }
    }, 1000); // Poll every second

    this.pollingIntervals.set(sessionId, pollInterval);
  }

  /**
   * Stop streaming messages from a session
   */
  stopStreaming(sessionId: string): void {
    this.cleanupConnection(sessionId);
  }

  /**
   * Get chat history for a session
   */
  async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    try {
      const messages = await callAPIWithETag<ChatMessage[]>(`/agent-chat/sessions/${sessionId}/messages`);
      return messages;
    } catch (error) {
      console.error('Failed to get chat history:', error);
      throw error;
    }
  }

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string): Promise<void> {
    try {
      // Clean up any active connections first
      this.cleanupConnection(sessionId);

      await callAPIWithETag(`/agent-chat/sessions/${sessionId}`, {
        method: 'DELETE',
      });
    } catch (error) {
      console.error('Failed to delete chat session:', error);
      throw error;
    }
  }

  /**
   * Get server status
   */
  async getServerStatus(): Promise<'online' | 'offline' | 'unknown'> {
    const serverHealthy = await serverHealthService.checkHealth();
    if (!serverHealthy) {
      this._serverStatus = 'offline';
      return 'offline';
    }

    // Return the status from checkServerStatus
    return this.checkServerStatus();
  }

  /**
   * Status property accessor for internal use or UI binding
   */
  get status(): 'online' | 'offline' | 'unknown' {
    return this._serverStatus;
  }

  /**
   * Clean up all connections
   */
  cleanup(): void {
    // Clean up all active polling
    this.pollingIntervals.forEach((interval) => {
      clearInterval(interval);
    });
    this.pollingIntervals.clear();
    this.messageHandlers.clear();
    this.errorHandlers.clear();
  }
}

export const agentChatService = new AgentChatService();
