# UI Error Message Deduplication for 700 MHz Range Validation

## 1. Context
This thread focused on a narrow web UI validation issue in the DVRS planner. The goal was to explain why a single invalid 700 MHz mobile TX range error appeared twice in the browser and to fix the presentation so users only see one clear message.

## 2. Problem Statement
When the user entered a 700 MHz mobile TX low value of `995` and a 700 MHz mobile TX high value of `804`, the UI displayed the same validation sentence twice:

`Lowest 700 MHz mobile TX must be lower than highest 700 MHz mobile TX.`

The problem to solve was whether the duplicate originated in validation logic, API error construction, or frontend rendering, and then remove the duplicate without losing legitimate multi-error reporting.

## 3. Key Decisions
- Decision: Inspect both backend validation code and frontend error formatting before changing behavior.
- Rationale: The duplicate could have come from repeated validation, repeated serialization, or repeated rendering, and changing the wrong layer could hide real errors.
- Alternatives considered (if any): A backend-only change was possible, but was not chosen because the API structure intentionally includes both a top-level error message and detailed rule violations.

- Decision: Keep the backend error payload unchanged and deduplicate repeated fragments in the frontend.
- Rationale: The backend was already providing structured error data consistently, and the duplication was caused by the UI concatenating `error.message` and identical `rule_violations[*].message` values.
- Alternatives considered (if any): Removing `rule_violations` data or suppressing the top-level message in the API response.

- Decision: Deduplicate message parts generically inside `buildUserFriendlyError()`.
- Rationale: A small reusable dedupe helper avoids this bug for this case and for any future repeated message fragments built from the same error object.
- Alternatives considered (if any): Special-casing only the 700 MHz validation message.

## 4. Implementation Summary
The investigation traced the message through:

- `dvrs_tool/engine.py`, where the range validation raises one `InputValidationError`
- `dvrs_tool/api.py`, where error responses preserve both a top-level message and `rule_violations`
- `dvrs_tool/static/app.js`, where `buildUserFriendlyError()` assembled the final text shown in the UI

The actual code change was made in `dvrs_tool/static/app.js`. A local `pushPart()` helper backed by a `Set` was introduced so repeated message fragments are only appended once before the final string is joined and rendered.

## 5. Challenges & Iterations
The first repository search attempt used `rg`, but `rg.exe` could not run in the environment, so the investigation switched to PowerShell `Select-String`. That fallback still surfaced the relevant backend and frontend files quickly. The review also confirmed that the backend validator itself was not raising the same rule twice; the duplication only happened when the UI combined the API's top-level message with the same text from `rule_violations`.

## 6. Final Outcome
The UI now suppresses duplicate error fragments while preserving distinct validation details. For the invalid 700 MHz range example, the user should see the sentence only once instead of twice.

## 7. Open Questions / Follow-ups
- Browser-based verification was not run in this thread, so a quick manual UI check could be useful if the app is already being tested interactively.
- If future UX work revisits error presentation, the team may want to decide whether the UI should continue merging top-level messages and rule violations into one sentence stream or render them as structured bullets.

## 8. Affected Files / Components
- `dvrs_tool/static/app.js`
- `dvrs_tool/engine.py`
- `dvrs_tool/api.py`
- Web UI error rendering path
- Backend validation/error payload inspection path
