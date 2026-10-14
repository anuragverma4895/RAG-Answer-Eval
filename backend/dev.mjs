import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const backendDir = dirname(fileURLToPath(import.meta.url));
const projectDir = resolve(backendDir, "..");
const windows = process.platform === "win32";
const venvPython = resolve(projectDir, ".venv", windows ? "Scripts/python.exe" : "bin/python");
const python = existsSync(venvPython) ? venvPython : (windows ? "python" : "python3");

if (!existsSync(venvPython)) {
  console.error("Project virtual environment not found at ../.venv.");
  console.error("Create it from the project root with: python -m venv .venv");
  console.error("Then install backend dependencies with: pip install -r backend/requirements.txt");
  process.exit(1);
}

const server = spawn(python, ["-m", "uvicorn", "app.main:app", "--reload"], {
  cwd: backendDir,
  stdio: "inherit",
});

server.on("error", (error) => {
  console.error("Could not start the backend:", error.message);
  process.exitCode = 1;
});

server.on("exit", (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exitCode = code ?? 1;
});
