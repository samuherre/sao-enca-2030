/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base de la API del backend (variable conceptual API_URL). */
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
