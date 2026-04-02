import json
from datetime import UTC, datetime
from pathlib import Path
import re

from ..config import get_settings
from ..db import get_app_settings
from ..schemas import (
    AppSettings,
    QuestionnaireQuestion,
    Recommendation,
    RecommendationRequest,
    RecommendationResponse,
    RuntimeStatus,
    Tool,
    WorkflowStep,
)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional until dependencies are installed
    OpenAI = None


QUESTIONNAIRE: list[QuestionnaireQuestion] = [
    QuestionnaireQuestion(
        id="goal",
        label="What are you trying to get done?",
        kind="text",
        help_text="Example: launch a landing page, automate outreach, build a content system.",
        placeholder="Example: research competitors and ship a landing page this week.",
    ),
    QuestionnaireQuestion(
        id="skill_level",
        label="How comfortable are you with AI tools right now?",
        kind="select",
        options=["beginner", "intermediate", "advanced"],
    ),
    QuestionnaireQuestion(
        id="budget",
        label="What budget range fits your current stack?",
        kind="select",
        options=["free", "low", "mid", "high"],
    ),
    QuestionnaireQuestion(
        id="workflow_style",
        label="What kind of workflow do you want?",
        kind="select",
        options=["fast execution", "deep research", "content production", "automation"],
    ),
    QuestionnaireQuestion(
        id="timeline",
        label="How fast does this need to move?",
        kind="select",
        options=["today", "this week", "this month"],
        help_text="Urgency changes which tools are worth the setup cost.",
    ),
    QuestionnaireQuestion(
        id="primary_outcome",
        label="What should this workflow produce first?",
        kind="select",
        options=[
            "research insights",
            "content asset",
            "working prototype",
            "automation system",
        ],
    ),
    QuestionnaireQuestion(
        id="team_context",
        label="Who needs to work with the output?",
        kind="select",
        options=["solo", "small team", "client work", "internal team"],
        show_when={"workflow_style": ["content production", "automation", "fast execution"]},
    ),
    QuestionnaireQuestion(
        id="install_preference",
        label="Where should the stack lean?",
        kind="select",
        options=["local-first", "cloud-ok", "no preference"],
        help_text="This helps Navagator favor installable and privacy-sensitive workflows when needed.",
        show_when={"workflow_style": ["automation", "fast execution", "deep research"]},
    ),
    QuestionnaireQuestion(
        id="pain_points",
        label="What is slowing you down most?",
        kind="multiselect",
        required=False,
        options=[
            "tool overload",
            "blank page",
            "too much manual work",
            "handoff friction",
            "cost confusion",
        ],
        show_when={"skill_level": ["intermediate", "advanced"]},
    ),
    QuestionnaireQuestion(
        id="constraints",
        label="What constraint matters most right now?",
        kind="text",
        required=False,
        help_text="Example: no coding, low budget, team handoff, speed.",
    ),
]

GOAL_SIGNAL_MAP: dict[str, set[str]] = {
    "research": {"research", "competitor", "compare", "analysis", "market", "find"},
    "writing": {"write", "copy", "content", "blog", "email", "landing"},
    "planning": {"plan", "strategy", "roadmap", "brief", "outline"},
    "automation": {"automation", "automate", "workflow", "sync", "trigger"},
    "coding": {"code", "build", "app", "prototype", "ship", "developer"},
    "documentation": {"docs", "documentation", "knowledge", "organize", "workspace"},
}

WORKFLOW_CATEGORY_BONUS: dict[str, set[str]] = {
    "fast execution": {"assistant", "workspace", "builder", "automation"},
    "deep research": {"research", "assistant"},
    "content production": {"assistant", "workspace", "builder"},
    "automation": {"automation", "workspace"},
}

OUTCOME_USE_CASE_MAP: dict[str, set[str]] = {
    "research insights": {"research"},
    "content asset": {"writing", "documentation"},
    "working prototype": {"coding", "planning"},
    "automation system": {"automation"},
}

_RUNTIME_STATE: dict[str, str | None] = {
    "engine_mode": "heuristic",
    "model_name": None,
    "engine_note": "OpenAI assist has not run yet. Using local heuristic mode.",
    "last_error": None,
    "last_run_at": None,
}


def load_catalog() -> list[Tool]:
    data_path: Path = get_settings().data_path
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    return [Tool.model_validate(item) for item in payload]


