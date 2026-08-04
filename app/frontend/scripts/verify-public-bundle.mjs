import { spawn } from "node:child_process";
import { access, mkdtemp, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const DEFAULT_TARGET = path.resolve(import.meta.dirname, "..", ".vercel", "output");
const BACKEND_ONLY_MARKERS = [
  "HOSPITAL_AI_DATABASE_URL",
  "HOSPITAL_AI_REDIS_URL",
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
  "redis://",
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

async function runCli(targetDir, options = {}) {
  const frontendRoot = path.resolve(import.meta.dirname, "..");
  const cliScriptPath = path.relative(frontendRoot, path.resolve(import.meta.dirname, "verify-public-bundle.mjs"));

  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cliScriptPath, targetDir], {
      cwd: frontendRoot,
      stdio: ["ignore", "pipe", "pipe"],
      ...options,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code, signal) => {
      resolve({
        code,
        signal,
        stdout,
        stderr,
      });
    });
  });
}

async function runSelfTest() {
  const tempRoot = await mkdtemp(path.join(os.tmpdir(), "verify-public-bundle-"));
  try {
    const safeDir = path.join(tempRoot, "safe");
    const nestedDir = path.join(tempRoot, "safe", "nested");
    const failingNameDir = path.join(tempRoot, "failing-names");
    const failingValueDir = path.join(tempRoot, "failing-values", "nested");

    await mkdir(nestedDir, { recursive: true });
    await mkdir(failingNameDir, { recursive: true });
    await mkdir(failingValueDir, { recursive: true });
    await writeFile(path.join(safeDir, "index.html"), "<html><body>safe bundle</body></html>", "utf8");
    await writeFile(path.join(nestedDir, "app.js"), "console.log('safe bundle');", "utf8");
    await writeFile(
      path.join(failingNameDir, "env.js"),
      [
        "window.__ENV__='",
        "HOSPITAL_AI_DATABASE_URL=leak;",
        "HOSPITAL_AI_REDIS_URL=leak;",
        "HOSPITAL_AI_R2_SECRET_ACCESS_KEY=leak;",
        "HOSPITAL_AI_GEMINI_API_KEY=leak;",
        "HOSPITAL_AI_HMS_API_KEY=leak;",
        "HOSPITAL_AI_JWT_HMAC_SECRET=leak",
        "';",
      ].join(""),
      "utf8",
    );
    await writeFile(
      path.join(failingValueDir, "bundle.js"),
      [
        "window.__ENV__='",
        "postgresql+asyncpg://hospital_ai:hospital_ai@db.internal:5432/hospital_ai;",
        "redis://cache.internal:6379/0",
        "';",
      ].join(""),
      "utf8",
    );

    const safeResult = await scanPublicBundle(safeDir);
    if (safeResult.violations.length !== 0 || safeResult.fileCount !== 2) {
      throw new Error("Scanner self-test failed: safe fixture did not pass cleanly.");
    }

    const failingNameResult = await scanPublicBundle(failingNameDir);
    const failingNameMarkers = new Set(failingNameResult.violations.map((violation) => violation.marker));
    const expectedNameMarkers = [
      "HOSPITAL_AI_DATABASE_URL",
      "HOSPITAL_AI_REDIS_URL",
      "HOSPITAL_AI_R2_SECRET_ACCESS_KEY",
      "HOSPITAL_AI_GEMINI_API_KEY",
      "HOSPITAL_AI_HMS_API_KEY",
      "HOSPITAL_AI_JWT_HMAC_SECRET",
    ];
    for (const marker of expectedNameMarkers) {
      if (!failingNameMarkers.has(marker)) {
        throw new Error(`Scanner self-test failed: missing backend-only name marker ${marker}.`);
      }
    }

    const failingValueResult = await scanPublicBundle(path.join(tempRoot, "failing-values"));
    const failingValueMarkers = new Set(failingValueResult.violations.map((violation) => violation.marker));
    const expectedValueMarkers = ["postgresql+asyncpg://", "redis://"];
    for (const marker of expectedValueMarkers) {
      if (!failingValueMarkers.has(marker)) {
        throw new Error(`Scanner self-test failed: missing backend-only value marker ${marker}.`);
      }
    }

    const failingCliDir = path.join(tempRoot, "failing-cli");
    await mkdir(failingCliDir, { recursive: true });
    await writeFile(
      path.join(failingCliDir, "env.js"),
      "window.__ENV__='HOSPITAL_AI_DATABASE_URL=leak';",
      "utf8",
    );

    const cliSmokeResult = await runCli(failingCliDir);
    const cliOutput = `${cliSmokeResult.stdout}\n${cliSmokeResult.stderr}`;
    if (cliSmokeResult.code !== 2) {
      throw new Error(`Scanner self-test failed: CLI smoke test exited ${cliSmokeResult.code} instead of 2.`);
    }
    if (!cliOutput.includes(path.resolve(failingCliDir))) {
      throw new Error("Scanner self-test failed: CLI smoke test did not report the scanned path.");
    }
    if (!cliOutput.includes("HOSPITAL_AI_DATABASE_URL")) {
      throw new Error("Scanner self-test failed: CLI smoke test did not report the offending marker.");
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
      failingNameResult,
      failingValueResult,
      cliSmokeResult,
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

function isDirectExecution(entryArg = process.argv[1]) {
  if (!entryArg) {
    return false;
  }

  return import.meta.url === pathToFileURL(path.resolve(entryArg)).href;
}

if (isDirectExecution()) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });
}
