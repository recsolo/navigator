# Desktop Shell

This folder prepares Navagator for an installable desktop wrapper.

## Current choice

Electron shell first.

Why:
- simple local packaging path
- can load the existing `frontend/index.html`
- can later launch or embed the local Python backend

## Current behavior

The Electron shell now:
- looks for `..\\..\\.venv\\Scripts\\python.exe` first
- falls back to `NAVAGATOR_PYTHON` or `python` from `PATH`
- starts `uvicorn` for the local FastAPI backend automatically
- waits for `GET /api/health` before opening the UI
- stops the backend process when the desktop app exits
- exposes runtime status in the UI for backend state, engine mode, profile, and database path

## First run later

From `desktop/electron/`:

```powershell
npm install
npm start
```

If PowerShell blocks `npm.ps1` on this machine, use:

```powershell
& 'C:\Program Files\nodejs\npm.cmd' install
& 'C:\Program Files\nodejs\npm.cmd' start
```

## OpenAI-backed ranking

- Set `OPENAI_API_KEY` to enable GPT-assisted recommendations.
- Tune model settings with:
  - `NAVAGATOR_OPENAI_MODEL`
  - `NAVAGATOR_REASONING_EFFORT`
  - `NAVAGATOR_VERBOSITY`
- If no API key is present, the backend stays usable in heuristic fallback mode.

## Packaging

From `desktop/electron/`:

```powershell
& 'C:\Program Files\nodejs\npm.cmd' run dist:win
```

Outputs:
- installer: `desktop/electron/dist/Navagator Setup 0.1.0.exe`
- unpacked app: `desktop/electron/dist/win-unpacked/`
- bundled backend exe: `desktop/dist-backend/navagator-backend.exe`

### Packaged app data and secrets

When the app is **installed/built** (`app.isPackaged` is true), Electron sets:

- `NAVAGATOR_APP_DATA_DIR` → Electron `userData` directory
- `NAVAGATOR_DATABASE_PATH` → `<userData>/navagator.db`

So session history and preferences persist per user profile, not next to the executable.

On Windows, OpenAI API keys are stored in Windows Credential Manager under a Navagator-specific generic credential. Tests and non-Windows fallback paths use app-data files instead.

Development mode (`npm start`) leaves these unset so the backend uses its default database path under `backend/app/data/`.

### Release process

See `docs/RELEASE_CHECKLIST.md` for version bumps, CI, smoke tests, and installer verification.

## Packaging direction

After the local guidance loop is stable:
- decide whether to stay on Electron or migrate to Tauri
- add publisher metadata and code signing for release distribution
