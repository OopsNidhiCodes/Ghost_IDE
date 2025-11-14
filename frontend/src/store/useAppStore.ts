import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface CodeFile {
  id: string;
  name: string;
  content: string;
  language: string;
  lastModified: Date;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'ghost';
  timestamp: Date;
  context?: {
    code?: string;
    language?: string;
    error?: string;
  };
}

export interface ExecutionResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  executionTime: number;
}

export interface UserPreferences {
  theme: 'ghost-dark' | 'ghost-light';
  fontSize: number;
  autoSave: boolean;
  ghostPersonality: 'spooky' | 'sarcastic' | 'helpful-ghost';
}

interface AppState {
  // Session management
  sessionId: string | null;
  isConnected: boolean;
  
  // Code editing
  currentFile: CodeFile | null;
  files: CodeFile[];
  currentLanguage: string;
  
  // Code execution
  isExecuting: boolean;
  executionResult: ExecutionResult | null;
  executionHistory: ExecutionResult[];
  
  // Ghost AI
  chatMessages: ChatMessage[];
  isGhostTyping: boolean;
  
  // UI state
  preferences: UserPreferences;
  layout: {
    editorWidth: number;
    outputHeight: number;
    chatWidth: number;
  };
  
  // Actions
  setSessionId: (sessionId: string | null) => void;
  setConnected: (connected: boolean) => void;
  
  // File management
  setCurrentFile: (file: CodeFile | null) => void;
  addFile: (file: CodeFile) => void;
  updateFile: (fileId: string, content: string) => void;
  removeFile: (fileId: string) => void;
  setCurrentLanguage: (language: string) => void;
  
  // Code execution
  setExecuting: (executing: boolean) => void;
  setExecutionResult: (result: ExecutionResult | null) => void;
  appendExecutionOutput: (stdout?: string, stderr?: string) => void;
  addToExecutionHistory: (result: ExecutionResult) => void;
  clearExecutionHistory: () => void;
  
  // Ghost AI
  addChatMessage: (message: ChatMessage) => void;
  setGhostTyping: (typing: boolean) => void;
  clearChatHistory: () => void;
  
  // Preferences
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  updateLayout: (layout: Partial<AppState['layout']>) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      sessionId: null,
      isConnected: false,
      
      currentFile: null,
      files: [],
      currentLanguage: 'python',
      
      isExecuting: false,
      executionResult: null,
      executionHistory: [],
      
      chatMessages: [],
      isGhostTyping: false,
      
      preferences: {
        theme: 'ghost-dark',
        fontSize: 14,
        autoSave: true,
        ghostPersonality: 'spooky',
      },
      
      layout: {
        editorWidth: 60,
        outputHeight: 30,
        chatWidth: 25,
      },
      
      // Actions
      setSessionId: (sessionId) => set({ sessionId }),
      setConnected: (isConnected) => set({ isConnected }),
      
      // File management
      setCurrentFile: (currentFile) => set({ currentFile }),
      
      addFile: (file) => set((state) => ({
        files: [...state.files, file],
        currentFile: file,
      })),
      
      updateFile: (fileId, content) => set((state) => ({
        files: state.files.map(file => 
          file.id === fileId 
            ? { ...file, content, lastModified: new Date() }
            : file
        ),
        currentFile: state.currentFile?.id === fileId 
          ? { ...state.currentFile, content, lastModified: new Date() }
          : state.currentFile,
      })),
      
      removeFile: (fileId) => set((state) => ({
        files: state.files.filter(file => file.id !== fileId),
        currentFile: state.currentFile?.id === fileId ? null : state.currentFile,
      })),
      
      setCurrentLanguage: (currentLanguage) => set({ currentLanguage }),
      
      // Code execution
      setExecuting: (isExecuting) => set({ isExecuting }),
      setExecutionResult: (executionResult) => set({ executionResult }),
      
      appendExecutionOutput: (stdout, stderr) => set((state) => {
        const current = state.executionResult || { stdout: '', stderr: '', exitCode: 0, executionTime: 0 };
        return {
          executionResult: {
            ...current,
            stdout: current.stdout + (stdout || ''),
            stderr: current.stderr + (stderr || ''),
          }
        };
      }),
      
      addToExecutionHistory: (result) => set((state) => ({
        executionHistory: [result, ...state.executionHistory.slice(0, 9)] // Keep last 10
      })),
      
      clearExecutionHistory: () => set({ executionHistory: [] }),
      
      // Ghost AI
      addChatMessage: (message) => set((state) => ({
        chatMessages: [...state.chatMessages, message],
      })),
      
      setGhostTyping: (isGhostTyping) => set({ isGhostTyping }),
      
      clearChatHistory: () => set({ chatMessages: [] }),
      
      // Preferences
      updatePreferences: (newPreferences) => set((state) => ({
        preferences: { ...state.preferences, ...newPreferences },
      })),
      
      updateLayout: (newLayout) => set((state) => ({
        layout: { ...state.layout, ...newLayout },
      })),
    }),
    {
      name: 'ghost-ide-store',
    }
  )
);