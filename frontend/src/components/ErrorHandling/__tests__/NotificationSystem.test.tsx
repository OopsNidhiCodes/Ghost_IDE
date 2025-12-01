
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { NotificationSystem } from '../NotificationSystem';
import { useNotificationStore } from '../../../store/useNotificationStore';

// Mock the store
vi.mock('../../../store/useNotificationStore');

const mockUseNotificationStore = useNotificationStore as any;

describe('NotificationSystem', () => {
  const mockRemoveNotification = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders nothing when there are no notifications', () => {
    mockUseNotificationStore.mockReturnValue({
      notifications: [],
      removeNotification: mockRemoveNotification,
    } as any);

    const { container } = render(<NotificationSystem />);
    expect(container.firstChild).toBeNull();
  });

  it('renders notifications correctly', () => {
    const notifications = [
      {
        id: '1',
        type: 'success' as const,
        title: 'Success Title',
        message: 'Success message',
        duration: 5000,
      },
      {
        id: '2',
        type: 'error' as const,
        title: 'Error Title',
        message: 'Error message',
        duration: 5000,
      },
    ];

    mockUseNotificationStore.mockReturnValue({
      notifications,
      removeNotification: mockRemoveNotification,
    } as any);

    render(<NotificationSystem />);

    expect(screen.getByText('Success Title')).toBeInTheDocument();
    expect(screen.getByText('Success message')).toBeInTheDocument();
    expect(screen.getByText('Error Title')).toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('auto-removes notifications after duration', async () => {
    const notifications = [
      {
        id: '1',
        type: 'info' as const,
        title: 'Auto Remove',
        message: 'This will auto remove',
        duration: 100, // Shorter duration for test
      },
    ];

    mockUseNotificationStore.mockReturnValue({
      notifications,
      removeNotification: mockRemoveNotification,
    } as any);

    render(<NotificationSystem />);

    // Fast-forward time
    vi.advanceTimersByTime(100);

    await waitFor(() => {
      expect(mockRemoveNotification).toHaveBeenCalledWith('1');
    }, { timeout: 1000 });
  });

  it('does not auto-remove persistent notifications', () => {
    const notifications = [
      {
        id: '1',
        type: 'warning' as const,
        title: 'Persistent',
        message: 'This is persistent',
        persistent: true,
      },
    ];

    mockUseNotificationStore.mockReturnValue({
      notifications,
      removeNotification: mockRemoveNotification,
    } as any);

    render(<NotificationSystem />);

    // Fast-forward time
    vi.advanceTimersByTime(10000);

    expect(mockRemoveNotification).not.toHaveBeenCalled();
  });

  it('removes notification when close button is clicked', () => {
    const notifications = [
      {
        id: '1',
        type: 'info' as const,
        title: 'Closeable',
        message: 'Click to close',
        duration: 5000,
      },
    ];

    mockUseNotificationStore.mockReturnValue({
      notifications,
      removeNotification: mockRemoveNotification,
    } as any);

    render(<NotificationSystem />);

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);

    expect(mockRemoveNotification).toHaveBeenCalledWith('1');
  });

  it('handles action button clicks', () => {
    const mockAction = vi.fn();
    const notifications = [
      {
        id: '1',
        type: 'error' as const,
        title: 'With Action',
        message: 'Has action button',
        action: {
          label: 'Take Action',
          onClick: mockAction,
        },
      },
    ];

    mockUseNotificationStore.mockReturnValue({
      notifications,
      removeNotification: mockRemoveNotification,
    } as any);

    render(<NotificationSystem />);

    const actionButton = screen.getByText('Take Action');
    fireEvent.click(actionButton);

    expect(mockAction).toHaveBeenCalled();
  });

  it('renders correct icons for different notification types', () => {
    const notifications = [
      { id: '1', type: 'success' as const, title: 'Success', message: 'Success' },
      { id: '2', type: 'error' as const, title: 'Error', message: 'Error' },
      { id: '3', type: 'warning' as const, title: 'Warning', message: 'Warning' },
      { id: '4', type: 'info' as const, title: 'Info', message: 'Info' },
      { id: '5', type: 'ghost' as const, title: 'Ghost', message: 'Ghost' },
    ];

    mockUseNotificationStore.mockReturnValue({
      notifications,
      removeNotification: mockRemoveNotification,
    } as any);

    const { container } = render(<NotificationSystem />);

    // Check that different icons are rendered (we can't easily test specific icons, but we can check they exist)
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(notifications.length); // Each notification has an icon + close button
  });

  it('applies correct styling for different notification types', () => {
    const notifications = [
      { id: '1', type: 'success' as const, title: 'Success', message: 'Success' },
      { id: '2', type: 'error' as const, title: 'Error', message: 'Error' },
    ];

    mockUseNotificationStore.mockReturnValue({
      notifications,
      removeNotification: mockRemoveNotification,
    } as any);

    const { container } = render(<NotificationSystem />);

    const notificationElements = container.querySelectorAll('[class*="border-l-"]');
    expect(notificationElements.length).toBe(2);
  });
});