import { access, mkdtemp, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_TARGET = path.resolve(import.meta.dirname, "..", ".vercel", "output");
const BACKEND_ONLY_MARKERS = [
  "HOSPITAL_AI_GEMINI_API_KEY",
  "HOSPITAL_AI_OPENAI_API_KEY",
  "HOSPITAL_AI_R2_ACCESS_KEY_ID",
  "HOSPITAL_AI_R2_SECRET_ACCESS_KEY",
  "HOSPITAL_AI_JWT_HMAC_SECRET",
  "HOSPITAL_AI_JWKS_URL",
  "HOSPITAL_AI_HMS_API_KEY",
  "GEMINI_API_KEY",
  "OPENAI_API_KEY",
  "HMS_JWT_SECRET",
  "postgresql+asyncpg://",
  "redis://localhost:6379/0",
  "http://localhost:11434",
];

async function assertDirectoryExists(targetPath) {
  await access(targetPath, fsConstants.R_OK);
}

async function collectFiles(rootDir) {
  const entries = await readdir(rootDir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectFiles(fullPath)));
    } else if (entry.isFile()) {
      files.push(fullPath);
    }
  }
  return files;
}

export async function scanPublicBundle(targetDir = DEFAULT_TARGET) {
  const resolvedTarget = path.resolve(targetDir);
  try {
    await assertDirectoryExists(resolvedTarget);
  } catch {
    throw new Error(`Public bundle target not found: ${resolvedTarget}`);
  }

  const files = await collectFiles(resolvedTarget);
  const violations = [];

  for (const file of files) {
    const content = await readFile(file, "utf8");
    for (const marker of BACKEND_ONLY_MARKERS) {
      if (content.includes(marker)) {
        violations.push({
          file,
          marker,
        });
      }
    }
  }

  return {
    targetDir: resolvedTarget,
    fileCount: files.length,
    violations,
  };
}

async function runSelfTest() {
  const tempRoot = await mkdtemp(path.join(os.tmpdir(), "verify-public-bundle-"));
  try {
    const safeDir = path.join(tempRoot, "safe");
    const nestedDir = path.join(tempRoot, "safe", "nested");
    const failingDir = path.join(tempRoot, "failing");

    await mkdir(nestedDir, { recursive: true });
    await mkdir(failingDir, { recursive: true });
    await writeFile(path.join(safeDir, "index.html"), "<html><body>safe bundle</body></html>", "utf8");
    await writeFile(path.join(nestedDir, "app.js"), "console.log('safe bundle');", "utf8");
    await writeFile(
      path.join(failingDir, "env.js"),
      "window.__ENV__='HOSPITAL_AI_GEMINI_API_KEY=leak';",
      "utf8",
    );

    const safeResult = await scanPublicBundle(safeDir);
    if (safeResult.violations.length !== 0 || safeResult.fileCount !== 2) {
      throw new Error("Scanner self-test failed: safe fixture did not pass cleanly.");
    }

    const failingResult = await scanPublicBundle(failingDir);
    if (failingResult.violations.length !== 1) {
      throw new Error("Scanner self-test failed: failing fixture did not report exactly one violation.");
    }

    let missingFailed = false;
    try {
      await scanPublicBundle(path.join(tempRoot, "missing"));
    } catch (error) {
      missingFailed =
        error instanceof Error &&
        error.message.includes("Public bundle target not found:");
    }

    if (!missingFailed) {
      throw new Error("Scanner self-test failed: missing target did not fail explicitly.");
    }

    console.log("Public bundle scanner self-test passed.");
    return {
      safeResult,
      failingResult,
    };
  } finally {
    await rm(tempRoot, { recursive: true, force: true });
  }
}

export async function main(argv = process.argv.slice(2)) {
  if (argv.includes("--self-test")) {
    return runSelfTest();
  }

  const targetDir = argv[0] || DEFAULT_TARGET;
  const result = await scanPublicBundle(targetDir);

  if (result.violations.length > 0) {
    console.error(`Public bundle scan failed: ${result.targetDir}`);
    for (const violation of result.violations) {
      console.error(`- ${path.relative(process.cwd(), violation.file)} contains ${violation.marker}`);
    }
    process.exitCode = 2;
    return result;
  }

  console.log(`Public bundle scan passed: ${result.targetDir} (${result.fileCount} files)`);
  return result;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });
}
