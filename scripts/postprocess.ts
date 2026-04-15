import { readFile, readdir, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

import { GENERATED_DIR } from "./_lib/paths.ts";

const GENERATED_ROOT_ENTRIES_TO_REMOVE = new Set([
  ".gitignore",
  ".openapi-generator-ignore",
  "README.md",
  "docs",
  "git_push.sh",
  "requirements.txt",
  "setup.cfg",
  "setup.py",
  "test",
  "test-requirements.txt",
  "tox.ini",
  ".github",
  ".gitlab-ci.yml",
  ".travis.yml",
  "pyproject.toml",
  "imgwire_generated_README.md",
]);

export async function runPostprocess(options?: {
  generatedDir?: string;
}): Promise<void> {
  const generatedDir = options?.generatedDir ?? GENERATED_DIR;

  for (const name of GENERATED_ROOT_ENTRIES_TO_REMOVE) {
    await rm(resolve(generatedDir, name), { force: true, recursive: true });
  }

  await rm(resolve(generatedDir, ".openapi-generator"), {
    force: true,
    recursive: true,
  });
  await rm(resolve(generatedDir, "imgwire_generated", "docs"), {
    force: true,
    recursive: true,
  });
  await rm(resolve(generatedDir, "imgwire_generated", "test"), {
    force: true,
    recursive: true,
  });

  await writeFile(
    resolve(generatedDir, "__init__.py"),
    '"""Disposable OpenAPI-generated client package."""\n',
    "utf8",
  );
  await writeFile(
    resolve(generatedDir, "imgwire_generated", "py.typed"),
    "",
    "utf8",
  );

  const pythonFiles = await listPythonFiles(generatedDir);
  for (const filePath of pythonFiles) {
    const source = await readFile(filePath, "utf8");
    const updated = source
      .replaceAll("from imgwire_generated", "from generated.imgwire_generated")
      .replaceAll(
        "import imgwire_generated",
        "import generated.imgwire_generated",
      );
    if (updated !== source) {
      await writeFile(filePath, updated, "utf8");
    }
  }
}

async function listPythonFiles(root: string): Promise<string[]> {
  const files: string[] = [];
  const stack = [root];

  while (stack.length > 0) {
    const current = stack.pop()!;
    const entries = await readdir(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = resolve(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
        continue;
      }

      if (entry.isFile() && entry.name.endsWith(".py")) {
        files.push(fullPath);
      }
    }
  }

  return files;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await runPostprocess();
}
