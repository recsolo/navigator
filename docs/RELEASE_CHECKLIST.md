# Release checklist (Navagator)

Use this before tagging a release or shipping an installer to testers.

## Version and metadata

- [ ] Bump `version` in `backend/pyproject.toml` and align `desktop/electron/package.json` if needed.
- [ ] Confirm `GET /api/health` returns the expected version after install.
- [ ] Update build notes in `desktop/README.md` if packaging commands or paths changed.

## Automated checks

- [ ] CI passes on the release branch (`backend` pytest workflow in `.github/workflows/ci.yml`).
- [ ] Run locally: `cd backend && python -m pytest`.

## Functional smoke (local)

- [ ] Start backend: `uvicorn app.main:app` from `backend/` (or desktop shell).
- [ ] Briefing loads from `GET /api/questionnaire` (or fallback if API down).
- [ ] Generate preview saves a session and shows a session id when online.
- [ ] **Export JSON backup** downloads a file from `GET /api/backup/export` and JSON opens with `schema_version`, `preferences`, and `sessions`.
- [ ] Save defaults persists mission + fields (SQLite `user_preferences`).

## Desktop packaging (Windows)

- [ ] Install Node dependencies: `desktop/electron/` → `npm install`.
- [ ] Build PyInstaller backend: `npm run build:backend` from `desktop/electron` (or `python desktop/build_backend.py` from repo root with venv activated).
- [ ] Build installer: `npm run dist:win` — confirm `navagator-backend.exe` is bundled under app resources.
- [ ] Install the NSIS build on a clean machine or VM; confirm SQLite lives under Electron **userData** (packaged app sets `NAVAGATOR_DATABASE_PATH`).
- [ ] Quit app; confirm backend process stops.

## Security and secrets

- [ ] No API keys or secrets committed; `OPENAI_API_KEY` remains environment-only for users who want GPT ranking.
- [ ] Review `Content-Disposition` export filename for unusual characters (default is timestamp-based).

## Optional distribution hardening

- [ ] Code signing for Windows binaries (not configured in repo by default).
- [ ] Crash reporting / telemetry (not included by default; local-first product).
