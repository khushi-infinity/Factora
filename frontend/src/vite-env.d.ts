/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Absolute API base URL. Empty/unset means "use the Vite dev proxy". */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
