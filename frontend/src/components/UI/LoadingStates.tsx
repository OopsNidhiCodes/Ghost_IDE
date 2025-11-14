import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'purple' | 'green' | 'orange' | 'red';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  color = 'purple',
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  };

  const colorClasses = {
    purple: 'border-spooky-purple',
    green: 'border-spooky-green',
    orange: 'border-spooky-orange',
    red: 'border-spooky-red'
  };

  return (
    <div 
      className={`animate-spin rounded-full border-2 border-t-transparent ${sizeClasses[size]} ${colorClasses[color]} ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
};

interface ProgressBarProps {
  progress: number; // 0-100
  color?: 'purple' | 'green' | 'orange' | 'red';
  showPercentage?: boolean;
  className?: string;
  animated?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  color = 'purple',
  showPercentage = false,
  className = '',
  animated = true
}) => {
  const colorClasses = {
    purple: 'bg-spooky-purple',
    green: 'bg-spooky-green',
    orange: 'bg-spooky-orange',
    red: 'bg-spooky-red'
  };

  const clampedProgress = Math.max(0, Math.min(100, progress));

  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between mb-1">
        {showPercentage && (
          <span className="text-sm text-ghost-300">{Math.round(clampedProgress)}%</span>
        )}
      </div>
      <div className="w-full bg-ghost-700 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} ${animated ? 'transition-all duration-300 ease-out' : ''}`}
          style={{ width: `${clampedProgress}%` }}
          role="progressbar"
          aria-valuenow={clampedProgress}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  animated?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1rem',
  className = '',
  animated = true
}) => {
  return (
    <div
      className={`bg-ghost-700 rounded ${animated ? 'animate-pulse' : ''} ${className}`}
      style={{ width, height }}
      role="status"
      aria-label="Loading content"
    />
  );
};

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  children?: React.ReactNode;
  className?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isVisible,
  message = 'Loading...',
  children,
  className = ''
}) => {
  if (!isVisible) return null;

  return (
    <div className={`absolute inset-0 bg-ghost-950/80 backdrop-blur-sm flex items-center justify-center z-50 ${className}`}>
      <div className="text-center">
        {children || (
          <>
            <LoadingSpinner size="lg" className="mx-auto mb-4" />
            <p className="text-ghost-200 text-lg">{message}</p>
          </>
        )}
      </div>
    </div>
  );
};

interface SpookyLoadingProps {
  message?: string;
  className?: string;
}

export const SpookyLoading: React.FC<SpookyLoadingProps> = ({
  message = 'Summoning spirits...',
  className = ''
}) => {
  return (
    <div className={`text-center ${className}`}>
      <div className="text-6xl mb-4 ghost-float">👻</div>
      <h2 className="text-xl text-ghost-200 mb-2">{message}</h2>
      <div className="flex justify-center space-x-1 mb-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-2 h-2 bg-spooky-purple rounded-full animate-bounce"
            style={{ animationDelay: `${i * 0.1}s` }}
          />
        ))}
      </div>
      <p className="text-ghost-400 text-sm">The Ghost AI is awakening...</p>
    </div>
  );
};

interface CodeExecutionLoadingProps {
  language: string;
  className?: string;
}

export const CodeExecutionLoading: React.FC<CodeExecutionLoadingProps> = ({
  language,
  className = ''
}) => {
  const messages = [
    `Compiling ${language} in the shadow realm...`,
    `The spirits are reviewing your ${language} code...`,
    `Executing ${language} with supernatural powers...`,
    `Ghost processes are running your ${language}...`
  ];

  const [messageIndex, setMessageIndex] = React.useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2000);

    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <LoadingSpinner size="sm" />
      <span className="text-ghost-300 animate-pulse">
        {messages[messageIndex]}
      </span>
    </div>
  );
};

interface ConnectionLoadingProps {
  isConnecting: boolean;
  isReconnecting?: boolean;
  className?: string;
}

export const ConnectionLoading: React.FC<ConnectionLoadingProps> = ({
  isConnecting,
  isReconnecting = false,
  className = ''
}) => {
  if (!isConnecting) return null;

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <LoadingSpinner size="sm" />
      <span className="text-ghost-300 text-sm">
        {isReconnecting ? 'Reconnecting to spirit realm...' : 'Connecting to Ghost AI...'}
      </span>
    </div>
  );
};