# DVRS In-Band Planning App Constitution and Current Specification

Last reviewed against the repository implementation: `2026-04-12`

This specification was refreshed after reviewing the repository documentation, engine, API, static web UI, desktop wrapper, and tests. It is intended to describe the current project state plus germane future roadmap items, not an aspirational architecture that the repo does not yet implement.

## 0. Problem Statement

This project addresses a planning problem faced by Motorola Solutions sales and planning stakeholders who need to recommend a standard in-band DVRS configuration without doing a manual engineering review for every quote.

Today that workflow depends on reading ordering guides, checking fixed plan ranges, reasoning about pairing rules, and manually deciding whether a proposed configuration is technically compatible or likely to require coordination. That process is slow, difficult to audit, and easy to misinterpret when the user is not a radio-system specialist.

The first-version product goal is a trustworthy planning aid that:

- accepts the system frequencies the customer already has
- evaluates the supported standard 700 MHz and 800 MHz DVRS plans against those frequencies
- explains why each plan is technically valid, invalid, or coordination-dependent
- produces an ordering-summary style output that is usable in the quote workflow

The project matters because it reduces avoidable quoting mistakes, makes plan-screening logic repeatable, and gives non-engineering users a more consistent path to a technically informed recommendation while still preserving the need for formal regulatory and vendor review where required.

## 1. Constitution

### 1.1 Purpose
Provide a planning aid for Motorola Solutions DVR-LX standard in-band DVRS configurations that helps a salesperson without detailed engineering knowledge:

- enter the system frequencies the customer already has
- evaluate standard 700 MHz and 800 MHz DVRS plans against those system frequencies
- see which plans are technically valid, technically invalid, or technically plausible but coordination-dependent
- produce an ordering-summary style output suitable for entry into Motorola Solutions Configure-Price-Quote tool

### 1.2 Product Principles

1. Accuracy before convenience.
   The tool must never imply that technical fit equals licensing approval.

2. Explainability over black-box output.
   Every invalid result must include rule-based failure reasons, and valid results should still preserve regulatory notes and warnings.

3. Regulatory humility.
   The product is a planning aid only. It is not a replacement for FCC, ISED, APCO/IMS A, border-area review, or Motorola Solutions review.

4. Vendor-faithful logic.
   Standard-plan behavior should follow the Motorola Solutions ordering guide and in-band operation references before any country-level overlay is applied.

5. Data-driven plan rules.
   Standard plans must be encoded as plan data, not hidden in UI-only logic.

6. Fixed ranges define the recommendation boundary.
   When the ordering guide publishes a fixed DVRS TX/RX range for a standard plan, that fixed range is the allowed recommendation boundary for that plan.

7. Return the surviving compliant sub-range.
   A plan should not fail merely because the full nominal DVRS range overlaps or crowds the system frequencies. The engine must search for the surviving paired DVRS sub-range that still satisfies the spacing, window, and pairing rules, and fail only when no compliant sub-range remains.

8. Conservative regulatory classification.
   When assignability is uncertain, the correct result is `COORDINATION_REQUIRED`, not a positive licensing claim.

9. Ordering-workflow alignment.
   Results must be usable by field, sales, and procurement stakeholders, not only by developers.

10. Current implementation honesty.
    This document must reflect the shipped Python/FastAPI plus static UI architecture until the codebase actually changes.

### 1.3 Current In-Scope Behavior

- Motorola Solutions DVR-LX standard 700 MHz and 800 MHz in-band configurations
- country selection for `United States` and `Canada`
- explicit system-frequency configuration selection:
  - `700 only`
  - `800 only`
  - `700 and 800`
- input of system frequencies using the current UI terminology `Mobile TX Frequency`
- inferred single-band detection when no mixed-band mode is selected
- mixed 700 MHz and 800 MHz evaluation using separate 700-side and 800-side ranges
- deterministic system pairing:
  - 700 system pair = entered system RX minus 30 MHz
  - 800 system pair = entered system RX plus 45 MHz
- parent-plan evaluation with internal submodel selection where required
- plan-by-plan technical status, regulatory status, rule violations, warnings, and notes
- optional exact `DVRS TX` and `DVRS RX` entries that can further constrain plan validity
- ordering-summary output and backend-generated PDF export
- browser-based delivery and a Windows desktop wrapper around the same web UI

