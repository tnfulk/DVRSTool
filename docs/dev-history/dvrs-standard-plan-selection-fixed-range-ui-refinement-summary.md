# DVRS Standard Plan Selection, Fixed-Range Logic, and UI Workflow Refinement

## 1. Context
This thread refined how the DVRS planner chooses and evaluates standard plans, especially for 800-only systems and fixed ordering-guide plan ranges. It also tightened the web UI workflow so results only appear after an explicit evaluation and invalid plans are presented more clearly.

## 2. Problem Statement
Several related problems were addressed:

- The initial 800-only plan-selection behavior did not match the intended product model.
- The engine treated some 700-only system cases as standard-plan candidates even though the ordering guide does not support them.
- Fixed plan ranges from the ordering guide were first treated as fixed published blocks, then refined so technical validity meant at least one valid channel inside the range, and finally refined again so the returned recommended DVRS ranges themselves satisfy separation rules.
- The `800-C` presentation was confusing because an interoperability fallback could appear under the `800-C` label, and later because full fixed plan blocks could be shown even when only part of the range was truly usable.
- The UI auto-ran evaluations, showed success banners too aggressively, exposed invalid-plan DVRS proposals visually, and lacked a reset flow.

## 3. Key Decisions
- Decision: Treat explicit `800 only` systems as a two-plan model: `700-A` and `800-C`.
  - Rationale: The product direction was that 800-only systems should present the two DVRS placement choices relevant to this model.
  - Alternatives considered (if any): The existing behavior of returning all native 800-family plans was rejected.

- Decision: Remove `700 only` as a supported standard-plan system model.
  - Rationale: The team concluded there are no standard plans that only include 700 MHz system frequencies.
  - Alternatives considered (if any): Keeping `700 only` as a hint or auto-detected band was abandoned.

- Decision: Apply the 800-only model to auto-detected 800 MHz systems as well.
  - Rationale: If the input mobile TX range clearly indicates an 800-only system, leaving the hint blank should not produce broader plan-selection behavior than explicitly choosing `800 only`.
  - Alternatives considered (if any): Keeping auto-detect broader than the explicit hint was rejected.

- Decision: Stop using interoperability fallbacks as hidden variants of native standard plans.
  - Rationale: A plan like `800-C` must continue to represent the ordering-guide layout associated with `800-C`, not silently switch to another topology under the same label.
  - Alternatives considered (if any): Keeping interop fallbacks under the same plan IDs was rejected after tracing `800-C` behavior.

- Decision: Use ordering-guide fixed plan ranges as the authoritative plan boundaries.
  - Rationale: After team clarification, the frequency ranges in `dvr-lx-ordering-guide-1 (1).pdf` were treated as fixed ordering-guide plan ranges rather than examples to be freely shifted by spacing-first logic.
  - Alternatives considered (if any): The earlier spacing-primary / “shrink and slide” proposal logic was explicitly reverted.

- Decision: For fixed-range plans, technical validity means at least one paired channel inside the published plan range can satisfy the rules.
  - Rationale: Whole-range rejection produced counterintuitive outcomes where a plan could fail without actual DVRS channels but pass with a valid exact DVRS pair inside the same published range.
  - Alternatives considered (if any): Requiring the full fixed plan block to clear spacing was abandoned.

- Decision: Recommended DVRS ranges must themselves satisfy plan separation requirements.
  - Rationale: Even when a plan is valid because some channel inside a published fixed range works, the tool should recommend only the feasible sub-range rather than a larger overlapping block.
  - Alternatives considered (if any): Displaying the entire published fixed range even when only a subset is feasible was replaced by spacing-compliant sub-range recommendations.

- Decision: Hide proposed DVRS channels and frequency visualizations for technically invalid plans.
  - Rationale: Invalid plans should still explain why they failed, but should not visually imply a usable recommendation.
  - Alternatives considered (if any): Showing full plan layouts for invalid plans was used temporarily for debugging and then removed from the UI.

- Decision: Hide evaluation results until the user explicitly clicks `Evaluate plans`, add `Reset`, and use the status banner only for active work messages or meaningful warnings/errors.
  - Rationale: The default view was cluttered, auto-evaluation was surprising, and a permanent green “Evaluation complete” banner was not useful.
  - Alternatives considered (if any): Auto-running evaluation on page load and keeping a generic success banner were removed.

