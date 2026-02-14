/**
 * WebSocket hook for real-time updates.
 *
 * Requirements:
 * - 6.1: Replace 1-second polling with WebSocket
 * - 6.2: Connect to WebSocket endpoint
 * - 6.4: Fall back to 30-second polling if WebSocket unavailable
 * - Implement exponential backoff on errors
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace(/^http/, 'ws');

// Connection states
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'failed';

// Message types from WebSocket
export type WSMessageType =
  | 'graph_update'
  | 'metrics_update'
  | 'intervention_update'
  | 'alert'
  | 'heartbeat'
  | 'error';

export interface WSMessage {
  type: WSMessageType;
  timestamp: string;
  data?: any;
  alert?: any;
}

// Polling fallback configuration
const POLLING_INTERVAL = 30000; // 30 seconds
const MAX_RECONNECT_DELAY = 30000; // 30 seconds
const INITIAL_RECONNECT_DELAY = 1000; // 1 second

interface UseWebSocketOptions {
  channel?: 'graph' | 'metrics' | 'interventions' | 'alerts';
  onMessage?: (message: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  fallbackPolling?: boolean;
  pollingEndpoint?: string;
  pollingFetcher?: () => Promise<any>;
}

interface UseWebSocketReturn {
  connectionState: ConnectionState;
  lastMessage: WSMessage | null;
  reconnect: () => void;
  disconnect: () => void;
}

/**
 * WebSocket hook with automatic polling fallback.
 *
 * Requirements:
 * - 6.4: Fall back to 30-second polling if WebSocket unavailable
 * - Implement exponential backoff on errors
 */
export function useWebSocket({
  channel = 'graph',
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  fallbackPolling = true,
  pollingEndpoint,
  pollingFetcher,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY);
  const reconnectAttemptsRef = useRef(0);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Start polling fallback
  const startPolling = useCallback(() => {
    if (!fallbackPolling || !pollingFetcher) return;

    console.log('Starting polling fallback');

    // Initial fetch
    pollingFetcher().then(data => {
      if (data) {
        const message: WSMessage = {
          type: 'graph_update',
          timestamp: new Date().toISOString(),
          data,
        };
        setLastMessage(message);
        onMessage?.(message);
      }
    });

    // Set up interval
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const data = await pollingFetcher();
        if (data) {
          const message: WSMessage = {
            type: 'graph_update',
            timestamp: new Date().toISOString(),
            data,
          };
          setLastMessage(message);
          onMessage?.(message);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, POLLING_INTERVAL);
  }, [fallbackPolling, pollingFetcher, onMessage]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Clean up existing connection
    cleanup();

    setConnectionState('connecting');

    try {
      const ws = new WebSocket(`${WS_URL}/ws?channel=${channel}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionState('connected');
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY;
        reconnectAttemptsRef.current = 0;
        onConnect?.();

        // Stop polling if WebSocket connected
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionState('disconnected');
        onDisconnect?.();

        // Try to reconnect with exponential backoff
        if (reconnectAttemptsRef.current < 10) {
          const delay = Math.min(
            reconnectDelayRef.current * Math.pow(2, reconnectAttemptsRef.current),
            MAX_RECONNECT_DELAY
          );

          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        } else {
          // Max reconnect attempts reached, start polling fallback
          console.log('Max reconnect attempts reached, using polling fallback');
          setConnectionState('failed');
          startPolling();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionState('failed');
      if (fallbackPolling) {
        startPolling();
      }
    }
  }, [channel, onConnect, onDisconnect, onError, fallbackPolling, startPolling, cleanup]);

  // Manual reconnect
  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    reconnectDelayRef.current = INITIAL_RECONNECT_DELAY;
    connect();
  }, [connect]);

  // Manual disconnect
  const disconnect = useCallback(() => {
    cleanup();
    setConnectionState('disconnected');
  }, [cleanup]);

  // Connect on mount
  useEffect(() => {
    connect();

    return cleanup;
  }, [connect, cleanup]);

  return {
    connectionState,
    lastMessage,
    reconnect,
    disconnect,
  };
}

/**
 * Hook for polling with exponential backoff.
 *
 * Requirements:
 * - 6.4: Fall back to 30-second polling if WebSocket unavailable
 */
export function usePolling<T>(
  endpoint: string,
  options: {
    interval?: number;
    enabled?: boolean;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
  } = {}
) {
  const {
    interval = 30000,
    enabled = true,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const [retryDelay, setRetryDelay] = useState(interval);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}${endpoint}`);

      // Check for 304 Not Modified (ETag support)
      if (res.status === 304) {
        return; // Use cached data
      }

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const json = await res.json();

      // Extract ETag for caching
      const etag = res.headers.get('ETag');

      setData(json);
      setError(null);
      setRetryDelay(interval); // Reset retry delay on success
      onSuccess?.(json);
    } catch (err) {
      const error = err as Error;
      setError(error);
      onError?.(error);

      // Exponential backoff
      setRetryDelay(prev => Math.min(prev * 2, 300000));
    } finally {
      setLoading(false);
    }
  }, [endpoint, interval, onSuccess, onError]);

  // Polling loop with exponential backoff
  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchData();

    // Set up polling with exponential backoff
    const scheduleNextFetch = () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }

      retryTimeoutRef.current = setTimeout(() => {
        fetchData();
        intervalRef.current = setInterval(fetchData, retryDelay);
      }, retryDelay);
    };

    scheduleNextFetch();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [enabled, fetchData, retryDelay]);

  const refetch = useCallback(() => {
    setLoading(true);
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}

/**
 * Connection status indicator hook.
 */
export function useConnectionStatus(channel: 'graph' | 'metrics' | 'interventions' | 'alerts') {
  const { connectionState } = useWebSocket({
    channel,
    fallbackPolling: false,
  });

  return connectionState;
}
