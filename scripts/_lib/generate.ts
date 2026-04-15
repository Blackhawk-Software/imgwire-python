import { execFile } from "node:child_process";
import { access, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { promisify } from "node:util";

import { computeCodegenVersion } from "./codegen-version.ts";
import { resetDir, writeJson } from "./fs.ts";
import {
  CODEGEN_VERSION_PATH,
  GENERATED_DIR,
  OPENAPI_DIR,
  RAW_OPENAPI_PATH,
  REPO_ROOT,
  SDK_OPENAPI_PATH,
} from "./paths.ts";
import { loadOpenApiSource, resolveOpenApiSource } from "./openapi.ts";

const execFileAsync = promisify(execFile);
const OPENAPI_GENERATOR_VERSION = "7.14.0";

type BuildSdkSpec = (options: {
  target: "python";
  source: unknown;
}) => Promise<unknown>;

export async function runGenerate(options?: {
  source?: string;
  outputDir?: string;
  rawOutputPath?: string;
  sdkOutputPath?: string;
  codegenVersionPath?: string;
}): Promise<void> {
  const source = options?.source ?? resolveOpenApiSource();
  const outputDir = options?.outputDir ?? GENERATED_DIR;
  const rawOutputPath = options?.rawOutputPath ?? RAW_OPENAPI_PATH;
  const sdkOutputPath = options?.sdkOutputPath ?? SDK_OPENAPI_PATH;
  const codegenVersionPath =
    options?.codegenVersionPath ?? CODEGEN_VERSION_PATH;

  const rawSpec = await loadOpenApiSource(source);
  await writeJson(rawOutputPath, rawSpec);

  const buildSdkSpec = await resolveBuildSdkSpec();
  const sdkSpec = await buildSdkSpec({
    target: "python",
    source: rawSpec,
  });
  await writeJson(sdkOutputPath, sdkSpec);

  await resetDir(outputDir);
  const generatorInputPath = resolve(
    OPENAPI_DIR,
    ".sdk.openapi.generator.json",
  );
  await writeJson(generatorInputPath, toGeneratorCompatibleSpec(sdkSpec));
  await runOpenApiGenerator(generatorInputPath, outputDir);

  const postprocessModule = await import(
    resolve(REPO_ROOT, "scripts/postprocess.ts")
  );
  await postprocessModule.runPostprocess({ generatedDir: outputDir });

  const codegenVersion = await computeCodegenVersion({
    packageJsonPath: resolve(REPO_ROOT, "package.json"),
    pyprojectPath: resolve(REPO_ROOT, "pyproject.toml"),
    rawOpenApiPath: rawOutputPath,
    sdkOpenApiPath: sdkOutputPath,
    generatorConfigPath: resolve(REPO_ROOT, "openapitools.json"),
  });
  await writeFile(codegenVersionPath, `${codegenVersion}\n`, "utf8");
}

function toGeneratorCompatibleSpec(input: unknown): unknown {
  if (Array.isArray(input)) {
    return input.map((item) => toGeneratorCompatibleSpec(item));
  }

  if (!input || typeof input !== "object") {
    return input;
  }

  const value = Object.fromEntries(
    Object.entries(input).map(([key, nestedValue]) => [
      key,
      toGeneratorCompatibleSpec(nestedValue),
    ]),
  ) as Record<string, unknown>;

  if (typeof value.openapi === "string" && value.openapi.startsWith("3.1")) {
    value.openapi = "3.0.3";
  }

  if (Array.isArray(value.anyOf)) {
    const nonNullVariants = value.anyOf.filter(
      (variant) =>
        !(
          variant &&
          typeof variant === "object" &&
          "type" in variant &&
          (variant as { type?: unknown }).type === "null"
        ),
    );
    const hasNullVariant = nonNullVariants.length !== value.anyOf.length;

    if (hasNullVariant && nonNullVariants.length === 1) {
      const [singleVariant] = nonNullVariants;
      if (singleVariant && typeof singleVariant === "object") {
        return {
          ...(singleVariant as Record<string, unknown>),
          nullable: true,
        };
      }
    }
  }

  return value;
}

async function resolveBuildSdkSpec(): Promise<BuildSdkSpec> {
  const candidates = [
    "@imgwire/codegen-core",
    resolve(REPO_ROOT, "../imgwire-codegen-core/dist/index.js"),
  ];

  for (const candidate of candidates) {
    try {
      const module = await import(candidate);
      if (typeof module.buildSdkSpec === "function") {
        return module.buildSdkSpec as BuildSdkSpec;
      }
    } catch {
      continue;
    }
  }

  throw new Error(
    "Unable to resolve @imgwire/codegen-core. Run yarn install or make the sibling imgwire-codegen-core package available.",
  );
}

async function runOpenApiGenerator(
  inputPath: string,
  outputDir: string,
): Promise<void> {
  const generatorArgs = [
    "generate",
    "-g",
    "python",
    "-i",
    inputPath,
    "-o",
    outputDir,
    "--additional-properties",
    [
      "packageName=imgwire_generated",
      "projectName=imgwire-generated",
      "packageVersion=0.1.0",
      "generateSourceCodeOnly=true",
    ].join(","),
  ];
  const generatorJarPath = await resolveOpenApiGeneratorJarPath();

  if (generatorJarPath) {
    await execFileAsync("java", ["-jar", generatorJarPath, ...generatorArgs], {
      cwd: REPO_ROOT,
      env: process.env,
    });
    return;
  }

  const mainJsPath = await resolveOpenApiGeneratorMainPath();
  await execFileAsync(process.execPath, [mainJsPath, ...generatorArgs], {
    cwd: REPO_ROOT,
    env: process.env,
  });
}

async function resolveOpenApiGeneratorJarPath(): Promise<string | null> {
  const candidates = [
    process.env.OPENAPI_GENERATOR_JAR,
    resolve(
      REPO_ROOT,
      `node_modules/@openapitools/openapi-generator-cli/versions/${OPENAPI_GENERATOR_VERSION}.jar`,
    ),
    resolve(
      REPO_ROOT,
      `../imgwire-js/node_modules/@openapitools/openapi-generator-cli/versions/${OPENAPI_GENERATOR_VERSION}.jar`,
    ),
    resolve(
      REPO_ROOT,
      `../imgwire-node/node_modules/@openapitools/openapi-generator-cli/versions/${OPENAPI_GENERATOR_VERSION}.jar`,
    ),
  ].filter((value): value is string => Boolean(value));

  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch {
      continue;
    }
  }

  return null;
}

async function resolveOpenApiGeneratorMainPath(): Promise<string> {
  const candidates = [
    resolve(
      REPO_ROOT,
      "node_modules/@openapitools/openapi-generator-cli/main.js",
    ),
    resolve(
      REPO_ROOT,
      "../imgwire-node/node_modules/@openapitools/openapi-generator-cli/main.js",
    ),
    resolve(
      REPO_ROOT,
      "../imgwire-js/node_modules/@openapitools/openapi-generator-cli/main.js",
    ),
  ];

  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch {
      continue;
    }
  }

  throw new Error(
    "Unable to resolve the OpenAPI Generator CLI. Run yarn install to install @openapitools/openapi-generator-cli.",
  );
}