def get_questionnaire() -> list[QuestionnaireQuestion]:
    return QUESTIONNAIRE


def get_effective_app_settings(profile_id: str | None = None) -> AppSettings:
    settings = get_settings()
    return get_app_settings(profile_id or settings.local_profile_id)


def update_runtime_state(
    *, engine_mode: str, model_name: str | None, engine_note: str | None
) -> None:
    _RUNTIME_STATE["engine_mode"] = engine_mode
    _RUNTIME_STATE["model_name"] = model_name
    _RUNTIME_STATE["engine_note"] = engine_note
    _RUNTIME_STATE["last_error"] = engine_note if engine_mode == "heuristic" else None
    _RUNTIME_STATE["last_run_at"] = datetime.now(UTC).isoformat()


def get_runtime_status(profile_id: str | None = None) -> RuntimeStatus:
    settings = get_settings()
    app_settings = get_effective_app_settings(profile_id)
    default_note = "OpenAI-backed ranking is ready." if app_settings.openai_api_key else (
        "OpenAI API key is not configured. Navagator is using local heuristic mode."
    )

    if app_settings.openai_api_key and OpenAI is None:
        default_note = "The OpenAI Python package is missing, so Navagator is using local heuristic mode."

    model_name = _RUNTIME_STATE["model_name"]
    if not model_name and app_settings.openai_api_key and OpenAI is not None:
        model_name = app_settings.recommendation_model

    return RuntimeStatus(
        backend_status="online",
        engine_mode=_RUNTIME_STATE["engine_mode"] or "heuristic",
        model_name=model_name,
        engine_note=_RUNTIME_STATE["engine_note"] or default_note,
        api_key_configured=bool(app_settings.openai_api_key),
        profile_id=profile_id or settings.local_profile_id,
        database_path=str(settings.database_path),
        catalog_path=str(settings.data_path),
    )


def normalize_tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if token}


def extract_goal_signals(goal: str, constraints: str) -> set[str]:
    tokens = normalize_tokens(goal) | normalize_tokens(constraints)
    matched: set[str] = set()

    for signal, keywords in GOAL_SIGNAL_MAP.items():
        if tokens & keywords:
            matched.add(signal)

    return matched


def build_comparison_note(
    tool: Tool, req: RecommendationRequest, ranked_tools: list[Tool]
) -> str | None:
    alternatives = [item for item in ranked_tools if item.id != tool.id]
    if not alternatives:
        return None

    alt = alternatives[0]

    if tool.category == "automation":
        if tool.name == "Zapier":
            return f"Choose {tool.name} over {alt.name} when you need faster no-code setup and less branching complexity."
        if tool.name == "Make":
            return f"Choose {tool.name} over {alt.name} when the workflow needs more branching, data shaping, or multi-step orchestration."

    if tool.category == "research":
        return f"Choose {tool.name} over {alt.name} when current information and source-backed comparison matter more than all-purpose drafting."

    if tool.category == "workspace":
        return f"Choose {tool.name} over {alt.name} when shared context, documentation, or handoff clarity matters more than raw generation speed."

    if tool.category == "builder":
        return f"Choose {tool.name} over {alt.name} when the goal is turning the plan into working product changes inside a codebase."

    if tool.category == "assistant":
        if req.timeline == "today":
            return f"Choose {tool.name} over {alt.name} when you need the fastest path from vague goal to usable draft today."
        return f"Choose {tool.name} over {alt.name} when you need a broader first tool instead of a narrower specialist."

    return None


def build_tool_step(
    step: int, tool: Tool, req: RecommendationRequest, prior_tool: str | None = None
) -> WorkflowStep:
    if tool.category == "research":
        detail = (
            f"Use {tool.name} to gather current examples, pricing, and competitor context for "
            f"'{req.goal}'. Capture only the sources that directly inform the decision."
        )
        title = "Research the landscape"
    elif tool.category == "assistant":
        detail = (
            f"Use {tool.name} to turn the goal into a concrete execution brief, draft prompts, and a first-pass plan for {req.primary_outcome}."
        )
        title = "Translate the goal into a brief"
    elif tool.category == "workspace":
        detail = (
            f"Use {tool.name} to organize the plan, source notes, and handoff steps so the workflow remains usable for a {req.team_context} setup."
        )
        title = "Create the operating layer"
    elif tool.category == "automation":
        detail = (
            f"Use {tool.name} to wire the repeatable flow, starting with the trigger and the single output that proves the automation works."
        )
        title = "Wire the repeatable system"
    elif tool.category == "builder":
        detail = (
            f"Use {tool.name} to implement the first working version of the flow, focusing only on the smallest shippable outcome."
        )
        title = "Build the working version"
    else:
        detail = f"Use {tool.name} to move the workflow forward without expanding scope."
        title = "Advance the workflow"

    if prior_tool:
        detail += f" Carry forward the output from {prior_tool} instead of starting from scratch."

    return WorkflowStep(step=step, title=title, detail=detail)


