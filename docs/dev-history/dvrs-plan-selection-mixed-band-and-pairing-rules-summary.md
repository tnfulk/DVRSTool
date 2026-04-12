# DVRS Plan Selection, Mixed-Band Inputs, and Pairing Rules Refinement

## 1. Context
This thread refined the DVRS planning engine and UI around real-world 700/800 interoperability scenarios, actual licensed DVRS frequencies, mixed-band system hints, and deterministic system TX/RX pairing rules. The work touched both backend validation logic and the browser-based planner so users could model more realistic 700-only, 800-only, mixed 700/800, and UHF workflows.

## 2. Problem Statement
Several related problems were addressed:

- `800-A1` was being marked technically invalid for an input set that should fit the ordering-guide spacing rules.
- The engine was using mobile TX alone to decide which plan family to evaluate, even when actual DVRS TX/RX frequencies clearly identified a native plan.
- Native plan active-window rules were not being enforced, which let the wrong plans survive.
- Mixed `700 and 800` systems were initially modeled with a single stitched mobile range, which was too coarse to pick the correct mixed-band plan.
- The UI introduced dynamic system-band fields, but stale or weak hide/show behavior caused the wrong inputs to remain visible.
- UHF 380-430 pairing still depended on manual RX input, even though the thread established deterministic 5 MHz pairing rules for those plans.

## 3. Key Decisions
- Decision: Correct `800-A1` to use a `45 MHz` DVRS TX-above-RX split with a `861-869 MHz` DVRS TX window.
  - Rationale: The repo graphic and the spacing-valid sample case showed the existing `35 MHz` / `851-869 MHz` encoding was wrong.
  - Alternatives considered (if any): None beyond confirming whether the failure was code vs. user input.

- Decision: When actual DVRS TX/RX is provided, treat those frequencies as the primary plan-family driver instead of rejecting them for not matching a computed subrange derived from mobile TX.
  - Rationale: Exact licensed DVRS channels are stronger evidence of the intended plan than a solver-generated default range.
  - Alternatives considered (if any): Keeping the old “actual frequency outside computed range” gate. This was abandoned.

- Decision: Enforce each plan’s active mobile TX/RX windows.
  - Rationale: Without active-window validation, plans could appear valid merely because a DVRS pair fit a coarse window.
  - Alternatives considered (if any): Relying only on DVRS frequency windows and pair offsets. This was insufficient.

- Decision: Add a `System Bands` hint with `VHF`, `UHF`, `700 only`, `800 only`, and `700 and 800`.
  - Rationale: Users needed a way to steer candidate plan families, especially for mixed-band workflows and ambiguous inputs.
  - Alternatives considered (if any): Keeping pure auto-detect. This did not support the required mixed-band cases.

- Decision: For `700 and 800`, add dedicated `700 Mobile TX` and `800 Mobile TX` inputs instead of inferring both systems from one combined range.
  - Rationale: A single combined range could not simultaneously identify the mixed-band plan slot and preserve spacing validity checks.
  - Alternatives considered (if any): Relaxing validation when mixed-band detail was missing. This was discussed, then replaced by explicit fields.

- Decision: In mixed `700 and 800` mode, use one side’s mobile range to identify the plan slot and the opposite side’s range to evaluate spacing, depending on the plan family.
  - Rationale: This matched the ordering-guide layout more closely and allowed cases like `700-B` to validate correctly.
  - Alternatives considered (if any): Using the same mobile range for both active-window checks and spacing. This produced false negatives.

- Decision: Make the frontend explicitly hide and disable inactive mobile-range fields, and harden the CSS with `[hidden], .is-hidden { display: none !important; }`.
  - Rationale: The UI logic was correct on disk, but stale assets and weak hide/show behavior made the wrong fields appear visible in practice.
  - Alternatives considered (if any): Relying on the `hidden` attribute alone. This was not robust enough.

- Decision: Honor explicit `700 only`, `800 only`, `VHF`, and `UHF` hints when resolving system-band pairing logic.
  - Rationale: Users needed deterministic pairing behavior even when their input TX range did not fit the previous auto-detect windows.
  - Alternatives considered (if any): Forcing all explicit hints back through auto-detect. This blocked valid intent-driven calculations.

