// Copies the React Router client build (build/client) into backend/app/static so
// the FastAPI backend can serve the frontend. Uses Node fs (cross-platform) instead
// of shell rm/cp, which bun's builtin shell mishandles on Windows.
import { rmSync, mkdirSync, cpSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "..", "build", "client");
const dest = resolve(here, "..", "..", "backend", "app", "static");

rmSync(dest, { recursive: true, force: true });
mkdirSync(dest, { recursive: true });
cpSync(src, dest, { recursive: true });
console.log(`前端产物已复制到 ${dest}`);