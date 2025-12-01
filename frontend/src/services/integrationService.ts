/**
 * Integration Service - Orchestrates complete end-to-end functionality
 * Connects frontend components with backend API endpoints and manages workflows
 */

import { apiService } from './apiService';
import { websocketService } from './websocketService';
import { languageService } from './languageService';
import { performanceService } from './performanceService';
import { useAppStore } from '../store/useAppStore';
import { useNotificationStore } from '../store/useNotificationStore';
import { errorService } from './errorService';

export interface SessionData {
  id: string;
  files: Array<{
    id: string;
    name: string;
    content: string;
    language: string;
    lastModified: string;
  }>;
  chatHistory: Array<{
    id: string;
    content: string;
    sender: 'user' | 'ghost';
    timestamp: string;
    context?: any;
  }>;
  preferences: {
    theme: string;
    font_size: number;
    auto_save: boolean;
    ghostPersonality?: string;
  };
  currentLanguage: string;
  lastActivity: string;
}

export interface CodeExecutionWorkflow {
  sessionId: string;
  code: string;
  language: string;
  input?: string;
}

export interface LanguageSwitchWorkflow {
  sessionId: string;
  newLanguage: string;
  preserveSession: boolean;
}

class IntegrationService {
  private autoSaveInterval: NodeJS.Timeout | null = null;
  private sessionSyncInterval: NodeJS.Timeout | null = null;
  private isInitialized = false;
  private isInitializing = false;  // Add flag to prevent concurrent initializations
  private debouncedAutoSave: (() => void) | null = null;
  private throttledSessionSync: (() => void) | null = null;

