# Navagator Release Notes

## v0.2.0 — Production Hardening & UX Polish

**Release date:** April 2, 2026  
**Status:** Production-ready for early access

### 🎯 What's new

#### Backend resilience & safety
- **Robust JSON parsing.** OpenAI response parser now handles edge cases gracefully, with clear error messages for malformed payloads.
- **Database recovery.** Corrupted SQLite files are automatically archived and recreated, preventing startup failures.
- **Form validation.** Questionnaire now enforces required fields before API requests (frontend + backend checks).

#### Frontend UX & accessibility
- **Responsive design.** Full mobile support with dedicated breakpoints (<880px, <480px).
- **Accessible navigation.** Skip link, semantic HTML (main/header/region), keyboard tab navigation (Arrow keys, Home/End).
- **Error messaging.** Inline form errors and status indicators (success/error states) guide users when validation fails.
- **Visual polish.** Enhanced card hover effects, loading states, and color-coded status pills.

#### CI/CD pipeline
- **Automated testing.** Backend pytest suite (13 tests) runs on every push.
- **Frontend linting.** GitHub Actions now includes frontend jobs alongside backend checks.
- **Configured for scale.** Ready to add Cypress E2E tests and security audits.

#### Desktop packaging
- **Electron shell polished.** Backend startup + health checks, frontend loading, data paths configured.
- **PyInstaller backend.** Windows `.exe` bundling ready; frontend + backend ship together.

### 🔧 Technical highlights

- **13 backend tests passing** (100% pass rate)
- **Zero breaking changes** from v0.1.0
- **All original features intact:**
  - Questionnaire schema from API
  - Heuristic + OpenAI ranking (with fallback)
  - Session history & preferences (SQLite)
  - Secure API key storage (Windows Credential Manager + file fallback)
  - JSON backup export

### 📦 How to run

#### Development (both servers already running at http://127.0.0.1:3000)
```bash
# Terminal 1: Backend on http://127.0.0.1:8001
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001

# Terminal 2: Frontend on http://127.0.0.1:3000
cd frontend
python -m http.server 3000 --bind 127.0.0.1

# Open http://127.0.0.1:3000
```

#### Desktop (Electron)
```bash
cd desktop/electron
npm install
npm start
```

#### Build installer (Windows)
```bash
cd desktop/electron
npm run build:backend
npm run dist:win
# Output: desktop/electron/dist/Navagator Setup 0.2.0.exe
```

### ✅ Verified behavior

- ✅ Backend health check passes
- ✅ Questionnaire schema loads dynamically
- ✅ Form validation works offline
- ✅ Recommendations generate with/without OpenAI
- ✅ Session saves and exports
- ✅ Preferences persist across refreshes
- ✅ Error states render & update status
- ✅ Mobile layout adapts <768px
- ✅ Keyboard navigation works (tabs, skip link)

### 🚀 Known limitations & future work

- Code signing for Windows binaries (not configured by default)
- Crash reporting / telemetry (not included; local-first product)
- WCAG AAA full audit (current: AA compliant)
- Advanced: Cypress E2E test suite
- macOS / Linux builds (Windows primary for now)

### 📋 Installation notes

**Windows users:**
1. Download `Navagator Setup 0.2.0.exe`
2. Run installer (NSIS wizard)
3. Choose installation directory (default: `Program Files\Navagator`)
4. Launch from Start menu or desktop shortcut
5. Backend starts automatically; first run may take 2–3 seconds for Python startup

**API key (optional):**
- To unlock GPT-assisted recommendations, set `OPENAI_API_KEY` in your environment or paste it into Settings > OpenAI API Key
- Keys are stored in Windows Credential Manager (encrypted) or local app data (development mode)
- Never included in backups or exports

### 🔐 Security notes

- **No secrets committed.** API keys are environment-only.
- **Local-first storage.** All data (preferences, sessions, keys) stored locally; no cloud sync by default.
- **Graceful fallback.** API key not found? Heuristic mode still works.

### 🙏 Thanks

- FastAPI & Uvicorn for lightweight ASGI server
- Pydantic for schema validation
- Electron for cross-platform desktop shell
- PyInstaller for single-file backend bundling
- Windows Credential Manager for secure key storage

### 📞 Support

- GitHub issues: [recsolo/navigator](https://github.com/recsolo/navigator)
- Development notes: See `docs/architecture.md` and `docs/mvp.md`

---

**Next version (v0.3.0):** Code signing, macOS support, and advanced telemetry options.
