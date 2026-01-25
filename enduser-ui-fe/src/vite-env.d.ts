/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  // 可以在這裡加入更多環境變數定義
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
