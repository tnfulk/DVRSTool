# Raw Thread: DVRS Standard Plan Selection, Fixed-Range Logic, and UI Workflow Refinement

## Overview
This thread focused on standard plan selection and recommendation behavior for the DVRS planner, especially around:

- 800-only vs 700-only system models
- standard plan matching for `700-A`, `700-B`, `700-C`, `800-A1`, `800-A2`, `800-B`, and `800-C`
- actual DVRS frequency handling
- ordering-guide fixed-range interpretation
- recommendation sub-ranges when overlap exists
- UI behavior for invalid plans and default page state

## Participants
- **User**: Directed product behavior, clarified ordering-guide interpretation, and requested both engine and UI changes.
- **Assistant**: Inspected code, updated the engine/spec/tests/UI, and repeatedly traced edge cases to refine the solution.

## Chronological Transcript

### 1. Starting point: 800-only systems and matching plans

**User**
- Wanted to work on testing standard configuration plans and identifying which plans match systems that only have 800 MHz frequencies, noting that DVRS frequencies may be 700 or 800.

**Assistant**
- Inspected the engine, plan data, tests, and design spec.
- Identified that:
  - explicit `800 only` originally returned the full native 800-family list,
  - actual DVRS frequencies could override that and surface matching 700-family plans.

### 2. Product change: 800-only systems should evaluate `700-A` and `800-C`

**User**
- Clarified that when only 800 MHz channels are provided, even without DVRS channels, the tool should evaluate `700-A` and `800-C`.
- Explained that the distinction is the location of the DVRS channels.

**Assistant**
- Changed `BAND_800_ONLY` plan selection so it returns only `700-A` and `800-C`.
- Updated tests accordingly.
- Verified the test suite.

### 3. Product change: remove `700 only`

**User**
- Explained that based on the ordering guide there are no standard plans that only include 700 MHz system frequencies.
- Requested removal of that option and its logic.

**Assistant**
- Removed `BAND_700_ONLY` from the model and engine logic.
- Removed the `700 only` option from the frontend.
- Added structured unsupported-model handling for auto-detected 700-only system inputs.
- Replaced earlier 700-only tests with unsupported-model tests and updated the rest of the suite.

### 4. Auto-detect should also enforce 800-only behavior

**User**
- Pointed out that a sample like `808-818` mobile TX is clearly an 800-only system and auto-detect should enforce that.

**Assistant**
- Updated auto-detected 800-band evaluation to use the same `700-A` / `800-C` model as explicit `800 only`.
- Added regression coverage for the exact sample.

### 5. Diagnosing `800-C` and incorrect ordering-guide presentation

**User**
- Observed that `800-C` should have `DVRS RX < Mobile TX < DVRS TX < Mobile RX`, but the tool results and visualization did not match that ordering.

**Assistant**
- Traced the issue and found that the engine could choose an interoperability fallback while still labeling the result as `800-C`.
- Proposed correcting that by preventing standard plans from silently switching to a different topology under the same plan ID.

### 6. Team clarification: ordering-guide ranges are fixed

**User**
- Reported a team decision that the frequency ranges in `dvr-lx-ordering-guide-1 (1).pdf` are fixed.
- Requested:
  - reverting the spacing-primary change,
  - making the ordering-guide windows controlling,
  - retaining spacing as a second-step recommendation check,
  - updating the spec.

**Assistant**
- Reworked the engine so fixed ordering-guide ranges became the plan-source-of-truth instead of spacing-generated windows.
- Removed standard-plan interop fallback selection.
- Updated the design spec to say ordering-guide fixed ranges come first and spacing is evaluated afterward.
- Updated tests around `800-A1`, `800-C`, and related scenarios.

### 7. UI rule: invalid plans should not show proposed DVRS channels or visualization

**User**
- Requested that if a plan is technically invalid, the UI should not show proposed DVRS channels or the visualization, but should still show the error.

**Assistant**
- Updated `app.js` so invalid plan cards:
  - hide proposed DVRS TX/RX values,
  - hide the chart,
  - still show failure reasons.
- Kept backend proposal data intact for engine logic and tests.

### 8. UI workflow cleanup: hide results until Evaluate, add Reset

**User**
- Requested that the results area stay hidden until the user clicks `Evaluate Plans`.
- Requested a `Reset` button to clear the tool and return it to default state.

**Assistant**
- Added a `Reset` button.
- Hid the results layout by default.
- Removed auto-submit on page load.
- Added reset behavior to:
  - reset the form,
  - hide results,
  - clear rendered summaries,
  - disable PDF export,
  - restore default date behavior.

### 9. Frontend cache issue

**User**
- Reported that the `Evaluation Complete` banner still appeared and results did not display after clicking `Evaluate Plans`.

