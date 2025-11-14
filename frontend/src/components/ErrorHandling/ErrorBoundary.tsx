import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // Log error to error reporting service
    this.logError(error, errorInfo);
  }

  private logError = (error: Error, errorInfo: ErrorInfo) => {
    // In a real app, you'd send this to an error reporting service
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    console.error('Error Report:', errorReport);
    
    // Store in localStorage for debugging
    try {
      const existingErrors = JSON.parse(localStorage.getItem('ghost-ide-errors') || '[]');
      existingErrors.push(errorReport);
      // Keep only last 10 errors
      localStorage.setItem('ghost-ide-errors', JSON.stringify(existingErrors.slice(-10)));
    } catch (e) {
      console.error('Failed to store error report:', e);
    }
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-ghost-950 text-ghost-100 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-ghost-900 border border-ghost-700 rounded-lg p-8 shadow-2xl">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-900/20 rounded-full mb-4">
                <AlertTriangle className="w-8 h-8 text-red-400" />
              </div>
              <h1 className="text-2xl font-bold text-ghost-100 mb-2">
                👻 The Ghost Has Encountered a Spectral Error
              </h1>
              <p className="text-ghost-300">
                Something supernatural has gone wrong in the ethereal realm of code.
              </p>
            </div>

            <div className="bg-ghost-800 border border-ghost-600 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold text-ghost-200 mb-2">Error Details:</h3>
              <p className="text-red-400 font-mono text-sm mb-2">
                {this.state.error?.message}
              </p>
              {process.env.NODE_ENV === 'development' && (
                <details className="mt-4">
                  <summary className="text-ghost-300 cursor-pointer hover:text-ghost-100">
                    Stack Trace (Development)
                  </summary>
                  <pre className="text-xs text-ghost-400 mt-2 overflow-auto max-h-40">
                    {this.state.error?.stack}
                  </pre>
                </details>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={this.handleRetry}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Resurrect the Interface
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-ghost-700 hover:bg-ghost-600 text-ghost-100 rounded-lg transition-colors"
              >
                <Home className="w-4 h-4" />
                Return to the Mortal Realm
              </button>
            </div>

            <div className="mt-6 text-center text-sm text-ghost-400">
              <p>
                The spirits have been notified of this disturbance. 
                If the problem persists, try refreshing the page or clearing your browser cache.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}