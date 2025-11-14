import { useEffect, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { socketService } from '../services/socketService';

export const useSocket = (sessionId?: string) => {
  const { isConnected } = useAppStore();

  const connect = useCallback(async (id?: string) => {
    try {
      await socketService.connect(id || sessionId);
    } catch (error) {
      console.error('Failed to connect to socket:', error);
    }
  }, [sessionId]);

  const disconnect = useCallback(() => {
    socketService.disconnect();
  }, []);

  const executeCode = useCallback((code: string, language: string, input?: string) => {
    try {
      socketService.executeCode(code, language, input);
    } catch (error) {
      console.error('Failed to execute code:', error);
      throw error;
    }
  }, []);

  const sendChatMessage = useCallback((message: string) => {
    try {
      socketService.sendChatMessage(message);
    } catch (error) {
      console.error('Failed to send chat message:', error);
      throw error;
    }
  }, []);

  const saveFile = useCallback((file: {
    id: string;
    name: string;
    content: string;
    language: string;
  }) => {
    try {
      socketService.saveFile(file);
    } catch (error) {
      console.error('Failed to save file:', error);
      throw error;
    }
  }, []);

  const triggerHook = useCallback((
    hookType: 'on_run' | 'on_error' | 'on_save',
    data: any
  ) => {
    try {
      socketService.triggerHook(hookType, data);
    } catch (error) {
      console.error('Failed to trigger hook:', error);
    }
  }, []);

  useEffect(() => {
    // Auto-connect if sessionId is provided and not already connected
    if (sessionId && !isConnected) {
      connect(sessionId);
    }

    // Cleanup on unmount
    return () => {
      // Don't auto-disconnect as user might navigate between pages
    };
  }, [sessionId, isConnected, connect]);

  return {
    isConnected,
    connect,
    disconnect,
    executeCode,
    sendChatMessage,
    saveFile,
    triggerHook,
  };
};