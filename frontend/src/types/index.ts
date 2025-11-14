// Re-export types from store for convenience
export type {
  CodeFile,
  ChatMessage,
  ExecutionResult,
  UserPreferences,
} from '../store/useAppStore';

// Socket.io event types
export interface SocketEvents {
  // Client to server
  execute_code: (data: {
    code: string;
    language: string;
    input?: string;
    sessionId: string;
  }) => void;
  
  ghost_chat: (data: {
    message: string;
    sessionId: string;
    context: {
      currentCode?: string;
      language?: string;
      recentOutput?: import('../store/useAppStore').ExecutionResult;
    };
  }) => void;
  
  save_file: (data: {
    id: string;
    name: string;
    content: string;
    language: string;
    sessionId: string;
  }) => void;
  
  hook_event: (data: {
    type: 'on_run' | 'on_error' | 'on_save';
    data: any;
    sessionId: string;
  }) => void;
  
  // Server to client
  execution_start: () => void;
  execution_output: (data: {
    stdout: string;
    stderr: string;
    exitCode?: number;
    executionTime?: number;
  }) => void;
  execution_complete: (data: import('../store/useAppStore').ExecutionResult) => void;
  execution_error: (data: { error: string }) => void;
  ghost_response: (data: {
    message: string;
    context?: any;
  }) => void;
  ghost_typing: () => void;
}

// Language configuration
export interface LanguageConfig {
  name: string;
  extension: string;
  monacoLanguage: string;
  icon: string;
  color: string;
  template: string;
  examples: string[];
}

// Hook event types
export type HookType = 'on_run' | 'on_error' | 'on_save';

export interface HookEvent {
  type: HookType;
  sessionId: string;
  timestamp: Date;
  data: {
    code?: string;
    error?: string;
    output?: string;
    language?: string;
  };
}

// Ghost AI personality types
export type GhostPersonality = 'spooky' | 'sarcastic' | 'helpful-ghost';

export interface GhostPersonalityConfig {
  name: string;
  traits: string[];
  responseTemplates: {
    encouragement: string[];
    mockery: string[];
    debugging: string[];
    codeReview: string[];
  };
  vocabularyStyle: GhostPersonality;
}

// UI Layout types
export interface LayoutConfig {
  editorWidth: number;
  outputHeight: number;
  chatWidth: number;
}

// Theme types
export type Theme = 'ghost-dark' | 'ghost-light';

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Session types
export interface SessionData {
  id: string;
  files: import('../store/useAppStore').CodeFile[];
  currentLanguage: string;
  chatHistory: import('../store/useAppStore').ChatMessage[];
  preferences: import('../store/useAppStore').UserPreferences;
  createdAt: Date;
  lastActivity: Date;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}