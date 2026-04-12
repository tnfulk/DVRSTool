# Raw Thread: DVRS 700/800 Interoperability And Visualization Refinement

## Overview
This thread began with investigation of why a 700 MHz Plan C scenario was being marked technically invalid, moved into implementation of 700/800 interoperability support in the calculation engine, then shifted into several rounds of cleanup for warnings, notes, and frontend visualization behavior. It ended with a request to convert the thread into reusable project documentation.

## Conversation

### User
Asked to look at 700 MHz Plan C and explain why a U.S. mobile TX range of `799.16875-804.84375` with DVRS TX `853.0125` and RX `808.0125` was being shown as technically invalid even though it should be valid.

### Assistant
Investigated the repository and traced the relevant logic through:
- `dvrs_tool/plan_data.py`
- `dvrs_tool/engine.py`
- `tests/test_engine.py`
- `dvrs_tool/static/app.js`

Key findings:
- The engine detects `799.16875-804.84375` as a `700 MHz` system from the mobile TX range alone.
- Once detected as `700 MHz`, only the native 700 MHz plans are evaluated.
- Native `700-C` was hard-coded with:
  - DVRS RX window `799.0-805.0`
  - DVRS TX window `769.0-775.0`
  - `30 MHz` `tx_below_rx` pairing
- The engine computed technical validity from the mobile TX range and plan windows, not from the entered optional licensed DVRS channels.
- With `700-C`, the required separation forced DVRS RX above `807.84375`, which is outside the hard-coded native `700-C` RX window.
- Optional licensed DVRS input also had a separate limitation: equal low/high values were rejected as invalid optional ranges.

The assistant explained that the engine was internally consistent with its current native-only rules, but those rules did not support the user’s intended 700/800 interoperability interpretation.

### User
Requested an update so all 700 MHz plans allow 700/800 interoperability, and all 800 MHz plans support 700 MHz interoperability as well.

### Assistant
Implemented interoperability support across the planning engine.

Changes made:
- Added native-plus-interop evaluation behavior per plan in `dvrs_tool/engine.py`
- Used `replace(plan, ...)` to create interoperability variants rather than adding a new model type
- For 700 MHz plans, added an interoperability variant with:
  - DVRS RX window `806.0-824.0`
  - DVRS TX window `851.0-869.0`
  - `45 MHz` `tx_above_rx` pairing
- For 800 MHz plans, added an interoperability variant with:
  - DVRS RX window `799.0-805.0`
  - DVRS TX window `769.0-775.0`
  - `30 MHz` `tx_below_rx` pairing
- Kept interop variants conservative by capping passband to `1.0 MHz`
- Updated optional licensed range validation so it checks both native and interoperability windows
- Changed optional licensed range validation so `low == high` is allowed for single-channel values
- Added plan-result selection logic that prefers a valid interoperability result when optional licensed DVRS values match that layout

Regulatory updates in `dvrs_tool/plan_data.py`:
- Added explicit coordination-required outcomes for U.S. and Canadian 700/800 interoperability layouts

Tests added and updated in `tests/test_engine.py`:
- Verified a wide 700 MHz mobile TX block can now produce a valid `700-C` interoperability result
- Verified an `800-C` plan can prefer the 700 MHz interoperability path when optional licensed channels match that path
- Verified single-channel optional licensed DVRS inputs are allowed and work with interop windows

Verification:
- `pytest` was not installed, so `python run_tests.py` was used
- One legacy test failed because interoperability made a formerly invalid case valid
- The failing test was replaced with another case that still exercised the exact no-solution failure path
- Final result: `python run_tests.py` passed

### User
Clarified that mobile system TX ranges will almost always be wider than the DVRS passband, so that warning is not relevant. Also asked to remove references to the exact band windows from the ordering guide.

### Assistant
Updated the engine and plan notes accordingly.

