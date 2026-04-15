import { mkdtemp, readFile, readdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

import { runGenerate } from "./_lib/generate.ts";
import {
  CODEGEN_VERSION_PATH,
  GENERATED_DIR,
  RAW_OPENAPI_PATH,
  SDK_OPENAPI_PATH,
} from "./_lib/paths.ts";

async function main(): Promise<void> {
  const tempRoot = await mkdtemp(resolve(tmpdir(), "imgwire-python-verify-"));

  await runGenerate({
    source: RAW_OPENAPI_PATH,
    outputDir: resolve(tempRoot, "generated"),
    rawOutputPath: resolve(tempRoot, "openapi", "raw.openapi.json"),
    sdkOutputPath: resolve(tempRoot, "openapi", "sdk.openapi.json"),
    codegenVersionPath: resolve(tempRoot, "CODEGEN_VERSION"),
  });

  await assertFileEquals(
    RAW_OPENAPI_PATH,
    resolve(tempRoot, "openapi", "raw.openapi.json"),
  );
  await assertFileEquals(
    SDK_OPENAPI_PATH,
    resolve(tempRoot, "openapi", "sdk.openapi.json"),
  );
  await assertFileEquals(
    CODEGEN_VERSION_PATH,
    resolve(tempRoot, "CODEGEN_VERSION"),
  );
  await assertTreeEquals(GENERATED_DIR, resolve(tempRoot, "generated"));
}

async function assertFileEquals(actualPath: string, expectedPath: string) {
  const [actual, expected] = await Promise.all([
    readFile(actualPath, "utf8"),
    readFile(expectedPath, "utf8"),
  ]);

  if (actual !== expected) {
    throw new Error(`Generated artifact is stale: ${actualPath}`);
  }
}

async function assertTreeEquals(actualDir: string, expectedDir: string) {
  const actualTree = await listTree(actualDir);
  const expectedTree = await listTree(expectedDir);

  if (JSON.stringify(actualTree) !== JSON.stringify(expectedTree)) {
    throw new Error("Generated directory file list is stale.");
  }

  for (const relativePath of actualTree) {
    await assertFileEquals(
      resolve(actualDir, relativePath),
      resolve(expectedDir, relativePath),
    );
  }
}

async function listTree(root: string): Promise<string[]> {
  return walk(root, "");
}

async function walk(root: string, prefix: string): Promise<string[]> {
  const entries = await readdir(resolve(root, prefix), { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) {
      files.push(...(await walk(root, relativePath)));
      continue;
    }

    if (entry.isFile()) {
      files.push(relativePath);
    }
  }

  return files.sort();
}

await main();
