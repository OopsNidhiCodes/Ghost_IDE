import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';
import { integrationService } from '../../services/integrationService';
import { languageService } from '../../services/languageService';
import { CodeEditor, LanguageSelector, EditorPreferences } from '../Editor';
import { OutputPanel } from '../Output';
import { GhostChat } from '../Chat';
import { ResponsiveLayout, ResizableHandle, ResponsivePanel } from '../Layout/ResponsiveLayout';
import { HelpButton } from '../UI/HelpSystem';
import { Tooltip } from '../UI/Tooltip';
import { LoadingOverlay } from '../UI/LoadingStates';
import { useKeyboardShortcuts, createEditorShortcuts, createNavigationShortcuts } from '../../hooks/useKeyboardShortcuts';
import { useAccessibility, useFocusManagement } from '../../hooks/useAccessibility';
import { useNotificationStore } from '../../store/useNotificationStore';

export const IDEView: React.FC = () => {
  const { sessionId: urlSessionId } = useParams();
  const navigate = useNavigate();
  const {
    sessionId,
    isConnected,
    currentFile,
    currentLanguage,
    isExecuting
  } = useAppStore();
  const { showError } = useNotificationStore();

  const [showPreferences, setShowPreferences] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [initializationError, setInitializationError] = useState<string | null>(null);

  // Refs for focus management
  const editorRef = useRef<HTMLDivElement>(null);
  const outputRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const isInitializingRef = useRef(false);

  // Accessibility hooks
  useAccessibility();
  const { announceToScreenReader, saveFocus, restoreFocus } = useFocusManagement();

  // Initialize the complete IDE system
  useEffect(() => {
    // Prevent multiple initializations
    if (isInitializingRef.current) {
      return;
    }

    const initializeIDE = async () => {
      isInitializingRef.current = true;
      setIsInitializing(true);
      setInitializationError(null);

      try {
        // Initialize integration service with complete workflow
        const finalSessionId = await integrationService.initialize(urlSessionId);

        // Only update URL if we didn't have a sessionId and got a new one
        if (!urlSessionId && finalSessionId && finalSessionId !== urlSessionId) {
          navigate(`/ide/${finalSessionId}`, { replace: true });
        }

        // Create initial file if none exists (only if not already initializing)
        const currentFiles = useAppStore.getState().files;
        if (currentFiles.length === 0 && !currentFile) {
          try {
            const languageConfig = await languageService.getLanguageInfo(currentLanguage);
            const template = await languageService.getLanguageTemplate(currentLanguage);

            const initialFile = {
              id: `file_${Date.now()}`,
              name: `untitled${languageConfig?.extension || '.py'}`,
              content: template || `# Welcome to the haunted ${languageConfig?.name || 'Python'} realm\nprint("Hello, mortal! The spirits are watching...")\n\n# Your code here\n`,
              language: currentLanguage,
              lastModified: new Date(),
            };
            useAppStore.getState().addFile(initialFile);
            console.log('Initial file created:', initialFile.name);
          } catch (err) {
            console.error('Failed to create initial file:', err);
            // Create fallback file
            const fallbackFile = {
              id: `file_${Date.now()}`,
              name: 'untitled.py',
              content: '# Welcome to Ghost IDE\nprint("Hello, World!")\n\n# Your code here\n',
              language: 'python',
              lastModified: new Date(),
            };
            useAppStore.getState().addFile(fallbackFile);
            console.log('Fallback file created');
          }
        }

        setIsInitializing(false);
        announceToScreenReader('IDE initialized successfully', 'polite');

      } catch (error) {
        console.error('Failed to initialize IDE:', error);
        setInitializationError((error as Error).message);
        setIsInitializing(false);
        isInitializingRef.current = false;

        showError(
          '💀 Failed to Enter Spirit Realm',
          'Unable to initialize the IDE. Please try refreshing the page.',
          {
            persistent: true,
            action: {
              label: 'Refresh',
              onClick: () => window.location.reload(),
            },
          }
        );
      }
    };

    initializeIDE();

    // Cleanup on unmount
    return () => {
      isInitializingRef.current = false;
      integrationService.cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlSessionId]);

  // Complete code execution workflow
  const handleRunCode = useCallback(async () => {
    console.log('handleRunCode called - State:', {
      hasFile: !!currentFile,
      fileName: currentFile?.name,
      hasSession: !!sessionId,
      sessionId: sessionId,
      isExecuting
    });

    if (!currentFile || !sessionId || isExecuting) {
      console.error('Run code BLOCKED:', {
        hasFile: !!currentFile,
        fileName: currentFile?.name,
        hasSession: !!sessionId,
        sessionId: sessionId,
        isExecuting
      });
      return;
    }

    console.log('Running code:', { language: currentFile.language, sessionId });

    try {
      announceToScreenReader('Code execution started', 'assertive');

      await integrationService.executeCodeWorkflow({
        sessionId,
        code: currentFile.content,
        language: currentFile.language,
      });

      console.log('Code execution workflow completed');
    } catch (error) {
      console.error('Code execution failed:', error);
      announceToScreenReader('Code execution failed', 'assertive');
    }
  }, [currentFile, sessionId, isExecuting, announceToScreenReader]);

  // Save current file with hooks
  const handleSave = useCallback(async () => {
    if (!currentFile) return;

    try {
      await integrationService.saveCurrentFile();
      announceToScreenReader('Code saved successfully', 'polite');
    } catch (error) {
      console.error('Save failed:', error);
      announceToScreenReader('Save failed', 'assertive');
    }
  }, [currentFile, announceToScreenReader]);

  // Handle language switching with session preservation
  const handleLanguageChange = useCallback(async (newLanguage: string) => {
    if (!sessionId || newLanguage === currentLanguage) return;

    try {
      await integrationService.switchLanguageWorkflow({
        sessionId,
        newLanguage,
        preserveSession: true,
      });

      announceToScreenReader(`Switched to ${newLanguage}`, 'polite');
    } catch (error) {
      console.error('Language switch failed:', error);
      announceToScreenReader('Language switch failed', 'assertive');
    }
  }, [sessionId, currentLanguage, announceToScreenReader]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
      announceToScreenReader('Entered fullscreen mode', 'polite');
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
      announceToScreenReader('Exited fullscreen mode', 'polite');
    }
  };

  const focusEditor = () => {
    editorRef.current?.focus();
    announceToScreenReader('Editor focused', 'polite');
  };

  const focusOutput = () => {
    outputRef.current?.focus();
    announceToScreenReader('Output panel focused', 'polite');
  };

  const focusChat = () => {
    chatRef.current?.focus();
    announceToScreenReader('Chat panel focused', 'polite');
  };

  // Keyboard shortcuts
  const editorShortcuts = createEditorShortcuts({
    save: handleSave,
    run: handleRunCode,
    toggleComment: () => { }, // Monaco editor handles this
    find: () => { }, // Monaco editor handles this
    replace: () => { }, // Monaco editor handles this
    formatCode: () => { }, // Monaco editor handles this
    toggleFullscreen
  });

  const navigationShortcuts = createNavigationShortcuts({
    openHelp: () => { }, // Will be handled by HelpButton
    openSettings: () => setShowPreferences(true),
    focusChat,
    focusEditor,
    focusOutput
  });

  useKeyboardShortcuts({
    shortcuts: [...editorShortcuts, ...navigationShortcuts],
    enabled: isConnected
  });

  // Show loading during initialization
  if (isInitializing) {
    return (
      <LoadingOverlay
        isVisible={true}
        message="Summoning the spirits and initializing the realm..."
      />
    );
  }

  // Show error if initialization failed
  if (initializationError) {
    return (
      <div className="flex items-center justify-center h-full bg-ghost-950 text-ghost-100">
        <div className="text-center p-8">
          <div className="text-6xl mb-4">💀</div>
          <h2 className="text-2xl font-bold mb-4">Failed to Enter Spirit Realm</h2>
          <p className="text-ghost-400 mb-6">{initializationError}</p>
          <button
            onClick={() => window.location.reload()}
            className="spooky-button px-6 py-3"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Show loading if not connected
  if (!isConnected || !integrationService.isReady()) {
    return (
      <LoadingOverlay
        isVisible={true}
        message="Connecting to the Spirit Realm..."
      />
    );
  }

  return (
    <ResponsiveLayout className="h-full" data-testid="ide-view">
      {/* Main IDE Layout */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div className="bg-ghost-900 border-b border-ghost-700 p-3 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <LanguageSelector onLanguageChange={handleLanguageChange} />

              <Tooltip content="Run code (Ctrl+Enter)" position="bottom">
                <button
                  onClick={handleRunCode}
                  disabled={isExecuting || !currentFile}
                  className={`spooky-button text-sm px-4 py-2 flex items-center space-x-2 ${isExecuting ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  aria-label="Run code"
                  data-testid="run-code-button"
                >
                  {isExecuting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Running...</span>
                    </>
                  ) : (
                    <>
                      <span>▶️</span>
                      <span>Run Code</span>
                    </>
                  )}
                </button>
              </Tooltip>

              <Tooltip content="Editor preferences (Ctrl+,)" position="bottom">
                <button
                  onClick={() => {
                    saveFocus();
                    setShowPreferences(true);
                  }}
                  className="bg-ghost-800 hover:bg-ghost-700 text-ghost-200 px-3 py-2 rounded border border-ghost-600 text-sm transition-colors flex items-center space-x-2"
                  aria-label="Open editor preferences"
                  data-testid="settings-button"
                >
                  <span>⚙️</span>
                  <span>Settings</span>
                </button>
              </Tooltip>

              <HelpButton />

              <Tooltip content="Toggle fullscreen (F11)" position="bottom">
                <button
                  onClick={toggleFullscreen}
                  className="bg-ghost-800 hover:bg-ghost-700 text-ghost-200 p-2 rounded border border-ghost-600 transition-colors"
                  aria-label="Toggle fullscreen"
                  data-testid="fullscreen-button"
                >
                  {isFullscreen ? '🪟' : '⛶'}
                </button>
              </Tooltip>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-ghost-400 text-sm">File:</span>
                <span className="text-ghost-300 font-mono text-sm">
                  {currentFile?.name || 'No file'}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-ghost-400 text-sm">Session:</span>
                <span className="text-ghost-300 font-mono text-sm">{sessionId?.slice(0, 12)}...</span>
              </div>
            </div>
          </div>
        </div>

        {/* Editor and Output Area */}
        <div className="flex-1 flex min-h-0">
          {/* Code Editor Panel */}
          <ResponsivePanel
            className="flex-[2] min-w-0"
            title="Code Editor"
            minWidth={400}
          >
            <div ref={editorRef} className="h-full" tabIndex={-1} data-testid="code-editor">
              <CodeEditor />
            </div>
          </ResponsivePanel>

          {/* Resizable Handle */}
          <ResizableHandle
            direction="horizontal"
            onMouseDown={(e) => {
              e.preventDefault();
              // Resizing handled by ResponsiveLayout parent
            }}
          />

          {/* Output Panel */}
          <ResponsivePanel
            className="flex-1 min-w-0"
            title="Output"
            minWidth={250}
            collapsible
          >
            <div ref={outputRef} className="h-full" tabIndex={-1} data-testid="output-panel">
              <OutputPanel />
            </div>
          </ResponsivePanel>
        </div>
      </div>

      {/* Resizable Handle for Chat */}
      <ResizableHandle
        direction="horizontal"
        onMouseDown={(e) => {
          e.preventDefault();
          // Resizing handled by ResponsiveLayout parent
        }}
      />

      {/* Ghost Chat Sidebar */}
      <ResponsivePanel
        className="border-l border-ghost-700"
        title="Ghost AI Chat"
        minWidth={280}
        collapsible
      >
        <div ref={chatRef} className="h-full" tabIndex={-1} data-testid="ghost-chat">
          <GhostChat />
        </div>
      </ResponsivePanel>

      {/* Editor Preferences Modal */}
      <EditorPreferences
        isOpen={showPreferences}
        onClose={() => {
          setShowPreferences(false);
          restoreFocus();
        }}
      />
    </ResponsiveLayout>
  );
};