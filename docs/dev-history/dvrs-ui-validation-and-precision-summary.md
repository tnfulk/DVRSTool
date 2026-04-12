# DVRS UI Validation Messaging And Precision Preservation

## 1. Context
This thread focused on improving the DVRS web UI experience around failed evaluations and post-evaluation display quality. The work started from a specific user-reported API failure during plan evaluation and ended with both clearer validation/error messaging and more faithful frequency formatting in the system summary.

## 2. Problem Statement
Two related usability issues were addressed:

1. The UI surfaced API failures too generically, making it hard to tell what input was actually invalid.
2. An optional numeric field, `Actual DVRS RX High`, could be set to `0` instead of left blank, causing a validation failure that was not explained well enough for correction.
3. After successful evaluation, the system summary always displayed four decimal places, even when the user entered a different precision in the input form.

## 3. Key Decisions
- Decision: Convert FastAPI request-body validation failures into structured DVRS-style errors.
  - Rationale: The frontend already understood the project’s structured error model better than FastAPI’s default 422 response shape.
  - Alternatives considered: Relying on FastAPI’s default validation payload was implicitly abandoned because it did not provide a consistent, user-oriented explanation path.

- Decision: Add engine-side validation for optional licensed DVRS TX/RX ranges.
  - Rationale: Optional ranges should either be blank or plausibly correspond to at least one supported plan window, otherwise the user likely entered a typo or partial value.
  - Alternatives considered: Only improving the UI text without adding engine validation was not chosen because it would leave unsupported optional values unchecked.

- Decision: Treat optional numeric zero values as a case that needs explicit corrective guidance.
  - Rationale: The user discovered that `0` was being entered where blank was intended, so the message needed to clearly suggest leaving the optional field blank.
  - Alternatives considered: A generic “invalid value” message was deemed insufficient.

- Decision: Preserve submitted input precision for the post-evaluation system summary instead of forcing `toFixed(4)`.
  - Rationale: Users expect the summary to reflect the same precision they entered, especially after the app was expanded to support five-decimal inputs.
  - Alternatives considered: Applying the same precision change across the entire UI was not done in this thread; the change was scoped to the system summary only.

## 4. Implementation Summary
The API layer gained a dedicated `RequestValidationError` handler that returns a structured error payload with field-specific messages and hints for optional numeric fields. The engine gained validation for optional licensed DVRS TX/RX ranges to ensure they are complete, ordered correctly, and fit at least one supported plan window for the detected band. The frontend was updated to translate structured backend errors into more readable, field-labeled corrective messages, including the suggestion to leave optional fields blank instead of entering `0`.

In a later refinement within the same thread, the frontend was also updated to capture decimal precision from the submitted input form and use that precision when rendering the post-evaluation system summary. Mobile TX, Mobile RX, System RX, and System TX in the summary now render using the same number of decimal places as were entered in the corresponding input fields.

## 5. Challenges & Iterations
An early investigation initially focused on the reported `mobile_TX_low` / `mobile_TX_high` values, but the root cause turned out to be an unrelated optional field (`Actual DVRS RX High = 0`). The thread also hit an implementation regression when request-validation edits accidentally displaced the engine’s existing decimal-place validation loop; that regression was caught by the test suite and then corrected. Another environment-specific wrinkle was that the new API regression test depended on `fastapi.testclient`, which in turn required `httpx`; the test was kept but made skippable when that dependency is missing locally.

The precision-preservation request arrived after the validation work was already complete. That required a second UI-only change, and the solution deliberately reused raw form inputs rather than numeric payload values so trailing zeros and entered precision would not be lost before rendering.

## 6. Final Outcome
The final state of the solution is:

- API body-validation failures are returned in a structured project-specific format instead of only FastAPI’s default validation output.
- Optional licensed DVRS TX/RX values are validated more meaningfully, with messages that instruct users to confirm or clear incorrect optional values.
- The frontend displays clearer, field-oriented corrective guidance for invalid inputs, especially optional numeric fields populated with `0`.
- The post-evaluation system summary preserves the precision entered by the user in the input form.
- The Python test suite passes with one environment-dependent API-client test skipped when `httpx` is unavailable.

## 7. Open Questions / Follow-ups
- The precision-preservation change only applies to the post-evaluation system summary. The rest of the UI still uses existing fixed formatting.
- Browser-based UI verification was not documented in-thread after the precision change; only a code-level sanity check was performed.
- If desired, the same “preserve entered precision” behavior could be extended later to plan cards, ordering summary output, and visual axis labels.

## 8. Affected Files / Components
- `dvrs_tool/api.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/static/app.js`
- `tests/test_engine.py`
- DVRS web UI error handling and system summary rendering
- FastAPI request validation path
- Engine validation for optional licensed DVRS ranges