  /**
   * Initialize the integration service and establish all connections
   */
  async initialize(sessionId?: string): Promise<string> {
    // Prevent multiple simultaneous initializations
    if (this.isInitialized) {
      const { sessionId: currentSessionId } = useAppStore.getState();
      console.log('IntegrationService already initialized, returning current session');
      return currentSessionId || '';
    }

    // Prevent concurrent initialization attempts
    if (this.isInitializing) {
      console.log('IntegrationService initialization already in progress, waiting...');
      // Wait for current initialization to complete
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (this.isInitialized || !this.isInitializing) {
            clearInterval(checkInterval);
            const { sessionId: currentSessionId } = useAppStore.getState();
            resolve(currentSessionId || '');
          }
        }, 100);
      });
    }

    this.isInitializing = true;

    return performanceService.measurePerformance('sessionLoad', async () => {
      try {
        // 1. Preload critical data for better performance
        await performanceService.preloadCriticalData();

        // 2. Optimize for mobile if needed
        performanceService.optimizeForMobile();

        // 3. Health check backend
        const isHealthy = await apiService.healthCheck();
        if (!isHealthy) {
          throw new Error('Backend service is not available');
        }

        // 4. Initialize or restore session
        const finalSessionId = await this.initializeSession(sessionId);

        // 5. Connect WebSocket
        await websocketService.connect(finalSessionId);

        // 6. Start auto-save and sync intervals
        this.startAutoSave();
        this.startSessionSync();

        // 7. Set up hook integrations
        this.setupHookIntegrations();

        // 8. Set up caching for better performance
        this.setupCaching();

        this.isInitialized = true;
        this.isInitializing = false;

        const { showSuccess } = useNotificationStore.getState();
        showSuccess(
          '👻 Welcome to the Spirit Realm',
          'All systems are haunted and ready for coding!',
          { duration: 3000 }
        );

        return finalSessionId;
      } catch (error) {
        this.isInitializing = false;
        errorService.handleError(error as Error, {
          component: 'IntegrationService',
          action: 'initialize',
        });
        throw error;
      }
    });
  }

  /**
   * Execute complete code execution workflow
   */
  async executeCodeWorkflow(workflow: CodeExecutionWorkflow): Promise<void> {
    return performanceService.measurePerformance('codeExecution', async () => {
      const { setExecuting } = useAppStore.getState();

      try {
        // 1. Validate code and language
        const isValid = await languageService.validateCode(workflow.code, workflow.language);
        if (!isValid) {
          throw new Error('Code validation failed');
        }

        // 2. Trigger on_run hook
        websocketService.triggerHook('on_run', {
          code: workflow.code,
          language: workflow.language,
          timestamp: new Date().toISOString(),
        });

        // 3. Start execution via WebSocket (real-time updates)
        setExecuting(true);
        websocketService.executeCode(workflow.code, workflow.language, workflow.input);

        // 5. The execution results will be handled by WebSocket listeners
        // This includes on_error hooks if execution fails

      } catch (error) {
        setExecuting(false);

        // Trigger on_error hook
        websocketService.triggerHook('on_error', {
          error: (error as Error).message,
          code: workflow.code,
          language: workflow.language,
          timestamp: new Date().toISOString(),
        });

        errorService.handleError(error as Error, {
          component: 'IntegrationService',
          action: 'executeCodeWorkflow',
          sessionId: workflow.sessionId,
        });

        throw error;
      }
    });
  }

  /**
   * Handle seamless language switching with session preservation
   */
  async switchLanguageWorkflow(workflow: LanguageSwitchWorkflow): Promise<void> {
    return performanceService.measurePerformance('languageSwitch', async () => {
      const { currentFile, addFile, setCurrentLanguage } = useAppStore.getState();

      try {
        // 1. Get language configuration
        const languageConfig = await languageService.getLanguageInfo(workflow.newLanguage);
        if (!languageConfig) {
          throw new Error(`Language ${workflow.newLanguage} not supported`);
        }

        // 2. Save current work if preserveSession is true
        if (workflow.preserveSession && currentFile) {
          await this.saveCurrentFile();
        }

        // 3. Update language in store
        setCurrentLanguage(workflow.newLanguage);

        // 4. Get template for the new language
        const template = await languageService.getLanguageTemplate(workflow.newLanguage);
        const templateCode = template || `# Welcome to ${languageConfig.name}\n# Start coding here\n`;

        // 5. Create a new file with the template
        const newFile = {
          id: `file_${Date.now()}`,
          name: `untitled${languageConfig.extension}`,
          content: templateCode,
          language: workflow.newLanguage,
          lastModified: new Date(),
        };

        addFile(newFile);

        // 5. Load language-specific examples (optional)
        await languageService.getLanguageExamples(workflow.newLanguage).catch(() => {
          // Examples are optional, don't fail if not available
        });

        // 6. Notify Ghost AI about language switch
        websocketService.sendGhostMessage(
          `I've switched to ${workflow.newLanguage}. Any spooky wisdom for this realm?`,
          {
            language: workflow.newLanguage,
            currentCode: currentFile?.content,
          }
        );

        const { showInfo } = useNotificationStore.getState();
        showInfo(
          `🔮 Switched to ${languageConfig.name}`,
          `The spirits now speak in ${languageConfig.name}`,
          { duration: 2000 }
        );

      } catch (error) {
        errorService.handleError(error as Error, {
          component: 'IntegrationService',
          action: 'switchLanguageWorkflow',
          sessionId: workflow.sessionId,
        });
        throw error;
      }
    });
  }

  /**
   * Handle Ghost AI interaction workflow
   */
  async ghostInteractionWorkflow(message: string, _context?: any): Promise<void> {
    return performanceService.measurePerformance('aiResponse', async () => {
      const { sessionId } = useAppStore.getState();

      try {
        // 1. Send message via WebSocket for real-time response
        websocketService.sendChatMessage(message);

        // 2. The response will be handled by WebSocket listeners

      } catch (error) {
        errorService.handleError(error as Error, {
          component: 'IntegrationService',
          action: 'ghostInteractionWorkflow',
          sessionId: sessionId || undefined,
        });
        throw error;
      }
    });
  }

  /**
   * Save current file and trigger on_save hook
   */
  async saveCurrentFile(): Promise<void> {
    const { currentFile, sessionId } = useAppStore.getState();

    if (!currentFile || !sessionId) {
      return;
    }

    try {
      // 1. Save file via API
      await apiService.put(`/api/v1/sessions/${sessionId}/files/${currentFile.id}`, {
        content: currentFile.content,
        lastModified: new Date().toISOString(),
      });

      // 2. Save via WebSocket for real-time sync
      websocketService.saveFile(currentFile);

      // 3. Trigger on_save hook
      websocketService.triggerHook('on_save', {
        file: currentFile,
        timestamp: new Date().toISOString(),
      });

      const { showSuccess } = useNotificationStore.getState();
      showSuccess(
        '💾 File Saved',
        `${currentFile.name} has been preserved in the ethereal realm`,
        { duration: 1500 }
      );

    } catch (error) {
      errorService.handleError(error as Error, {
        component: 'IntegrationService',
        action: 'saveCurrentFile',
        sessionId,
      });
      throw error;
    }
  }

  /**
   * Restore session from backend
   */
  async restoreSession(sessionId: string): Promise<SessionData | null> {
    try {
      const response = await apiService.get<SessionData>(`/api/v1/sessions/${sessionId}`);

      if (response.success && response.data) {
        // Update store with restored data
        const {
          setSessionId,
          addFile,
          setCurrentLanguage,
          addChatMessage,
          updatePreferences
        } = useAppStore.getState();

        console.log('Session restored successfully:', response.data.id);
        setSessionId(response.data.id);
        setCurrentLanguage(response.data.currentLanguage);

        // Update preferences with safe defaults
        if (response.data.preferences) {
          updatePreferences({
            theme: (response.data.preferences.theme as 'ghost-dark' | 'ghost-light') || 'ghost-dark',
            fontSize: response.data.preferences.font_size || 14,
            autoSave: response.data.preferences.auto_save ?? true,
            ghostPersonality: 'spooky',
          });
        }

        // Restore files
        response.data.files.forEach(file => {
          addFile({
            ...file,
            lastModified: new Date(file.lastModified),
          });
        });

        // Restore chat history
        response.data.chatHistory.forEach(message => {
          addChatMessage({
            ...message,
            timestamp: new Date(message.timestamp),
          });
        });

        return response.data;
      }

      return null;
    } catch (error) {
      errorService.handleError(error as Error, {
        component: 'IntegrationService',
        action: 'restoreSession',
        sessionId: sessionId || undefined,
      });
      return null;
    }
  }

  /**
   * Create new session
   */
  async createSession(): Promise<string> {
    try {
      const { preferences, currentLanguage } = useAppStore.getState();
      const response = await apiService.post<{ session: { id: string } }>('/api/v1/sessions', {
        current_language: currentLanguage,
        preferences: {
          theme: preferences.theme as 'ghost-dark' | 'ghost-light',
          font_size: preferences.fontSize,
          auto_save: preferences.autoSave,
        },
      });

      if (response.success && response.data?.session) {
        console.log('Session created successfully:', response.data.session.id);
        useAppStore.getState().setSessionId(response.data.session.id);
        return response.data.session.id;
      }

      throw new Error('Failed to create session');
    } catch (error) {
      errorService.handleError(error as Error, {
        component: 'IntegrationService',
        action: 'createSession',
      });
      throw error;
    }
  }

  /**
   * Performance optimization: Cache frequently used data
   */
  private setupCaching(): void {
    // Set up editor optimizations
    performanceService.optimizeEditor();

    // Cache user preferences in performance service
    const preferences = localStorage.getItem('ghost-ide-preferences');
    if (preferences) {
      try {
        const parsed = JSON.parse(preferences);
        performanceService.set('user_preferences', parsed, 3600000); // Cache for 1 hour
        useAppStore.getState().updatePreferences(parsed);
      } catch (error) {
        console.warn('Failed to parse cached preferences:', error);
      }
    }

    // Set up debounced auto-save
    this.debouncedAutoSave = performanceService.debounce(
      () => this.saveCurrentFile(),
      2000 // 2 second debounce
    );

    // Set up throttled session sync
    this.throttledSessionSync = performanceService.throttle(
      () => this.syncSession(),
      10000 // 10 second throttle
    );
  }

  /**
   * Set up hook integrations for automated AI responses
   */
  private setupHookIntegrations(): void {
    // These are handled by the WebSocket service and backend hook manager
    // The integration service just needs to ensure hooks are triggered at the right times
    console.log('Hook integrations set up for automated Ghost AI responses');
  }

  /**
   * Initialize session (create new or restore existing)
   */
  private async initializeSession(sessionId?: string): Promise<string> {
    const { sessionId: currentSessionId, setSessionId } = useAppStore.getState();
    console.log('initializeSession called:', { urlSessionId: sessionId, storeSessionId: currentSessionId });

    // If we already have this session in the store, don't re-initialize
    if (sessionId && currentSessionId === sessionId) {
      console.log('Session already initialized:', sessionId);
      return sessionId;
    }

    if (sessionId) {
      // Try to restore existing session
      const restored = await this.restoreSession(sessionId);
      if (restored) {
        console.log('Session restored, setting in store:', sessionId);
        setSessionId(sessionId);
        return sessionId;
      }
    }

    // Create new session only if we don't have a sessionId in URL
    if (!sessionId) {
      const newSessionId = await this.createSession();
      console.log('New session created:', newSessionId);
      if (newSessionId) {
        setSessionId(newSessionId);
        console.log('Session ID set in store:', newSessionId);
      }
      return newSessionId || '';
    }

    // Fallback: ensure we set whatever sessionId we have
    if (sessionId && !currentSessionId) {
      console.log('Setting fallback sessionId in store:', sessionId);
      setSessionId(sessionId);
    }

    return sessionId;
  }

  /**
   * Start auto-save functionality
   */
  private startAutoSave(): void {
    const { preferences } = useAppStore.getState();

    if (preferences.autoSave && this.debouncedAutoSave) {
      this.autoSaveInterval = setInterval(() => {
        this.debouncedAutoSave!();
      }, 30000); // Auto-save every 30 seconds
    }
  }

  /**
   * Start session synchronization
   */
  private startSessionSync(): void {
    if (this.throttledSessionSync) {
      this.sessionSyncInterval = setInterval(() => {
        this.throttledSessionSync!();
      }, 60000); // Sync every minute
    }
  }

  /**
   * Sync session data with backend
   */
  private async syncSession(): Promise<void> {
    const { sessionId, files, chatMessages, preferences } = useAppStore.getState();

    if (sessionId) {
      try {
        await apiService.put(`/api/v1/sessions/${sessionId}/sync`, {
          files: files.map(f => ({
            ...f,
            lastModified: f.lastModified.toISOString(),
          })),
          chatHistory: chatMessages.map(m => ({
            ...m,
            timestamp: m.timestamp.toISOString(),
          })),
          preferences,
          lastActivity: new Date().toISOString(),
        });
      } catch (error) {
        console.warn('Session sync failed:', error);
      }
    }
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }

    if (this.sessionSyncInterval) {
      clearInterval(this.sessionSyncInterval);
      this.sessionSyncInterval = null;
    }

    // Clean up performance service
    performanceService.cleanup();

    websocketService.disconnect();
    this.isInitialized = false;
  }

  /**
   * Check if service is initialized
   */
  isReady(): boolean {
    return this.isInitialized && websocketService.isConnected();
  }
}

export const integrationService = new IntegrationService();