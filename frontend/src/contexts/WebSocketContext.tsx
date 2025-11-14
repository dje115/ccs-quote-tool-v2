import React, { createContext, useContext, ReactNode } from 'react';
import { useWebSocket, UseWebSocketReturn } from '../hooks/useWebSocket';

interface WebSocketContextType extends UseWebSocketReturn {}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

/**
 * WebSocket Context Provider
 * Provides WebSocket connection and event subscription to all child components
 */
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const websocket = useWebSocket();

  return (
    <WebSocketContext.Provider value={websocket}>
      {children}
    </WebSocketContext.Provider>
  );
};

/**
 * Hook to access WebSocket context
 * @throws Error if used outside WebSocketProvider
 */
export const useWebSocketContext = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
};

