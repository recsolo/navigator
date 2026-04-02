from __future__ import annotations


def test_health(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_questionnaire_matches_request_fields(client) -> None:
    response = client.get("/api/questionnaire")
    assert response.status_code == 200
    items = response.json()
    ids = {item["id"] for item in items}
    expected = {
        "goal",
        "skill_level",
        "budget",
        "workflow_style",
        "timeline",
        "primary_outcome",
        "team_context",
        "install_preference",
        "pain_points",
        "constraints",
    }
    assert expected.issubset(ids)


def test_recommendation_preview_returns_session_id(client) -> None:
    payload = {
        "goal": "research competitors and outline a launch plan",
        "skill_level": "intermediate",
        "budget": "low",
        "workflow_style": "deep research",
        "timeline": "this week",
        "primary_outcome": "research insights",
        "team_context": "solo",
        "install_preference": "local-first",
        "pain_points": ["tool overload"],
        "constraints": "no coding",
    }
    response = client.post("/api/recommendations/preview", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert body.get("session_id")
    assert len(body.get("recommendations", [])) >= 1


def test_export_backup_json(client) -> None:
    preview = {
        "goal": "export test goal",
        "skill_level": "beginner",
        "budget": "low",
        "workflow_style": "fast execution",
        "timeline": "this week",
        "primary_outcome": "research insights",
        "team_context": "solo",
        "install_preference": "local-first",
        "pain_points": [],
        "constraints": "",
    }
    client.post("/api/recommendations/preview", json=preview)
    response = client.get("/api/backup/export")
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "").lower()
    body = response.json()
    assert body["schema_version"] == 1
    assert "preferences" in body
    assert len(body["sessions"]) >= 1
    assert body["sessions"][0]["goal"] == "export test goal"


def test_preferences_roundtrip(client) -> None:
    payload = {
        "profile_id": "default",
        "goal": "Test saved mission text",
        "skill_level": "beginner",
        "budget": "free",
        "workflow_style": "fast execution",
        "timeline": "today",
        "primary_outcome": "working prototype",
        "team_context": "solo",
        "install_preference": "local-first",
        "pain_points": [],
        "constraints": "speed",
    }
    put = client.put("/api/preferences", json=payload)
    assert put.status_code == 200
    get = client.get("/api/preferences")
    assert get.status_code == 200
    saved = get.json()
    assert saved["goal"] == "Test saved mission text"
    assert saved["budget"] == "free"


def test_app_settings_roundtrip(client) -> None:
    payload = {
        "profile_id": "default",
        "openai_api_key": "sk-local-test-key",
        "recommendation_model": "gpt-5.4",
        "recommendation_reasoning_effort": "medium",
        "recommendation_verbosity": "low",
    }
    put = client.put("/api/app-settings", json=payload)
    assert put.status_code == 200

    get = client.get("/api/app-settings")
    assert get.status_code == 200
    saved = get.json()
    assert saved["openai_api_key"] == "sk-local-test-key"
    assert saved["recommendation_reasoning_effort"] == "medium"


def test_runtime_status_reflects_saved_app_settings(client) -> None:
    client.put(
        "/api/app-settings",
        json={
            "profile_id": "default",
            "openai_api_key": "sk-local-test-key",
            "recommendation_model": "gpt-5.4",
            "recommendation_reasoning_effort": "low",
            "recommendation_verbosity": "medium",
        },
    )
    response = client.get("/api/runtime-status")
    assert response.status_code == 200
    body = response.json()
    assert body["api_key_configured"] is True
    assert body["model_name"] == "gpt-5.4"