### 1.4 Out of Scope

- active VHF technical plan support - targeted for future expansion
- active UHF technical plan support - targeted for future expansion
- direct FCC ULS or ISED license lookup
- automatic coordination or final licensing approval
- custom Motorola Solutions filter-plan synthesis
- saved scenarios or persistent project storage
- admin editing of rule tables from the UI
- a native desktop UI distinct from the current embedded web app

### 1.5 Output Model
The current product exposes technical and regulatory status separately rather than collapsing everything into one combined label.

Technical status:

- `TECHNICALLY_VALID`
- `TECHNICALLY_INVALID`

Regulatory status:

- `LIKELY_LICENSABLE`
- `COORDINATION_REQUIRED`
- `LIKELY_NOT_LICENSABLE`
- `NOT_EVALUATED`

## 2. Current Specification

### 2.1 Source Constraints
The current app encodes these working assumptions from the bundled references and later approved project decisions:

- Only standard plans are treated as standard offerings; anything else requires engineering review.
- In-band filters are mechanically tuned and are not treated as field-retunable.
- The ordering guide is the source of truth for fixed standard-plan ranges.
- Later approved scope decisions refine how those ranges are evaluated, especially the requirement to return the remaining compliant DVRS slice instead of failing early.
- The supplemental ordering form is the model for the ordering summary and PDF export, but the PDF export is a generated approximation rather than a filled vendor template.

### 2.2 User Inputs

Required inputs in the current UI/API:

- `country`
- `system_band_hint`
- single-band mode:
  - `mobile_tx_low_mhz`
  - `mobile_tx_high_mhz`
- mixed mode:
  - `mobile_tx_700_low_mhz`
  - `mobile_tx_700_high_mhz`
  - `mobile_tx_800_low_mhz`
  - `mobile_tx_800_high_mhz`

Optional planning inputs:

- `actual_dvrs_tx_mhz`
- `actual_dvrs_rx_mhz`

Optional ordering metadata:

- `agency_name`
- `quote_date`
- `mobile_radio_type`
- `control_head_type`
- `msu_antenna_type`
- `agency_notes`

Compatibility input retained in the API:

- `mobile_rx_low_mhz`
- `mobile_rx_high_mhz`

Current status of that compatibility input:

- The API model still accepts manual mobile RX override values.
- The current browser UI does not expose those fields.
- For the present 700/800 workflow, deterministic pairing is the default and expected path.

Current status of `use_latest_ordering_ruleset`:

- The checkbox exists in the UI and request model.
- The repository currently encodes only one active ruleset path in the engine.
- The flag should therefore be treated as a reserved forward-compatibility toggle, not as evidence of multiple live rule engines.

### 2.3 Input Semantics and Terminology
The planner asks for the frequencies already present in the customer system, not the desired DVRS plan family.

Important terminology rule:

- Standard plan names such as `700-A`, `700-B`, `700-C`, `800-A1`, `800-A2`, `800-B`, and `800-C` refer to DVRS plan families.
- They do not necessarily match the system band entered by the user.
- Because of that, a `700` parent plan may evaluate successfully against an `800 only` system model, and an `800` parent plan may evaluate successfully against a `700 only` system model, when the encoded plan data allows it.

### 2.4 Supported Band Detection and Range Windows

- 700-side system input is supported when the entered system-frequency range fits `799.0-805.0 MHz`
- 800-side system input is supported when the entered system-frequency range fits `806.0-824.0 MHz`
- any other single-band range is rejected as unsupported or ambiguous
- mixed mode requires separate 700-side and 800-side inputs and evaluates each candidate plan against the band-specific system range relevant to that plan

### 2.5 System Pairing and Summary Rules
The current engine and UI treat the entered system frequencies as system RX values and derive paired system TX values from them.

Deterministic defaults:

- `700 only`: system TX = entered range minus 30 MHz
- `800 only`: system TX = entered range plus 45 MHz
- `700 and 800`: both deterministic pairings are retained in the mixed-band summary, and each candidate plan uses the matching side of the system during evaluation

### 2.6 Technical Plan Coverage
Current encoded standard plans:

- 700 MHz: `700-A`, `700-B`, `700-C`
- 800 MHz: `800-A1`, `800-A2`, `800-B`, `800-C`

