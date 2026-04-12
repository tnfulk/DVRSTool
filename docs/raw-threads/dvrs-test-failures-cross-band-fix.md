# Raw Thread: DVRS Test Failures And Cross-Band Fixes

## Overview
This thread started as a test-and-diagnose request and ended with engine changes plus project documentation. The work centered on running the full DVRS test suite, tracing failing tests to cross-band and actual-frequency plan-selection logic, implementing engine-only fixes, and then recording the thread in the repo docs.

## Participants
- **User**
- **Assistant**

## 1. Initial Request

### User
Asked to run the full test series on the project, identify failing tests, and propose solutions.

### Assistant
Started by inspecting the repo structure, test entrypoints, and repo status before running the suite. During discovery:

- Confirmed the project was a Python repo.
- Found unstaged local changes and explicitly avoided reverting them.
- Noted that `rg.exe` was not executable in the environment and fell back to PowerShell-native file discovery.

Key files identified:

- `run_tests.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `tests/test_engine.py`

## 2. Full Test Run And Failure Review

### Assistant
Ran:

```powershell
python run_tests.py
```

Initial result:

- `52` tests run
- `9` failures
- `1` skipped

The skipped test was:

- `test_api_returns_structured_error_for_optional_zero_value`
  - Reason: `FastAPI test client is not installed.`

The failing tests were:

- `test_actual_700_mhz_dvrs_pair_selects_700_plan_family`
- `test_actual_dvrs_frequency_can_leave_only_matching_plans_valid`
- `test_actual_dvrs_window_mismatch_does_not_override_spacing_and_plan_rules`
- `test_700_a_is_preferred_for_800_system_when_actual_dvrs_pair_is_700_mhz`
- `test_actual_dvrs_native_plan_driver_overrides_system_band_hint`
- `test_800_only_hint_with_700_mhz_dvrs_pair_does_not_leak_non_700_800_plans`
- `test_700_b_parent_passes_for_800_only_system_via_internal_submodel`
- `test_700_c_parent_passes_for_800_only_system_via_internal_submodel`
- `test_active_mobile_windows_limit_plan_validity`

Representative failure patterns:

- Extra plans stayed valid when an actual 700 MHz DVRS pair should have narrowed the result to `700-A`.
- Expected 700/800 parent-plan submodels returned the wrong DVRS ranges.
- Active mobile window enforcement was not invalidating some plans when actual licensed frequencies were present.
- Some actual-frequency matching cases returned too few plans because the engine was not using the expected cross-band/interoperability interpretation.

## 3. Investigation

### Assistant
Read the relevant tests in `tests/test_engine.py` and inspected these engine areas in `dvrs_tool/engine.py`:

- `_request_with_plan_specific_pairing()`
- `_plan_variants()`
- `_candidate_plans()`
- `_native_plan_matches_actual_dvrs()`
- `_build_cross_band_variant()`
- `_build_interop_variant()`
- `_select_best_plan_result()`
- `_build_variant_system_summary()`
- `_variant_request_model_matches()`
- `_validate_active_mobile_windows()`

### Findings During Investigation

1. `_build_interop_variant()` already existed but was not being used by the main variant-selection path.
2. `_request_with_plan_specific_pairing()` was still a stub.
3. `_candidate_plans()` and `_select_best_plan_result()` were not sufficiently differentiating between:
   - Auto-detected system model
   - Explicit `700 only` / `800 only` hints
   - Requests that included actual licensed DVRS TX/RX values
4. The tests implicitly required different behavior for:
   - Auto-detected 700/800 systems
   - Explicit opposite-band single-band hints
   - Actual licensed DVRS matching

### Important Intermediate Reasoning

The assistant identified that:

- Auto-detected single-band systems were expected to keep using native table ranges for parent plans.
- Explicit single-band hints were expected to use an interoperability-style internal submodel.
- Actual licensed DVRS frequencies needed to influence both candidate filtering and best-result selection.
- The user explicitly said not to change the plan window table, so the fix had to stay in selection/evaluation logic.

## 4. First Implementation Attempt

### User
After reviewing the failure analysis, asked:

- Execute the proposed fixes.
- Do **not** change the plan window table.

### Assistant
Began modifying `dvrs_tool/engine.py` only.

### First Change Set
The first pass:

- Changed `_plan_variants()` to use interoperability variants directly for cross-band parents.
- Changed `_select_best_plan_result()` so actual licensed matches were preferred ahead of unrelated generic valid results.

### Result
After rerunning the test suite, many of the original failures were fixed, but new regressions appeared.

New failures showed that this approach was too broad:

- Explicit cross-band single-band scenarios improved.
- Auto-detected single-band parent-plan behavior regressed.
- Some tests that expected native table ranges for parent plans now returned interoperability ranges instead.

This led to an important refinement:

- The engine could not use one static cross-band interpretation for every scenario.

## 5. Second Iteration

### Assistant
Adjusted the variant-model gating.

Changes in this phase included:

- Separating “candidate-model matching” from broader evaluation-model matching.
- Reordering some 800-family variants.
- Making `_variant_request_model_matches()` more permissive for evaluation while using a stricter helper for candidate filtering.

### Result
This recovered several expectations, but some failures remained. The remaining failing tests showed that:

- Auto-detected 700/800 systems still needed native-style cross-band preview behavior.
- Explicit opposite-band single-band hints needed a different internal submodel than auto-detected systems.
- Actual licensed DVRS matching needed yet another layer of dynamic interpretation.

## 6. Final Iteration

### Assistant
Introduced dynamic variant resolution instead of forcing `_plan_variants()` itself to encode every case.

### Final Engine Changes
The final approach in `dvrs_tool/engine.py` did the following:

- Restored `_plan_variants()` to primarily use the original cross-band preview path.
- Added `_resolved_variant_plan()` to choose the effective variant dynamically.
- Updated `_build_interop_variant()` so its interop windows were represented as fixed ranges rather than unrestricted windows.
- Applied `_resolved_variant_plan()` in:
  - `_evaluate_plan_variant()`
  - `_build_variant_system_summary()`
  - `_native_plan_matches_actual_dvrs()`
  - `_select_best_plan_result()`
- Changed `_variant_matches_actual_licensed()` to delegate to `_single_plan_matches_actual_dvrs()` so exact matching used the full rule set rather than only a coarse TX/RX window check.

### Dynamic Rules Encoded
The final logic effectively became:

- Use native/cross-band preview behavior for normal auto-detected parent-plan evaluation.
- Use interoperability variants when the user explicitly requests the opposite-band single-band model.
- Use interoperability variants for actual-frequency matching on cross-band variants.
- Prefer actual-frequency-matching results over unrelated technically valid variants.

## 7. Final Verification

### Assistant
Ran the full test suite again:

```powershell
python run_tests.py
```

Final result:

- `52` tests run
- `0` failures
- `1` skipped

The skipped test remained:

- `test_api_returns_structured_error_for_optional_zero_value`
  - `FastAPI test client is not installed.`

### Assistant Summary Back To User
Reported that the engine was fixed entirely in `dvrs_tool/engine.py`, that the approved plan table was untouched, and that the full test suite passed.

## 8. Documentation Request

### User
Then asked for the entire conversation to be converted into reusable project documentation by creating:

- `docs/dev-history/<thread-slug>-summary.md`
- `docs/raw-threads/<thread-slug>.md`

Also requested:

- A 3-5 sentence summary appended to `docs/dev-log.md`

### Assistant
Inspected:

- `docs/dev-history/`
- `docs/raw-threads/`
- `docs/dev-log.md`

Then created:

- `docs/dev-history/dvrs-test-failures-cross-band-fix-summary.md`
- `docs/raw-threads/dvrs-test-failures-cross-band-fix.md`

And appended a new thread summary to:

- `docs/dev-log.md`

## 9. Important Technical Takeaways

- The plan table was intentionally left unchanged throughout this thread.
- The failing behavior was in engine selection and submodel resolution logic, not in the encoded plan data.
- The main conceptual distinction introduced by the final fix is that cross-band parent-plan handling is context-sensitive:
  - Auto-detected single-band systems
  - Explicit opposite-band hints
  - Actual licensed DVRS TX/RX matching

## 10. Files Mentioned Or Modified

Primary code files:

- `dvrs_tool/engine.py`
- `tests/test_engine.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/models.py`
- `run_tests.py`

Documentation files added/updated:

- `docs/dev-history/dvrs-test-failures-cross-band-fix-summary.md`
- `docs/raw-threads/dvrs-test-failures-cross-band-fix.md`
- `docs/dev-log.md`
