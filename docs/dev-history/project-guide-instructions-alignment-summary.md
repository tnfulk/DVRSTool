# Project Guide Instructions Alignment Summary

## 1. Context
The project guide in the repository was reviewed against the current instruction documents to check whether the repo-level guidance fully reflected the course expectations for specification structure and development workflow.

## 2. Problem Statement
The existing documentation already described the DVRS product scope well, but it did not fully capture the course guide's recommended project-spec structure or its required iterative workflow of spec, run, test, and commit. The goal of this thread was to close those gaps without changing shipped application behavior.

## 3. Key Decisions
- Decision:
  Treat the project guide as the reference for missing documentation expectations and update both `dvrs-web-app-design.md` and `codex.md` to align with it.
- Rationale:
  The guide is the course-facing source for how the project should be structured and how the coding agent should work inside the repository.
- Alternatives considered:
  Leave the current docs as-is and rely on conversational reminders instead of repository instructions.

- Decision:
  Expand `dvrs-web-app-design.md` with explicit course-project sections for problem framing, workflow, plan, MVP, task sequencing, and acceptance-oriented verification.
- Rationale:
  The existing specification was strong on current-state behavior, but the guide also expects a problem statement, plan, and task structure with acceptance criteria.
- Alternatives considered:
  Keep the spec as a current-state product document only and place all workflow guidance in `codex.md`.

- Decision:
  Expand `codex.md` with spec-first execution rules and the course guide's iterative run, test, and commit cycle.
- Rationale:
  The previous instructions emphasized documentation but underrepresented the guide's core engineering loop.
- Alternatives considered:
  Keep `codex.md` documentation-first and rely on default Codex behavior for verification and commits.

## 4. Implementation Summary
The specification file gained a new problem statement, user workflow, acceptance-oriented verification targets, architecture plan, MVP definition, and ordered task sequence with acceptance criteria. The instruction file gained sections covering spec-first execution, required development cycle, incremental delivery, verification and testing, acceptance criteria, commit checkpoints, context recovery, and secret handling.

## 5. Challenges & Iterations
The main challenge was preserving the repository's current implementation-honest documentation style while also adding the more course-oriented project structure expected by the guide. The final edits kept the current-state sections intact and layered the missing project-spec and workflow sections on top.

## 6. Final Outcome
The repository documentation now aligns more closely with the course guide's expectations. The project spec better captures problem framing, planned execution, and acceptance criteria, while the Codex instructions now explicitly require spec-driven, incremental, verified development.

## 7. Open Questions / Follow-ups
- Decide later whether `dvrs-web-app-design.md` should be further split into a concise course-project spec and a separate implementation-status document.
- Revisit whether future documentation checks should enforce the new task and acceptance-criteria sections automatically.

## 8. Affected Files / Components
- `dvrs-web-app-design.md`
- `codex.md`
- `docs/dev-history/project-guide-instructions-alignment-summary.md`
- `docs/raw-threads/project-guide-instructions-alignment.md`
- `docs/dev-log.md`
