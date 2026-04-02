# Navagator Desktop Build & Release Guide

This guide covers building the Navagator desktop application from source and creating a distribution-ready Windows installer.

## Prerequisites

Ensure you have:
- **Python 3.11+** with a virtual environment in `backend/.venv`
- **Node.js 20+** and npm (from nodejs.org)
- **git** for version control
- A **Windows machine** (primary target for now)

## Quick start: Run locally (development)

### 1. Start the backend API

```powershell
cd c:\Users\mnanc\navigator\navigator\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend will be available at `http://127.0.0.1:8000` (or adjust `--port` as needed).

### 2. Start the frontend (separate terminal)

```powershell
cd c:\Users\mnanc\navigator\navigator\frontend
python -m http.server 3000 --bind 127.0.0.1
```

Frontend will be served at `http://127.0.0.1:3000`.

### 3. Start the Electron app (optional, separate terminal)

```powershell
cd c:\Users\mnanc\navigator\navigator\desktop\electron
& 'C:\Program Files\nodejs\npm.cmd' start
```

Electron will:
- Launch a desktop window
- Auto-detect and start the backend on port 8000
- Load the frontend
- Show runtime status (backend, engine mode, database path)

## Build process: Create a Windows installer

### Step 1: Install npm dependencies

```powershell
cd c:\Users\mnanc\navigator\navigator\desktop\electron
& 'C:\Program Files\nodejs\npm.cmd' install
```

This installs:
- `electron` (desktop framework)
- `electron-builder` (Windows installer + NSIS builder)

### Step 2: Build the backend executable

```powershell
cd c:\Users\mnanc\navigator\navigator\desktop\electron
& 'C:\Program Files\nodejs\npm.cmd' run build:backend
```

This runs `desktop/build_backend.py`, which:
- Uses `PyInstaller` to bundle `backend/` into a single `.exe`
- Includes all Python dependencies (fastapi, pydantic, keyring, openai, etc.)
- Includes the tool catalog (`backend/app/data/tool_catalog.json`)
- Outputs to `desktop/dist-backend/navagator-backend.exe`

**Note:** This can take 2–5 minutes depending on your system.

### Step 3: Build the Windows installer

```powershell
cd c:\Users\mnanc\navigator\navigator\desktop\electron
& 'C:\Program Files\nodejs\npm.cmd' run dist:win
```

This runs `electron-builder`, which:
- Packages frontend (`frontend/**/*`)
- Bundles backend exe (`dist-backend/navagator-backend.exe`)
- Creates a Windows installer using NSIS
- Outputs to `desktop/electron/dist/Navagator Setup 0.2.0.exe`

**Output files:**
- `dist/Navagator Setup 0.2.0.exe` — Full NSIS installer (ready to distribute)
- `dist/win-unpacked/` — Unpacked app directory (for portable use)

## Installing and running the built app

### From the installer

1. Download `Navagator Setup 0.2.0.exe`
2. Run the installer (NSIS wizard)
3. Choose installation directory (default: `C:\Program Files\Navagator`)
4. Launch from **Start Menu** → Navagator or desktop shortcut

