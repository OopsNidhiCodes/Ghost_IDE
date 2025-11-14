import React, { useState } from 'react';
import { useErrorHandler } from '../../hooks/useErrorHandler';
import { useNotificationStore } from '../../store/useNotificationStore';
import { errorService } from '../../services/errorService';
import { apiService } from '../../services/apiService';

export const ErrorHandlingDemo: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { handleError, handleAsyncError, showSpookyError, showCriticalError } = useErrorHandler({
    component: 'ErrorHandlingDemo',
  });
  const { showSuccess, showInfo, showWarning } = useNotificationStore();

  const handleSyncError = () => {
    try {
      throw new Error('This is a synchronous error for demonstration');
    } catch (error) {
      handleError(error as Error, { action: 'demo_sync_error' });
    }
  };

  const handleAsyncErrorDemo = async () => {
    setIsLoading(true);
    
    const result = await handleAsyncError(async () => {
      // Simulate an async operation that fails
      await new Promise(resolve => setTimeout(resolve, 1000));
      throw new Error('This is an async error for demonstration');
    }, { action: 'demo_async_error' });

    setIsLoading(false);
    
    if (result === null) {
      console.log('Async operation failed and was handled');
    }
  };

  const handleNetworkError = async () => {
    setIsLoading(true);
    
    // This will trigger network error handling
    const response = await apiService.get('/nonexistent-endpoint');
    
    setIsLoading(false);
    
    if (!response.success) {
      console.log('Network request failed:', response.error);
    }
  };

  const handleRetryableOperation = async () => {
    setIsLoading(true);
    
    try {
      const result = await errorService.withRetry(
        async () => {
          // Simulate a flaky operation that fails 2 times then succeeds
          if (Math.random() > 0.3) {
            throw new Error('Temporary failure');
          }
          return 'Success!';
        },
        {
          maxAttempts: 5,
          delay: 500,
          backoff: 'exponential',
        },
        { component: 'ErrorHandlingDemo', action: 'retryable_operation' }
      );
      
      showSuccess('Operation Succeeded', `Result: ${result}`);
    } catch (error) {
      console.log('Operation failed after retries');
    }
    
    setIsLoading(false);
  };

  const showNotificationExamples = () => {
    showSuccess('👻 Spectral Success', 'The spirits have blessed your code!');
    
    setTimeout(() => {
      showInfo('🔮 Mystical Information', 'The crystal ball reveals hidden knowledge.');
    }, 1000);
    
    setTimeout(() => {
      showWarning('⚠️ Ghostly Warning', 'The spirits sense disturbance in the code.');
    }, 2000);
    
    setTimeout(() => {
      showSpookyError('🕷️ Creepy Error', 'The spiders have tangled your web of code!');
    }, 3000);
    
    setTimeout(() => {
      showCriticalError(
        '💀 Critical Haunting',
        'A powerful ghost has possessed your application!',
        {
          label: 'Perform Exorcism',
          onClick: () => showInfo('✨ Exorcism Complete', 'The ghost has been banished!'),
        }
      );
    }, 4000);
  };

  const showErrorStats = () => {
    const stats = errorService.getErrorStats();
    showInfo(
      '📊 Error Statistics',
      `Total errors: ${stats.totalErrors}, Recent: ${stats.recentErrors}`
    );
  };

  const clearErrorLog = () => {
    errorService.clearErrorLog();
    showSuccess('🧹 Error Log Cleared', 'All error records have been purged from the spirit realm.');
  };

  return (
    <div className="p-6 bg-ghost-900 rounded-lg border border-ghost-700">
      <h2 className="text-2xl font-bold text-ghost-100 mb-6">
        👻 Error Handling System Demo
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <button
          onClick={handleSyncError}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
        >
          Trigger Sync Error
        </button>
        
        <button
          onClick={handleAsyncErrorDemo}
          disabled={isLoading}
          className="px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          {isLoading ? 'Loading...' : 'Trigger Async Error'}
        </button>
        
        <button
          onClick={handleNetworkError}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          {isLoading ? 'Loading...' : 'Trigger Network Error'}
        </button>
        
        <button
          onClick={handleRetryableOperation}
          disabled={isLoading}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          {isLoading ? 'Retrying...' : 'Test Retry Logic'}
        </button>
        
        <button
          onClick={showNotificationExamples}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        >
          Show Notification Examples
        </button>
        
        <button
          onClick={showErrorStats}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
        >
          Show Error Stats
        </button>
        
        <button
          onClick={clearErrorLog}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
        >
          Clear Error Log
        </button>
      </div>
      
      <div className="bg-ghost-800 border border-ghost-600 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-ghost-200 mb-2">
          Error Handling Features:
        </h3>
        <ul className="text-ghost-300 space-y-1 text-sm">
          <li>• Global error boundary for React component errors</li>
          <li>• Spooky-themed user notifications with different types</li>
          <li>• Automatic retry mechanisms with exponential backoff</li>
          <li>• Network error detection and graceful degradation</li>
          <li>• Error logging and statistics tracking</li>
          <li>• WebSocket connection monitoring and reconnection</li>
          <li>• API service with built-in error handling</li>
          <li>• Custom error handling hooks for components</li>
        </ul>
      </div>
    </div>
  );
};