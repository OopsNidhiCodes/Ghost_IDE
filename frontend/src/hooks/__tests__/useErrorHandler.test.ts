import { renderHook } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useErrorHandler } from '../useErrorHandler';
import { errorService } from '../../services/errorService';
import { useNotificationStore } from '../../store/useNotificationStore';

// Mock dependencies
vi.mock('../../services/errorService');
vi.mock('../../store/useNotificationStore');

const mockErrorService = errorService as any;
const mockUseNotificationStore = useNotificationStore as any;

describe('useErrorHandler', () => {
  const mockShowError = vi.fn();
  const mockShowGhost = vi.fn();
  const mockLogError = vi.fn();
  const mockHandleError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockUseNotificationStore.mockReturnValue({
      showError: mockShowError,
      showGhost: mockShowGhost,
    } as any);

    mockErrorService.logError = mockLogError;
    mockErrorService.handleError = mockHandleError;
  });

  it('handles errors with default options', () => {
    const { result } = renderHook(() => useErrorHandler());
    const error = new Error('Test error');

    result.current.handleError(error);

    expect(mockLogError).toHaveBeenCalledWith(error, {
      component: 'UnknownComponent',
    });
    expect(mockHandleError).toHaveBeenCalledWith(error, {
      component: 'UnknownComponent',
    }, true);
  });

  it('handles errors with custom component name', () => {
    const { result } = renderHook(() => useErrorHandler({ component: 'TestComponent' }));
    const error = new Error('Test error');

    result.current.handleError(error);

    expect(mockLogError).toHaveBeenCalledWith(error, {
      component: 'TestComponent',
    });
  });

  it('handles string errors', () => {
    const { result } = renderHook(() => useErrorHandler());

    result.current.handleError('String error');

    expect(mockLogError).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'String error' }),
      expect.any(Object)
    );
  });

  it('does not show notifications when disabled', () => {
    const { result } = renderHook(() => useErrorHandler({ showNotifications: false }));
    const error = new Error('Test error');

    result.current.handleError(error);

    expect(mockHandleError).toHaveBeenCalledWith(error, {
      component: 'UnknownComponent',
    }, false);
  });

  it('does not log errors when disabled', () => {
    const { result } = renderHook(() => useErrorHandler({ logErrors: false }));
    const error = new Error('Test error');

    result.current.handleError(error);

    expect(mockLogError).not.toHaveBeenCalled();
    expect(mockHandleError).toHaveBeenCalledWith(error, expect.any(Object), true);
  });

  it('handles async errors successfully', async () => {
    const { result } = renderHook(() => useErrorHandler());
    const asyncFn = vi.fn().mockResolvedValue('success');

    const response = await result.current.handleAsyncError(asyncFn);

    expect(response).toBe('success');
    expect(mockLogError).not.toHaveBeenCalled();
  });

  it('handles async errors that throw', async () => {
    const { result } = renderHook(() => useErrorHandler());
    const error = new Error('Async error');
    const asyncFn = vi.fn().mockRejectedValue(error);

    const response = await result.current.handleAsyncError(asyncFn);

    expect(response).toBeNull();
    expect(mockLogError).toHaveBeenCalledWith(error, expect.any(Object));
  });

  it('wraps async functions correctly', async () => {
    const { result } = renderHook(() => useErrorHandler());
    const asyncFn = vi.fn().mockResolvedValue('wrapped success');

    const wrappedFn = result.current.wrapAsyncFunction(asyncFn);
    const response = await wrappedFn('arg1', 'arg2');

    expect(response).toBe('wrapped success');
    expect(asyncFn).toHaveBeenCalledWith('arg1', 'arg2');
  });

  it('wraps async functions that throw', async () => {
    const { result } = renderHook(() => useErrorHandler());
    const error = new Error('Wrapped error');
    const asyncFn = vi.fn().mockRejectedValue(error);

    const wrappedFn = result.current.wrapAsyncFunction(asyncFn);
    const response = await wrappedFn();

    expect(response).toBeNull();
    expect(mockLogError).toHaveBeenCalledWith(error, expect.any(Object));
  });

  it('shows spooky errors', () => {
    const { result } = renderHook(() => useErrorHandler());

    result.current.showSpookyError('Spooky Title', 'Spooky message');

    expect(mockShowGhost).toHaveBeenCalledWith('Spooky Title', 'Spooky message', {
      duration: 6000,
    });
  });

  it('shows critical errors', () => {
    const { result } = renderHook(() => useErrorHandler());
    const action = { label: 'Fix it', onClick: vi.fn() };

    result.current.showCriticalError('Critical Title', 'Critical message', action);

    expect(mockShowError).toHaveBeenCalledWith('Critical Title', 'Critical message', {
      persistent: true,
      action,
    });
  });

  it('includes additional context in error handling', () => {
    const { result } = renderHook(() => useErrorHandler({ component: 'TestComponent' }));
    const error = new Error('Test error');
    const context = { action: 'testAction', userId: '123' };

    result.current.handleError(error, context);

    expect(mockLogError).toHaveBeenCalledWith(error, {
      component: 'TestComponent',
      action: 'testAction',
      userId: '123',
    });
  });
});