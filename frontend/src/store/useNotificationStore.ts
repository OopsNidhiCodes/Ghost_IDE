import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Notification } from '../components/ErrorHandling/NotificationSystem';

interface NotificationState {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  showSuccess: (title: string, message: string, options?: Partial<Notification>) => void;
  showError: (title: string, message: string, options?: Partial<Notification>) => void;
  showWarning: (title: string, message: string, options?: Partial<Notification>) => void;
  showInfo: (title: string, message: string, options?: Partial<Notification>) => void;
  showGhost: (title: string, message: string, options?: Partial<Notification>) => void;
}

export const useNotificationStore = create<NotificationState>()(
  devtools(
    (set, get) => ({
      notifications: [],

      addNotification: (notification) => {
        const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        const newNotification: Notification = {
          id,
          duration: 5000,
          ...notification,
        };

        set((state) => ({
          notifications: [...state.notifications, newNotification],
        }));

        // Auto-remove after duration if not persistent
        if (!newNotification.persistent && newNotification.duration !== 0) {
          setTimeout(() => {
            get().removeNotification(id);
          }, newNotification.duration);
        }
      },

      removeNotification: (id) => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      },

      clearAllNotifications: () => {
        set({ notifications: [] });
      },

      showSuccess: (title, message, options = {}) => {
        get().addNotification({
          type: 'success',
          title,
          message,
          ...options,
        });
      },

      showError: (title, message, options = {}) => {
        get().addNotification({
          type: 'error',
          title,
          message,
          duration: 8000, // Errors stay longer
          ...options,
        });
      },

      showWarning: (title, message, options = {}) => {
        get().addNotification({
          type: 'warning',
          title,
          message,
          ...options,
        });
      },

      showInfo: (title, message, options = {}) => {
        get().addNotification({
          type: 'info',
          title,
          message,
          ...options,
        });
      },

      showGhost: (title, message, options = {}) => {
        get().addNotification({
          type: 'ghost',
          title,
          message,
          ...options,
        });
      },
    }),
    {
      name: 'notification-store',
    }
  )
);