# Codex Project Instructions: Documentation-First Development

## Purpose
This project requires Codex to treat documentation as a first-class deliverable.
All development work must produce structured, reusable documentation artifacts.

Codex should assume that chat threads represent important development history
and must be captured for future reference, auditing, and onboarding.

---

## Core Rule
Every meaningful task MUST result in documentation updates.

No task is complete until documentation has been created or updated.

---

## Spec-First Execution

`dvrs-web-app-design.md` is the primary project specification and the default source of truth for product intent, scope, workflow, and acceptance targets.

Codex must:
- review the current specification before making meaningful product changes
- work from the spec instead of ad hoc prompt drift whenever the spec covers the task
- identify conflicts between the spec, repository behavior, and user requests before changing implemented behavior
- update the specification when project decisions materially change scope, workflow, architecture, or acceptance expectations

If the specification is incomplete for a requested task, Codex should make the smallest reasonable assumption, state it, and prefer updating the spec so future conversations inherit the decision.

---

## Required Development Cycle

This project follows the course guide's core development loop:

1. define or confirm the task against the spec
2. implement the smallest useful increment
3. run the relevant application path or command when feasible
4. add or update tests that prove the change works
5. review results against the spec and acceptance criteria
6. create a commit checkpoint when the increment is working

Codex must not treat broken, unverified, or untested work as complete when verification is feasible.

---

## Incremental Delivery Rules

Codex must prefer small, dependency-aware increments over broad multi-feature changes.

When working on implementation:
- start with the simplest version that can be run and checked
- complete one scoped task at a time unless the user explicitly requests a larger bundled change
- keep the repository in a working state between increments whenever feasible
- avoid speculative architecture changes that are not required by the current task or spec

If a requested feature is large or ambiguous, Codex should break it into concrete increments and execute the earliest useful one first.

---

## Verification and Testing

Meaningful product changes must be verified, not just described.

Codex must:
- run relevant commands after meaningful code changes when feasible
- report whether the app, script, or test command was actually run
- add or update tests for behavior changes unless the task is explicitly exploratory or documentation-only
- check outcomes against the specification, not only against whether code compiles

Relevant verification can include:
- unit tests
- integration tests
- API checks
- local UI smoke tests
- packaging verification when the shipped desktop deliverable changes

If verification is blocked, Codex must say what could not be verified and why.

---

## Acceptance Criteria

Tasks should be grounded in explicit acceptance criteria whenever possible.

Codex must:
- use acceptance criteria already present in the specification when available
- infer practical acceptance criteria from the spec when they are implied but unstated
- surface missing or conflicting acceptance criteria before making high-risk behavior changes

---

## Commit Checkpoints

This project should maintain recoverable working checkpoints throughout development.

When an increment is implemented and verified, Codex should:
- prepare the repo for a clean commit checkpoint
- summarize what the checkpoint represents
- recommend or create a commit when the user asks for commit help or when the workflow clearly includes committing

Codex should preserve the guide's principle that each completed increment should leave the project in a state that can be returned to safely.

---

## Project Memory and Context Recovery

Documentation is not only a deliverable; it is also the continuity layer between conversations.

Codex should:
- keep the spec, summaries, and dev log current enough that a new conversation can resume work reliably
- capture important design decisions, acceptance decisions, and abandoned approaches
- prefer updating project documents over relying on long conversational memory

If a conversation becomes long, inconsistent, or degraded, Codex should rely on the repository documents as the durable source of project memory.

---

## Security and Secret Handling

Codex must not request, copy into docs, or echo secrets unless absolutely required by the task.

Codex should:
- avoid placing credentials, API keys, tokens, or passwords into project documentation or archived threads
- prefer redacted examples when configuration documentation is necessary
- warn clearly if a task appears to require handling sensitive values

---

## Windows Release Workflow

This repository ships its Windows desktop executable through GitHub Releases.

When meaningful application changes are made, Codex must treat the Windows package as part of the deliverable.

Meaningful application changes include:
- changes under `dvrs_tool/`
- UI changes under `dvrs_tool/static/`
- desktop-launcher changes such as `run_desktop.py`, `dvrs_tool/desktop.py`, `dvrs_desktop.spec`, `requirements-desktop.txt`, or `build_windows.ps1`

When those files change, Codex must:
- rebuild the Windows package before closing the task
- verify the rebuilt executable launches successfully when feasible
- prepare or update the GitHub Release asset workflow for the same change set
- document that the package was rebuilt and which release version it represents

If a task is documentation-only or otherwise does not change the shipped application behavior, Codex may skip the rebuild, but should say why.

---

## Documentation Outputs

For any task or thread, Codex must create or update the following:

### 1. Thread Summary (Required)
Path:
docs/dev-history/<thread-slug>-summary.md

Structure:

# <Descriptive Title>

## 1. Context
## 2. Problem Statement
## 3. Key Decisions
- Decision:
- Rationale:
- Alternatives considered:

## 4. Implementation Summary
## 5. Challenges & Iterations
## 6. Final Outcome
## 7. Open Questions / Follow-ups
## 8. Affected Files / Components

---

### 2. Raw Thread Archive (Required for existing threads)
Path:
docs/raw-threads/<thread-slug>.md

Requirements:
- Convert full conversation into readable markdown
- Preserve all meaningful technical details
- Remove only obvious repetition
- Clearly label user vs assistant messages
- Add headings for readability

---

### 3. Development Log (Append Only)
Path:
docs/dev-log.md

Requirements:
- Append a 3–5 sentence summary of what was accomplished
- Include:
  - What changed
  - Why it matters
  - Any follow-up work

---

## Thread Slug Rules

Generate a filesystem-safe slug:
- lowercase
- kebab-case
- descriptive but concise

Examples:
- auth-token-refresh
- websocket-reconnect-fix
- ui-loading-state-refactor

---

## Decision Documentation Standards

When documenting decisions:
- Be explicit about WHY the decision was made
- Include alternatives when they were discussed
- Clearly identify final vs abandoned approaches

If conflicting approaches exist:
- Label them clearly:
  - "Initial approach (abandoned):"
  - "Final approach (implemented):"

---

## Quality Standards

Codex must:
- NOT invent information
- Prioritize clarity over verbosity
- Avoid vague summaries
- Ensure documentation is usable by a new engineer with no prior context

---

## When to Trigger Documentation

Documentation must be created when:
- A feature is implemented
- A bug is fixed
- A design decision is made
- Multiple approaches are explored
- A thread contains meaningful technical discussion

---

## Handling Existing Threads

When working in an existing thread:
- Treat the entire conversation as source material
- Extract and summarize all relevant technical content
- Archive the full thread
- Do not skip older context unless clearly irrelevant

---

## File Organization

docs/
  dev-history/
  raw-threads/
  dev-log.md

Codex should create these directories if they do not exist.

---

## Tone and Style

- Professional engineering documentation
- Clear, structured, and concise
- Avoid conversational language
- Optimize for future maintainability

---

## Definition of Done

A task is NOT complete until:
- Summary file is created
- Raw thread is archived (if applicable)
- dev-log.md is updated

If any of these are missing, the task is incomplete.

---
