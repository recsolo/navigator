from __future__ import annotations

from app.schemas import RecommendationRequest
from app.services.recommendations import score_tool
from app.services.recommendations import load_catalog


def test_score_tool_matches_skill_and_budget() -> None:
    catalog = load_catalog()
    chatgpt = next(t for t in catalog if t.id == "chatgpt")
    req = RecommendationRequest(
        goal="write a landing page",
        skill_level="beginner",
        budget="low",
        workflow_style="fast execution",
        timeline="this week",
        primary_outcome="content asset",
        team_context="solo",
        install_preference="local-first",
        pain_points=[],
        constraints="",
    )
    rec = score_tool(chatgpt, req)
    assert rec.score > 0
    assert any("beginner" in r.lower() for r in rec.reasons)


def test_score_tool_flags_budget_mismatch_for_free_user() -> None:
    catalog = load_catalog()
    cursor = next(t for t in catalog if t.id == "cursor")
    req = RecommendationRequest(
        goal="ship code",
        skill_level="advanced",
        budget="free",
        workflow_style="fast execution",
        timeline="this week",
        primary_outcome="working prototype",
        team_context="solo",
        install_preference="local-first",
        pain_points=[],
        constraints="",
    )
    rec = score_tool(cursor, req)
    assert any("budget" in c.lower() for c in rec.cautions) or rec.score <= 0
