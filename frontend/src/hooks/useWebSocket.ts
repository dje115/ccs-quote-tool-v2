import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketEvent {
  type: string;
  tenant_id: string;
  data: any;
  timestamp: string;
}

interface UseWebSocketReturn {
  subscribe: (eventType: string, callback: (event: WebSocketEvent) => void) => () => void;
  unsubscribe: (eventType: string, callback: (event: WebSocketEvent) => void) => void;
  isConnected: boolean;
  tenantId: string | null;
}

/**
 * WebSocket hook for real-time updates
 * Manages WebSocket connection with automatic reconnection
 * Provides event subscription/unsubscription API
 */
export const useWebSocket = (): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [tenantId, setTenantId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const eventHandlersRef = useRef<Map<string, Set<(event: WebSocketEvent) => void>>>(new Map());
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connections
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      console.log('[WebSocket] Connection already in progress, skipping');
      return;
    }
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected, skipping');
      return;
    }

    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.log('[WebSocket] No auth token, skipping connection');
      return;
    }

    // Get WebSocket URL from environment or construct from API URL
    // SECURITY: Token will be sent as first message, not in URL (prevents logging/caching)
    // Use same base URL logic as api.ts for consistency
    const getWebSocketUrl = (): string => {
      // 1. Check for dedicated WebSocket URL environment variable
      if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_WS_URL) {
        return import.meta.env.VITE_WS_URL;
      }
      
      // 2. Construct from API URL (same source as api.ts)
      const API_BASE_URL = typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL
        ? import.meta.env.VITE_API_URL
        : 'http://localhost:8000';
      
      // Convert HTTP/HTTPS to WS/WSS properly
      if (API_BASE_URL.startsWith('https://')) {
        return API_BASE_URL.replace(/^https/, 'wss');
      } else if (API_BASE_URL.startsWith('http://')) {
        return API_BASE_URL.replace(/^http/, 'ws');
      }
      
      // 3. Fallback: construct from current window location
      if (typeof window !== 'undefined') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host.replace(':3000', ':8000');
        return `${protocol}//${host}`;
      }
      
      // 4. Final fallback
      return 'ws://localhost:8000';
    };
    
    const wsBaseUrl = getWebSocketUrl();
    const wsUrl = `${wsBaseUrl}/api/v1/ws`;

    try {
      // Close existing connection if any
      if (wsRef.current) {
        try {
          wsRef.current.close(1000, 'Reconnecting');
        } catch (e) {
          // Ignore errors
        }
      }

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        
        // SECURITY: Send token as first message instead of query parameter
        // This prevents token from appearing in server logs, caches, or URL history
        try {
          ws.send(JSON.stringify({ type: 'auth', token }));
        } catch (error) {
          console.error('[WebSocket] Error sending auth token:', error);
          ws.close();
          return;
        }
        
        // Store ping interval ID for cleanup
        const pingIntervalId = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            try {
              ws.send('ping');
            } catch (error) {
              console.error('[WebSocket] Error sending ping:', error);
              clearInterval(pingIntervalId);
            }
          } else {
            clearInterval(pingIntervalId);
          }
        }, 30000); // Ping every 30 seconds
        
        // Store interval ID in wsRef for cleanup
        (ws as any).pingIntervalId = pingIntervalId;
      };

      ws.onmessage = (event) => {
        try {
          // Handle pong response (plain text, not JSON)
          if (event.data === 'pong') {
            return;
          }
          
          const message = JSON.parse(event.data);
          
          // Handle connection established message
          if (message.type === 'connection.established') {
            setTenantId(message.tenant_id);
            console.log('[WebSocket] Connection established for tenant:', message.tenant_id);
            return;
          }

          // Handle error messages
          if (message.type === 'error') {
            console.error('[WebSocket] Error:', message.message);
            return;
          }

          // Validate tenant_id matches
          if (message.tenant_id && tenantId && message.tenant_id !== tenantId) {
            console.warn('[WebSocket] Received event for different tenant, ignoring');
            return;
          }

          // Dispatch event to all subscribers
          const handlers = eventHandlersRef.current.get(message.type);
          if (handlers) {
            handlers.forEach((callback) => {
              try {
                callback(message);
              } catch (error) {
                console.error('[WebSocket] Error in event handler:', error);
              }
            });
          }

          // Also dispatch to wildcard subscribers (e.g., 'ai_analysis.*')
          const wildcardHandlers = eventHandlersRef.current.get('*');
          if (wildcardHandlers) {
            wildcardHandlers.forEach((callback) => {
              try {
                callback(message);
              } catch (error) {
                console.error('[WebSocket] Error in wildcard event handler:', error);
              }
            });
          }
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected', event.code, event.reason);
        setIsConnected(false);
        setTenantId(null);
        
        // Clear ping interval if it exists
        if ((ws as any).pingIntervalId) {
          clearInterval((ws as any).pingIntervalId);
        }

        // Attempt to reconnect only if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`[WebSocket] Reconnecting (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay * reconnectAttemptsRef.current);
        } else if (event.code === 1000) {
          console.log('[WebSocket] Normal closure, not reconnecting');
        } else {
          console.error('[WebSocket] Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[WebSocket] Failed to connect:', error);
      setIsConnected(false);
    }
  }, []); // Remove tenantId dependency to prevent reconnection loops

  useEffect(() => {
    // Connect on mount
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        // Clear ping interval if it exists
        if ((wsRef.current as any).pingIntervalId) {
          clearInterval((wsRef.current as any).pingIntervalId);
        }
        // Close with normal closure code
        try {
          wsRef.current.close(1000, 'Component unmounting');
        } catch (error) {
          // Ignore errors during cleanup
        }
        wsRef.current = null;
      }
    };
  }, [connect]);

  const subscribe = useCallback((eventType: string, callback: (event: WebSocketEvent) => void) => {
    if (!eventHandlersRef.current.has(eventType)) {
      eventHandlersRef.current.set(eventType, new Set());
    }
    eventHandlersRef.current.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      const handlers = eventHandlersRef.current.get(eventType);
      if (handlers) {
        handlers.delete(callback);
        if (handlers.size === 0) {
          eventHandlersRef.current.delete(eventType);
        }
      }
    };
  }, []);

  const unsubscribe = useCallback((eventType: string, callback: (event: WebSocketEvent) => void) => {
    const handlers = eventHandlersRef.current.get(eventType);
    if (handlers) {
      handlers.delete(callback);
      if (handlers.size === 0) {
        eventHandlersRef.current.delete(eventType);
      }
    }
  }, []);

  return {
    subscribe,
    unsubscribe,
    isConnected,
    tenantId,
  };
};