## 4. Implementation Summary
- Updated the engine’s plan-selection rules so `BAND_800_ONLY` returns `700-A` and `800-C`.
- Removed `BAND_700_ONLY` from the domain model and engine handling, and replaced 700-only auto-detect with a structured unsupported-model error.
- Applied the same 800-only plan-selection model to auto-detected 800 MHz systems.
- Removed hidden interop-variant selection from standard plan evaluation.
- Reworked fixed-range recommendation logic in the engine multiple times:
  - first to use ordering-guide fixed ranges instead of spacing-derived windows,
  - then to validate plans when at least one channel in the fixed range works,
  - finally to recommend only the feasible sub-range inside the fixed plan boundary so the displayed proposal itself satisfies spacing.
- Updated tests throughout to match each rules-engine refinement, including `800-C`, `800-A1`, actual-DVRS fit behavior, auto-detect, and unsupported 700-only behavior.
- Updated `dvrs-web-app-design.md` to reflect the final rule set: fixed guide ranges define plan boundaries, validity can be satisfied by at least one channel inside the range, and returned proposed DVRS ranges must be spacing-compliant subsets when overlap exists.
- Updated the frontend so invalid plans hide proposed DVRS channels and visualizations but still show failure reasons.
- Refined the web app workflow:
  - results hidden until `Evaluate plans`,
  - added `Reset`,
  - removed auto-submit on load,
  - moved serious ordering-summary warnings (such as consulting Motorola Presales) into the status panel,
  - stopped showing a persistent green “Evaluation complete” banner,
  - added cache-busting querystring updates after frontend asset changes.

## 5. Challenges & Iterations
- The first 800-only adjustment changed explicit hint behavior but not auto-detect, so the engine still returned a broader 800-family set when the hint was omitted.
- Removing 700-only support invalidated several earlier tests that assumed 700-only auto-detection remained valid.
- The first “fixed guide ranges first” implementation made `800-C` appear invalid in no-DVRS cases because the engine compared the entire fixed block to system spacing, while exact DVRS inputs could still validate inside that same range.
- A first attempt to support “at least one channel in range is valid” added an any-channel shortcut but left the older whole-range mobile-RX spacing rejection in place, which still caused false invalid results.
- A later refinement showed that simply marking a plan valid if some internal channel worked was not sufficient; the returned recommended ranges also had to be narrowed to the actual feasible sub-range so the displayed recommendation itself was technically correct.
- Frontend behavior briefly appeared inconsistent because the browser was still using cached JS/CSS after HTML changes. The asset version strings in `index.html` had to be updated so the current logic actually loaded.

## 6. Final Outcome
The final state of this thread is:

- 700-only standard-plan systems are no longer supported.
- 800-only systems, whether explicitly selected or auto-detected, use the two-plan model `700-A` and `800-C`.
- Standard plans no longer silently switch to interoperability topologies under the same plan ID.
- Fixed ordering-guide ranges define each plan’s allowed recommendation boundary.
- A fixed-range plan is technically valid when at least one paired DVRS channel inside the published range satisfies the rules.
- The returned recommended DVRS TX/RX ranges are now the feasible spacing-compliant sub-range inside the plan boundary, not a larger overlapping block.
- Invalid plans still show why they failed, but the UI no longer shows proposed DVRS channels or frequency visualizations for them.
- The results area is hidden until evaluation is requested, `Reset` restores the default form state, and the status panel is reserved for meaningful warnings/errors or transient progress.

## 7. Open Questions / Follow-ups
- The ordering-summary “best plan” selection still depends heavily on list order when multiple technically valid plans match the same entered DVRS frequencies. A future explicit tie-break policy may be useful.
- The tool now computes feasible recommended sub-ranges inside published fixed plan boundaries, but there is still room to clarify whether the UI should also expose the original full published plan range separately for planner reference.
- If additional standard-plan families or future ordering-guide revisions are added, the same “boundary vs recommended sub-range” rule should be applied consistently and documented early.

## 8. Affected Files / Components
- `dvrs_tool/engine.py`
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `tests/test_engine.py`
- `dvrs-web-app-design.md`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/styles.css`
- `docs/dev-log.md`

