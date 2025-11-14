import React from 'react';
import { useAppStore } from '../../store/useAppStore';

export const StatusBar: React.FC = () => {
  const { 
    currentLanguage, 
    isExecuting, 
    executionResult, 
    currentFile,
    isConnected 
  } = useAppStore();

  return (
    <footer className="bg-ghost-900 border-t border-ghost-700 px-4 py-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-4">
          {/* Current Language */}
          <div className="flex items-center space-x-2">
            <span className="text-ghost-400">Language:</span>
            <span className="text-spooky-purple font-medium">{currentLanguage}</span>
          </div>

          {/* Current File */}
          {currentFile && (
            <div className="flex items-center space-x-2">
              <span className="text-ghost-400">File:</span>
              <span className="text-ghost-300">{currentFile.name}</span>
            </div>
          )}

          {/* Execution Status */}
          {isExecuting && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-spooky-orange rounded-full animate-pulse" />
              <span className="text-spooky-orange">Executing...</span>
            </div>
          )}

          {/* Last Execution Result */}
          {executionResult && !isExecuting && (
            <div className="flex items-center space-x-2">
              <div 
                className={`w-2 h-2 rounded-full ${
                  executionResult.exitCode === 0 ? 'bg-spooky-green' : 'bg-spooky-red'
                }`} 
              />
              <span className={executionResult.exitCode === 0 ? 'text-spooky-green' : 'text-spooky-red'}>
                {executionResult.exitCode === 0 ? 'Success' : 'Error'}
              </span>
              {executionResult.executionTime > 0 && (
                <span className="text-ghost-400">
                  ({executionResult.executionTime.toFixed(2)}s)
                </span>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            <div 
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-spooky-green' : 'bg-spooky-red'
              }`}
            />
            <span className="text-ghost-400">
              {isConnected ? 'Online' : 'Offline'}
            </span>
          </div>

          {/* Spooky Message */}
          <span className="text-ghost-500 italic">
            "The spirits are watching your code..." 👻
          </span>
        </div>
      </div>
    </footer>
  );
};