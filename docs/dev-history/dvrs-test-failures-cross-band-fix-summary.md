# DVRS Cross-Band Test Failure Investigation And Engine Fix

## 1. Context
This thread focused on stabilizing the DVRS engine after the desktop-runtime work by running the full existing test suite, identifying the failing behaviors, and correcting the engine logic without changing the approved plan window table.

## 2. Problem Statement
The project test suite was failing in scenarios involving:

- Actual licensed DVRS TX/RX frequencies
- Cross-band parent-plan evaluation between 700 MHz and 800 MHz systems
- Selection of the correct internal submodel for explicit single-band hints versus auto-detected systems
- Active mobile window enforcement when actual licensed frequencies were supplied

The user explicitly required that the fixes be made in engine logic only and that the published plan window table remain unchanged.

## 3. Key Decisions
- Decision: Fix the failures in `dvrs_tool/engine.py` instead of editing `dvrs_tool/plan_data.py`.
  - Rationale: The user explicitly said not to change the plan window table, and the failing tests pointed to selection/evaluation logic rather than incorrect table data.
  - Alternatives considered: Adjusting the plan table was rejected.

- Decision: Use the existing interoperability concept dynamically instead of forcing one cross-band interpretation for every scenario.
  - Rationale: The tests distinguished between auto-detected systems, explicitly hinted systems, and requests with actual licensed DVRS frequencies. A single static cross-band variant could not satisfy all of them.
  - Alternatives considered: Always using interop variants was tried and abandoned because it broke auto-detected single-band parent-plan behavior.

- Decision: Preserve analog cross-band preview behavior for auto-detected parent-plan evaluation, but resolve to interoperability variants for explicit opposite-band hints and actual licensed DVRS matching.
  - Rationale: This matched the test expectations: auto-detected systems still used native table ranges for parent plans, while explicit `700 only` / `800 only` hints and actual licensed DVRS frequencies needed interoperability-aware behavior.
  - Alternatives considered: Restricting all evaluation to system-model-matched variants was too narrow and caused incorrect plan selection.

- Decision: Prioritize actual licensed DVRS matches when selecting the returned result for a parent plan.
  - Rationale: Some failing tests expected an actual licensed pair to override a merely valid but unrelated internal submodel.
  - Alternatives considered: Keeping generic valid results ahead of actual matches caused incorrect plan validity and summary outcomes.

## 4. Implementation Summary
The thread began by running `python run_tests.py`, which initially produced 9 failing tests and 1 skipped test. The failures were traced to `dvrs_tool/engine.py`, especially around:

- `_plan_variants()`
- `_candidate_plans()`
- `_select_best_plan_result()`
- `_variant_request_model_matches()`
- `_build_variant_system_summary()`
- `_validate_active_mobile_windows()`

The final implementation:

- Added dynamic variant resolution so cross-band parent plans can use either the existing cross-band preview or an interoperability profile depending on request context.
- Kept the original cross-band variant definitions in `_plan_variants()` for normal auto-detected single-band behavior.
- Added `_resolved_variant_plan()` to swap in an interoperability variant when:
  - The user explicitly selected the opposite-band single-band hint, or
  - Actual licensed DVRS frequencies were being matched
- Updated `_native_plan_matches_actual_dvrs()` and `_select_best_plan_result()` to use the resolved variant behavior when matching actual licensed frequencies.
- Changed `_variant_matches_actual_licensed()` to use the full `_single_plan_matches_actual_dvrs()` validation path instead of only checking coarse TX/RX windows.
- Adjusted `_build_interop_variant()` so interoperability ranges are represented as fixed ranges, which allowed the engine to return the expected full surviving compliant intervals during explicit single-band submodel evaluation.
- Preserved the approved plan table unchanged.

## 5. Challenges & Iterations
- The first investigation identified likely root causes correctly, but the first implementation attempt over-applied interoperability variants to all cross-band parent plans.
- That initial change fixed the actual-frequency leakage but broke the tests that expected auto-detected 700/800 systems to continue using native table ranges for parent plans.
- A second iteration separated candidate-model matching from broader evaluation-model matching so the engine could:
  - Remain strict enough for candidate filtering
  - Remain flexible enough for direct plan evaluation and actual-frequency-driven result selection
- A further refinement introduced dynamic resolution between cross-band preview variants and interoperability variants, which reconciled all remaining edge cases without touching the plan table.

## 6. Final Outcome
The engine was corrected entirely in `dvrs_tool/engine.py`, the approved plan table was left unchanged, and the full suite passed successfully:

- `52` tests run
- `0` failures
- `1` skipped test

The skipped test remained the pre-existing FastAPI test-client skip (`FastAPI test client is not installed.`).

## 7. Open Questions / Follow-ups
- The engine now contains both cross-band preview logic and dynamically resolved interoperability logic; future maintainers may want to document that distinction more explicitly in the product/design spec.
- The skipped FastAPI test still depends on local test-client availability and may be worth standardizing in project setup.

## 8. Affected Files / Components
- `dvrs_tool/engine.py`
- `tests/test_engine.py`
- `run_tests.py`
- Project test workflow triggered from the repo root