def score_tool(tool: Tool, req: RecommendationRequest) -> Recommendation:
    goal = req.goal.lower()
    workflow = req.workflow_style.lower()
    constraints = (req.constraints or "").lower()
    goal_signals = extract_goal_signals(req.goal, constraints)
    tool_use_cases = {use_case.lower() for use_case in tool.use_cases}
    outcome_targets = OUTCOME_USE_CASE_MAP.get(req.primary_outcome, set())

    score = 0
    reasons: list[str] = []
    cautions: list[str] = []

    if req.skill_level in tool.skill_fit:
        score += 4
        reasons.append(f"Fits a {req.skill_level} user.")
    else:
        score -= 2
        cautions.append(f"May be a stretch for a {req.skill_level} user.")

    if req.budget == tool.price_band:
        score += 4
        reasons.append("Matches the stated budget.")
    elif req.budget == "free" and tool.price_band != "free":
        score -= 3
        cautions.append("May exceed a free-only budget.")
    elif req.budget == "low" and tool.price_band == "high":
        score -= 2
        cautions.append("High pricing may not fit the current stack budget.")
    elif req.budget in {"mid", "high"} and tool.price_band in {"free", "low"}:
        score += 1
        reasons.append("Delivers value without forcing an expensive stack.")

    if workflow in (style.lower() for style in tool.workflow_styles):
        score += 3
        reasons.append(f"Supports a {req.workflow_style} workflow.")
    elif tool.category in WORKFLOW_CATEGORY_BONUS.get(workflow, set()):
        score += 2
        reasons.append(f"Category fit is strong for {req.workflow_style}.")

    if tool_use_cases & outcome_targets:
        score += 3
        reasons.append(f"Helps produce a {req.primary_outcome}.")

    direct_matches = sorted(goal_signals & tool_use_cases)
    if direct_matches:
        score += 3 + len(direct_matches)
        reasons.append(f"Matches the requested {direct_matches[0]} job.")
    else:
        goal_tokens = normalize_tokens(goal)
        strength_hits = sum(
            1 for strength in tool.strengths if normalize_tokens(strength) & goal_tokens
        )
        if strength_hits:
            score += min(strength_hits, 2)
            reasons.append("Strengths line up with the stated outcome.")

    if constraints:
        if "no coding" in constraints and tool.category in {
            "automation",
            "workspace",
            "assistant",
        }:
            reasons.append("Works without heavy engineering setup.")
            score += 2
        if "no coding" in constraints and tool.category == "builder":
            score -= 2
            cautions.append("Builder-heavy tools may add more setup than you want.")
        if any(term in constraints for term in {"speed", "fast", "quick"}):
            reasons.append("Good fit when speed matters more than customization.")
            score += 2
        if any(term in constraints for term in {"team", "handoff", "shared"}) and tool.category == "workspace":
            score += 2
            reasons.append("Useful when work needs to be handed off or shared.")
        if any(term in constraints for term in {"automation", "repeatable"}) and tool.category == "automation":
            score += 2
            reasons.append("Well suited to repeatable process work.")

    if req.timeline == "today":
        if tool.category in {"assistant", "research", "workspace"}:
            score += 2
            reasons.append("Low setup overhead fits a same-day timeline.")
        if tool.category == "automation":
            score -= 1
            cautions.append("Automation setup may be slower than the current timeline allows.")
    elif req.timeline == "this month" and tool.category in {"automation", "builder"}:
        score += 1
        reasons.append("Worth the setup cost for a longer runway.")

    if req.team_context in {"small team", "client work", "internal team"} and tool.category == "workspace":
        score += 2
        reasons.append("Good for sharing work across people.")

    if req.install_preference == "local-first":
        if tool.category in {"assistant", "workspace", "builder"}:
            score += 1
            reasons.append("Can sit in a local-first working stack.")
    elif req.install_preference == "cloud-ok" and tool.category == "automation":
        score += 1
        reasons.append("Cloud-connected tooling is acceptable here.")

    pain_points = {item.lower() for item in req.pain_points}
    if "tool overload" in pain_points and tool.category in {"assistant", "workspace"}:
        score += 1
        reasons.append("Helps reduce stack sprawl.")
    if "too much manual work" in pain_points and tool.category == "automation":
        score += 2
        reasons.append("Directly addresses manual process drag.")
    if "handoff friction" in pain_points and tool.category == "workspace":
        score += 2
        reasons.append("Makes handoff and visibility easier.")
    if "cost confusion" in pain_points and tool.price_band in {"free", "low"}:
        score += 1
        reasons.append("Keeps the stack simpler to justify on cost.")

    if not reasons:
        reasons.append(tool.best_for)

    unique_reasons = list(dict.fromkeys(reasons))
    unique_cautions = list(dict.fromkeys(cautions))

    return Recommendation(
        tool=tool,
        score=max(score, 0),
        reasons=unique_reasons[:4],
        cautions=unique_cautions[:3],
        comparison_note=None,
    )


