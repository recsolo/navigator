from typing import Literal

from pydantic import BaseModel, Field


class Tool(BaseModel):
    id: str
    name: str
    category: str
    price_band: Literal["free", "low", "mid", "high"]
    skill_fit: list[Literal["beginner", "intermediate", "advanced"]]
    workflow_styles: list[str]
    use_cases: list[str]
    description: str
    strengths: list[str]
    best_for: str


class QuestionnaireQuestion(BaseModel):
    id: str
    label: str
    kind: Literal["text", "select", "multiselect"]
    required: bool = True
    options: list[str] = Field(default_factory=list)
    help_text: str | None = None
    placeholder: str | None = None
    show_when: dict[str, list[str]] = Field(default_factory=dict)


class RecommendationRequest(BaseModel):
    goal: str
    skill_level: Literal["beginner", "intermediate", "advanced"]
    budget: Literal["free", "low", "mid", "high"]
    workflow_style: str
    timeline: Literal["today", "this week", "this month"]
    team_context: Literal["solo", "small team", "client work", "internal team"] = "solo"
    primary_outcome: Literal["research insights", "content asset", "working prototype", "automation system"]
    install_preference: Literal["local-first", "cloud-ok", "no preference"] = "local-first"
    pain_points: list[str] = Field(default_factory=list)
    constraints: str | None = None


class UserPreferences(BaseModel):
    profile_id: str = "default"
    goal: str | None = None
    skill_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    budget: Literal["free", "low", "mid", "high"] = "low"
    workflow_style: str = "fast execution"
    timeline: Literal["today", "this week", "this month"] = "this week"
    team_context: Literal["solo", "small team", "client work", "internal team"] = "solo"
    primary_outcome: Literal["research insights", "content asset", "working prototype", "automation system"] = "working prototype"
    install_preference: Literal["local-first", "cloud-ok", "no preference"] = "local-first"
    pain_points: list[str] = Field(default_factory=list)
    constraints: str | None = None


class Recommendation(BaseModel):
    tool: Tool
    score: int
    reasons: list[str]
    cautions: list[str]
    comparison_note: str | None = None


class WorkflowStep(BaseModel):
    step: int
    title: str
    detail: str


class RecommendationResponse(BaseModel):
    summary: str
    recommendations: list[Recommendation]
    workflow: list[WorkflowStep]
    session_id: str | None = None
    engine_mode: Literal["heuristic", "openai"] = "heuristic"
    model_name: str | None = None
    engine_note: str | None = None


class SavedSession(BaseModel):
    id: str
    created_at: str
    goal: str
    skill_level: Literal["beginner", "intermediate", "advanced"]
    budget: Literal["free", "low", "mid", "high"]
    workflow_style: str
    constraints: str | None = None
    top_tool_name: str | None = None
    summary: str
    engine_mode: Literal["heuristic", "openai"] = "heuristic"
    model_name: str | None = None


class SavedSessionDetail(SavedSession):
    request: RecommendationRequest
    response: RecommendationResponse


class RuntimeStatus(BaseModel):
    backend_status: Literal["online"] = "online"
    engine_mode: Literal["heuristic", "openai"] = "heuristic"
    model_name: str | None = None
    engine_note: str | None = None
    api_key_configured: bool = False
    profile_id: str = "default"
    database_path: str
    catalog_path: str
