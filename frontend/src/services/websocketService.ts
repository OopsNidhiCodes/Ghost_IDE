/**
 * Native WebSocket Service for GhostIDE
 * Connects to FastAPI WebSocket endpoints
 */

import { useAppStore } from '../store/useAppStore';
import { useNotificationStore } from '../store/useNotificationStore';
import { errorService } from './errorService';

export interface WebSocketMessage {
  type: 'execution_start' | 'execution_output' | 'execution_complete' | 'execution_error' | 'ghost_response' | 'ghost_typing' | 'session_update' | 'connect' | 'pong' | 'ai_response' | 'ai_typing' | 'file_saved' | 'hook_triggered';
  data: any;
  sessionId?: string;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private connectionState: 'disconnected' | 'connecting' | 'connected' | 'reconnecting' = 'disconnected';
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private lastHeartbeat: Date | null = null;
  private currentSessionId: string | null = null;

  connect(sessionId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.connectionState === 'connecting' || this.connectionState === 'connected') {
        resolve();
        return;
      }

      this.connectionState = 'connecting';
      this.currentSessionId = sessionId || 'default';

      const serverUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      const wsUrl = serverUrl.replace('http', 'ws');
      const fullUrl = `${wsUrl}/ws/${this.currentSessionId}`;

      console.log('Connecting to WebSocket:', fullUrl);

      try {
        this.ws = new WebSocket(fullUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
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
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.connectionState = 'disconnected';
          useAppStore.getState().setConnected(false);
          this.stopHeartbeat();

          errorService.logError(new Error(`WebSocket disconnected: ${event.code} ${event.reason}`), {
            component: 'WebSocketService',
            action: 'disconnect',
          });

          // Only show notification for unexpected disconnections
          if (event.code !== 1000) { // 1000 = normal closure
            const { showWarning } = useNotificationStore.getState();
            showWarning(
              '⚡ Connection to Spirit Realm Lost',
              'Attempting to reconnect to the ethereal network...',
              { duration: 4000 }
            );
          }

          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.connectionState = 'disconnected';
          useAppStore.getState().setConnected(false);

          errorService.handleError(new Error('WebSocket connection error'), {
            component: 'WebSocketService',
            action: 'connect',
          }, false);

          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        this.connectionState = 'disconnected';
        reject(error);
      }
    });
  }

  private handleMessage(message: WebSocketMessage) {
    console.log('Received WebSocket message:', message);

    switch (message.type) {
      case 'connect':
        console.log('Connection acknowledged by server');
        break;

      case 'pong':
        console.log('Heartbeat pong received');
        break;

      case 'execution_start':
        useAppStore.getState().setExecuting(true);
        break;

      case 'execution_output':
        // Backend streams execution output as { output: str, stream: 'stdout'|'stderr' }
        try {
          const out = message.data?.output || '';
          const stream = message.data?.stream || 'stdout';
          if (stream === 'stderr') {
            useAppStore.getState().appendExecutionOutput(undefined, out);
          } else {
            useAppStore.getState().appendExecutionOutput(out, undefined);
          }
        } catch (e) {
          console.warn('Malformed execution_output payload', message.data);
        }
        break;

      case 'execution_complete':
        useAppStore.getState().setExecuting(false);
        // Backend wraps the result under `data.result` (see MessageRouter.notify_execution_complete)
        // Accept either shape for compatibility: { result: {...} } or direct result object
        try {
          const result = (message.data && (message.data.result ?? message.data)) || null;
          useAppStore.getState().setExecutionResult(result);
          const execTime = result?.executionTime ?? result?.execution_time ?? 0;
          if (result && (result.stdout || result.stderr || execTime > 0)) {
            useAppStore.getState().addToExecutionHistory(result);
          }
        } catch (e) {
          console.warn('Malformed execution_complete payload', message.data);
        }
        break;

      case 'execution_error':
        useAppStore.getState().setExecuting(false);
        useAppStore.getState().setExecutionResult({
          stdout: '',
          stderr: message.data.error,
          exitCode: 1,
          executionTime: 0,
        });
        break;

      case 'ai_response':
      case 'ghost_response':
        useAppStore.getState().setGhostTyping(false);
        useAppStore.getState().addChatMessage({
          id: Date.now().toString(),
          content: message.data.message,
          sender: 'ghost',
          timestamp: new Date(),
          context: message.data.context,
        });
        break;

      case 'ai_typing':
      case 'ghost_typing':
        useAppStore.getState().setGhostTyping(message.data.is_typing ?? true);
        break;

      case 'file_saved':
        // Informational: file saved notification from backend
        console.log('File saved notification received', message.data);
        break;

      default:
        console.warn('Unknown message type:', message.type, message);
    }
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
        if (this.connectionState === 'reconnecting') {
          this.connect(this.currentSessionId || undefined);
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
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', data: {} });
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
    if (this.ws) {
      this.connectionState = 'disconnected';
      this.stopHeartbeat();
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
      useAppStore.getState().setConnected(false);
      this.reconnectAttempts = 0;
    }
  }

  // Send messages to server with error handling
  private send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  executeCode(code: string, language: string, input?: string) {
    return this.withErrorHandling(() => {
      console.log('Executing code via WebSocket:', { language, codeLength: code.length, hasInput: !!input });

      this.send({
        type: 'execute_code',
        data: {
          code,
          language,
          input,
          sessionId: useAppStore.getState().sessionId,
        }
      });

      console.log('Execute code message sent');
    }, 'executeCode');
  }

  sendChatMessage(message: string) {
    return this.withErrorHandling(() => {
      const chatMessage = {
        id: Date.now().toString(),
        content: message,
        sender: 'user' as const,
        timestamp: new Date(),
      };

      useAppStore.getState().addChatMessage(chatMessage);
      useAppStore.getState().setGhostTyping(true);

      this.send({
        type: 'ghost_chat',
        data: {
          message,
          sessionId: useAppStore.getState().sessionId,
          context: {
            currentCode: useAppStore.getState().currentFile?.content,
            language: useAppStore.getState().currentLanguage,
            recentOutput: useAppStore.getState().executionResult,
          },
        }
      });
    }, 'sendChatMessage');
  }

  sendGhostMessage(message: string, context?: any) {
    return this.withErrorHandling(() => {
      console.log('Sending Ghost AI message via WebSocket:', { messageLength: message.length, hasContext: !!context });

      useAppStore.getState().setGhostTyping(true);

      this.send({
        type: 'ghost_chat',
        data: {
          message,
          sessionId: useAppStore.getState().sessionId,
          context: context || {
            currentCode: useAppStore.getState().currentFile?.content,
            language: useAppStore.getState().currentLanguage,
            recentOutput: useAppStore.getState().executionResult,
          },
        }
      });

      console.log('Ghost message sent');
    }, 'sendGhostMessage');
  }

  saveFile(file: { id: string; name: string; content: string; language: string }) {
    return this.withErrorHandling(() => {
      this.send({
        type: 'save_file',
        data: {
          ...file,
          sessionId: useAppStore.getState().sessionId,
        }
      });
    }, 'saveFile');
  }

  triggerHook(hookType: 'on_run' | 'on_error' | 'on_save', data: any) {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      return;
    }

    this.send({
      type: 'hook_event',
      data: {
        type: hookType,
        data,
        sessionId: useAppStore.getState().sessionId,
      }
    });
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
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
        component: 'WebSocketService',
        action,
        sessionId: useAppStore.getState().sessionId || undefined,
      });
      throw error;
    }
  }
}

export const websocketService = new WebSocketService();