def build_workflow(
    req: RecommendationRequest, recommendations: list[Recommendation]
) -> list[WorkflowStep]:
    top = recommendations[:3]
    workflow: list[WorkflowStep] = []
    prior_tool: str | None = None

    for index, item in enumerate(top, start=1):
        workflow.append(build_tool_step(index, item.tool, req, prior_tool))
        prior_tool = item.tool.name

    if len(workflow) < 3:
        workflow.append(
            WorkflowStep(
                step=len(workflow) + 1,
                title="Review the result",
                detail="Capture what worked, what was unclear, and what should change before the next run.",
            )
        )

    return workflow[:3]


def build_heuristic_response(
    req: RecommendationRequest, catalog: list[Tool], engine_note: str | None = None
) -> RecommendationResponse:
    scored = [score_tool(tool, req) for tool in catalog]
    ranked = sorted(
        scored,
        key=lambda item: (item.score, len(item.reasons), -len(item.cautions)),
        reverse=True,
    )[:3]
    ranked_tools = [item.tool for item in ranked]
    ranked = [
        item.model_copy(
            update={
                "comparison_note": build_comparison_note(item.tool, req, ranked_tools)
            }
        )
        for item in ranked
    ]
    summary = (
        f"Navagator recommends a short stack for {req.goal}. "
        f"The list favors {req.workflow_style} work at a {req.budget} budget for a {req.skill_level} user."
    )
    workflow = build_workflow(req, ranked)
    return RecommendationResponse(
        summary=summary,
        recommendations=ranked,
        workflow=workflow,
        engine_mode="heuristic",
        model_name=None,
        engine_note=engine_note,
    )


def build_openai_prompt(req: RecommendationRequest, catalog: list[Tool]) -> str:
    catalog_payload = [
        {
            "id": tool.id,
            "name": tool.name,
            "category": tool.category,
            "price_band": tool.price_band,
            "skill_fit": tool.skill_fit,
            "workflow_styles": tool.workflow_styles,
            "use_cases": tool.use_cases,
            "description": tool.description,
            "strengths": tool.strengths,
            "best_for": tool.best_for,
        }
        for tool in catalog
    ]

    return f"""
You are Navagator's AI guidance engine. Pick exactly three tools from the provided catalog and create a practical first workflow.

Return JSON only. Do not wrap the JSON in markdown.

JSON schema:
{{
  "summary": "string",
  "recommendations": [
    {{
      "tool_id": "string from the catalog",
      "score": "integer 1-10",
      "reasons": ["up to 4 short strings"],
      "cautions": ["up to 3 short strings"],
      "comparison_note": "one short comparison sentence"
    }}
  ],
  "workflow": [
    {{
      "step": "integer starting at 1",
      "title": "short string",
      "detail": "one short paragraph"
    }}
  ]
}}

Ranking rules:
- Choose only tools that fit the user's budget, skill level, workflow style, install preference, timeline, and pain points.
- Prefer the smallest stack that can actually get the job done.
- Make the workflow actionable and tool-specific.
- Use only tool ids from the catalog below.
- Return exactly 3 recommendations and exactly 3 workflow steps.

User profile:
{json.dumps(req.model_dump(mode="json"), indent=2)}

Tool catalog:
{json.dumps(catalog_payload, indent=2)}
""".strip()


