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