Changes made:
- Removed the warning that the mobile system TX range is wider than the DVRS passband
- Removed illustrative ordering-guide window comparison warnings from plan evaluation
- Reworded no-solution failures to say:
  - “No contiguous DVRS RX window satisfies this plan’s spacing and frequency constraints”
  instead of referencing “ordering-guide constraints”
- Rewrote 700/800 plan notes in `dvrs_tool/plan_data.py` from “Exact windows...” style wording to generic “Supports the standard ... layout” wording

Tests updated:
- Replaced warning-content assertions with assertions that no warning is emitted in the wide-mobile case
- Added coverage that no failure reason mentions “ordering-guide”

Verification:
- `python run_tests.py` passed

### User
Requested visualization changes:
- Put all four components (`Mobile TX`, `System TX`, `DVRS RX`, `DVRS TX`) visually into a common line
- Include more granular labels on the visualization for frequencies
- Retain the existing color coding scheme

### Assistant
Refactored the frontend visualization.

Files examined:
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`

Changes made:
- Reworked the visualization into a common-axis structure
- Added shared-axis tick generation with more granular labels
- Kept color coding for:
  - Mobile TX: blue
  - System TX: green
  - DVRS RX: gold
  - DVRS TX: red
- Introduced a lane-based shared-axis view with lane labels and per-range start/end labels

Verification:
- `python run_tests.py` passed

### User
Requested another refinement:
- Eliminate the lanes completely
- Keep a single axis for the chart
- Keep a reasonably granular scale with frequency labels

### Assistant
Simplified the visualization again.

Changes made:
- Removed lane-specific visualization structure
- Converted the chart into a true single-axis overlay
- Left legend and color coding intact
- Rendered the bars as overlays sharing one common axis line
- Kept axis tick labels on the chart

Verification:
- `python run_tests.py` passed

### User
Requested a refinement for label collision issues.

### Assistant
Implemented lightweight collision handling for in-chart labels.

Changes made:
- Added helper functions in `app.js` for:
  - estimating label width in percent
  - assigning stacked collision levels
  - computing label layout for top/bottom groups
- Updated CSS to use `--label-level` variables so labels could stack vertically when crowded
- Increased chart height to prevent clipping in dense cases

Verification:
- `python run_tests.py` passed

### User
Requested another simplification:
- Eliminate the in-chart labels
- Move the axis labels below the visualization

### Assistant
Removed the in-chart labels entirely and changed the chart to use only:
- the shared axis line
- the colored bars
- tick marks
- frequency labels below the chart

Changes made:
- Deleted in-chart overlay labels and range labels from `app.js`
- Removed associated collision-avoidance code and CSS
- Reused the axis label rendering below the chart as `viz-axis-foot`

Verification:
- Checked for leftover frontend selectors related to in-chart labels
- `python run_tests.py` passed

### User
Requested conversion of the full thread into project documentation:
- Create a dev-history summary markdown file
- Create a cleaned raw-thread markdown file
- Append a 3-5 sentence summary to `docs/dev-log.md`

### Assistant
Reviewed the existing docs structure:
- `docs/dev-history/`
- `docs/raw-threads/`
- `docs/dev-log.md`

Observed existing naming patterns and created a new thread slug based on the topic:
- `dvrs-700-800-interop-and-visualization-refinement`

Prepared:
- `docs/dev-history/dvrs-700-800-interop-and-visualization-refinement-summary.md`
- `docs/raw-threads/dvrs-700-800-interop-and-visualization-refinement.md`
- appended summary entry in `docs/dev-log.md`

## Files Mentioned Or Modified
- `dvrs_tool/engine.py`
- `dvrs_tool/plan_data.py`
- `tests/test_engine.py`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `docs/dev-log.md`
- `docs/dev-history/dvrs-700-800-interop-and-visualization-refinement-summary.md`
- `docs/raw-threads/dvrs-700-800-interop-and-visualization-refinement.md`
