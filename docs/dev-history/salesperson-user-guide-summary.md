# Salesperson User Guide Documentation Update

## 1. Context

The repository already contained the current specification, bundled source artifacts, and substantial development documentation for the DVRS Planner, but it did not include a dedicated end-user guide written specifically for a salesperson audience.

## 2. Problem Statement

Sales-facing users needed a separate document that explains how to use the planner in practical quoting and qualification workflows, while preserving the product's documented limits around technical screening, regulatory uncertainty, and engineering escalation. The follow-up requirement also called for a shorter quick-reference version, better discoverability from the repository root, automated maintenance tests, and styled PDF outputs that feel closer to the bundled DVR-LX ordering guide.

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

Created `docs/salesperson-user-guide.md` as a dedicated sales-oriented user guide and added `docs/salesperson-quick-reference.md` as a shorter companion for quick field use. Updated `README.md` to link both the markdown and PDF versions directly, then added a release-handoff note so the front page now matches the release playbook for companion user documents. Added `tests/test_documentation.py` so the repository now checks that both guides exist, preserve the required escalation language, and are at least as recently updated as the tracked tool sources they are expected to follow. Added `tools/generate_sales_doc_pdfs.py` and generated `docs/salesperson-user-guide.pdf` plus `docs/salesperson-quick-reference.pdf` with branded cover pages, revision blocks, and layout choices intended to feel similar in spirit to the bundled DVR-LX ordering guide. Audited `requirements.txt` and `requirements-desktop.txt`, retaining the desktop file structure and adding `pypdf` to `requirements.txt` because the maintained documentation and test workflow now depends on it. Updated `docs/release-process.md` so release preparation now explicitly includes regenerating and shipping the salesperson-facing PDF handoff documents when they are part of the executable deliverable set.

## 5. Challenges & Iterations

The main challenge was balancing a non-engineering audience with the technical and regulatory nuance captured in the existing specification. The final guide keeps the language practical and sales-oriented while preserving the repository's existing "planning aid, not final approval" posture. Because the task was documentation-only, no build or packaging iteration was necessary.

## 6. Final Outcome

The repository now contains both a full salesperson-targeted DVRS Planner guide and a separate quick-reference version in markdown and PDF form, each aligned with the bundled references and current implementation documentation. The required escalation path is documented clearly and consistently with the product's conservative workflow assumptions, and the automated documentation tests now create explicit maintenance checkpoints for both the markdown sources and the generated PDFs.

## 7. Open Questions / Follow-ups

- Confirm whether the guide should later be linked directly from the application UI or desktop package.
- Confirm whether future releases should add screenshots once the UI is considered stable enough for long-lived end-user documentation.

## 8. Affected Files / Components

- `README.md`
- `docs/salesperson-user-guide.md`
- `docs/salesperson-quick-reference.md`
- `docs/salesperson-user-guide.pdf`
- `docs/salesperson-quick-reference.pdf`
- `docs/release-process.md`
- `tests/test_documentation.py`
- `tools/generate_sales_doc_pdfs.py`
- `docs/dev-history/salesperson-user-guide-summary.md`
- `docs/raw-threads/salesperson-user-guide.md`
- `docs/dev-log.md`
