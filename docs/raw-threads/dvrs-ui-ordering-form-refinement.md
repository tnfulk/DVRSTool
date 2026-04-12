# DVRS UI Ordering Form And Visualization Refinement

## Overview
This thread focused on refining the existing DVRS planner UI. The work started with label cleanup and removal of an unhelpful reference image, expanded into adding ordering-form capture fields, then evolved into several rounds of evaluation-card visualization changes, precision updates, and final form-UX restructuring.

## Conversation

### User
Requested a UI update with the following requirements:

- Remove the 800 MHz Frequency Plan image.
- Rename `Manual Mobile RX low MHz` to `System TX Low (MHz)`.
- Rename `Manual Mobile RX high MHz` to `System TX High (MHz)`.
- Normalize other input-area frequency labels to use `(MHz)`.
- Review the supplemental ordering guide for any additional useful input fields and add them to the UI.
- Do not change the calculation engine.
- For each standard configuration, add a visualization showing Mobile TX, System TX, DVRS RX, and DVRS TX after evaluation.
- The visualization should be consistent with ordering-guide samples but uniquely generated and labeled for each evaluated standard configuration.
- Evaluated configurations do not need to be scored.
- Remove `Vehicle Mount` and `Suitcase` references from the evaluation section.

### Assistant
Inspected the repository and found:

- Frontend files in `dvrs_tool/static/`
- Backend request/data models in `dvrs_tool/models.py` and `dvrs_tool/api.py`
- PDF export in `dvrs_tool/pdf_export.py`
- A supplemental ordering PDF: `supplemental-ordering-form-b2bf88f7.pdf`

The assistant attempted to use `rg`, but it failed in this environment, so PowerShell-native file discovery and search were used instead.

### Assistant
Read key frontend files:

- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`

The initial UI state included:

- An embedded `800mhz-frequency-plans.png` image in the intro section
- Frequency inputs using labels such as `Mobile TX low MHz` and `Manual mobile RX low MHz`
- No evaluation visualizations
- Plan cards showing confidence percentages and mount badges

### Assistant
Extracted text from `supplemental-ordering-form-b2bf88f7.pdf` with `pypdf`. The form contained:

- Agency name
- Date
- DVRS/VRX order code
- Configuration selection
- Power requirement
- DVR/VRX frequencies
- Trunked/system frequencies
- Mobile radio type
- Control head type
- MSU antenna type
- Special notes

### Assistant
Implemented the first round of changes:

- Removed the 800 MHz image from the intro.
- Updated frequency labels:
  - `Mobile TX Low (MHz)`
  - `Mobile TX High (MHz)`
  - `System TX Low (MHz)`
  - `System TX High (MHz)`
  - `Actual DVRS TX/RX ... (MHz)`
- Added new optional order-capture fields:
  - `agency_name`
  - `quote_date`
  - `dvrs_order_code`
  - `power_requirement`
  - `mobile_radio_type`
  - `control_head_type`
  - `msu_antenna_type`
- Extended the request model and FastAPI schema so those values could be accepted without affecting the engine.
- Updated the ordering-summary PDF to populate those fields.
- Added summary rendering for those values in the UI.
- Added a per-plan visualization block using generated frequency ranges.
- Removed confidence percentages from plan cards.
- Removed mount badges from evaluation cards.

### Assistant
Ran tests. The initial `python -m unittest -v` run discovered no tests, so the assistant reran with explicit discovery:

`python -m unittest discover -s tests -v`

This passed.

### User
Reported that the UI was still missing the visualizations and was still showing `Vehiclemount` and `Suitcase` labels.

### Assistant
Re-inspected the static files and confirmed that:

- The current `app.js` source already contained visualization rendering.
- The current `app.js` source no longer rendered mount badges.

This suggested the likely issue was stale static assets in the browser rather than missing source changes.

### Assistant
Added cache-busting and anti-cache updates to `dvrs_tool/static/index.html`:

- Added `Cache-Control`, `Pragma`, and `Expires` meta tags.
- Changed:
  - `styles.css` to `styles.css?v=20260409b`
  - `app.js` to `app.js?v=20260409b`

### User
Requested that the visualization be displayed on a single range view.

### Assistant
Changed the visualization implementation:

- Moved from multiple row-level tracks to one shared range view.
- Rendered a single common axis with stacked bars for:
  - `Mobile TX`
  - `System TX`
  - `DVRS RX`
  - `DVRS TX`
- Added a labeled legend below the shared visualization.

Tests were rerun and passed.

### User
Asked for an explanation of why plans `A1`, `A2`, and `B` all looked the same.

### Assistant
Explained that the current backend plan definitions for `800-A1`, `800-A2`, and `800-B` were technically equivalent in the current data model, so the UI was correctly drawing them identically. The assistant pointed to `dvrs_tool/plan_data.py` as the place where meaningful distinctions would need to be encoded if the ordering guide intended those plans to differ.

### User
Requested that the visualization show truly relative range sizes and that the axis leave extra space to the left and right beyond the defined ranges.

### Assistant
Adjusted the shared range visualization:

- Removed the JavaScript-side minimum-width inflation of bars.
- Added padded axis bounds so the visualization had breathing room on both ends.
- Kept a minimal CSS `min-width: 1px` so very narrow ranges remained visible without distorting layout math.

Tests were rerun and passed.

### User
Requested that input fields accept up to five decimal places because that matched the calculation engine standard.

### Assistant
Updated all frequency inputs in `index.html` from `step="0.0001"` to `step="0.00001"` and verified that all relevant frequency fields used the new precision.

### User
Requested additional form changes:

- Visually highlight required fields.
- Separate optional fields into a distinct section/style.
- Make `Mobile Radio Type` a dropdown with:
  - `APX5500`
  - `APX6500`
  - `APX7500 - Single Band`
  - `APX7500 - Dual Band`
  - `APX8500 - All Band`
- Make `Control Head Type` a dropdown with:
  - `02`
  - `03`
  - `05`
  - `07`
  - `09`
- Make `Antenna Type` a dropdown with:
  - `Single Band`
  - `All Band`
- Remove `power requirement` and `order code` fields.

### Assistant
Applied the final round of UI and data-flow changes:

- Removed `dvrs_order_code` and `power_requirement` from:
  - `dvrs_tool/models.py`
  - `dvrs_tool/api.py`
  - `dvrs_tool/static/app.js`
  - UI ordering-summary rendering
  - test data in `tests/test_engine.py`
- Left the engine logic unchanged.
- Reworked the form in `index.html` into two sections:
  - `Planning Inputs` marked as required
  - `Ordering Details` marked as optional
- Added stronger visual emphasis for required fields in `styles.css`.
- Added softer styling for optional fields.
- Replaced free-text fields with dropdowns:
  - `Mobile Radio Type`
  - `Control Head Type`
  - `Antenna Type`
- Removed the `Power requirement` and `DVRS/VRX order code` controls from the form.
- Updated the static asset version suffix again:
  - `styles.css?v=20260409c`
  - `app.js?v=20260409c`

### Assistant
Ran:

`python -m unittest discover -s tests -v`

Final result for that pass:

- 18 tests run
- 18 tests passed

## Final State Reached In This Thread

- The planner intro no longer includes the 800 MHz reference image.
- Frequency labels use the updated `(MHz)` style and system terminology.
- Frequency inputs accept up to five decimal places.
- Plan cards no longer show confidence percentages or mount labels.
- Each evaluated plan includes a shared-axis visualization comparing Mobile TX, System TX, DVRS RX, and DVRS TX.
- The visualization uses padded axis bounds and proportional widths.
- Required planning inputs are visually emphasized.
- Optional ordering details are separated into a different visual section.
- `Mobile Radio Type`, `Control Head Type`, and `Antenna Type` are dropdown-based.
- `Power requirement` and `DVRS/VRX order code` are removed from the active UI flow.

## Files Mentioned Or Modified

- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/pdf_export.py`
- `tests/test_engine.py`
- `supplemental-ordering-form-b2bf88f7.pdf`
- `dvrs_tool/plan_data.py`

