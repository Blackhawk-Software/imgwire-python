import { resolve } from "node:path";

const repoRoot = resolve(new URL("../..", import.meta.url).pathname);

export const REPO_ROOT = repoRoot;
export const OPENAPI_DIR = resolve(REPO_ROOT, "openapi");
export const RAW_OPENAPI_PATH = resolve(OPENAPI_DIR, "raw.openapi.json");
export const SDK_OPENAPI_PATH = resolve(OPENAPI_DIR, "sdk.openapi.json");
export const GENERATED_DIR = resolve(REPO_ROOT, "generated");
export const CODEGEN_VERSION_PATH = resolve(REPO_ROOT, "CODEGEN_VERSION");
