# StudyMate — Presentation (8 minutes)

## Slide 1 — Problem and user (1 min)
Students need a lightweight way to track study tasks. StudyMate supports task capture, listing and search.

## Slide 2 — Live demo (2 min)
1. Run `python agent.py`
2. `add task: Review OS notes by Thursday`
3. `list tasks`
4. `search: OS`
5. `delete T001` (show that it asks for approval)
6. `confirm delete T001` (only after confirming the ID)

## Slide 3 — Architecture and workflow (2 min)
User → CLI → command parser → guarded tool → local JSON store → result/log.
MCP client → stdio MCP server → same guarded tools.
Context policy is stored in `AGENTS.md`.

## Slide 4 — Evaluation and error analysis (2 min)
Run `python evals.py`. Present the generated `eval_results.json`; compare baseline and guarded behavior. Explain any failed case honestly. These are deterministic harness checks, not evidence of live LLM accuracy.

## Slide 5 — Security and limitations (1 min)
- Injection-like task content is blocked by a simple pattern guard.
- Delete requires exact human confirmation.
- API keys are excluded from Git.
- Limitations: pattern-based detection is incomplete; MCP client integration and live-model mode must be verified in the actual environment.
