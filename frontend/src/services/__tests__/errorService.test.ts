import { vi, describe, it, expect, beforeEach } from 'vitest';
import { errorService } from '../errorService';
import { useNotificationStore } from '../../store/useNotificationStore';

// Mock the notification store
vi.mock('../../store/useNotificationStore');

useNotificationStore as any;

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('ErrorService', () => {
  const mockShowError = vi.fn();
  const mockShowGhost = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    console.error = vi.fn();
    
    // Mock the store's getState method
    (useNotificationStore as any).getState = vi.fn().mockReturnValue({
      showError: mockShowError,
      showGhost: mockShowGhost,
    });
  });

  describe('logError', () => {
    it('logs error with context', () => {
      const error = new Error('Test error');
      const context = { component: 'TestComponent', action: 'testAction' };

      errorService.logError(error, context);

      expect(console.error).toHaveBeenCalledWith(
        'Error logged:',
        expect.objectContaining({
          error,
          context,
          timestamp: expect.any(Date),
          id: expect.any(String),
        })
      );
    });

    it('stores error in localStorage', () => {
      mockLocalStorage.getItem.mockReturnValue('[]');
      
      const error = new Error('Test error');
      errorService.logError(error);

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'ghost-ide-error-log',
        expect.stringContaining('Test error')
      );
    });

    it('handles localStorage errors gracefully', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });

      const error = new Error('Test error');
      
      // Should not throw
      expect(() => errorService.logError(error)).not.toThrow();
    });
  });

  describe('handleError', () => {
    it('shows network error notification', () => {
      const error = new Error('network error occurred');
      
      errorService.handleError(error);

      expect(mockShowError).toHaveBeenCalledWith(
        '👻 Connection to the Spirit Realm Lost',
        'The ethereal connection has been severed. Check your internet connection.',
        expect.objectContaining({
          persistent: true,
          action: expect.any(Object),
        })
      );
    });

    it('shows validation error notification', () => {
      const error = new Error('validation failed');
      
      errorService.handleError(error);

      expect(mockShowGhost).toHaveBeenCalledWith(
        '🔮 The Spirits Reject Your Offering',
        expect.stringContaining('validation'),
        expect.objectContaining({ duration: 6000 })
      );
    });

    it('shows generic error notification', () => {
      const error = new Error('generic error');
      
      errorService.handleError(error);

      expect(mockShowError).toHaveBeenCalledWith(
        '⚡ A Supernatural Disturbance Occurred',
        expect.stringContaining('generic error'),
        expect.objectContaining({
          action: expect.any(Object),
        })
      );
    });

    it('does not show notification when showNotification is false', () => {
      const error = new Error('test error');
      
      errorService.handleError(error, {}, false);

      expect(mockShowError).not.toHaveBeenCalled();
      expect(mockShowGhost).not.toHaveBeenCalled();
    });
  });

  describe('withRetry', () => {
    it('succeeds on first attempt', async () => {
      const mockFn = vi.fn().mockResolvedValue('success');
      const config = { maxAttempts: 3, delay: 100 };

      const result = await errorService.withRetry(mockFn, config);

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('retries on failure and eventually succeeds', async () => {
      const mockFn = vi.fn()
        .mockRejectedValueOnce(new Error('fail 1'))
        .mockRejectedValueOnce(new Error('fail 2'))
        .mockResolvedValue('success');
      
      const config = { maxAttempts: 3, delay: 10 };

      const result = await errorService.withRetry(mockFn, config);

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalledTimes(3);
    });

    it('fails after max attempts', async () => {
      const mockFn = vi.fn().mockRejectedValue(new Error('persistent failure'));
      const config = { maxAttempts: 2, delay: 10 };

      await expect(errorService.withRetry(mockFn, config)).rejects.toThrow('persistent failure');
      expect(mockFn).toHaveBeenCalledTimes(2);
    });

    it('uses exponential backoff', async () => {
      const mockFn = vi.fn()
        .mockRejectedValueOnce(new Error('fail 1'))
        .mockRejectedValueOnce(new Error('fail 2'))
        .mockResolvedValue('success');
      
      const config = { maxAttempts: 3, delay: 10, backoff: 'exponential' as const };

      const startTime = Date.now();
      await errorService.withRetry(mockFn, config);
      const endTime = Date.now();

      // Should take at least 10 + 20 = 30ms due to exponential backoff
      expect(endTime - startTime).toBeGreaterThan(25);
    });

    it('respects shouldRetry function', async () => {
      const mockFn = vi.fn().mockRejectedValue(new Error('should not retry'));
      const config = {
        maxAttempts: 3,
        delay: 10,
        shouldRetry: () => false,
      };

      await expect(errorService.withRetry(mockFn, config)).rejects.toThrow('should not retry');
      expect(mockFn).toHaveBeenCalledTimes(1);
    });
  });

  describe('wrapAsync', () => {
    it('wraps function and handles errors', async () => {
      const mockFn = vi.fn().mockRejectedValue(new Error('wrapped error'));
      const wrappedFn = errorService.wrapAsync(mockFn);

      await expect(wrappedFn()).rejects.toThrow('wrapped error');
      expect(mockShowError).toHaveBeenCalled();
    });

    it('passes through successful results', async () => {
      const mockFn = vi.fn().mockResolvedValue('success');
      const wrappedFn = errorService.wrapAsync(mockFn);

      const result = await wrappedFn();
      expect(result).toBe('success');
    });
  });

  describe('getErrorStats', () => {
    it('returns error statistics', () => {
      // Clear any existing errors
      errorService.clearErrorLog();
      
      // Add some test errors
      errorService.logError(new Error('Error 1'), { component: 'Component1' });
      errorService.logError(new Error('Error 2'), { component: 'Component1' });
      errorService.logError(new Error('Error 1'), { component: 'Component2' });

      const stats = errorService.getErrorStats();

      expect(stats.totalErrors).toBe(3);
      expect(stats.errorsByComponent).toEqual({
        Component1: 2,
        Component2: 1,
      });
      expect(stats.mostCommonErrors).toEqual([
        { message: 'Error 1', count: 2 },
        { message: 'Error 2', count: 1 },
      ]);
    });
  });

  describe('clearErrorLog', () => {
    it('clears error log and localStorage', () => {
      errorService.logError(new Error('Test error'));
      errorService.clearErrorLog();

      const stats = errorService.getErrorStats();
      expect(stats.totalErrors).toBe(0);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('ghost-ide-error-log');
    });
  });
});