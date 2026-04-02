# Navagator Agent Rules

Navagator is an installable AI guidance product, not a generic landing page.

## Product focus

Build for these first-run outcomes:
- understand the user's goal
- recommend a short tool stack
- explain why those tools fit
- show the first workflow to execute

Do not expand into broad social or scraper automation work unless the current task explicitly asks for it.

## Architecture bias

Prefer a local-first architecture.

Current repo assumptions:
- `backend/` is the product logic layer
- `frontend/` is the installable app shell prototype
- packaging for desktop comes later

## UI rules

Keep the interface direct and decision-oriented.

Prefer:
- clear onboarding questions
- recommendation cards with reasons
- workflow steps the user can act on immediately

Avoid:
- generic marketing filler
- dark-pattern pricing copy
- vague AI hype language

## Implementation rules

When adding product logic:
- keep data structures explicit
- isolate matching logic from transport/UI code
- prefer deterministic placeholder behavior over fake intelligence hidden in UI copy

When adding data:
- use local JSON or SQLite-friendly shapes first
- do not require remote infrastructure unless the task truly depends on it

When adding AI integrations:
- keep prompts versioned or easy to inspect
- do not hardcode secret keys
- support bring-your-own-key assumptions unless product direction changes
