import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const isWin = process.platform === 'win32';
const npmCmd = isWin ? 'npm.cmd' : 'npm';

function getPythonExecutable() {
  // Potential virtual environment paths relative to workspace root
  const venvPaths = [
    '.venv312',
    '.venv',
    'backend/.venv313',
    'backend/.venv',
  ];

  for (const venvPath of venvPaths) {
    const binDir = isWin ? 'Scripts' : 'bin';
    const exeName = isWin ? 'python.exe' : 'python3';
    const fullPath = path.resolve(venvPath, binDir, exeName);
    
    if (fs.existsSync(fullPath)) {
      console.log(`[dev] Found virtual environment python: ${fullPath}`);
      return fullPath;
    }
  }

  // Fallback to system python
  return isWin ? 'python' : 'python3';
}

const pythonCmd = getPythonExecutable();

function run(command, args, name, cwd = process.cwd()) {
  const finalCommand = isWin && !command.endsWith('.exe') ? 'cmd.exe' : command;
  const finalArgs = isWin && !command.endsWith('.exe') ? ['/d', '/s', '/c', command, ...args] : args;
  
  console.log(`[dev] Starting ${name} in ${cwd}...`);
  const child = spawn(finalCommand, finalArgs, {
    stdio: 'inherit',
    cwd,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  });
  
  child.on('exit', (code) => {
    if (code && code !== 0) {
      process.exitCode = code;
    }
  });
  return child;
}

const apiPort = process.env.API_PORT || '8000';
const port = process.env.PORT || '5173';

console.log(`[dev] Frontend: http://localhost:${port}`);
console.log(`[dev] Backend : http://localhost:${apiPort}`);

const server = run(pythonCmd, ['main.py'], 'backend', path.resolve('backend'));
const client = run(npmCmd, ['--prefix', 'frontend', 'run', 'dev'], 'frontend');

function shutdown() {
  server.kill('SIGINT');
  client.kill('SIGINT');
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
