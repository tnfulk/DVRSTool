# Raw Thread: DVRS Mixed-Plan Sub-Range Spec Alignment

## Overview
This thread covered a DVRS plan-evaluation discrepancy for a mixed `700 and 800` system. The user supplied a concrete test sequence aimed at `700-C`, identified that the specification should allow returning valid sub-ranges when nominal plan ranges are close to or partially overlap system ranges, requested spec-first clarification, then asked for the implementation and tests to be aligned. The thread concluded with a Git commit after the changes were validated.

## Initial User Question

### User
Asked for evaluation of a test sequence intended for the `700-C` plan using:

- `700 Mobile TX`: `799.2125-801.8875`
- `800 Mobile TX`: `806.0125-822.3875`

Requested:

- Which plans are valid for this range
- Which DVRS frequency options should be recommended

## Initial Investigation

### Assistant
Inspected the repository to answer from the encoded rules rather than by assumption.

Key findings during repository review:

- The project already contained a DVRS engine, API, tests, and an extensive design/spec document.
- `dvrs_tool/plan_data.py` defined the relevant plan windows:
  - `700-B`
    - active mobile TX: `802.0-805.0`
    - fixed DVRS RX: `799.0-802.0`
    - fixed DVRS TX: `769.0-772.0`
  - `700-C`
    - active mobile TX: `799.0-802.0`
    - fixed DVRS RX: `802.0-805.0`
    - fixed DVRS TX: `772.0-775.0`
  - `800-A1`
    - active mobile TX: `806.0-819.0`
  - `800-A2`
    - active mobile TX: `811.0-824.0`
  - `800-B`
    - active mobile TX: `806.0-821.0`
- `dvrs_tool/engine.py` showed that in mixed `700/800` mode, plan evaluation was intended to use band-specific mobile TX ranges per candidate plan.
- `tests/test_engine.py` contained numerous regression tests around mixed-band behavior, actual DVRS frequencies, and fixed ordering-guide plan ranges.

## First Evaluation of the User's Sample

### Assistant
Ran the engine against the user's exact mixed-system inputs using:

- `system_band_hint = BAND_700_AND_800`
- `mobile_tx_700_low_mhz = 799.2125`
- `mobile_tx_700_high_mhz = 801.8875`
- `mobile_tx_800_low_mhz = 806.0125`
- `mobile_tx_800_high_mhz = 822.3875`

Observed result before changes:

- Evaluated plans: `700-B`, `700-C`, `800-A1`, `800-A2`, `800-B`
- All were returned as technically invalid
- Ordering summary note: `No technically valid standard plan proposal was produced.`

Detailed outcomes before changes:

- `700-B`
  - Invalid
  - Preview DVRS RX: `799.0-802.0`
  - Preview DVRS TX: `769.0-772.0`
  - Failure: mobile TX outside active mobile TX window `802.0-805.0`
- `700-C`
  - Invalid
  - No proposed DVRS range returned
  - Failure: `No channel inside the plan's fixed ordering-guide DVRS RX range satisfies the required constraints.`
- `800-A1`
  - Invalid
  - Preview DVRS RX: `816.0-824.0`
  - Preview DVRS TX: `861.0-869.0`
  - Failure: mobile TX outside active mobile TX window `806.0-819.0`
- `800-A2`
  - Invalid
  - Preview DVRS RX: `806.0-814.0`
  - Preview DVRS TX: `851.0-859.0`
  - Failure: mobile TX outside active mobile TX window `811.0-824.0`
- `800-B`
  - Invalid
  - Preview DVRS RX: `809.0-824.0`
  - Preview DVRS TX: `854.0-869.0`
  - Failure: mobile TX outside active mobile TX window `806.0-821.0`

### Assistant
Reported that, with the current implementation, there was no technically valid standard plan for the sample mixed-band input and therefore no standard DVRS frequency option to recommend.

## User Clarification on Intended Behavior

### User
Directed attention back to the specification and stated that the system should return valid ranges even when the DVRS and system ranges overlap, so long as the returned range still satisfies the separation rules for that plan.

Requested confirmation before any implementation changes.

### Assistant
Confirmed understanding:

- Plans should not fail merely because the full nominal DVRS range overlaps or sits close to the system range.
- The engine should search within each plan's fixed range or allowed window.
- If a surviving contiguous sub-range still meets spacing, window, and pairing rules, that sub-range should be returned.
- A plan should fail only when no compliant sub-range remains.

The assistant explicitly paused before changing code until the user confirmed.

## User Instruction to Proceed

### User
Confirmed that this logic should apply to all plans and asked for the following sequence:

1. Update the specification
2. Align the tool with the refined specification
3. Re-run the earlier sample and show which plans are valid and which DVRS frequency options should appear

## Spec Review and Design Alignment

### Assistant
Reviewed `dvrs-web-app-design.md` and found that the specification already partially supported this direction.

Important pre-existing statements identified in the spec:

- Fixed ordering-guide DVRS ranges define plan boundaries
- The tool should recommend the feasible sub-range inside the published plan range
- Technical validity means at least one paired DVRS channel inside the fixed range satisfies the plan rules
- In mixed `700 and 800` systems, plan evaluation must use the band-specific mobile TX range attached to each candidate plan

The assistant concluded that:

- The spec needed to be made more explicit for both fixed and non-fixed plans
- The engine was still misaligned with that intent

## Spec Changes

### Assistant
Updated `dvrs-web-app-design.md` to make the requirement explicit.

