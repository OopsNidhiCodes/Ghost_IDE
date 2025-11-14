import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { GhostChat } from '../GhostChat';
import { useAppStore } from '../../../store/useAppStore';
import { socketService } from '../../../services/socketService';

// Mock the store
vi.mock('../../../store/useAppStore');
const mockUseAppStore = vi.mocked(useAppStore);

// Mock the socket service
vi.mock('../../../services/socketService', () => ({
  socketService: {
    sendGhostMessage: vi.fn(),
  },
}));

const mockSocketService = vi.mocked(socketService);

describe('GhostChat', () => {
  const mockStoreState = {
    chatMessages: [],
    isGhostTyping: false,
    addChatMessage: vi.fn(),
    sessionId: 'test-session-123',
    currentFile: {
      id: 'file1',
      name: 'test.py',
      content: 'print("Hello World")',
      language: 'python',
      lastModified: new Date(),
    },
    currentLanguage: 'python',
    executionResult: {
      stdout: 'Hello World\n',
      stderr: '',
      exitCode: 0,
      executionTime: 0.1,
    },
    preferences: {
      theme: 'ghost-dark' as const,
      fontSize: 14,
      autoSave: true,
      ghostPersonality: 'spooky' as const,
    },
  };

  beforeEach(() => {
    mockUseAppStore.mockReturnValue(mockStoreState as any);
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('renders the ghost chat interface correctly', () => {
    render(<GhostChat />);
    
    expect(screen.getByText('Ghost AI')).toBeInTheDocument();
    expect(screen.getByText('Your supernatural coding companion')).toBeInTheDocument();
    expect(screen.getByText('Haunting')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Summon the ghost with your question...')).toBeInTheDocument();
  });

  it('displays empty state when no messages', () => {
    render(<GhostChat />);
    
    expect(screen.getByText('The spirit realm is quiet...')).toBeInTheDocument();
    expect(screen.getByText('Ask me anything about your code, and I\'ll materialize with help!')).toBeInTheDocument();
  });

  it('displays chat messages correctly', () => {
    const messagesState = {
      ...mockStoreState,
      chatMessages: [
        {
          id: 'msg1',
          content: 'Hello ghost!',
          sender: 'user' as const,
          timestamp: new Date('2023-01-01T10:00:00Z'),
        },
        {
          id: 'msg2',
          content: 'Greetings, mortal! How may I haunt your code today?',
          sender: 'ghost' as const,
          timestamp: new Date('2023-01-01T10:00:30Z'),
        },
      ],
    };
    
    mockUseAppStore.mockReturnValue(messagesState as any);
    render(<GhostChat />);
    
    expect(screen.getByText('Hello ghost!')).toBeInTheDocument();
    expect(screen.getByText('Greetings, mortal! How may I haunt your code today?')).toBeInTheDocument();
  });

  it('shows typing indicator when ghost is typing', () => {
    const typingState = {
      ...mockStoreState,
      isGhostTyping: true,
    };
    
    mockUseAppStore.mockReturnValue(typingState as any);
    render(<GhostChat />);
    
    expect(screen.getByText('The ghost is materializing a response...')).toBeInTheDocument();
  });

  it('sends message when user types and presses Enter', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    
    fireEvent.change(input, { target: { value: 'Help me debug this code' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(mockStoreState.addChatMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        content: 'Help me debug this code',
        sender: 'user',
        context: {
          code: 'print("Hello World")',
          language: 'python',
        },
      })
    );
    
    expect(mockSocketService.sendGhostMessage).toHaveBeenCalledWith(
      'Help me debug this code',
      {
        currentCode: 'print("Hello World")',
        language: 'python',
        recentOutput: mockStoreState.executionResult,
      }
    );
  });

  it('sends message when user clicks send button', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    const sendButton = screen.getByTitle('Send message');
    
    fireEvent.change(input, { target: { value: 'What does this error mean?' } });
    fireEvent.click(sendButton);
    
    expect(mockStoreState.addChatMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        content: 'What does this error mean?',
        sender: 'user',
      })
    );
    
    expect(mockSocketService.sendGhostMessage).toHaveBeenCalled();
  });

  it('does not send empty messages', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    
    fireEvent.change(input, { target: { value: '   ' } }); // Only whitespace
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(mockStoreState.addChatMessage).not.toHaveBeenCalled();
    expect(mockSocketService.sendGhostMessage).not.toHaveBeenCalled();
  });

  it('allows new line with Shift+Enter', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    
    fireEvent.change(input, { target: { value: 'First line' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', shiftKey: true });
    
    // Shift+Enter should not trigger send
    expect(mockStoreState.addChatMessage).not.toHaveBeenCalled();
  });

  it('disables input when no session', () => {
    const noSessionState = {
      ...mockStoreState,
      sessionId: null,
    };
    
    mockUseAppStore.mockReturnValue(noSessionState as any);
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    const sendButton = screen.getByTitle('Send message');
    
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('displays correct ghost personality emoji', () => {
    const personalities = [
      { personality: 'spooky', emoji: '👻' },
      { personality: 'sarcastic', emoji: '😈' },
      { personality: 'helpful-ghost', emoji: '🤖' },
    ];
    
    personalities.forEach(({ personality, emoji }) => {
      const personalityState = {
        ...mockStoreState,
        preferences: {
          ...mockStoreState.preferences,
          ghostPersonality: personality as any,
        },
      };
      
      mockUseAppStore.mockReturnValue(personalityState as any);
      const { unmount } = render(<GhostChat />);
      
      // Use getAllByText since there might be multiple instances of the emoji
      const emojiElements = screen.getAllByText(emoji);
      expect(emojiElements.length).toBeGreaterThan(0);
      unmount();
    });
  });

  it('formats timestamps correctly', () => {
    const testDate = new Date('2023-01-01T14:30:00');
    const messageWithTimestamp = {
      ...mockStoreState,
      chatMessages: [
        {
          id: 'msg1',
          content: 'Test message',
          sender: 'user' as const,
          timestamp: testDate,
        },
      ],
    };
    
    mockUseAppStore.mockReturnValue(messageWithTimestamp as any);
    render(<GhostChat />);
    
    // The timestamp should be formatted as HH:MM
    const expectedTime = new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(testDate);
    
    expect(screen.getByText(expectedTime)).toBeInTheDocument();
  });

  it('clears input after sending message', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    expect(input).toHaveValue('Test message');
    
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(input).toHaveValue('');
  });

  it('shows character count', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    
    expect(screen.getByText('0/500')).toBeInTheDocument();
    
    fireEvent.change(input, { target: { value: 'Hello' } });
    expect(screen.getByText('5/500')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<GhostChat className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('handles message context correctly', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    
    fireEvent.change(input, { target: { value: 'Debug help' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(mockStoreState.addChatMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        context: {
          code: 'print("Hello World")',
          language: 'python',
        },
      })
    );
  });

  it('handles focus and blur events on input', async () => {
    render(<GhostChat />);
    
    const input = screen.getByPlaceholderText('Summon the ghost with your question...');
    
    fireEvent.focus(input);
    // Focus styling should be applied (ring-2 ring-spooky-purple)
    
    fireEvent.blur(input);
    // Focus styling should be removed
  });
});