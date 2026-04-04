# Desktop Shell

This folder prepares Navigator for an installable desktop wrapper.

## Current choice

Electron shell first.

Why:
- simple local packaging path
- can load the existing `frontend/index.html`
- can later launch or embed the local Python backend

## Current behavior

The Electron shell now:
- looks for `..\\..\\.venv\\Scripts\\python.exe` first
- falls back to `NAVIGATOR_PYTHON` or legacy `NAVAGATOR_PYTHON`, then `python` from `PATH`
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
  - `NAVIGATOR_OPENAI_MODEL`
  - `NAVIGATOR_REASONING_EFFORT`
  - `NAVIGATOR_VERBOSITY`
- Legacy `NAVAGATOR_*` environment names are still supported during transition.
- If no API key is present, the backend stays usable in heuristic fallback mode.

## Packaging

From `desktop/electron/`:

```powershell
& 'C:\Program Files\nodejs\npm.cmd' run dist:win
```

Outputs:
- installer: `desktop/electron/dist/Navigator Setup 0.2.0.exe`
- unpacked app: `desktop/electron/dist/win-unpacked/`
- bundled backend exe: `desktop/dist-backend/navigator-backend.exe`

### Packaged app data and secrets

When the app is **installed/built** (`app.isPackaged` is true), Electron sets:

- `NAVIGATOR_APP_DATA_DIR` → Electron `userData` directory
- `NAVIGATOR_DATABASE_PATH` → `<userData>/navigator.db`

So session history and preferences persist per user profile, not next to the executable.

On Windows, OpenAI API keys are stored in Windows Credential Manager under a Navigator-specific generic credential. Legacy Navagator credentials are still read during transition. Tests and non-Windows fallback paths use app-data files instead.

Development mode (`npm start`) leaves these unset so the backend uses its default database path under `backend/app/data/`.

### Release process

See `docs/RELEASE_CHECKLIST.md` for version bumps, CI, smoke tests, and installer verification.

## Packaging direction

After the local guidance loop is stable:
- decide whether to stay on Electron or migrate to Tauri
- add publisher metadata and code signing for release distribution
