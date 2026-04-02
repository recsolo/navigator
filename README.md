# Navagator

Navagator is an installable AI guidance engine. The product helps people choose the right AI tools, learn how to use them together, and stay current without drowning in tool overload.

## Product direction

- Local-first desktop-oriented software
- Python backend for matching, saved sessions, and preference storage
- Lightweight frontend shell for onboarding, recommendations, and workflows
- Electron desktop wrapper scaffold for installable packaging

## Repo layout

- `frontend/` - app shell and browser-based prototype UI
- `backend/` - FastAPI service, local tool catalog, recommendation logic, SQLite persistence
- `desktop/` - packaging-ready desktop shell scaffold
- `docs/` - product, MVP, and architecture docs
- `AGENTS.md` - working rules for Cursor and Codex in this repo

## Current state

This repo now includes:
- branching questionnaire fields
- local tool catalog
- recommendation preview API with OpenAI-backed ranking and heuristic fallback
- workflow preview generation
- saved session history in SQLite
- separate stored user defaults / preferences
- Windows Credential Manager storage for local OpenAI API keys
- desktop shell scaffold that can start the local Python backend automatically
- desktop runtime status bar showing backend state, active engine, profile, and database path
- custom Windows app and installer icon
- Windows installer packaging output under `desktop/electron/dist/`

## Environment

- Copy [backend/.env.example](C:\Users\mnanc\OneDrive\Documents\New%20project\navagator\backend\.env.example) if you want explicit local settings.
- Set `OPENAI_API_KEY` to use GPT-assisted ranking.
- Without that key, Navagator falls back to the local heuristic engine.

## Run

Backend target command:
`uvicorn app.main:app --reload --app-dir backend`

Desktop shell target:
`npm start` from `desktop/electron/`

Windows installer build:
`npm run dist:win` from `desktop/electron/`

## Next build priorities

1. Add richer profile management instead of only the default local profile.
2. Replace the current flat tool catalog with scraper-fed or curated updates.
3. Add publisher metadata and code-signing for release builds.
4. Add multi-profile support instead of a single default profile.
