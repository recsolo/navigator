# Architecture

## Near-term architecture

Navagator starts as a local-first web UI plus Python API.

- `frontend/`
  Browser-based shell for onboarding, recommendations, session history, and saved defaults
- `backend/`
  FastAPI app for questionnaire schema, matching, workflow output, SQLite persistence, and preferences
- `desktop/`
  Electron shell scaffold for the installable desktop wrapper
- local data
  JSON catalog plus SQLite for sessions and preferences

## Why this shape

This keeps product logic explicit and packageable.

It supports four phases:
1. prototype in browser
2. stabilize the guidance engine
3. preserve local history and defaults
4. wrap in a desktop shell for installation

## Packaging direction

After the core experience is proven, the desktop shell should:
- launch the local Python backend automatically
- host the frontend in a desktop window
- package a Windows installer first

Electron is scaffolded now because it is the fastest route to a local installable product. Tauri remains an option later if footprint matters more than speed of iteration.