The installed app will:
- Extract backend exe to app resources
- Set environment variables (`NAVAGATOR_APP_DATA_DIR`, `NAVAGATOR_DATABASE_PATH`)
- Store user data (sessions, preferences, API keys) in `%APPDATA%\Navagator\`
- Auto-start the backend on app launch

### From the unpacked directory

```powershell
cd dist\win-unpacked
.\Navagator.exe
```

Runs the app directly without installing.

## Configuration and environment variables

### For end users

**Optional: Enable GPT-assisted recommendations**

Set the `OPENAI_API_KEY` environment variable before launching:

```powershell
$env:OPENAI_API_KEY = "sk-..."
& 'C:\Program Files\Navagator\Navagator.exe'
```

Or paste your API key in the app's **Settings** tab.

### For developers / CI/CD

**Override API base:**

```powershell
$env:NAVAGATOR_API_BASE = "http://localhost:8001"
```

**Override Python executable:**

```powershell
$env:NAVAGATOR_PYTHON = "C:\path\to\python.exe"
```

**Force app data location:**

```powershell
$env:NAVAGATOR_APP_DATA_DIR = "C:\custom\data"
```

## Packaging options and advanced configuration

### Electron builder config (`desktop/electron/package.json`)

Current build configuration:

```json
{
  "build": {
    "appId": "com.navagator.desktop",
    "productName": "Navagator",
    "files": ["main.js", "preload.js", "../../frontend/**/*"],
    "extraResources": [
      {
        "from": "../../dist-backend/navagator-backend.exe",
        "to": "backend/navagator-backend.exe"
      }
    ],
    "win": {
      "target": ["nsis"]
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  }
}
```

To customize:
- **Product name:** Change `"productName"` in package.json
- **Install directory:** Modify `nsis.allowToChangeInstallationDirectory`
- **One-click install:** Set `nsis.oneClick` to `true`
- **Icons:** Replace `assets/navagator.ico` with your own

### Code signing (optional)

For production, add code signing:

```json
{
  "win": {
    "certificateFile": "/path/to/cert.pfx",
    "certificatePassword": "password",
    "signingHashAlgorithms": ["sha256"],
    "signAndEditExecutable": true
  }
}
```

Then run:

```powershell
& 'C:\Program Files\nodejs\npm.cmd' run dist:win -- --publish=never
```

### Auto-update (Electron Updater)

To add automatic updates:

```bash
npm install electron-updater
```

Then configure in `main.js`:

```javascript
const { autoUpdater } = require("electron-updater");
autoUpdater.checkForUpdatesAndNotify();
```

## Troubleshooting

### "PyInstaller not found" error

Install PyInstaller in the venv:

```powershell
cd backend
.venv\Scripts\python.exe -m pip install pyinstaller
```

### Backend doesn't start in packaged app

Ensure `dist-backend/navagator-backend.exe` exists:

```powershell
Test-Path 'desktop/dist-backend/navagator-backend.exe'
```

If missing, re-run `npm run build:backend`.

### "Only one usage of each socket address" (port 8000 in use)

Kill the existing process or use a different port:

```powershell
$env:NAVAGATOR_API_BASE = "http://127.0.0.1:8001"
```

### Installation fails with "admin rights required"

Ensure you have Windows admin privileges. If NSIS permissions are an issue, edit `package.json`:

```json
{
  "nsis": {
    "installerIcon": "assets/navagator.ico",
    "oneClick": true
  }
}
```

### Database file not persisting

Verify `NAVAGATOR_DATABASE_PATH` is set correctly in packaged mode. Check Electron userData path:

```powershell
# In app console (DevTools)
console.log(window.navagatorDesktop)
```

## Release workflow (for maintainers)

1. **Update version:**
   ```toml
   # backend/pyproject.toml
   version = "0.2.0"
   ```

   ```json
   // desktop/electron/package.json
   "version": "0.2.0"
   ```

2. **Update release notes:**
   ```markdown
   # docs/RELEASE_NOTES.md
   ## v0.2.0 — Title
   ...
   ```

3. **Test locally:**
   ```powershell
   cd backend && .venv\Scripts\python.exe -m pytest
   cd ../desktop/electron && & 'C:\Program Files\nodejs\npm.cmd' start
   ```

4. **Build installer:**
   ```powershell
   cd desktop/electron
   & 'C:\Program Files\nodejs\npm.cmd' run dist:win
   ```

5. **Verify installer:**
   - Extract and test on a clean VM or spare machine
   - Confirm database and secrets are stored in `%APPDATA%\Navagator\`
   - Test with and without `OPENAI_API_KEY`

6. **Commit and tag:**
   ```powershell
   git add pyproject.toml package.json docs/RELEASE_NOTES.md
   git commit -m "v0.2.0: Release"
   git tag -a v0.2.0 -m "Production release: v0.2.0"
   git push origin master --tags
   ```

7. **Publish:**
   - Upload `desktop/electron/dist/Navagator Setup 0.2.0.exe` to GitHub Releases
   - Share download link with testers or end users

## Resources

- [Electron documentation](https://www.electronjs.org/docs)
- [Electron Builder](https://www.electron.build/)
- [PyInstaller docs](https://pyinstaller.org/)
- [NSIS reference](https://nsis.sourceforge.io/Docs/)

---

**Questions or issues?** File a GitHub issue or check the main [README.md](../README.md).
