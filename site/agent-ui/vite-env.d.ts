/// <reference types="vite/client" />
/// <reference types="vite/types/importMeta.d.ts" />

interface ViteTypeOptions {
    // By adding this line, you can make the type of ImportMetaEnv strict
    // to disallow unknown keys.
    // strictImportMetaEnv: unknown
}

interface ImportMetaEnv {
    readonly VITE_API_BASE: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
