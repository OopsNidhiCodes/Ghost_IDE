import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ErrorBoundary } from '../ErrorBoundary';
import { NotificationSystem } from '../NotificationSystem';
import { useNotificationStore } from '../../../store/useNotificationStore';

// Mock the notification store
vi.mock('../../../store/useNotificationStore');

const mockUseNotificationStore = useNotificationStore as any;

describe('Error Handling Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    console.error = vi.fn();
    
    mockUseNotificationStore.mockReturnValue({
      notifications: [],
      removeNotification: vi.fn(),
    });
  });

  it('renders error boundary and notification system together', () => {
    const TestApp = () => (
      <>
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
        <NotificationSystem />
      </>
    );

    render(<TestApp />);
    
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('shows error boundary when component throws', () => {
    const ThrowingComponent = () => {
      throw new Error('Test error');
    };

    const TestApp = () => (
      <>
        <ErrorBoundary>
          <ThrowingComponent />
        </ErrorBoundary>
        <NotificationSystem />
      </>
    );

    render(<TestApp />);
    
    expect(screen.getByText(/The Ghost Has Encountered a Spectral Error/)).toBeInTheDocument();
  });

  it('renders notification system with notifications', () => {
    mockUseNotificationStore.mockReturnValue({
      notifications: [
        {
          id: '1',
          type: 'success',
          title: 'Success',
          message: 'Operation completed',
        },
      ],
      removeNotification: vi.fn(),
    });

    render(<NotificationSystem />);
    
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText('Operation completed')).toBeInTheDocument();
  });
});