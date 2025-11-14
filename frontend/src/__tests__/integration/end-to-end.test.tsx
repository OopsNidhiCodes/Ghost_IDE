/**
 * End-to-End Integration Tests
 * Tests complete user workflows including coding, execution, and AI interaction
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

import { IDEView } from '../../components/Views/IDEView';
import { integrationService } from '../../services/integrationService';
import { socketService } from '../../services/socketService';
import { languageService } from '../../services/languageService';
import { apiService } from '../../services/apiService';
import { useAppStore } from '../../store/useAppStore';

// Mock services
vi.mock('../../services/integrationService');
vi.mock('../../services/socketService');
vi.mock('../../services/languageService');
vi.mock('../../services/apiService');

const mockIntegrationService = vi.mocked(integrationService);
const mockSocketService = vi.mocked(socketService);
const mockLanguageService = vi.mocked(languageService);
const mockApiService = vi.mocked(apiService);

// Mock React Router
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ sessionId: 'test-session-123' }),
    useNavigate: () => mockNavigate,
  };
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('End-to-End Integration Tests', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset store
    useAppStore.getState().setSessionId(null);
    useAppStore.getState().setConnected(false);
    
    // Setup default mocks
    mockIntegrationService.initialize.mockResolvedValue('test-session-123');
    mockIntegrationService.isReady.mockReturnValue(true);
    mockIntegrationService.executeCodeWorkflow.mockResolvedValue();
    mockIntegrationService.saveCurrentFile.mockResolvedValue();
    mockIntegrationService.switchLanguageWorkflow.mockResolvedValue();
    
    mockSocketService.isConnected.mockReturnValue(true);
    
    mockLanguageService.getLanguageConfig.mockResolvedValue({
      name: 'Python',
      displayName: 'Python',
      fileExtension: '.py',
      monacoLanguage: 'python',
      icon: '🐍',
      color: '#3776ab',
      template: 'print("Hello, World!")',
      examples: [],
    });
    
    mockLanguageService.getTemplate.mockResolvedValue('print("Hello, World!")');
    
    mockApiService.healthCheck.mockResolvedValue(true);
    
    // Set initial store state
    act(() => {
      useAppStore.getState().setSessionId('test-session-123');
      useAppStore.getState().setConnected(true);
      useAppStore.getState().addFile({
        id: 'test-file-1',
        name: 'test.py',
        content: 'print("Hello, World!")',
        language: 'python',
        lastModified: new Date(),
      });
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Complete Code Execution Workflow', () => {
    it('should execute complete workflow from editor to output', async () => {
      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalledWith('test-session-123');
      });

      // Find and click run button
      const runButton = await screen.findByTestId('run-code-button');
      expect(runButton).toBeInTheDocument();
      expect(runButton).not.toBeDisabled();

      // Execute code
      await user.click(runButton);

      // Verify integration service was called with correct workflow
      await waitFor(() => {
        expect(mockIntegrationService.executeCodeWorkflow).toHaveBeenCalledWith({
          sessionId: 'test-session-123',
          code: 'print("Hello, World!")',
          language: 'python',
        });
      });

      // Verify UI updates
      expect(screen.getByTestId('code-editor')).toBeInTheDocument();
      expect(screen.getByTestId('output-panel')).toBeInTheDocument();
    });

    it('should handle execution errors gracefully', async () => {
      // Mock execution failure
      mockIntegrationService.executeCodeWorkflow.mockRejectedValue(
        new Error('Syntax error in code')
      );

      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      const runButton = await screen.findByTestId('run-code-button');
      await user.click(runButton);

      // Should still attempt execution
      await waitFor(() => {
        expect(mockIntegrationService.executeCodeWorkflow).toHaveBeenCalled();
      });

      // Error should be handled gracefully (no crash)
      expect(screen.getByTestId('ide-view')).toBeInTheDocument();
    });

    it('should prevent multiple simultaneous executions', async () => {
      // Set executing state
      act(() => {
        useAppStore.getState().setExecuting(true);
      });

      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      const runButton = await screen.findByTestId('run-code-button');
      expect(runButton).toBeDisabled();

      await user.click(runButton);

      // Should not execute when already executing
      expect(mockIntegrationService.executeCodeWorkflow).not.toHaveBeenCalled();
    });
  });

  describe('Language Switching with Session Preservation', () => {
    it('should switch languages seamlessly with session preservation', async () => {
      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      // Find language selector
      const languageSelector = screen.getByTitle('Select programming language');
      expect(languageSelector).toBeInTheDocument();

      // Change language
      await user.selectOptions(languageSelector, 'javascript');

      // Verify integration service was called
      await waitFor(() => {
        expect(mockIntegrationService.switchLanguageWorkflow).toHaveBeenCalledWith({
          sessionId: 'test-session-123',
          newLanguage: 'javascript',
          preserveSession: true,
        });
      });
    });

    it('should handle language switch failures', async () => {
      mockIntegrationService.switchLanguageWorkflow.mockRejectedValue(
        new Error('Language switch failed')
      );

      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      const languageSelector = screen.getByTitle('Select programming language');
      await user.selectOptions(languageSelector, 'javascript');

      // Should attempt switch
      await waitFor(() => {
        expect(mockIntegrationService.switchLanguageWorkflow).toHaveBeenCalled();
      });

      // Should handle error gracefully
      expect(screen.getByTestId('ide-view')).toBeInTheDocument();
    });
  });

  describe('Ghost AI Integration', () => {
    it('should integrate Ghost AI responses with user interactions', async () => {
      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      // Verify Ghost chat is present
      const ghostChat = screen.getByTestId('ghost-chat');
      expect(ghostChat).toBeInTheDocument();

      // The actual chat interaction would be tested in the GhostChat component tests
      // Here we verify the integration is properly set up
    });
  });

  describe('File Save Operations', () => {
    it('should save files with hook integration', async () => {
      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      // Trigger save via keyboard shortcut
      const editor = screen.getByTestId('code-editor');
      await user.click(editor);
      
      // Simulate Ctrl+S
      fireEvent.keyDown(editor, { key: 's', ctrlKey: true });

      // Verify save was called
      await waitFor(() => {
        expect(mockIntegrationService.saveCurrentFile).toHaveBeenCalled();
      });
    });
  });

  describe('Session Management', () => {
    it('should initialize session and restore state', async () => {
      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      // Verify initialization was called with session ID
      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalledWith('test-session-123');
      });

      // Verify UI is ready
      expect(screen.getByTestId('ide-view')).toBeInTheDocument();
      expect(screen.getByTestId('code-editor')).toBeInTheDocument();
      expect(screen.getByTestId('output-panel')).toBeInTheDocument();
      expect(screen.getByTestId('ghost-chat')).toBeInTheDocument();
    });

    it('should handle initialization failures', async () => {
      mockIntegrationService.initialize.mockRejectedValue(
        new Error('Backend service unavailable')
      );

      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      // Should show error state
      await waitFor(() => {
        expect(screen.getByText('Failed to Enter Spirit Realm')).toBeInTheDocument();
      });

      expect(screen.getByText('Backend service unavailable')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    it('should show loading state during initialization', async () => {
      // Make initialization take time
      mockIntegrationService.initialize.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve('test-session'), 100))
      );

      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      // Should show loading initially
      expect(screen.getByText('Summoning the spirits and initializing the realm...')).toBeInTheDocument();

      // Wait for initialization to complete
      await waitFor(() => {
        expect(screen.getByTestId('ide-view')).toBeInTheDocument();
      }, { timeout: 200 });
    });
  });

  describe('Responsive Layout and User Experience', () => {
    it('should render responsive layout with all panels', async () => {
      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      // Verify all main panels are present
      expect(screen.getByTestId('code-editor')).toBeInTheDocument();
      expect(screen.getByTestId('output-panel')).toBeInTheDocument();
      expect(screen.getByTestId('ghost-chat')).toBeInTheDocument();

      // Verify toolbar elements
      expect(screen.getByTestId('run-code-button')).toBeInTheDocument();
      expect(screen.getByTestId('settings-button')).toBeInTheDocument();
      expect(screen.getByTestId('fullscreen-button')).toBeInTheDocument();
    });

    it('should handle fullscreen toggle', async () => {
      // Mock fullscreen API
      Object.defineProperty(document, 'fullscreenElement', {
        writable: true,
        value: null,
      });
      
      document.documentElement.requestFullscreen = vi.fn().mockResolvedValue(undefined);
      document.exitFullscreen = vi.fn().mockResolvedValue(undefined);

      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      const fullscreenButton = screen.getByTestId('fullscreen-button');
      await user.click(fullscreenButton);

      expect(document.documentElement.requestFullscreen).toHaveBeenCalled();
    });

    it('should handle keyboard shortcuts', async () => {
      render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      const editor = screen.getByTestId('code-editor');
      
      // Test Ctrl+Enter for run
      fireEvent.keyDown(editor, { key: 'Enter', ctrlKey: true });
      
      await waitFor(() => {
        expect(mockIntegrationService.executeCodeWorkflow).toHaveBeenCalled();
      });
    });
  });

  describe('Performance and Caching', () => {
    it('should not re-initialize if already ready', async () => {
      mockIntegrationService.isReady.mockReturnValue(true);

      const { rerender } = render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalledTimes(1);
      });

      // Re-render component
      rerender(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      // Should not initialize again
      expect(mockIntegrationService.initialize).toHaveBeenCalledTimes(1);
    });

    it('should cleanup resources on unmount', async () => {
      const { unmount } = render(
        <TestWrapper>
          <IDEView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockIntegrationService.initialize).toHaveBeenCalled();
      });

      unmount();

      expect(mockIntegrationService.cleanup).toHaveBeenCalled();
    });
  });
});