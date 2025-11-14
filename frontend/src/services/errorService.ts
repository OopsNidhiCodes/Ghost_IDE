import { useNotificationStore } from '../store/useNotificationStore';

export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  sessionId?: string;
  additionalData?: Record<string, any>;
}

export interface RetryConfig {
  maxAttempts: number;
  delay: number;
  backoff?: 'linear' | 'exponential';
  shouldRetry?: (error: Error, attempt: number) => boolean;
}

export class ErrorService {
  private static instance: ErrorService;
  private errorLog: Array<{
    error: Error;
    context: ErrorContext;
    timestamp: Date;
    id: string;
  }> = [];

  static getInstance(): ErrorService {
    if (!ErrorService.instance) {
      ErrorService.instance = new ErrorService();
    }
    return ErrorService.instance;
  }

  /**
   * Log an error with context information
   */
  logError(error: Error, context: ErrorContext = {}) {
    const errorEntry = {
      error,
      context,
      timestamp: new Date(),
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
    };

    this.errorLog.push(errorEntry);

    // Keep only last 100 errors in memory
    if (this.errorLog.length > 100) {
      this.errorLog = this.errorLog.slice(-100);
    }

    // Store in localStorage for persistence
    try {
      const storedErrors = JSON.parse(localStorage.getItem('ghost-ide-error-log') || '[]');
      storedErrors.push({
        message: error.message,
        stack: error.stack,
        context,
        timestamp: errorEntry.timestamp.toISOString(),
        id: errorEntry.id,
      });
      
      // Keep only last 50 errors in localStorage
      localStorage.setItem('ghost-ide-error-log', JSON.stringify(storedErrors.slice(-50)));
    } catch (e) {
      console.error('Failed to store error in localStorage:', e);
    }

    console.error('Error logged:', errorEntry);
  }

  /**
   * Handle an error with user-friendly notifications
   */
  handleError(error: Error, context: ErrorContext = {}, showNotification = true) {
    this.logError(error, context);

    if (showNotification) {
      const { showError, showGhost } = useNotificationStore.getState();
      
      // Determine if this is a network error
      if (this.isNetworkError(error)) {
        showError(
          '👻 Connection to the Spirit Realm Lost',
          'The ethereal connection has been severed. Check your internet connection.',
          {
            persistent: true,
            action: {
              label: 'Retry Connection',
              onClick: () => window.location.reload(),
            },
          }
        );
      } else if (this.isValidationError(error)) {
        showGhost(
          '🔮 The Spirits Reject Your Offering',
          this.getSpookyErrorMessage(error.message),
          { duration: 6000 }
        );
      } else {
        showError(
          '⚡ A Supernatural Disturbance Occurred',
          this.getSpookyErrorMessage(error.message),
          {
            action: {
              label: 'Report to the Ghostly Council',
              onClick: () => this.reportError(error, context),
            },
          }
        );
      }
    }
  }

  /**
   * Execute a function with automatic retry logic
   */
  async withRetry<T>(
    fn: () => Promise<T>,
    config: RetryConfig,
    context: ErrorContext = {}
  ): Promise<T> {
    let lastError: Error = new Error('Retry failed');
    
    for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        
        // Check if we should retry
        if (attempt === config.maxAttempts || 
            (config.shouldRetry && !config.shouldRetry(lastError, attempt))) {
          break;
        }

        // Calculate delay
        let delay = config.delay;
        if (config.backoff === 'exponential') {
          delay = config.delay * Math.pow(2, attempt - 1);
        } else if (config.backoff === 'linear') {
          delay = config.delay * attempt;
        }

        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, delay));
        
        console.log(`Retrying operation (attempt ${attempt + 1}/${config.maxAttempts})...`);
      }
    }

    // All retries failed
    this.handleError(lastError, {
      ...context,
      action: 'retry_failed',
      additionalData: { maxAttempts: config.maxAttempts },
    });
    
    throw lastError;
  }

  /**
   * Wrap an async function with error handling
   */
  wrapAsync<T extends any[], R>(
    fn: (...args: T) => Promise<R>,
    context: ErrorContext = {}
  ) {
    return async (...args: T): Promise<R> => {
      try {
        return await fn(...args);
      } catch (error) {
        this.handleError(error as Error, context);
        throw error;
      }
    };
  }

  /**
   * Check if error is network-related
   */
  private isNetworkError(error: Error): boolean {
    const networkErrorMessages = [
      'network error',
      'fetch failed',
      'connection refused',
      'timeout',
      'not connected to server',
    ];
    
    return networkErrorMessages.some(msg => 
      error.message.toLowerCase().includes(msg)
    );
  }

  /**
   * Check if error is validation-related
   */
  private isValidationError(error: Error): boolean {
    const validationErrorMessages = [
      'validation',
      'invalid',
      'required',
      'format',
    ];
    
    return validationErrorMessages.some(msg => 
      error.message.toLowerCase().includes(msg)
    );
  }

  /**
   * Convert error messages to spooky themed messages
   */
  private getSpookyErrorMessage(originalMessage: string): string {
    const spookyMessages: Record<string, string> = {
      'network error': 'The spectral network has been disrupted by malevolent forces',
      'timeout': 'The spirits have grown impatient and vanished into the void',
      'not found': 'The requested soul has departed to the other side',
      'unauthorized': 'You lack the proper incantations to access this realm',
      'forbidden': 'The ancient guardians forbid your passage',
      'server error': 'The ghostly server has been possessed by chaotic entities',
      'validation': 'Your mystical formula contains forbidden symbols',
      'syntax error': 'The arcane syntax has angered the code spirits',
    };

    const lowerMessage = originalMessage.toLowerCase();
    
    for (const [key, spookyMessage] of Object.entries(spookyMessages)) {
      if (lowerMessage.includes(key)) {
        return spookyMessage;
      }
    }

    return `The ethereal realm whispers: "${originalMessage}"`;
  }

  /**
   * Report error to external service (mock implementation)
   */
  private reportError(error: Error, context: ErrorContext) {
    console.log('Reporting error to ghostly council:', { error, context });
    
    const { showInfo } = useNotificationStore.getState();
    showInfo(
      '📨 Message Sent to the Spirit Realm',
      'The ghostly council has been notified of this disturbance.',
      { duration: 3000 }
    );
  }

  /**
   * Get error statistics
   */
  getErrorStats() {
    const now = new Date();
    const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const recentErrors = this.errorLog.filter(entry => entry.timestamp > last24Hours);
    
    return {
      totalErrors: this.errorLog.length,
      recentErrors: recentErrors.length,
      errorsByComponent: this.groupErrorsByComponent(),
      mostCommonErrors: this.getMostCommonErrors(),
    };
  }

  private groupErrorsByComponent() {
    const groups: Record<string, number> = {};
    
    this.errorLog.forEach(entry => {
      const component = entry.context.component || 'unknown';
      groups[component] = (groups[component] || 0) + 1;
    });
    
    return groups;
  }

  private getMostCommonErrors() {
    const errorCounts: Record<string, number> = {};
    
    this.errorLog.forEach(entry => {
      const message = entry.error.message;
      errorCounts[message] = (errorCounts[message] || 0) + 1;
    });
    
    return Object.entries(errorCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([message, count]) => ({ message, count }));
  }

  /**
   * Clear error log
   */
  clearErrorLog() {
    this.errorLog = [];
    localStorage.removeItem('ghost-ide-error-log');
  }
}

export const errorService = ErrorService.getInstance();