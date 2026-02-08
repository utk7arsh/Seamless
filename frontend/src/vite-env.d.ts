/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_FLOWGLAD_API_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module "*.mp4" {
  const src: string;
  export default src;
}