The plan dataset is currently implemented in `dvrs_tool/plan_data.py` and protected by `dvrs_tool/plan_table_guard.py` so edits require explicit confirmation.

### 2.7 Parent-Plan and Submodel Evaluation
The UI presents parent plans only. The engine may internally evaluate one or more compatible interpretations for a parent plan and select the best surviving result. The alignment of expected candidate sets was defined from the DVRS-LX Ordering Guide, and confirmed by interview with the product management team.

Current expected candidate sets:

- `700 only`: `700-A`, `700-B`, `700-C`, `800-A1`, `800-A2`, `800-B`
- `800 only`: `700-A`, `700-B`, `700-C`, `800-A1`, `800-A2`, `800-B`, `800-C`
- `700 and 800`: `700-B`, `700-C`, `800-A1`, `800-A2`, `800-B`

Important current behavior:

- the winning parent-plan result preserves the system ranges used by the winning submodel
- mixed-band plan evaluation uses the candidate plan's own band-specific system ranges
- actual supplied DVRS frequencies can narrow the returned candidate set in some workflows

### 2.8 Technical Evaluation Rules
For each candidate plan, the current engine is expected to evaluate at least the following concerns:

1. Whether the selected system model is supported by the plan or plan variant.
2. Whether the active mobile TX and mobile RX windows are satisfied.
3. Whether the DVRS proposal can remain within the plan's fixed range, if one exists.
4. Whether a surviving contiguous DVRS RX range exists after applying spacing and window rules.
5. Whether the paired DVRS TX range derived from that solution stays valid for the plan.
6. Whether the required duplex or simplex pairing relationship is preserved.
7. Whether exact user-supplied DVRS TX/RX values fit the plan rules when provided.

Required recommendation behavior:

- For fixed-range plans, search inside the published fixed range and return the feasible compliant sub-range.
- For allowed-window plans, search inside the plan window and return the surviving compliant sub-range.
- Do not fail a plan simply because the full nominal range does not fit; fail only when no compliant paired sub-range remains.

Current actual-DVRS behavior:

- `actual_dvrs_tx_mhz` and `actual_dvrs_rx_mhz` are treated as exact frequencies, not as mandatory low/high ranges.
- Those exact values can make some plans valid and others invalid.
- The engine may add advisory notes when the exact point is acceptable but a widened plus/minus 0.5 MHz comfort window would reduce spacing margin.

### 2.9 Regulatory Evaluation Rules
The regulatory classifier is a second-stage overlay on top of technical evaluation.

Current result fields:

- `regulatory_status`
- `confidence`
- `regulatory_reasons`

Current conservative rules encoded in `dvrs_tool/plan_data.py`:

- United States:
  - 700 MHz DVRS proposals inside `769-775 / 799-805` are treated as likely licensable
  - supported 700/800 interoperability layouts are usually classified as coordination required
  - other 800 MHz outcomes remain coordination required unless a stronger negative condition is later encoded
- Canada:
  - `768-776 / 798-806` is treated as likely licensable for 700 MHz public-safety-capable use
  - `821-824 / 866-869` is treated as likely licensable for the Canadian 800 MHz public-safety block
  - broader 800 MHz outcomes default to coordination required

### 2.10 Result Presentation
The shipped web UI presents three main panels:

1. `System`
   - detected band
   - pairing source
   - entered system frequencies
   - derived system TX values
   - mixed-band 700-side and 800-side summaries where applicable

2. `Plans`
   - one card per parent plan returned by the engine
   - technical and regulatory badges
   - proposed DVRS TX/RX for technically valid plans
   - rule and warning text
   - shared-axis frequency visualization for technically valid plans

3. `Quote Draft`
   - system TX/RX
   - proposed DVRS TX/RX
   - actual DVRS TX/RX, if provided
   - optional ordering metadata
   - summary notes
   - PDF export action

### 2.11 User Workflow
The intended primary workflow for the current release is:

1. Select the country and the applicable system-frequency mode.
2. Enter the customer system frequencies already in use.
3. Optionally enter exact DVRS TX/RX values when validating a known proposal.
4. Review the returned parent-plan results, including technical status, regulatory status, and explanatory notes.
5. Compare the surviving valid or coordination-dependent options in the quote workflow.
6. Export or reference the ordering-summary style output for downstream procurement activity.

