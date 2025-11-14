import React, { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';

interface OutputPanelProps {
  className?: string;
}

export const OutputPanel: React.FC<OutputPanelProps> = ({ className = '' }) => {
  const { 
    executionResult, 
    isExecuting, 
    setExecutionResult,
    executionHistory,
    addToExecutionHistory
  } = useAppStore();
  
  const [showHistory, setShowHistory] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const [executionStartTime, setExecutionStartTime] = useState<number | null>(null);

  // Track execution start time
  useEffect(() => {
    if (isExecuting && !executionStartTime) {
      setExecutionStartTime(Date.now());
    } else if (!isExecuting && executionStartTime) {
      setExecutionStartTime(null);
    }
  }, [isExecuting, executionStartTime]);

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [executionResult?.stdout, executionResult?.stderr]);

  // Add completed executions to history
  useEffect(() => {
    if (executionResult && !isExecuting && executionResult.executionTime > 0) {
      addToExecutionHistory(executionResult);
    }
  }, [executionResult, isExecuting, addToExecutionHistory]);

  const clearOutput = () => {
    setExecutionResult(null);
  };

  const clearHistory = () => {
    useAppStore.getState().clearExecutionHistory();
  };

  const formatExecutionTime = (time: number): string => {
    if (time < 1000) {
      return `${time.toFixed(0)}ms`;
    }
    return `${(time / 1000).toFixed(2)}s`;
  };

  const getCurrentExecutionTime = (): string => {
    if (!executionStartTime) return '0ms';
    const elapsed = Date.now() - executionStartTime;
    return formatExecutionTime(elapsed);
  };

  const parseErrorWithLineNumbers = (error: string): JSX.Element[] => {
    const lines = error.split('\n');
    return lines.map((line, index) => {
      // Match common error patterns with line numbers
      const lineNumberMatch = line.match(/line (\d+)/i) || 
                             line.match(/File ".*", line (\d+)/i) ||
                             line.match(/at line (\d+)/i);
      
      if (lineNumberMatch) {
        const lineNum = lineNumberMatch[1];
        return (
          <div key={index} className="flex">
            <span className="text-red-400 hover:text-red-300 cursor-pointer" 
                  title={`Jump to line ${lineNum}`}>
              {line}
            </span>
          </div>
        );
      }
      
      return <div key={index}>{line}</div>;
    });
  };

  const getStatusColor = () => {
    if (isExecuting) return 'text-yellow-400';
    if (!executionResult) return 'text-ghost-400';
    if (executionResult.exitCode === 0) return 'text-green-400';
    return 'text-red-400';
  };

  const getStatusIcon = () => {
    if (isExecuting) return '⏳';
    if (!executionResult) return '⚪';
    if (executionResult.exitCode === 0) return '✅';
    return '❌';
  };

  const getStatusText = () => {
    if (isExecuting) return 'Executing...';
    if (!executionResult) return 'Ready';
    if (executionResult.exitCode === 0) return 'Success';
    return 'Error';
  };

  return (
    <div className={`flex flex-col h-full bg-ghost-900 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-ghost-700 bg-ghost-800">
        <div className="flex items-center space-x-3">
          <h3 className="text-ghost-200 font-medium flex items-center space-x-2">
            <span>📺</span>
            <span>Output</span>
          </h3>
          
          {/* Status indicator */}
          <div className={`flex items-center space-x-2 text-sm ${getStatusColor()}`}>
            <span>{getStatusIcon()}</span>
            <span>{getStatusText()}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Execution time */}
          <div className="text-xs text-ghost-400">
            {isExecuting ? (
              <span>⏱️ {getCurrentExecutionTime()}</span>
            ) : executionResult?.executionTime ? (
              <span>⏱️ {formatExecutionTime(executionResult.executionTime)}</span>
            ) : null}
          </div>

          {/* History toggle */}
          {executionHistory.length > 0 && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="text-xs bg-ghost-700 hover:bg-ghost-600 text-ghost-300 px-2 py-1 rounded transition-colors"
              title="Toggle execution history"
            >
              📚 History ({executionHistory.length})
            </button>
          )}

          {/* Clear button */}
          <button
            onClick={clearOutput}
            disabled={!executionResult && !isExecuting}
            className="text-xs bg-ghost-700 hover:bg-ghost-600 disabled:opacity-50 disabled:cursor-not-allowed text-ghost-300 px-2 py-1 rounded transition-colors"
            title="Clear output"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* History panel */}
      {showHistory && executionHistory.length > 0 && (
        <div className="border-b border-ghost-700 bg-ghost-850 max-h-32 overflow-y-auto">
          <div className="p-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-ghost-400 font-medium">Execution History</span>
              <button
                onClick={clearHistory}
                className="text-xs text-ghost-500 hover:text-ghost-400 transition-colors"
              >
                Clear History
              </button>
            </div>
            <div className="space-y-1">
              {executionHistory.map((result, index) => (
                <div
                  key={index}
                  className="text-xs p-2 bg-ghost-800 rounded cursor-pointer hover:bg-ghost-700 transition-colors"
                  onClick={() => setExecutionResult(result)}
                >
                  <div className="flex items-center justify-between">
                    <span className={result.exitCode === 0 ? 'text-green-400' : 'text-red-400'}>
                      {result.exitCode === 0 ? '✅' : '❌'} 
                      {result.exitCode === 0 ? 'Success' : 'Error'}
                    </span>
                    <span className="text-ghost-400">
                      {formatExecutionTime(result.executionTime)}
                    </span>
                  </div>
                  {result.stdout && (
                    <div className="text-ghost-300 truncate mt-1">
                      📤 {result.stdout.split('\n')[0]}
                    </div>
                  )}
                  {result.stderr && (
                    <div className="text-red-300 truncate mt-1">
                      ⚠️ {result.stderr.split('\n')[0]}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Output content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {isExecuting && (
          <div className="p-3 bg-ghost-850 border-b border-ghost-700">
            <div className="flex items-center space-x-2 text-yellow-400">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
              <span className="text-sm">Executing code in the spirit realm...</span>
            </div>
            <div className="mt-2 text-xs text-ghost-400">
              The ghosts are processing your code. Please wait while they work their magic.
            </div>
          </div>
        )}

        <div 
          ref={outputRef}
          className="flex-1 overflow-y-auto p-4 font-mono text-sm"
        >
          {!executionResult && !isExecuting ? (
            <div className="text-center text-ghost-400 mt-8">
              <div className="text-4xl mb-4 ghost-float">👻</div>
              <p className="text-lg mb-2">The spirits await your code...</p>
              <p className="text-sm">
                Click the "Run Code" button to execute your program and see the results here.
              </p>
              <div className="mt-4 p-3 bg-ghost-800 rounded-lg text-left max-w-md mx-auto">
                <p className="text-xs text-ghost-300 italic">
                  "I can see the future of your code... but first, you must run it!" 
                  <br />- The Ghost AI
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Standard output */}
              {(executionResult?.stdout || isExecuting) && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-green-400 text-xs font-semibold">📤 STDOUT</span>
                    {executionResult?.stdout && (
                      <span className="text-ghost-500 text-xs">
                        ({executionResult.stdout.split('\n').length - 1} lines)
                      </span>
                    )}
                  </div>
                  <div className="bg-ghost-800 rounded p-3 border-l-4 border-green-400">
                    <pre className="text-green-100 whitespace-pre-wrap break-words">
                      {executionResult?.stdout || (isExecuting ? 'Waiting for output...' : '')}
                    </pre>
                  </div>
                </div>
              )}

              {/* Error output */}
              {executionResult?.stderr && (
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-red-400 text-xs font-semibold">⚠️ STDERR</span>
                    <span className="text-ghost-500 text-xs">
                      ({executionResult.stderr.split('\n').length - 1} lines)
                    </span>
                  </div>
                  <div className="bg-ghost-800 rounded p-3 border-l-4 border-red-400">
                    <div className="text-red-100 whitespace-pre-wrap break-words">
                      {parseErrorWithLineNumbers(executionResult.stderr)}
                    </div>
                  </div>
                </div>
              )}

              {/* Execution metadata */}
              {executionResult && !isExecuting && (
                <div className="border-t border-ghost-700 pt-3 mt-4">
                  <div className="flex items-center justify-between text-xs text-ghost-400">
                    <div className="flex items-center space-x-4">
                      <span>Exit Code: 
                        <span className={executionResult.exitCode === 0 ? 'text-green-400' : 'text-red-400'}>
                          {executionResult.exitCode}
                        </span>
                      </span>
                      <span>Execution Time: {formatExecutionTime(executionResult.executionTime)}</span>
                    </div>
                    <div className="text-ghost-500">
                      {new Date().toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};