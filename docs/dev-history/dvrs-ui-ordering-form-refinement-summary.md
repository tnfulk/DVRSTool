# DVRS UI Ordering Form And Visualization Refinement

## 1. Context
This thread refined the browser-based DVRS planning UI after the initial web interface was already in place. The work focused on improving the ordering form inputs, cleaning up the evaluation presentation, and making the plan visualizations more useful for comparing standard configurations.

## 2. Problem Statement
The existing UI included elements that were not helpful or were misleading for the intended workflow:

- The embedded 800 MHz reference image was not useful in the live planner.
- Frequency input labels did not match the intended system terminology.
- The ordering capture form was missing several fields from the supplemental ordering form.
- Evaluation cards still showed mount-related labels and confidence scoring that were not desired in this workflow.
- The initial visualization treatment did not meet the desired presentation style and required multiple rounds of refinement.
- The browser UI needed to accept frequency inputs with up to five decimal places.
- Optional ordering details were not clearly separated from required planning inputs.

## 3. Key Decisions
- Decision: Remove the 800 MHz frequency plan image from the planner.
  - Rationale: The image was not helping users complete the actual task in this UI.
  - Alternatives considered: Keep the image as a reference, but it was explicitly deemed unhelpful here.

- Decision: Rename `Manual mobile RX` inputs to `System TX Low (MHz)` and `System TX High (MHz)`.
  - Rationale: The planner is being used to capture system-ordering information, so the labels should reflect the terminology users expect.
  - Alternatives considered: Keep the backend field names and only change helper text, but the thread chose explicit label changes instead.

- Decision: Normalize frequency input labels to use `(MHz)` formatting.
  - Rationale: This made the form more consistent and aligned better with ordering-form conventions.
  - Alternatives considered: Leave existing mixed label formatting in place.

- Decision: Add supplemental ordering-form fields to the UI without changing the calculation engine.
  - Rationale: These fields were needed for order capture and export, not for frequency-plan computation.
  - Alternatives considered: Extend engine logic to use those fields, but that was explicitly avoided.

- Decision: Add per-plan visualizations generated from evaluated ranges.
  - Rationale: Users needed a quick way to compare Mobile TX, System TX, DVRS RX, and DVRS TX across standard configurations.
  - Alternatives considered: Keep text-only plan summaries.

- Decision: Remove confidence percentages and mount labels from the evaluation cards.
  - Rationale: The evaluated configurations did not need to be scored, and `VehicleMount` / `Suitcase` were not useful in the UI.
  - Alternatives considered: Keep them as metadata badges, but they were explicitly requested to be removed from the evaluation presentation.

- Decision: Force static-asset refreshes with cache-busting query strings and no-cache headers.
  - Rationale: The source code already reflected the requested UI behavior, but the browser was still presenting stale assets.
  - Alternatives considered: Assume the issue was in the rendering logic; inspection showed caching was the more likely cause.

- Decision: Change the visualization from multi-row tracks to a single shared range view.
  - Rationale: The user wanted one combined comparison view rather than separate row-level tracks.
  - Alternatives considered: Keep the initial row-per-range visualization.

- Decision: Pad the visualization axis and scale bar widths proportionally to true ranges.
  - Rationale: The user wanted the relative range sizes to read correctly while still leaving visual breathing room on both ends of the axis.
  - Alternatives considered: Keep the prior rendering that used tighter edges and a minimum-width bias in JavaScript.

- Decision: Update numeric form inputs to accept values up to five decimal places.
  - Rationale: The UI should match the precision standard already used by the calculation engine.
  - Alternatives considered: Keep four-decimal input stepping.

- Decision: Split the form into required planning inputs and optional ordering details, and convert several free-text fields into constrained dropdowns.
  - Rationale: Required fields needed stronger visual emphasis, while optional order metadata needed a secondary feel and more standardized values.
  - Alternatives considered: Keep a flat form with free-text inputs for radio, control-head, and antenna metadata.

- Decision: Remove `power requirement` and `DVRS/VRX order code` from the UI flow.
  - Rationale: The user explicitly said those fields were not needed.
  - Alternatives considered: Keep them as optional export-only values.

## 4. Implementation Summary
The UI was reworked in several passes:

- Removed the intro image from the planner shell.
- Renamed and normalized frequency input labels.
- Added order-capture fields from the supplemental ordering form, then later narrowed that set based on follow-up feedback.
- Added generated plan visualizations based on evaluated `mobile_tx`, `system_tx`, `proposed_dvrs_rx`, and `proposed_dvrs_tx` ranges.
- Removed confidence percentages and mount-compatibility badges from plan cards.
- Added cache-busting to `app.js` and `styles.css` to prevent stale browser assets from masking UI changes.
- Updated frequency field `step` values to `0.00001`.
- Redesigned the form into visually distinct required and optional sections.
- Converted `Mobile Radio Type`, `Control Head Type`, and `Antenna Type` into dropdowns with fixed allowed values.
- Removed `DVRS/VRX order code` and `Power requirement` from the UI, payload builder, summary rendering, request schema, and related PDF/test usage.

## 5. Challenges & Iterations
- The first visualization design used separate row tracks. That was later replaced with a single shared range view after user feedback.
- After the initial UI change, the user still saw mount labels and missing visualizations. Inspection showed the source code already reflected the requested behavior, so a cache-busting update was added to make sure the browser loaded the latest static assets.
- The user asked why `800-A1`, `800-A2`, and `800-B` looked identical. The explanation was that their backend plan definitions were currently equivalent, so the UI was accurately reflecting the data rather than hiding a rendering bug.
- The ordering fields were initially expanded from the supplemental form, then pared back once the user clarified which metadata was actually useful.

## 6. Final Outcome
The final UI state is a more task-focused DVRS planner:

- Required planning inputs are visually emphasized.
- Optional ordering details are clearly separated.
- Frequency fields support five decimal places.
- The evaluation cards show a single shared range visualization for each configuration.
- Confidence scoring and mount labels are no longer shown in the evaluation cards.
- The ordering metadata uses constrained dropdowns where appropriate.
- Unneeded order-code and power fields were removed from the active UI flow.

## 7. Open Questions / Follow-ups
- `800-A1`, `800-A2`, and `800-B` still render similarly when their backend technical definitions are equivalent. If the ordering guide distinguishes them materially, `dvrs_tool/plan_data.py` should be updated to encode those differences.
- The PDF export still contains labeled lines for order code and power requirement, but they are no longer populated from the UI. That export layout may be worth simplifying later if the ordering form is meant to mirror the live UI more closely.

## 8. Affected Files / Components
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/pdf_export.py`
- `tests/test_engine.py`
- `supplemental-ordering-form-b2bf88f7.pdf`
- `docs/dev-log.md`

