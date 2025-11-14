import { io, Socket } from 'socket.io-client';
import { useAppStore } from '../store/useAppStore';
import { useNotificationStore } from '../store/useNotificationStore';
import { errorService } from './errorService';

export interface SocketMessage {
  type: 'execution_start' | 'execution_output' | 'execution_complete' | 'execution_error' | 'ghost_response' | 'session_update';
  data: any;
  sessionId?: string;
}

class SocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' = 'disconnected';
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private lastHeartbeat: Date | null = null;

  connect(sessionId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.connectionState === 'connecting' || this.connectionState === 'connected') {
        resolve();
        return;
      }

      this.connectionState = 'connecting';
      const serverUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      
      this.socket = io(serverUrl, {
        transports: ['websocket'],
        query: sessionId ? { sessionId } : {},
        timeout: 10000,
        forceNew: true,
      });

      this.socket.on('connect', () => {
        console.log('Connected to server');
        this.connectionState = 'connected';
        useAppStore.getState().setConnected(true);
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        
        const { showSuccess } = useNotificationStore.getState();
        if (this.reconnectAttempts > 0) {
          showSuccess(
            '👻 Reconnected to the Spirit Realm',
            'The ethereal connection has been restored.',
            { duration: 3000 }
          );
        }
        
        resolve();
      });

      this.socket.on('disconnect', (reason) => {
        console.log('Disconnected from server:', reason);
        this.connectionState = 'disconnected';
        useAppStore.getState().setConnected(false);
        this.stopHeartbeat();
        
        errorService.logError(new Error(`Socket disconnected: ${reason}`), {
          component: 'SocketService',
          action: 'disconnect',
        });

        // Only show notification for unexpected disconnections
        if (reason !== 'io client disconnect') {
          const { showWarning } = useNotificationStore.getState();
          showWarning(
            '⚡ Connection to Spirit Realm Lost',
            'Attempting to reconnect to the ethereal network...',
            { duration: 4000 }
          );
        }
        
        this.handleReconnect();
      });

      this.socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        this.connectionState = 'disconnected';
        useAppStore.getState().setConnected(false);
        
        errorService.handleError(error, {
          component: 'SocketService',
          action: 'connect',
        }, false); // Don't show notification here, we'll handle it in reconnect logic
        
        reject(error);
      });

      // Handle incoming messages
      this.socket.on('message', this.handleMessage.bind(this));
      
      // Handle specific event types
      this.socket.on('execution_start', () => {
        useAppStore.getState().setExecuting(true);
      });

      this.socket.on('execution_output', (data) => {
        // Handle streaming output
        useAppStore.getState().appendExecutionOutput(data.stdout, data.stderr);
      });

      this.socket.on('execution_complete', (data) => {
        useAppStore.getState().setExecuting(false);
        useAppStore.getState().setExecutionResult(data);
        // Add to history if execution was successful or had meaningful output
        if (data.stdout || data.stderr || data.executionTime > 0) {
          useAppStore.getState().addToExecutionHistory(data);
        }
      });

      this.socket.on('execution_error', (data) => {
        useAppStore.getState().setExecuting(false);
        useAppStore.getState().setExecutionResult({
          stdout: '',
          stderr: data.error,
          exitCode: 1,
          executionTime: 0,
        });
      });

      this.socket.on('ghost_response', (data) => {
        useAppStore.getState().setGhostTyping(false);
        useAppStore.getState().addChatMessage({
          id: Date.now().toString(),
          content: data.message,
          sender: 'ghost',
          timestamp: new Date(),
          context: data.context,
        });
      });

      this.socket.on('ghost_typing', () => {
        useAppStore.getState().setGhostTyping(true);
      });
    });
  }

  private handleMessage(message: SocketMessage) {
    console.log('Received message:', message);
    // Handle generic messages if needed
  }

  private handleReconnect() {
    if (this.connectionState === 'reconnecting' || this.connectionState === 'connected') {
      return;
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.connectionState = 'reconnecting';
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
      
      setTimeout(() => {
        if (this.socket && this.connectionState === 'reconnecting') {
          this.socket.connect();
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.connectionState = 'disconnected';
      
      const { showError } = useNotificationStore.getState();
      showError(
        '💀 Connection to Spirit Realm Failed',
        'Unable to establish connection after multiple attempts. Please refresh the page.',
        {
          persistent: true,
          action: {
            label: 'Refresh Page',
            onClick: () => window.location.reload(),
          },
        }
      );
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.lastHeartbeat = new Date();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping');
        this.lastHeartbeat = new Date();
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  disconnect() {
    if (this.socket) {
      this.connectionState = 'disconnected';
      this.stopHeartbeat();
      this.socket.disconnect();
      this.socket = null;
      useAppStore.getState().setConnected(false);
      this.reconnectAttempts = 0;
    }
  }

  // Send messages to server with error handling
  executeCode(code: string, language: string, input?: string) {
    return this.withErrorHandling(() => {
      if (!this.socket?.connected) {
        throw new Error('Not connected to server');
      }

      this.socket.emit('execute_code', {
        code,
        language,
        input,
        sessionId: useAppStore.getState().sessionId,
      });
    }, 'executeCode');
  }

  sendChatMessage(message: string) {
    return this.withErrorHandling(() => {
      if (!this.socket?.connected) {
        throw new Error('Not connected to server');
      }

      const chatMessage = {
        id: Date.now().toString(),
        content: message,
        sender: 'user' as const,
        timestamp: new Date(),
      };

      useAppStore.getState().addChatMessage(chatMessage);
      useAppStore.getState().setGhostTyping(true);

      this.socket.emit('ghost_chat', {
        message,
        sessionId: useAppStore.getState().sessionId,
        context: {
          currentCode: useAppStore.getState().currentFile?.content,
          language: useAppStore.getState().currentLanguage,
          recentOutput: useAppStore.getState().executionResult,
        },
      });
    }, 'sendChatMessage');
  }

  sendGhostMessage(message: string, context?: {
    currentCode?: string;
    language?: string;
    recentOutput?: any;
  }) {
    return this.withErrorHandling(() => {
      if (!this.socket?.connected) {
        throw new Error('Not connected to server');
      }

      useAppStore.getState().setGhostTyping(true);

      this.socket.emit('ghost_chat', {
        message,
        sessionId: useAppStore.getState().sessionId,
        context: context || {
          currentCode: useAppStore.getState().currentFile?.content,
          language: useAppStore.getState().currentLanguage,
          recentOutput: useAppStore.getState().executionResult,
        },
      });
    }, 'sendGhostMessage');
  }

  saveFile(file: { id: string; name: string; content: string; language: string }) {
    return this.withErrorHandling(() => {
      if (!this.socket?.connected) {
        throw new Error('Not connected to server');
      }

      this.socket.emit('save_file', {
        ...file,
        sessionId: useAppStore.getState().sessionId,
      });
    }, 'saveFile');
  }

  triggerHook(hookType: 'on_run' | 'on_error' | 'on_save', data: any) {
    if (!this.socket?.connected) {
      return;
    }

    this.socket.emit('hook_event', {
      type: hookType,
      data,
      sessionId: useAppStore.getState().sessionId,
    });
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionState(): string {
    return this.connectionState;
  }

  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  getLastHeartbeat(): Date | null {
    return this.lastHeartbeat;
  }

  private withErrorHandling<T>(fn: () => T, action: string): T {
    try {
      return fn();
    } catch (error) {
      errorService.handleError(error as Error, {
        component: 'SocketService',
        action,
        sessionId: useAppStore.getState().sessionId || undefined,
      });
      throw error;
    }
  }
}

export const socketService = new SocketService();