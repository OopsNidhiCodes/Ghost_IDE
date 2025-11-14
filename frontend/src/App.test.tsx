import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the socket service to avoid connection attempts during testing
vi.mock('./services/socketService', () => ({
  socketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    executeCode: vi.fn(),
    sendChatMessage: vi.fn(),
    saveFile: vi.fn(),
    triggerHook: vi.fn(),
    isConnected: vi.fn(() => false),
  },
}));

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText('GhostIDE')).toBeInTheDocument();
  });

  it('displays the welcome view by default', () => {
    render(<App />);
    expect(screen.getByText('A Spooky Online IDE with AI Assistant')).toBeInTheDocument();
  });
});