import { useEffect, useRef } from 'react';

/**
 * useSSE Hook (Phase 5.1.1)
 * Listens to real-time task updates from the backend and dispatches global window events.
 */
import { getBaseUrl } from '../services/api/apiClient';

export function useSSE() {
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Determine SSE URL dynamically using getBaseUrl()
    const envBase = getBaseUrl();
    const sseUrl = envBase ? `${envBase}/api/sse/tasks` : '/api/sse/tasks';

    console.log('📡 Initializing SSE connection to:', sseUrl);

    if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
      console.log('📡 SSE Mocked for testing');
      return;
    }

    const es = new EventSource(sseUrl);    eventSourceRef.current = es;

    es.onopen = () => {
      console.log('📡 SSE connection established.');
    };

    es.onerror = (err) => {
      console.error('📡 SSE connection error:', err);
    };

    // Listen for task_updated events
    es.addEventListener('task_updated', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📡 Task updated event received:', data);
        
        // Dispatch a global custom event for reactive components (XState machines, etc.)
        const customEvent = new CustomEvent('archon:task_updated', { detail: data });
        window.dispatchEvent(customEvent);
        
      } catch (e) {
        console.error('📡 Failed to parse SSE event data:', e);
      }
    });

    // Welcome message
    es.addEventListener('welcome', (event: MessageEvent) => {
      console.log('📡 SSE Welcome:', JSON.parse(event.data));
    });

    return () => {
      console.log('📡 Closing SSE connection.');
      es.close();
      eventSourceRef.current = null;
    };
  }, []);

  return eventSourceRef.current;
}
