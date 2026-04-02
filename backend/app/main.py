from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .db import (
    export_full_backup,
    get_app_settings,
    get_app_settings_view,
    get_preferences,
    get_saved_session,
    init_db,
    list_saved_sessions,
    save_app_settings,
    save_preferences,
    save_session,
)
from .schemas import AppSettingsUpdate, RecommendationRequest, UserPreferences
from .services.recommendations import (
    get_questionnaire,
    get_runtime_status,
    load_catalog,
    recommend,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "version": settings.version}


@app.get("/api/runtime-status")
def runtime_status():
    return get_runtime_status(settings.local_profile_id)


@app.get("/api/questionnaire")
def questionnaire():
    return get_questionnaire()


@app.get("/api/tools")
def tools():
    return load_catalog()


@app.post("/api/recommendations/preview")
def recommendation_preview(payload: RecommendationRequest):
    response = recommend(payload)
    saved = save_session(payload, response)
    response.session_id = saved.id
    return response


@app.get("/api/sessions")
def sessions(limit: int = 8):
    return list_saved_sessions(limit=max(1, min(limit, 20)))


@app.get("/api/sessions/{session_id}")
def session_detail(session_id: str):
    session = get_saved_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/api/preferences")
def preferences():
    return get_preferences()


@app.get("/api/app-settings")
def app_settings():
    return get_app_settings_view(settings.local_profile_id)


@app.put("/api/app-settings")
def update_app_settings(payload: AppSettingsUpdate):
    return save_app_settings(payload)


@app.put("/api/preferences")
def update_preferences(payload: UserPreferences):
    return save_preferences(payload)


@app.get("/api/backup/export")
def export_backup():
    payload = export_full_backup()
    filename = (
        f"navagator-backup-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}Z.json"
    )
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
