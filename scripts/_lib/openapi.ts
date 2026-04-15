import { readFile } from "node:fs/promises";
import { isAbsolute, resolve } from "node:path";

export const DEFAULT_LOCAL_OPENAPI_SOURCE =
  "http://localhost:8000/openapi.json";
export const DEFAULT_RELEASE_OPENAPI_SOURCE =
  "https://api.imgwire.dev/openapi.json";

export function resolveOpenApiSource(): string {
  return (
    process.env.OPENAPI_SOURCE ??
    (process.env.OPENAPI_RELEASE === "true"
      ? DEFAULT_RELEASE_OPENAPI_SOURCE
      : DEFAULT_LOCAL_OPENAPI_SOURCE)
  );
}

export async function loadOpenApiSource(
  source: string,
): Promise<Record<string, unknown>> {
  if (/^https?:\/\//.test(source)) {
    const response = await fetch(source);
    if (!response.ok) {
      throw new Error(
        `Failed to fetch OpenAPI source ${source}: ${response.status} ${response.statusText}`,
      );
    }

    return (await response.json()) as Record<string, unknown>;
  }

  const filePath = isAbsolute(source) ? source : resolve(source);
  return JSON.parse(await readFile(filePath, "utf8")) as Record<
    string,
    unknown
  >;
}
