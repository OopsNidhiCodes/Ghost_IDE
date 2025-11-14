/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_GHOST_PERSONALITY: string;
  readonly VITE_DEBUG_MODE: string;
  readonly VITE_LOG_LEVEL: string;
  readonly VITE_ENABLE_GHOST_CHAT: string;
  readonly VITE_ENABLE_CODE_EXECUTION: string;
  readonly VITE_ENABLE_FILE_PERSISTENCE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}