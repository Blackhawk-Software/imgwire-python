import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const packageJsonPath = resolve(process.cwd(), "package.json");
const pyprojectPath = resolve(process.cwd(), "pyproject.toml");

const command = process.argv[2];

if (!command) {
  printUsageAndExit();
}

if (command === "set-version") {
  const version = process.argv[3];
  setVersion(version);
} else if (command === "verify-tag") {
  const tag = process.argv[3];
  verifyTag(tag);
} else {
  printUsageAndExit();
}

function setVersion(version) {
  if (!isValidSemver(version)) {
    fail(
      `Invalid version "${version}". Expected semver like 0.2.0 or 1.0.0-beta.1.`
    );
  }

  const packageJson = readJson(packageJsonPath);
  packageJson.version = version;
  writeJson(packageJsonPath, packageJson);

  const pyproject = readFileSync(pyprojectPath, "utf8");
  const updatedPyproject = replaceProjectVersion(pyproject, version);
  writeFileSync(pyprojectPath, updatedPyproject, "utf8");

  console.log(`Updated pyproject.toml and package.json to version ${version}.`);
  console.log("Next steps:");
  console.log("1. Run make ci.");
  console.log("2. Review the diff.");
  console.log(`3. Commit and push the version bump.`);
  console.log(`4. Publish or tag a release for v${version}.`);
}

function verifyTag(tag) {
  if (!tag) {
    fail("Missing release tag. Usage: yarn release:verify-tag v0.1.0");
  }

  const pyproject = readFileSync(pyprojectPath, "utf8");
  const version = readProjectVersion(pyproject);
  const expectedTag = `v${version}`;

  if (tag !== expectedTag) {
    fail(
      `Release tag ${tag} does not match pyproject.toml version ${version}. Expected ${expectedTag}.`
    );
  }

  console.log(`Release tag ${tag} matches pyproject.toml version ${version}.`);
}

function readProjectVersion(pyproject) {
  const projectSection = getProjectSection(pyproject);
  const versionLine = projectSection.find((line) =>
    line.startsWith("version = ")
  );

  if (!versionLine) {
    fail("Could not find [project].version in pyproject.toml.");
  }

  const match = versionLine.match(/^version = "([^"]+)"$/);
  if (!match) {
    fail("Found [project].version but could not parse it in pyproject.toml.");
  }

  return match[1];
}

function replaceProjectVersion(pyproject, version) {
  const lines = pyproject.split("\n");
  let inProjectSection = false;
  let updated = false;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    if (line === "[project]") {
      inProjectSection = true;
      continue;
    }

    if (inProjectSection && /^\[.+\]$/.test(line)) {
      break;
    }

    if (inProjectSection && line.startsWith("version = ")) {
      lines[index] = `version = "${version}"`;
      updated = true;
      break;
    }
  }

  if (!updated) {
    fail("Could not update [project].version in pyproject.toml.");
  }

  return lines.join("\n");
}

function getProjectSection(pyproject) {
  const lines = pyproject.split("\n");
  const section = [];
  let inProjectSection = false;

  for (const line of lines) {
    if (line === "[project]") {
      inProjectSection = true;
      continue;
    }

    if (inProjectSection && /^\[.+\]$/.test(line)) {
      break;
    }

    if (inProjectSection) {
      section.push(line);
    }
  }

  if (!inProjectSection) {
    fail("Could not find [project] section in pyproject.toml.");
  }

  return section;
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function isValidSemver(version) {
  return /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/.test(
    version
  );
}

function printUsageAndExit() {
  console.error("Usage:");
  console.error("  yarn release:set-version <version>");
  console.error("  yarn release:verify-tag <tag>");
  process.exit(1);
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