### 2.12 Delivery Architecture
The current repository started as a draft using React/TypeScript, but has since been modified. It is not a React/TypeScript app and should not be documented as one.

Current shipped architecture:

- core engine: Python in `dvrs_tool/engine.py`
- plan and regulatory data: Python in `dvrs_tool/plan_data.py`
- API layer: FastAPI in `dvrs_tool/api.py`
- web UI: static HTML/CSS/JavaScript in `dvrs_tool/static/`
- CLI: `python -m dvrs_tool`
- desktop wrapper: PySide6 WebEngine launcher in `dvrs_tool/desktop.py` with `run_desktop.py`
- Windows packaging path: PyInstaller via `dvrs_desktop.spec` and `build_windows.ps1`

### 2.13 Testing and Quality Expectations

- plan-table edits must be intentional and accompanied by a guard-file update
- engine, API, CLI, and PDF-export behavior should remain covered by unit tests
- regressions around mixed-band evaluation, plan sub-ranges, exact DVRS frequencies, and validation messages should remain tested
- each meaningful increment should leave the app runnable and the relevant checks passing
- tests should verify both correct outcomes and explanation quality for invalid or coordination-dependent results

### 2.14 Acceptance-Oriented Verification Targets
The following checks capture the intended meaning of done for the current scope:

- given supported `700 only` input, the engine returns the expected candidate parent plans and preserves deterministic system pairing
- given supported `800 only` input, the engine returns the expected candidate parent plans including `800-C` where applicable
- given mixed `700 and 800` input, each candidate plan evaluates against the correct side-specific system ranges
- given spacing or window conflicts, a plan fails only when no compliant paired DVRS sub-range survives
- given exact DVRS TX/RX inputs outside the allowed rules, the result explains the violation clearly
- given technically valid output, the UI and PDF summary preserve the recommended DVRS frequencies and explanatory notes

## 3. Implementation Status

### 3.1 Implemented

- Python calculation engine
- FastAPI evaluation endpoint
- static web planner UI
- mixed 700/800 workflow
- parent-plan evaluation with submodels
- exact DVRS TX/RX validation
- ordering summary panel
- generated PDF export
- CLI entrypoint
- Windows desktop wrapper and packaging scaffold

### 3.2 Partially Implemented or Reserved

- `use_latest_ordering_ruleset` exists but does not yet switch between multiple active rulesets
- manual mobile RX override exists in the API model but is not exposed in the browser UI - This is because the bands covered in this release are deterministic, so manual override is not relevant today
- regulatory classification is intentionally conservative and still coarse compared with full licensing review

### 3.3 Not Implemented

- VHF planning
- UHF planning
- direct regulator or licensing-system integration
- scenario persistence
- template-filled vendor PDF output

## 4. Current Architecture

- core engine: `dvrs_tool/engine.py`
- plan and regulatory data: `dvrs_tool/plan_data.py`
- request and response models: `dvrs_tool/models.py`
- API layer: `dvrs_tool/api.py`
- PDF export: `dvrs_tool/pdf_export.py`
- web UI: `dvrs_tool/static/index.html`, `styles.css`, `app.js`
- CLI: `dvrs_tool/cli.py`
- desktop runtime: `dvrs_tool/desktop.py` and `run_desktop.py`
- packaging: `dvrs_desktop.spec` and `build_windows.ps1`
- regression suite: `tests/test_engine.py` and `tests/test_plan_table_guard.py`

## 5. Plan

### 5.1 Architecture Plan
The project should continue to evolve through a data-driven Python backend with a thin presentation layer rather than moving technical rule logic into the UI.

Planned component responsibilities:

- `dvrs_tool/plan_data.py`: standard-plan definitions, regulatory overlays, and encoded policy assumptions
- `dvrs_tool/engine.py`: deterministic evaluation of plan compatibility, range survival, pairing, and status classification
- `dvrs_tool/api.py` and `dvrs_tool/models.py`: stable request/response contract for UI and automation clients
- `dvrs_tool/static/`: user workflow, explanation display, and quote-draft interaction
- `dvrs_tool/pdf_export.py`: generated ordering-summary output suitable for downstream quoting workflows
- desktop packaging files: Windows delivery path for users who need an installed local executable

Technology choices remain intentionally simple for the current scope:

