# Salesperson User Guide Documentation Update

## 1. Context

The repository already contained the current specification, bundled source artifacts, and substantial development documentation for the DVRS Planner, but it did not include a dedicated end-user guide written specifically for a salesperson audience.

## 2. Problem Statement

Sales-facing users needed a separate document that explains how to use the planner in practical quoting and qualification workflows, while preserving the product's documented limits around technical screening, regulatory uncertainty, and engineering escalation. The follow-up requirement also called for a shorter quick-reference version, better discoverability from the repository root, and an automated test that reminds maintainers to review these guides when the tool changes.

## 3. Key Decisions

- Decision: Add a standalone salesperson-facing guide under `docs/` rather than folding this content into the README or design specification.
  - Rationale: The README is developer-oriented and the specification is product/engineering oriented. A separate guide is easier for a sales user to consume and maintain.
  - Alternatives considered: Expanding `README.md`; adding a short appendix to `dvrs-web-app-design.md`.

- Decision: Anchor the guide in the bundled source artifacts and current specification instead of inventing new workflow claims.
  - Rationale: The repo already defines the product boundaries, supported countries, supported bands, and conservative regulatory posture. The guide should reflect those sources faithfully.
  - Alternatives considered: Writing a generic sales quick-start without explicit source alignment.

- Decision: Make the escalation path explicit when no technically valid standard plan is found.
  - Rationale: The user requested stronger emphasis on validating customer input first and then engaging Motorola Solutions presales engineering, with possible involvement from DVRS product management and development engineering.
  - Alternatives considered: Leaving escalation guidance implicit in the general cautionary language.

- Decision: Skip any Windows rebuild or executable work.
  - Rationale: This change is documentation-only and does not affect shipped application behavior.
  - Alternatives considered: Re-running packaging steps despite no code or UI changes.

## 4. Implementation Summary

Created `docs/salesperson-user-guide.md` as a dedicated sales-oriented user guide and added `docs/salesperson-quick-reference.md` as a shorter companion for quick field use. Updated `README.md` to link both guides directly and clarify that they should be reviewed during documentation passes when tool changes affect workflow, inputs, outputs, statuses, or escalation guidance. Added `tests/test_documentation.py` so the repository now checks that both guides exist, preserve the required escalation language, and are at least as recently updated as the tracked tool sources they are expected to follow.

## 5. Challenges & Iterations

The main challenge was balancing a non-engineering audience with the technical and regulatory nuance captured in the existing specification. The final guide keeps the language practical and sales-oriented while preserving the repository's existing "planning aid, not final approval" posture. Because the task was documentation-only, no build or packaging iteration was necessary.

## 6. Final Outcome

The repository now contains both a full salesperson-targeted DVRS Planner guide and a separate quick-reference version, each aligned with the bundled references and current implementation documentation. The required escalation path is documented clearly and consistently with the product's conservative workflow assumptions, and the automated documentation test creates an explicit maintenance checkpoint for future tool changes.

## 7. Open Questions / Follow-ups

- Confirm whether the guide should later be linked directly from the application UI or desktop package.
- Confirm whether future releases should add screenshots once the UI is considered stable enough for long-lived end-user documentation.

## 8. Affected Files / Components

- `README.md`
- `docs/salesperson-user-guide.md`
- `docs/salesperson-quick-reference.md`
- `tests/test_documentation.py`
- `docs/dev-history/salesperson-user-guide-summary.md`
- `docs/raw-threads/salesperson-user-guide.md`
- `docs/dev-log.md`
