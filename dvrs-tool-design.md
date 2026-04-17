# DVRS In-Band Planning Tool

This draft was refreshed against the repository on `2026-04-16`.

Primary spec note:

- `dvrs-tool-design.md` is the primary constitution and specification document for the repository.
- `dvrs-web-app-design.md` remains the deeper technical reference and should be maintained as a core project document.
- Development agents should continue to read and preserve `dvrs-web-app-design.md` so the more detailed rules, implementation guidance, and acceptance nuances captured there are not lost when future work updates the primary spec.

## Problem Statement

Motorola Solutions sales and planning stakeholders need to assess standard in-band DVRS configuration options without doing a manual engineering review for every quote.

Today that work depends on reading ordering guides, checking fixed plan ranges, reasoning through spacing and pairing constraints, and manually deciding whether a proposed configuration appears technically compatible or likely to require coordination. That process is slow, hard to audit, and easy to misapply when the user is not a radio-system specialist.

The DVRS tool's job is to make that screening process faster, more repeatable, and easier to explain. It is not meant to replace regulatory review, licensing approval, or Motorola Solutions engineering judgment. It is meant to help a user enter the customer system frequencies already in use, evaluate the supported standard 700 MHz and 800 MHz DVRS plan families, explain the technical outcome, and produce an ordering-summary-style result that can support quote preparation.

## Domain Research

The underlying planning logic is based on the Motorola Solutions DVRS-LX ordering guide, the in-band operation reference material, the supplemental ordering form, and the repository's implemented rule interpretations.

Repository evidence reviewed for this draft includes:

