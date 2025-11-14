import { useCallback } from 'react';
import { errorService, ErrorContext } from '../services/errorService';
import { useNotificationStore } from '../store/useNotificationStore';

export interface UseErrorHandlerOptions {
  component?: string;
  showNotifications?: boolean;
  logErrors?: boolean;
}

export const useErrorHandler = (options: UseErrorHandlerOptions = {}) => {
  const {
    component = 'UnknownComponent',
    showNotifications = true,
    logErrors = true,
  } = options;

  const { showError, showGhost } = useNotificationStore();

  const handleError = useCallback(
    (error: Error | string, context: Partial<ErrorContext> = {}) => {
      const errorObj = typeof error === 'string' ? new Error(error) : error;
      const fullContext: ErrorContext = {
        component,
        ...context,
      };

      if (logErrors) {
        errorService.logError(errorObj, fullContext);
      }

      if (showNotifications) {
        errorService.handleError(errorObj, fullContext, true);
      }
    },
    [component, showNotifications, logErrors]
  );

  const handleAsyncError = useCallback(
    async <T>(
      asyncFn: () => Promise<T>,
      context: Partial<ErrorContext> = {}
    ): Promise<T | null> => {
      try {
        return await asyncFn();
      } catch (error) {
        handleError(error as Error, context);
        return null;
      }
    },
    [handleError]
  );

  const wrapAsyncFunction = useCallback(
    <T extends any[], R>(
      fn: (...args: T) => Promise<R>,
      context: Partial<ErrorContext> = {}
    ) => {
      return async (...args: T): Promise<R | null> => {
        try {
          return await fn(...args);
        } catch (error) {
          handleError(error as Error, context);
          return null;
        }
      };
    },
    [handleError]
  );

  const showSpookyError = useCallback(
    (title: string, message: string) => {
      showGhost(title, message, { duration: 6000 });
    },
    [showGhost]
  );

  const showCriticalError = useCallback(
    (title: string, message: string, action?: { label: string; onClick: () => void }) => {
      showError(title, message, {
        persistent: true,
        action,
      });
    },
    [showError]
  );

  return {
    handleError,
    handleAsyncError,
    wrapAsyncFunction,
    showSpookyError,
    showCriticalError,
  };
};