- Python for the rules engine and API
- FastAPI for the local planning service
- static HTML/CSS/JavaScript for the current browser UI
- PySide6 WebEngine for the desktop wrapper
- PyInstaller for Windows packaging

This plan favors explainability, low operational complexity, and easy inspection over framework complexity or premature infrastructure work.

### 5.2 MVP Definition
The minimum viable product for the course project is the currently scoped 700/800 in-band planner that:

- accepts the supported customer system inputs
- evaluates the encoded standard plans
- presents technical and regulatory outcomes with explanations
- produces an ordering-summary style output
- remains runnable locally in browser and desktop-wrapper form

The following are stretch goals rather than MVP requirements:

- VHF or UHF support
- multiple live rulesets
- scenario persistence
- direct regulator or licensing-system integration
- template-filled vendor PDF output

## 6. Tasks

Work should continue as small, testable increments that leave the project in a working state after each step.

### 6.1 Ordered Task Sequence

1. Stabilize and document the current 700/800 evaluation rules.
   Acceptance criteria:
   - the standard-plan dataset matches the approved project interpretation
   - guarded plan-table changes remain intentional and reviewable
   - regression tests cover the current parent-plan candidate sets and sub-range behavior

2. Preserve explanation quality in API and UI outputs.
   Acceptance criteria:
   - invalid results include rule-based reasons
   - technically valid results preserve regulatory notes and warnings
   - quote-summary output reflects the same core recommendation shown in the plan results

3. Harden mixed-band and exact-DVRS workflows.
   Acceptance criteria:
   - mixed-band evaluation uses the correct side-specific system inputs
   - exact DVRS TX/RX values narrow or invalidate plans correctly
   - tests cover the expected mixed-band and exact-input regressions

4. Keep browser, CLI, PDF, and desktop workflows aligned.
   Acceptance criteria:
   - the shipped browser workflow remains runnable
   - CLI and API outputs remain consistent with engine results
   - PDF export remains available for valid quote-draft output
   - Windows packaging remains buildable when shipped application behavior changes

5. Add future scope only as explicitly bounded follow-on work.
   Acceptance criteria:
   - new band support or rulesets come with explicit scope boundaries
   - plan data, engine logic, UI behavior, and tests are updated together
   - the specification is updated before or alongside implementation

## 7. Important Assumptions

1. When the ordering guide and older narrative material differ, the approved newer project interpretation should control, especially for fixed plan ranges and sub-range recommendation behavior.
2. The current product targets standard public-safety planning workflows for U.S. and Canadian users, not federal-only or specialized rail, utility, or other profiles.
3. `COORDINATION_REQUIRED` is the correct default whenever the project cannot justify a stronger licensing conclusion.
4. Future scope additions should extend the current data-driven Python engine rather than forcing rule logic into the UI.

## 8. Germane Future Development Roadmap

The following roadmap items are germane to the current product direction and should remain documented even though they are not yet implemented:

- activate true multi-ruleset support if the `use_latest_ordering_ruleset` toggle is intended to become functional
- refine regulatory classification only when authoritative channel-block or profile-specific rules are ready to encode and test
- add scenario save/load support if planner reuse becomes a regular workflow need
- consider admin-managed policy or plan tables only after the current guarded plan-table workflow is proven stable
- decide whether to keep the current static web UI or migrate to a richer frontend framework if UI complexity materially increases
- evaluate template-based PDF filling if the generated ordering-summary PDF is no longer sufficient
- reintroduce VHF or UHF only as deliberate scoped projects with dedicated plan data, pairing logic, regulatory rules, and regression coverage
- consider direct license-import integrations only after the core 700/800 planning workflow is stable and reviewable

## 9. Research Notes and Source Basis

Primary bundled references:

- `dvr-lx-ordering-guide-1 (1).pdf`
- `Introduction to  In-Band Operation-v1_2019-06-19.pdf`
- `supplemental-ordering-form-b2bf88f7.pdf`

Repository evidence reviewed during this refresh:

- `README.md`
- `docs/dev-log.md`
- `docs/dev-history/*.md`
- `dvrs_tool/api.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/pdf_export.py`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_desktop.spec`
- `tests/test_engine.py`
- `tests/test_plan_table_guard.py`

Regulatory caution:

- U.S. and Canadian assignability remains channel-specific, border-sensitive, and coordinator-dependent.
- The correct role of this product is technical and policy-informed screening, not automatic approval.
