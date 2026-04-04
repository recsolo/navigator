# Navigator

Navigator is a Windows app that helps entrepreneurs pick the right AI tools for their goal, understand why they fit, and get a workflow to run first.

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

## Why this product matters

People are wasting time and money bouncing between AI tools, random YouTube advice, and subscriptions they do not need.

Navigator exists to help a buyer:
- choose the right AI stack faster
- avoid paying for the wrong tools
- get a first workflow they can actually run

## Environment

- Copy `backend/.env.example` if you want explicit local settings.
- Set `OPENAI_API_KEY` to use GPT-assisted ranking.
- Without that key, Navigator falls back to the local heuristic engine.

## Run

Backend target command:
`uvicorn app.main:app --reload --app-dir backend`

Desktop shell target:
`npm start` from `desktop/electron/`

Windows installer build:
`npm run dist:win` from `desktop/electron/`

## Next build priorities

1. Tighten trust and recommendation transparency for first-time buyers.
2. Add richer profile management instead of only the default local profile.
3. Replace the current flat tool catalog with scraper-fed or curated updates.
4. Add publisher metadata and code-signing for release builds.