The changes added and clarified that:

- Every plan, whether fixed-range or not, must return the surviving compliant DVRS sub-range inside its plan boundary before failing
- Near-adjacency or partial overlap is not itself a reason to reject a plan
- Mixed `700/800` evaluation must use the candidate plan's own band-specific mobile/system ranges
- Returned DVRS TX/RX ranges must themselves satisfy spacing, window, and pairing rules, even if only a narrow slice of the nominal plan range remains

## Engine Diagnosis

### Assistant
Traced the implementation problem to mixed-band plan-specific summary construction in `dvrs_tool/engine.py`.

Key diagnosis:

- In mixed `700/800` mode, `700` candidate plans were building their system summary from the `800` mobile TX range
- That caused `700-C` to be evaluated against the wrong system side
- With the wrong input, the engine concluded no feasible `700-C` slice remained

The assistant highlighted that this was not only a proposal-shrinking issue; the engine was using the wrong spacing reference for mixed `700` plans.

## Engine Change

### Assistant
Updated `dvrs_tool/engine.py` so that in mixed mode:

- `700` candidate plans use the `700` mobile TX range and `700` deterministic system TX range
- `800` candidate plans use the `800` mobile TX range and `800` deterministic system TX range

This corrected `_build_plan_system_summary(...)` so the candidate plan's own band-specific system ranges are used consistently.

## First Post-Change Sample Evaluation

### Assistant
Re-ran the sample mixed-band evaluation after the engine change.

Observed result after the fix:

- `700-B`
  - Technically invalid
  - Preview DVRS RX: `799.0-802.0`
  - Preview DVRS TX: `769.0-772.0`
  - Failure: mobile TX outside active mobile TX window `802.0-805.0`
- `700-C`
  - Technically valid
  - Proposed DVRS RX: `804.8875-805.0`
  - Proposed DVRS TX: `774.8875-775.0`
  - No failures
- `800-A1`
  - Technically invalid
  - Failure: mobile TX outside active mobile TX window `806.0-819.0`
- `800-A2`
  - Technically invalid
  - Failure: mobile TX outside active mobile TX window `811.0-824.0`
- `800-B`
  - Technically invalid
  - Failure: mobile TX outside active mobile TX window `806.0-821.0`

- Ordering summary note:
  - `Best preliminary standard plan: 700 MHz In-Band Plan C.`

This matched the user's intended interpretation: `700-C` remained valid by returning the narrow surviving compliant slice instead of failing the whole plan.

## Test Updates

### Assistant
Updated `tests/test_engine.py` to align with the refined specification and the corrected mixed-band implementation.

Changes included:

- Revising mixed-band expectations so `700` plan summaries use the `700` side instead of the `800` side
- Adding a regression test for the user's exact mixed-band scenario to prove that `700-C` returns:
  - DVRS RX: `804.8875-805.0`
  - DVRS TX: `774.8875-775.0`
- Removing outdated expectations that `700-B` should validate with actual `770.0/800.0` DVRS frequencies in a mixed-band scenario

Reason for the `700-B` test adjustment:

- The actual `700-B` pair `TX=770.0`, `RX=800.0` sits only `2.0 MHz` away from the `700` mobile TX block `802.0-803.0`
- That still violates the `3.0 MHz` minimum spacing rule for `700-B`
- Therefore the old test expectation was inconsistent with the corrected plan-specific spacing logic

## Test Execution

### Assistant
Ran the full test suite with `python run_tests.py`.

First run:

- Most tests passed
- Two tests failed because they still encoded the old mixed-band assumptions

After updating those tests, ran `python run_tests.py` again:

- Result: all tests passed
- Final status:
  - `38` tests run
  - `1` skipped
  - `OK`

## Final Report Back to the User

### Assistant
Reported the final planner behavior for the user's sample:

- Valid plan:
  - `700-C`
  - DVRS RX: `804.8875-805.0000 MHz`
  - DVRS TX: `774.8875-775.0000 MHz`
- Invalid plans:
  - `700-B`
  - `800-A1`
  - `800-A2`
  - `800-B`

Reason the others stayed invalid:

- They still violate their active mobile TX window rules

The assistant also noted that the ordering summary now correctly prefers `700 MHz In-Band Plan C`.

## Git Commit

### User
Asked for the changes to be committed.

### Assistant
Checked the working tree and confirmed only the three task-related files were modified:

- `dvrs-web-app-design.md`
- `dvrs_tool/engine.py`
- `tests/test_engine.py`

Attempted to stage them with `git add`, but the command failed due to:

- `Unable to create ... .git/index.lock: Permission denied`

Retried staging with elevated permissions, which succeeded, then created the commit:

- Commit hash: `f717cb1`
- Commit message: `Refine DVRS sub-range planning for mixed systems`

## Files Mentioned or Modified

### Modified
- `dvrs-web-app-design.md`
- `dvrs_tool/engine.py`
- `tests/test_engine.py`

### Inspected During the Thread
- `README.md`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/api.py`
- `dvrs_tool/cli.py`
- `run_tests.py`

## Final Technical Outcome

The thread established the following final behavior:

- In mixed `700/800` evaluation, candidate plans use their own band-specific system ranges
- All plans should return the surviving compliant DVRS sub-range before failing
- The sample mixed-band input now yields a valid `700-C` recommendation instead of rejecting all standard plans
- The behavior is documented in the spec, enforced in the engine, and covered by regression tests