def extract_json_payload(raw_text: str) -> dict:
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError(
                "OpenAI engine output was not valid JSON and no JSON object could be extracted"
            ) from exc
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc2:
            raise ValueError(
                "OpenAI engine output contained malformed JSON payload in extracted block"
            ) from exc2


def build_openai_response(
    req: RecommendationRequest, catalog: list[Tool], app_settings: AppSettings
) -> RecommendationResponse:
    if not app_settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured.")
    if OpenAI is None:
        raise RuntimeError("The OpenAI package is not installed.")

    client = OpenAI(api_key=app_settings.openai_api_key)
    response = client.responses.create(
        model=app_settings.recommendation_model,
        reasoning={"effort": app_settings.recommendation_reasoning_effort},
        text={"verbosity": app_settings.recommendation_verbosity},
        input=build_openai_prompt(req, catalog),
    )

    raw_output = getattr(response, "output_text", None)
    if not raw_output:
        raise ValueError("OpenAI response is missing output text.")

    payload = extract_json_payload(raw_output)
    tool_map = {tool.id: tool for tool in catalog}

    recommendations_payload = payload.get("recommendations", [])
    workflow_payload = payload.get("workflow", [])

    if len(recommendations_payload) != 3 or len(workflow_payload) != 3:
        raise ValueError("Model output did not return exactly three recommendations and three workflow steps.")

    ranked: list[Recommendation] = []
    seen_tool_ids: set[str] = set()
    for item in recommendations_payload:
        tool_id = item.get("tool_id")
        if tool_id not in tool_map:
            raise ValueError(f"Unknown tool id returned by model: {tool_id}")
        if tool_id in seen_tool_ids:
            raise ValueError("Model returned duplicate tools.")

        seen_tool_ids.add(tool_id)
        ranked.append(
            Recommendation(
                tool=tool_map[tool_id],
                score=max(int(item.get("score", 0)), 0),
                reasons=[str(reason) for reason in item.get("reasons", [])][:4],
                cautions=[str(caution) for caution in item.get("cautions", [])][:3],
                comparison_note=item.get("comparison_note"),
            )
        )

    workflow = [
        WorkflowStep(
            step=int(item.get("step", index + 1)),
            title=str(item.get("title", f"Step {index + 1}")),
            detail=str(item.get("detail", "")),
        )
        for index, item in enumerate(workflow_payload)
    ]

    return RecommendationResponse(
        summary=str(payload.get("summary", "")).strip()
        or f"Navagator recommends a concise stack for {req.goal}.",
        recommendations=ranked,
        workflow=workflow,
        engine_mode="openai",
        model_name=app_settings.recommendation_model,
        engine_note=f"Recommendations were generated with {app_settings.recommendation_model}.",
    )


def recommend(req: RecommendationRequest) -> RecommendationResponse:
    settings = get_settings()
    catalog = load_catalog()
    app_settings = get_effective_app_settings(settings.local_profile_id)

    if app_settings.openai_api_key and OpenAI is not None:
        try:
            response = build_openai_response(req, catalog, app_settings)
            update_runtime_state(
                engine_mode="openai",
                model_name=response.model_name,
                engine_note=response.engine_note,
            )
            return response
        except Exception as exc:  # pragma: no cover - network/model failures are runtime-only
            note = f"OpenAI assist failed, so Navagator fell back to local heuristic mode: {exc}"
            response = build_heuristic_response(req, catalog, engine_note=note)
            update_runtime_state(
                engine_mode="heuristic",
                model_name=None,
                engine_note=note,
            )
            return response

    if app_settings.openai_api_key and OpenAI is None:
        note = "OpenAI API key is set, but the OpenAI Python package is missing. Using local heuristic mode."
    else:
        note = "OpenAI API key is not configured. Using local heuristic mode."

    response = build_heuristic_response(req, catalog, engine_note=note)
    update_runtime_state(
        engine_mode="heuristic",
        model_name=None,
        engine_note=note,
    )
    return response
