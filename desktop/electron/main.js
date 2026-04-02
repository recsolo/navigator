const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const repoRoot = path.resolve(__dirname, '..', '..');
const backendDir = path.join(repoRoot, 'backend');
const frontendEntry = path.join(repoRoot, 'frontend', 'index.html');
const apiBase = process.env.NAVAGATOR_API_BASE || 'http://127.0.0.1:8000';

let backendProcess = null;

function apiUrl(pathname) {
  return new URL(pathname, apiBase).toString();
}

function checkBackendHealth(timeoutMs = 1500) {
  return new Promise((resolve) => {
    const request = http.get(apiUrl('/api/health'), (response) => {
      response.resume();
      resolve(response.statusCode === 200);
    });

    request.setTimeout(timeoutMs, () => {
      request.destroy();
      resolve(false);
    });

    request.on('error', () => resolve(false));
  });
}

function resolveBackendCommand() {
  if (app.isPackaged) {
    const packagedBackend = path.join(
      process.resourcesPath,
      'backend',
      'navagator-backend.exe'
    );
    return { command: packagedBackend, extraArgs: [] };
  }

  const localVenvPython = path.join(repoRoot, '.venv', 'Scripts', 'python.exe');
  if (fs.existsSync(localVenvPython)) {
    return {
      command: localVenvPython,
      extraArgs: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--app-dir', backendDir]
    };
  }

  if (process.env.NAVAGATOR_PYTHON) {
    return {
      command: process.env.NAVAGATOR_PYTHON,
      extraArgs: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--app-dir', backendDir]
    };
  }

  return {
    command: 'python',
    extraArgs: ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--app-dir', backendDir]
  };
}

function launchBackend() {
  if (backendProcess) {
    return;
  }

  const backend = resolveBackendCommand();
  const args = [...backend.extraArgs];

  const childEnv = {
    ...process.env,
    PYTHONUTF8: '1',
    NAVAGATOR_API_BASE: apiBase,
    NAVAGATOR_DESKTOP_MODE: 'electron'
  };
  if (app.isPackaged) {
    const userDataPath = app.getPath('userData');
    childEnv.NAVAGATOR_APP_DATA_DIR = userDataPath;
    childEnv.NAVAGATOR_DATABASE_PATH = path.join(userDataPath, 'navagator.db');
  }

  backendProcess = spawn(backend.command, args, {
    cwd: repoRoot,
    env: childEnv,
    stdio: 'pipe',
    windowsHide: true
  });

  backendProcess.stdout.on('data', (chunk) => {
    process.stdout.write(`[navagator-backend] ${chunk}`);
  });

  backendProcess.stderr.on('data', (chunk) => {
    process.stderr.write(`[navagator-backend] ${chunk}`);
  });

  backendProcess.on('error', (error) => {
    backendProcess = null;
    dialog.showErrorBox(
      'Navagator backend failed to start',
      `Electron could not launch the Python backend.\n\n${error.message}`
    );
  });

  backendProcess.on('exit', (code) => {
    backendProcess = null;
    if (!app.isQuitting && code !== 0) {
      dialog.showErrorBox(
        'Navagator backend stopped',
        `The local backend exited with code ${code}.`
      );
    }
  });
}

async function ensureBackendReady() {
  if (await checkBackendHealth()) {
    return;
  }

  launchBackend();

  for (let attempt = 0; attempt < 25; attempt += 1) {
    if (await checkBackendHealth()) {
      return;
    }

    await new Promise((resolve) => setTimeout(resolve, 400));
  }

  dialog.showErrorBox(
    'Navagator backend unavailable',
    'The desktop shell could not connect to the local backend. The UI will still open, but API-backed features will stay offline until the backend is fixed.'
  );
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1180,
    minHeight: 760,
    backgroundColor: '#03040a',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  window.loadFile(frontendEntry);
}

function stopBackend() {
  if (!backendProcess) {
    return;
  }

  const processToStop = backendProcess;
  backendProcess = null;
  processToStop.kill();
}

app.whenReady().then(async () => {
  await ensureBackendReady();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('before-quit', () => {
  app.isQuitting = true;
  stopBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