- Decision: Make UHF 380-430 pairing deterministic with a 5 MHz split and plan-specific direction instead of requiring manual RX input.
  - Rationale: The thread established concrete 5 MHz pairing rules and corresponding plan directions.
  - Alternatives considered (if any): Keeping UHF 380 duplex plans in manual mode. This was no longer aligned with the requested rules.

## 4. Implementation Summary
- Corrected `800-A1` plan metadata in `dvrs_tool/plan_data.py`.
- Removed the old `ACTUAL_DVRS_FREQUENCY_OUTSIDE_COMPUTED_RANGE` rejection path so actual DVRS values are validated against plan rules rather than solver defaults.
- Added active mobile TX/RX window validation for plans.
- Changed candidate plan selection so actual DVRS frequencies can drive native plan-family selection.
- Added `SystemBandHint` to the request model and API, and wired a `System Bands` dropdown into the web UI.
- Added mixed-mode UI inputs for `700 Mobile TX Low/High` and `800 Mobile TX Low/High`.
- Updated mixed-band engine behavior so plan evaluation uses the appropriate 700-side or 800-side system ranges for active-window checks and spacing.
- Tightened native DVRS matching with fixed-range checks so mixed 700 plans can differentiate `700-B` from `700-C`.
- Updated frontend field toggling to hide/disable inactive controls and refreshed static asset version strings.
- Updated system-band resolution so explicit hints can drive 700 and 800 pairing rules.
- Added deterministic UHF 380 plan-specific pairing and removed the blanket requirement for manual RX input there.
- Expanded the automated test suite to cover all of the above scenarios.

## 5. Challenges & Iterations
- The first `800-A1` fix revealed that the deeper issue was not just bad plan data: the engine was still invalidating exact DVRS values if they did not match its computed “best-fit” subrange.
- After actual-DVRS-driven plan selection was added, the engine still surfaced wrong plans because active mobile TX/RX windows were encoded but never enforced.
- Mixed `700 and 800` logic went through two materially different approaches:
  - First attempt: allow a single stitched mobile TX range and relax validation.
  - Final approach: explicitly collect separate 700-side and 800-side mobile TX ranges and use them differently for plan identification vs. spacing.
- The frontend field visibility issue appeared solved in code but still looked broken in the browser. This led to the conclusion that stale static assets and weak hide/show behavior were both contributing factors, so the implementation was hardened with asset-version bumps and explicit CSS hiding.
- UHF 380 pairing required a second round of work because the engine’s original architecture assumed manual mobile RX for that family, while the requested behavior depended on per-plan deterministic pairing.

## 6. Final Outcome
The final state of the solution is:

- `800-A1` uses the corrected 45 MHz pairing and validates spacing-valid licensed DVRS pairs correctly.
- Actual DVRS TX/RX frequencies now drive native plan-family evaluation when supplied.
- Active mobile TX/RX windows are enforced.
- `System Bands` exists in the UI and API.
- Mixed `700 and 800` mode now dynamically asks for separate 700-side and 800-side mobile TX ranges and uses both during plan evaluation.
- The planner hides or disables the wrong fields based on `System Bands`.
- Explicit 700-only and 800-only hints now drive deterministic pairing calculations.
- UHF 380-430 plans use deterministic 5 MHz pairing with plan-specific direction.
- The test suite was expanded substantially and passes after the changes made in this thread.

## 7. Open Questions / Follow-ups
- The thread corrected `800-A3` to `800-B`; no `800-A3` implementation remains.
- The mixed-band system summary shown in the UI is still a simplified display summary; most of the nuanced mixed-band logic lives in plan-specific evaluation paths.
- UHF 380 directionality for plans beyond the explicitly discussed A-series examples was implemented based on the thread’s requested 5 MHz rule and plan naming patterns, but may still benefit from confirmation against the authoritative ordering guide.
- The UI field-visibility issue looked like a stale/static-asset problem at least once; if it reappears, the deployment/runtime path serving static assets should be checked.

## 8. Affected Files / Components
- `dvrs_tool/engine.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `tests/test_engine.py`
- `docs/dev-log.md`
- `docs/dev-history/*`
- `docs/raw-threads/*`