**Assistant**
- Determined that browser asset caching was the likely cause:
  - HTML had changed,
  - but the old JS/CSS was still being served from cache.
- Updated asset version querystrings in `index.html`.

### 10. Status banner refinement

**User**
- Requested that the `Evaluation Complete` banner not appear by default.
- Asked to use that status space for core warnings/errors, such as needing Motorola Presales Engineering.
- Requested non-green styling for error states.

**Assistant**
- Removed the persistent green success-state usage.
- Kept the status area hidden until an evaluation is requested.
- Added warning handling for serious ordering-summary notes like:
  - no technically valid standard plan,
  - consult Motorola Presale Engineer.
- Added a yellow warning style distinct from green success and red error.

### 11. Tracing `800-C` validity with actual DVRS frequencies

**User**
- Asked about a case with:
  - mobile TX `811-818`
  - DVRS RX/TX `807/852`
- Believed `800-C` should be valid and asked why the tool seemed to say otherwise.

**Assistant**
- Traced the exact input through the engine.
- Found that the engine actually marked both `800-A2` and `800-C` as technically valid.
- Explained that the apparent rejection was likely due to ordering-summary tie-breaking:
  - multiple plans matched,
  - `800-A2` was encountered first in plan order,
  - the ordering summary selected `800-A2` as the “best preliminary standard plan.”

### 12. Tracing inconsistency: `800-C` invalid without actual DVRS, valid with actual DVRS

**User**
- Removed the specified DVRS channels and noticed the tool then said `800-C` was invalid because mobile TX to DVRS RX spacing was below the requirement.
- Pointed out that this felt wrong because specifying `807/852` made `800-C` validate.

**Assistant**
- Traced both cases.
- Explained the inconsistency:
  - without actual DVRS, the engine validated the full fixed plan block,
  - with actual DVRS, it validated the exact specified point.
- Identified the product question:
  - should fixed-range validity require the whole range to clear spacing,
  - or just at least one valid channel inside the range?

### 13. Product decision: use “at least one valid channel in the range”

**User**
- Chose the second option.
- Requested a rewrite of the logic for all plans and an update to the spec so the tool validates whether at least one channel in the range is valid.

**Assistant**
- Updated the engine so fixed-range plans are technically valid when at least one paired channel inside the published fixed range satisfies the rules.
- Updated the spec to match.
- Updated tests, especially for `800-C`.
- Verified that the `811-818` overlap case now kept `800-C` valid both with and without actual DVRS frequencies.

### 14. Product refinement: recommended ranges themselves must satisfy separation

**User**
- Added one more rule:
  - if there is overlap between the ranges, the recommended DVRS channel ranges themselves must meet the required separation for the selected plan.

**Assistant**
- Identified that the previous “at least one valid channel exists somewhere in the fixed range” logic was not enough for recommendations.
- Reworked the engine again so fixed-range plans now return the feasible sub-range inside the published plan boundary.
- This preserved:
  - published plan boundaries as the allowed recommendation space,
  - but changed the displayed/recommended DVRS ranges to a spacing-compliant subset.
- Example traced and verified:
  - For mobile TX `811-818` with no actual DVRS, `800-C` now recommends:
    - DVRS RX `806.0-808.0`
    - DVRS TX `851.0-853.0`
  - With actual DVRS `807/852`, `800-C` still validates and returns the exact entered pair.
- Updated the spec again so it now states:
  - fixed ordering-guide ranges define the recommendation boundary,
  - returned proposed ranges must be spacing-compliant subsets when overlap exists.

## Final Technical State

### Standard plan selection
- `700 only` is not supported.
- `800 only` systems return `700-A` and `800-C`.
- Auto-detected 800 systems use the same two-plan model.

### Standard plan identity
- Standard plans no longer silently switch to hidden interop topologies under the same plan label.

### Fixed-range behavior
- Ordering-guide fixed ranges define plan boundaries.
- A fixed-range plan is technically valid when at least one paired channel inside the range satisfies the rules.
- The returned recommended DVRS ranges are now the feasible spacing-compliant sub-range inside that plan boundary.

### Actual DVRS behavior
- If actual DVRS TX/RX is entered, exact entered frequencies still override the recommended proposal during validation.

### UI behavior
- Results are hidden until the user clicks `Evaluate plans`.
- `Reset` restores the default form state and clears results.
- Invalid plans hide proposed DVRS ranges and charts, but still show failure reasons.
- The status banner is hidden by default and now used primarily for meaningful warnings/errors or transient evaluation/export status.
- Cache-busting version strings in `index.html` were updated after frontend behavior changes.

## Files Mentioned or Modified During the Thread
- `dvrs_tool/engine.py`
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `tests/test_engine.py`
- `dvrs-web-app-design.md`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/styles.css`
- `docs/dev-log.md`

