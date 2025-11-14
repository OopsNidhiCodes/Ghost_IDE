import React, { useEffect } from 'react';
import { X, AlertTriangle, CheckCircle, Info, Skull } from 'lucide-react';
import { useNotificationStore } from '../../store/useNotificationStore';

export type NotificationType = 'success' | 'error' | 'warning' | 'info' | 'ghost';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const NotificationItem: React.FC<{ notification: Notification }> = ({ notification }) => {
  const { removeNotification } = useNotificationStore();

  useEffect(() => {
    if (!notification.persistent && notification.duration !== 0) {
      const timer = setTimeout(() => {
        removeNotification(notification.id);
      }, notification.duration || 5000);

      return () => clearTimeout(timer);
    }
  }, [notification.id, notification.duration, notification.persistent, removeNotification]);

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-400" />;
      case 'ghost':
        return <Skull className="w-5 h-5 text-purple-400" />;
      default:
        return <Info className="w-5 h-5 text-ghost-400" />;
    }
  };

  const getStyles = () => {
    const baseStyles = "border-l-4 bg-ghost-800 border-ghost-600 shadow-lg";
    
    switch (notification.type) {
      case 'success':
        return `${baseStyles} border-l-green-500 bg-green-900/20`;
      case 'error':
        return `${baseStyles} border-l-red-500 bg-red-900/20`;
      case 'warning':
        return `${baseStyles} border-l-yellow-500 bg-yellow-900/20`;
      case 'info':
        return `${baseStyles} border-l-blue-500 bg-blue-900/20`;
      case 'ghost':
        return `${baseStyles} border-l-purple-500 bg-purple-900/20`;
      default:
        return baseStyles;
    }
  };

  return (
    <div className={`${getStyles()} rounded-r-lg p-4 mb-3 animate-slide-in-right`}>
      <div className="flex items-start">
        <div className="flex-shrink-0 mr-3">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-ghost-100 mb-1">
            {notification.title}
          </h4>
          <p className="text-sm text-ghost-300">
            {notification.message}
          </p>
          {notification.action && (
            <button
              onClick={notification.action.onClick}
              className="mt-2 text-sm text-purple-400 hover:text-purple-300 underline"
            >
              {notification.action.label}
            </button>
          )}
        </div>
        <button
          onClick={() => removeNotification(notification.id)}
          className="flex-shrink-0 ml-3 text-ghost-400 hover:text-ghost-200 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export const NotificationSystem: React.FC = () => {
  const { notifications } = useNotificationStore();

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm w-full">
      {notifications.map((notification) => (
        <NotificationItem key={notification.id} notification={notification} />
      ))}
    </div>
  );
};