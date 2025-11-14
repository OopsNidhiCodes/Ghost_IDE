import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CodeEditor } from '../CodeEditor';
import { useAppStore } from '../../../store/useAppStore';
import { socketService } from '../../../services/socketService';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: vi.fn(({ onChange, onMount, value }) => {
    const mockEditor = {
      addCommand: vi.fn(),
      updateOptions: vi.fn(),
      getModel: vi.fn(() => ({
        setValue: vi.fn(),
      })),
    };

    const mockMonaco = {
      editor: {
        defineTheme: vi.fn(),
        setTheme: vi.fn(),
        setModelLanguage: vi.fn(),
      },
      KeyMod: {
        CtrlCmd: 1,
      },
      KeyCode: {
        KeyS: 2,
        Enter: 3,
      },
    };

    // Simulate editor mount
    React.useEffect(() => {
      if (onMount) {
        onMount(mockEditor, mockMonaco);
      }
    }, []);

    return (
      <div data-testid="monaco-editor">
        <textarea
          data-testid="editor-textarea"
          value={value}
          onChange={(e) => onChange && onChange(e.target.value)}
        />
      </div>
    );
  }),
}));

// Mock socket service
vi.mock('../../../services/socketService', () => ({
  socketService: {
    saveFile: vi.fn(),
    triggerHook: vi.fn(),
    executeCode: vi.fn(),
  },
}));

// Mock store
vi.mock('../../../store/useAppStore');

describe('CodeEditor', () => {
  const mockFile = {
    id: 'test-file-1',
    name: 'test.py',
    content: 'print("Hello, World!")',
    language: 'python',
    lastModified: new Date(),
  };

  const mockPreferences = {
    theme: 'ghost-dark' as const,
    fontSize: 14,
    autoSave: true,
    ghostPersonality: 'spooky' as const,
  };

  const mockStore = {
    currentFile: mockFile,
    updateFile: vi.fn(),
    preferences: mockPreferences,
    currentLanguage: 'python',
    sessionId: 'test-session-123',
  };

  beforeEach(() => {
    vi.mocked(useAppStore).mockReturnValue(mockStore as any);
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  it('renders editor with current file content', () => {
    render(<CodeEditor />);
    
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    expect(screen.getByDisplayValue('print("Hello, World!")')).toBeInTheDocument();
  });

  it('displays file name and language in header', () => {
    render(<CodeEditor />);
    
    expect(screen.getByText('test.py')).toBeInTheDocument();
    expect(screen.getByText('(Python)')).toBeInTheDocument();
  });

  it('shows auto-save indicator when enabled', () => {
    render(<CodeEditor />);
    
    expect(screen.getByText('Auto-save')).toBeInTheDocument();
  });

  it('does not show auto-save indicator when disabled', () => {
    const storeWithoutAutoSave = {
      ...mockStore,
      preferences: { ...mockPreferences, autoSave: false },
    };
    vi.mocked(useAppStore).mockReturnValue(storeWithoutAutoSave as any);

    render(<CodeEditor />);
    
    expect(screen.queryByText('Auto-save')).not.toBeInTheDocument();
  });

  it('calls updateFile when content changes', async () => {
    render(<CodeEditor />);
    
    const textarea = screen.getByTestId('editor-textarea');
    fireEvent.change(textarea, { target: { value: 'print("Updated!")' } });
    
    expect(mockStore.updateFile).toHaveBeenCalledWith('test-file-1', 'print("Updated!")');
  });

  it('calls saveFile when save button is clicked', () => {
    render(<CodeEditor />);
    
    const saveButton = screen.getByTitle('Save (Ctrl+S)');
    fireEvent.click(saveButton);
    
    expect(socketService.saveFile).toHaveBeenCalledWith({
      id: 'test-file-1',
      name: 'test.py',
      content: 'print("Hello, World!")',
      language: 'python',
    });
  });

  it('triggers hook event when save is triggered', () => {
    render(<CodeEditor />);
    
    const saveButton = screen.getByTitle('Save (Ctrl+S)');
    fireEvent.click(saveButton);
    
    expect(socketService.triggerHook).toHaveBeenCalledWith('on_save', {
      code: 'print("Hello, World!")',
      language: 'python',
    });
  });

  it('calls executeCode when run button is clicked', () => {
    render(<CodeEditor />);
    
    const runButton = screen.getByTitle('Run Code (Ctrl+Enter)');
    fireEvent.click(runButton);
    
    expect(socketService.executeCode).toHaveBeenCalledWith(
      'print("Hello, World!")',
      'python'
    );
  });

  it('handles auto-save with debounce', async () => {
    vi.useFakeTimers();
    
    render(<CodeEditor />);
    
    const textarea = screen.getByTestId('editor-textarea');
    fireEvent.change(textarea, { target: { value: 'print("Auto-saved!")' } });
    
    // Should not call saveFile immediately
    expect(socketService.saveFile).not.toHaveBeenCalled();
    
    // Fast-forward time to trigger auto-save
    vi.advanceTimersByTime(2000);
    
    // Run all pending timers
    vi.runAllTimers();
    
    // Check if save was called
    expect(socketService.saveFile).toHaveBeenCalledWith(expect.objectContaining({
      content: 'print("Auto-saved!")',
    }));
    
    vi.useRealTimers();
  });

  it('shows template content when no current file', () => {
    const storeWithoutFile = {
      ...mockStore,
      currentFile: null,
    };
    vi.mocked(useAppStore).mockReturnValue(storeWithoutFile as any);

    render(<CodeEditor />);
    
    expect(screen.getByDisplayValue(/Welcome to the haunted Python realm/)).toBeInTheDocument();
  });

  it('handles different programming languages', () => {
    const javaStore = {
      ...mockStore,
      currentLanguage: 'java',
      currentFile: {
        ...mockFile,
        language: 'java',
        name: 'Test.java',
      },
    };
    vi.mocked(useAppStore).mockReturnValue(javaStore as any);

    render(<CodeEditor />);
    
    expect(screen.getByText('Test.java')).toBeInTheDocument();
    expect(screen.getByText('(Java)')).toBeInTheDocument();
  });

  it('does not call socket methods when no session ID', () => {
    const storeWithoutSession = {
      ...mockStore,
      sessionId: null,
    };
    vi.mocked(useAppStore).mockReturnValue(storeWithoutSession as any);

    render(<CodeEditor />);
    
    const saveButton = screen.getByTitle('Save (Ctrl+S)');
    fireEvent.click(saveButton);
    
    expect(socketService.saveFile).not.toHaveBeenCalled();
    expect(socketService.triggerHook).not.toHaveBeenCalled();
  });

  it('does not call socket methods when no current file', () => {
    const storeWithoutFile = {
      ...mockStore,
      currentFile: null,
    };
    vi.mocked(useAppStore).mockReturnValue(storeWithoutFile as any);

    render(<CodeEditor />);
    
    const runButton = screen.getByTitle('Run Code (Ctrl+Enter)');
    fireEvent.click(runButton);
    
    expect(socketService.executeCode).not.toHaveBeenCalled();
  });
});