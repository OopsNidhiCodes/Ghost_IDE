import React, { useEffect, useState } from 'react';
import { Wifi, WifiOff, AlertCircle, RefreshCw } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { websocketService } from '../../services/websocketService';

export const ConnectionStatus: React.FC = () => {
  const { isConnected } = useAppStore();
  const [connectionState, setConnectionState] = useState<string>('disconnected');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setConnectionState(websocketService.getConnectionState());
      setReconnectAttempts(websocketService.getReconnectAttempts());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleReconnect = () => {
    websocketService.disconnect();
    setTimeout(() => {
      const { sessionId } = useAppStore.getState();
      websocketService.connect(sessionId || undefined);
    }, 1000);
  };

  const getStatusIcon = () => {
    switch (connectionState) {
      case 'connected':
        return <Wifi className="w-4 h-4 text-green-400" />;
      case 'connecting':
      case 'reconnecting':
        return <RefreshCw className="w-4 h-4 text-yellow-400 animate-spin" />;
      default:
        return <WifiOff className="w-4 h-4 text-red-400" />;
    }
  };

  const getStatusText = () => {
    switch (connectionState) {
      case 'connected':
        return 'Connected to Spirit Realm';
      case 'connecting':
        return 'Connecting to Spirit Realm...';
      case 'reconnecting':
        return `Reconnecting... (${reconnectAttempts}/5)`;
      default:
        return 'Disconnected from Spirit Realm';
    }
  };

  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'text-green-400';
      case 'connecting':
      case 'reconnecting':
        return 'text-yellow-400';
      default:
        return 'text-red-400';
    }
  };

  // Don't show if connected and stable
  if (isConnected && connectionState === 'connected') {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <div className="bg-ghost-800 border border-ghost-600 rounded-lg p-3 shadow-lg max-w-sm">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div className="flex-1">
            <p className={`text-sm font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </p>
            {connectionState === 'disconnected' && reconnectAttempts >= 5 && (
              <button
                onClick={handleReconnect}
                className="text-xs text-purple-400 hover:text-purple-300 underline mt-1"
              >
                Try Again
              </button>
            )}
          </div>
          {connectionState === 'disconnected' && reconnectAttempts >= 5 && (
            <AlertCircle className="w-4 h-4 text-red-400" />
          )}
        </div>
      </div>
    </div>
  );
};