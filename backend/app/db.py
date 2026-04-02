from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .config import get_settings
from .schemas import RecommendationRequest, RecommendationResponse, SavedSession, SavedSessionDetail, UserPreferences


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_column(
    connection: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    existing_columns = {row["name"] for row in rows}
    if column not in existing_columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                goal TEXT NOT NULL,
                skill_level TEXT NOT NULL,
                budget TEXT NOT NULL,
                workflow_style TEXT NOT NULL,
                constraints TEXT,
                top_tool_name TEXT,
                summary TEXT NOT NULL,
                engine_mode TEXT NOT NULL DEFAULT 'heuristic',
                model_name TEXT,
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                profile_id TEXT PRIMARY KEY,
                skill_level TEXT NOT NULL,
                budget TEXT NOT NULL,
                workflow_style TEXT NOT NULL,
                timeline TEXT NOT NULL,
                team_context TEXT NOT NULL,
                primary_outcome TEXT NOT NULL,
                install_preference TEXT NOT NULL,
                pain_points_json TEXT NOT NULL,
                constraints TEXT
            )
            """
        )
        ensure_column(
            connection,
            "saved_sessions",
            "engine_mode",
            "engine_mode TEXT NOT NULL DEFAULT 'heuristic'",
        )
        ensure_column(connection, "saved_sessions", "model_name", "model_name TEXT")
        ensure_column(connection, "user_preferences", "goal", "goal TEXT")
        connection.commit()


def save_session(
    request: RecommendationRequest, response: RecommendationResponse
) -> SavedSession:
    created_at = datetime.now(UTC).isoformat()
    session_id = str(uuid4())
    top_tool_name = (
        response.recommendations[0].tool.name if response.recommendations else None
    )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO saved_sessions (
                id,
                created_at,
                goal,
                skill_level,
                budget,
                workflow_style,
                constraints,
                top_tool_name,
                summary,
                engine_mode,
                model_name,
                request_json,
                response_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                created_at,
                request.goal,
                request.skill_level,
                request.budget,
                request.workflow_style,
                request.constraints,
                top_tool_name,
                response.summary,
                response.engine_mode,
                response.model_name,
                request.model_dump_json(),
                response.model_dump_json(),
            ),
        )
        connection.commit()

    return SavedSession(
        id=session_id,
        created_at=created_at,
        goal=request.goal,
        skill_level=request.skill_level,
        budget=request.budget,
        workflow_style=request.workflow_style,
        constraints=request.constraints,
        top_tool_name=top_tool_name,
        summary=response.summary,
        engine_mode=response.engine_mode,
        model_name=response.model_name,
    )


def list_saved_sessions(limit: int = 8) -> list[SavedSession]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                goal,
                skill_level,
                budget,
                workflow_style,
                constraints,
                top_tool_name,
                summary,
                engine_mode,
                model_name
            FROM saved_sessions
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [SavedSession.model_validate(dict(row)) for row in rows]


def get_saved_session(session_id: str) -> SavedSessionDetail | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                created_at,
                goal,
                skill_level,
                budget,
                workflow_style,
                constraints,
                top_tool_name,
                summary,
                engine_mode,
                model_name,
                request_json,
                response_json
            FROM saved_sessions
            WHERE id = ?
            """,
            (session_id,),
        ).fetchone()

    if row is None:
        return None

    payload = dict(row)
    return SavedSessionDetail(
        id=payload["id"],
        created_at=payload["created_at"],
        goal=payload["goal"],
        skill_level=payload["skill_level"],
        budget=payload["budget"],
        workflow_style=payload["workflow_style"],
        constraints=payload["constraints"],
        top_tool_name=payload["top_tool_name"],
        summary=payload["summary"],
        engine_mode=payload["engine_mode"],
        model_name=payload["model_name"],
        request=RecommendationRequest.model_validate(json.loads(payload["request_json"])),
        response=RecommendationResponse.model_validate(
            json.loads(payload["response_json"])
        ),
    )


def get_preferences(profile_id: str = "default") -> UserPreferences:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                profile_id,
                goal,
                skill_level,
                budget,
                workflow_style,
                timeline,
                team_context,
                primary_outcome,
                install_preference,
                pain_points_json,
                constraints
            FROM user_preferences
            WHERE profile_id = ?
            """,
            (profile_id,),
        ).fetchone()

    if row is None:
        return UserPreferences(profile_id=profile_id)

    payload = dict(row)
    payload["pain_points"] = json.loads(payload.pop("pain_points_json"))
    return UserPreferences.model_validate(payload)


def save_preferences(preferences: UserPreferences) -> UserPreferences:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_preferences (
                profile_id,
                goal,
                skill_level,
                budget,
                workflow_style,
                timeline,
                team_context,
                primary_outcome,
                install_preference,
                pain_points_json,
                constraints
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                goal = excluded.goal,
                skill_level = excluded.skill_level,
                budget = excluded.budget,
                workflow_style = excluded.workflow_style,
                timeline = excluded.timeline,
                team_context = excluded.team_context,
                primary_outcome = excluded.primary_outcome,
                install_preference = excluded.install_preference,
                pain_points_json = excluded.pain_points_json,
                constraints = excluded.constraints
            """,
            (
                preferences.profile_id,
                preferences.goal,
                preferences.skill_level,
                preferences.budget,
                preferences.workflow_style,
                preferences.timeline,
                preferences.team_context,
                preferences.primary_outcome,
                preferences.install_preference,
                json.dumps(preferences.pain_points),
                preferences.constraints,
            ),
        )
        connection.commit()

    return get_preferences(preferences.profile_id)


def list_all_session_ids() -> list[str]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id FROM saved_sessions
            ORDER BY datetime(created_at) DESC
            """
        ).fetchall()
    return [str(row["id"]) for row in rows]


def export_full_backup() -> dict[str, Any]:
    settings = get_settings()
    sessions_out: list[dict[str, Any]] = []
    for session_id in list_all_session_ids():
        detail = get_saved_session(session_id)
        if detail is not None:
            sessions_out.append(detail.model_dump(mode="json"))
    prefs = get_preferences()
    return {
        "schema_version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "app_version": settings.version,
        "app_name": settings.app_name,
        "database_path": str(settings.database_path),
        "preferences": prefs.model_dump(mode="json"),
        "sessions": sessions_out,
    }