- `dvrs-web-app-design.md`
- `README.md`
- `docs/dev-log.md`
- `docs/dev-history/*.md`
- `dvrs_tool/engine.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/pdf_export.py`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/desktop.py`
- `tests/test_engine.py`
- `tests/test_desktop.py`
- `tests/test_documentation.py`

The key domain conclusion carried into this draft is that the project's value is not generic frequency lookup. Its value is repeatable standard-plan screening with rule-based explanations, conservative regulatory posture, and outputs that are useful in a quoting workflow.

## Constitution

These values guide design decisions when tradeoffs arise.

- Accuracy before convenience. The tool must not imply that technical fit automatically means licensing approval or deployment approval.
- Explainability before black-box output. A user should be able to see why a plan survived, failed, or requires coordination.
- Regulatory humility before false certainty. When assignability is uncertain, the safer result is `COORDINATION_REQUIRED`.
- Shared-engine truth before channel-specific reinvention. Browser, CLI, PDF export, and desktop workflows should all depend on the same backend rules.
- Repository honesty before aspirational design. The specification should describe the tool that actually exists now, not an imagined React rewrite or a native desktop product that has not been built.
- Workflow usefulness before unnecessary complexity. Outputs should help sales and planning users move through quote preparation, not just satisfy internal engineering curiosity.

## Specification

### What the tool does

The tool lets a user evaluate supported standard in-band DVRS plan families against customer system frequencies for United States and Canada workflows.

It currently supports:

- standard 700 MHz plans: `700-A`, `700-B`, `700-C`
- standard 800 MHz plans: `800-A1`, `800-A2`, `800-B`, `800-C`
- explicit system-frequency modes: `700 only`, `800 only`, `700 and 800`
- optional exact `DVRS TX` and `DVRS RX` validation
- plan-by-plan technical and regulatory results
- ordering-summary-style output with generated PDF export

### Core workflow

1. User selects the country.
2. User selects the system-frequency configuration: `700 only`, `800 only`, or `700 and 800`.
3. User enters the customer system frequencies already in use using the current `Mobile TX Frequency` terminology.
4. User optionally enters exact `DVRS TX` and `DVRS RX` values when validating a known proposal.
5. Tool evaluates the supported parent plans using the shared engine.
6. Tool shows technical status, regulatory status, explanatory notes, and any surviving recommended DVRS frequencies or compliant sub-range.
7. User reviews the quote-draft summary and optionally exports the generated PDF.

### What the user sees

The current UI and outputs center around three main result areas:

- `System`
  The entered system frequencies, derived pairing context, and mixed-band side-specific summaries where applicable.
- `Plans`
  One card per parent plan with technical status, regulatory status, rule violations, warnings, notes, and proposed DVRS frequencies for technically valid outcomes.
- `Quote Draft`
  A condensed ordering-summary-style output with system values, recommended DVRS values, optional metadata, and PDF export.

The current product also exposes the same core behavior through:

- a FastAPI-served browser UI
- a CLI entrypoint via `python -m dvrs_tool`
- a Windows desktop wrapper that embeds the same web UI

### Inputs

Required inputs in the current tool:

- `country`
- `system_band_hint`
- single-band system frequencies:
  - `mobile_tx_low_mhz`
  - `mobile_tx_high_mhz`
- mixed-band system frequencies:
  - `mobile_tx_700_low_mhz`
  - `mobile_tx_700_high_mhz`
  - `mobile_tx_800_low_mhz`
  - `mobile_tx_800_high_mhz`

Optional technical validation inputs:

- `actual_dvrs_tx_mhz`
- `actual_dvrs_rx_mhz`

Optional ordering metadata:

- `agency_name`
- `quote_date`
- `mobile_radio_type`
- `control_head_type`
- `msu_antenna_type`
- `agency_notes`

Compatibility inputs still retained in the API model:

- `mobile_rx_low_mhz`
- `mobile_rx_high_mhz`

Current implementation note:

- The API still accepts manual mobile RX override values.
- The browser UI does not expose those fields in the current 700/800 workflow.
- Deterministic pairing is the intended path for the current scope.

### Evaluation behavior

The current engine behavior includes:

- parent-plan presentation with internal submodel selection where needed
- deterministic system pairing
- mixed-band evaluation using separate 700-side and 800-side system ranges
- exact DVRS frequency validation that can narrow or invalidate plans
- technical and regulatory status reported separately

Deterministic pairing rules:

- 700-side system pair = entered system RX minus 30 MHz
- 800-side system pair = entered system RX plus 45 MHz

Important terminology:

- Standard plan names such as `700-A` or `800-B` refer to DVRS plan families.
- They do not always match the customer's system band directly.
- Because of that, some cross-band-compatible parent plans may evaluate successfully against a different system-band input model when the encoded plan data allows it.

### Output model

Technical status:

- `TECHNICALLY_VALID`
- `TECHNICALLY_INVALID`

Regulatory status:

- `LIKELY_LICENSABLE`
- `COORDINATION_REQUIRED`
- `LIKELY_NOT_LICENSABLE`
- `NOT_EVALUATED`

Returned plan results may include:

- recommended DVRS TX/RX frequencies
- a surviving compliant DVRS sub-range
- technical rule violations
- warnings and notes
- regulatory reasons and confidence

### Why this tool matters

The important product distinction is that this tool turns a manual plan-screening exercise into a repeatable decision-support workflow.

Without the tool, a salesperson has to read the guide, infer which standard plans might fit, reason through spacing and fixed-range constraints, and manually prepare a summary for the quote process. With the tool, they can enter the customer system values, see the technically surviving options, and carry forward a more defensible recommendation while still escalating appropriately when the result is uncertain or invalid.

## Plan

### Architecture

- Browser UI
  Static HTML, CSS, and JavaScript served by FastAPI
- API layer
  `dvrs_tool/api.py` and `dvrs_tool/models.py`
- Planning engine
  `dvrs_tool/engine.py`
- Plan and regulatory data
  `dvrs_tool/plan_data.py`
- PDF export
  `dvrs_tool/pdf_export.py`
- Desktop delivery
  `dvrs_tool/desktop.py`, `run_desktop.py`, `dvrs_desktop.spec`, `build_windows.ps1`

### Technology choices

- Python for the shared planning engine and API
- FastAPI for the local service layer
- static HTML, CSS, and JavaScript for the frontend
- PySide6 WebEngine for the packaged desktop launcher
- PyInstaller for Windows packaging

The architecture direction should remain simple: keep the technical rules in the Python backend, keep the frontend thin, and treat browser, CLI, PDF, and desktop as delivery paths for one shared planning tool.

### API and delivery design

The tool is not only a web page. The current design is a single rules engine with several access modes:

- browser workflow for interactive use
- CLI workflow for direct invocation and automation-friendly output
- PDF export for quote handoff
- desktop packaging for local installed use without requiring the user to launch a browser manually

That means future work should prefer shared request and response contracts rather than duplicating logic in each surface.

## Status

The core historical development sequence is complete. The current repository includes the shared planning engine, FastAPI API, browser UI, CLI, generated PDF export, Windows desktop wrapper, packaging workflow, and maintained documentation/test support.

Completed task sequence:

- Task 1: Planning engine and API foundation - done (core Python engine, FastAPI contract, validation model, and initial tests)
- Task 2: First browser planner workflow - done (static web UI, system summary, plan results, and ordering-summary export path)
- Task 3: CLI and repository workflow setup - done (`python -m dvrs_tool`, repo cleanup, and testable command-line usage)
- Task 4: Plan-rule refinement and standards alignment - done (plan table corrections, spacing-first evaluation, fixed-range interpretation, and guarded plan data maintenance)
- Task 5: 700/800 workflow expansion - done (interoperability support, mixed-band handling, parent-plan submodels, and explicit system-frequency input model)
- Task 6: Exact DVRS and validation refinement - done (single-frequency DVRS TX/RX inputs, clearer invalid-input handling, and per-plan exact-fit evaluation)
- Task 7: UI and quote-workflow refinement - done (cleaner labels, shared-axis visualization, ordering-focused form layout, build indicator, and branded presentation updates)
- Task 8: Desktop packaging and release workflow - done (PySide6 desktop wrapper, packaged-runtime safeguards, build script hardening, and GitHub release process)
- Task 9: Sales and maintenance documentation - done (sales guides, PDF handoff docs, release playbooks, dev-history, and spec/instruction alignment)

Reserved or partial items still present in the repository:

- `use_latest_ordering_ruleset` exists as a reserved toggle but does not switch among multiple live rulesets
- manual mobile RX override still exists in the API model but is not exposed in the browser UI
- regulatory classification is intentionally conservative and coarser than full licensing review

## Tasks

Ordered by dependency. Each task should produce a working, testable increment.

### Task 1: Planning engine and API foundation (Completed)

Acceptance criteria:

- Python engine evaluates standard-plan compatibility from maintained plan data
- FastAPI exposes a stable evaluation contract
- invalid requests return useful validation feedback
- baseline tests cover engine and API behavior

### Task 2: First browser planner workflow (Completed)

Acceptance criteria:

- browser UI loads from the local FastAPI service
- users can enter supported planning inputs and run evaluations
- results show system summary, plan results, and ordering-summary information
- generated PDF export is available from the workflow

### Task 3: CLI and repository workflow setup (Completed)

Acceptance criteria:

- tool can run directly from `python -m dvrs_tool`
- CLI output reflects the same core result model as the API
- repository is independently maintainable with predictable git workflow
- tests remain runnable from the repo root

### Task 4: Plan-rule refinement and standards alignment (Completed)

Acceptance criteria:

- encoded plan data reflects the approved interpretation of the bundled references
- spacing, window, and fixed-range behavior are evaluated consistently
- guarded plan-table updates require explicit acknowledgment
- regression tests cover key plan-selection and range-survival behavior

### Task 5: 700/800 workflow expansion (Completed)

Acceptance criteria:

- supported workflows include `700 only`, `800 only`, and `700 and 800`
- mixed-band evaluation uses the correct side-specific system ranges
- parent plans can evaluate through internal submodels where required
- the current spec and UI terminology reflect system-frequency-driven input

### Task 6: Exact DVRS and validation refinement (Completed)

Acceptance criteria:

- exact `DVRS TX` and `DVRS RX` values can narrow or invalidate plan outcomes
- invalid optional inputs produce corrective, field-usable feedback
- exact-frequency checks are part of per-plan evaluation rather than a disconnected prefilter
- tests cover the accepted exact-frequency and validation paths

### Task 7: UI and quote-workflow refinement (Completed)

Acceptance criteria:

- the planner UI uses current terminology and reduced-noise layout
- technically valid plans show useful visual and textual explanation
- the quote draft preserves the core recommendation clearly
- branded presentation and build/version visibility remain in place

### Task 8: Desktop packaging and release workflow (Completed)

Acceptance criteria:

- the desktop launcher starts the shared planning workflow without requiring a browser launch
- packaged runtime failures are guarded and testable
- build scripts produce versioned release artifacts reliably
- release documentation captures the required tag, asset, and verification steps

### Task 9: Sales and maintenance documentation (Completed)

Acceptance criteria:

- salesperson-facing guides explain supported workflow and escalation expectations
- PDF handoff docs can be regenerated and validated
- development history and durable project docs are maintained
- the primary and companion specifications stay aligned with repo behavior

### Task 10: Stabilize and protect the current 700/800 rules

Acceptance criteria:

- standard-plan definitions remain intentional and reviewable
- guarded plan-table changes stay explicit
- regression tests continue to cover parent-plan candidate sets and surviving-sub-range behavior

### Task 11: Preserve explanation quality across API, UI, CLI, and PDF output

Acceptance criteria:

- invalid results include rule-based failure reasons
- technically valid results retain warnings and regulatory notes
- all delivery surfaces continue to communicate the same core recommendation

### Task 12: Extend regulatory and ruleset sophistication only when explicitly scoped

Acceptance criteria:

- any new ruleset support has explicit boundaries and a documented source basis
- regulatory refinements improve clarity without overstating approval certainty
- reserved toggles do not imply capabilities that the engine does not actually implement

### Task 13: Add future scope only as explicitly bounded follow-on work

Acceptance criteria:

- any new band support or persistence feature has explicit scope boundaries
- plan data, engine logic, UI behavior, desktop behavior, and tests are updated together
- this design document and the deeper technical companion spec are updated alongside meaningful scope changes

## Out of Scope

These are things the current project is explicitly not building now:

- VHF planning logic
- UHF planning logic
- direct regulator database lookup
- automatic licensing or coordination approval
- saved scenarios or user accounts
- admin editing of plan tables from the UI
- a separate native desktop frontend
- replacing the shared Python engine with duplicated frontend rule logic
