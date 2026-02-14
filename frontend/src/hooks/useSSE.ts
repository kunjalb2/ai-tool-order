import { useState, useEffect, useRef, useCallback } from 'react';
import { SSEEvent } from '../types/chat';

export function useSSE(endpoint: string, sessionId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const eventHandlersRef = useRef<Map<string, (data: any) => void>>(new Map());
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isManuallyClosedRef = useRef(false);

  const connect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (!sessionId || sessionId.trim() === '') {
      console.log('[SSE] No sessionId, skipping connection');
      setIsConnected(false);
      return;
    }

    if (isManuallyClosedRef.current) {
      console.log('[SSE] Manually closed, not reconnecting');
      return;
    }

    const url = endpoint + '?session_id=' + sessionId;
    console.log('[SSE] Connecting to ' + url);

    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      console.log('[SSE] Connection established');
      setIsConnected(true);
    };

    eventSource.onerror = () => {
      console.error('[SSE] Connection error');
      setIsConnected(false);
      eventSource.close();

      if (!isManuallyClosedRef.current && !reconnectTimerRef.current) {
        reconnectTimerRef.current = setTimeout(() => {
          reconnectTimerRef.current = null;
          connect();
        }, 1000);
      }
    };

    eventSource.onmessage = (event) => {
      try {
        const parsedEvent = JSON.parse(event.data);
        console.log('[SSE] Event: ' + parsedEvent.type);
        const handler = eventHandlersRef.current.get(parsedEvent.type);
        if (handler) {
          handler(parsedEvent.data);
        }
      } catch (e) {
        console.error('[SSE] Error: ' + e);
      }
    };

    return eventSource;
  }, [endpoint, sessionId]);

  const onEvent = useCallback((eventType: string, handler: (data: any) => void) => {
    eventHandlersRef.current.set(eventType, handler);
  }, []);

  const disconnect = useCallback(() => {
    console.log('[SSE] Manual disconnect');
    isManuallyClosedRef.current = true;

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    setIsConnected(false);
  }, []);

  useEffect(() => {
    isManuallyClosedRef.current = false;
    const eventSource = connect();

    return () => {
      console.log('[SSE] Cleanup');
      isManuallyClosedRef.current = true;
      if (eventSource) {
        eventSource.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [sessionId, connect]);

  return {
    isConnected,
    onEvent,
    disconnect,
  };
}
