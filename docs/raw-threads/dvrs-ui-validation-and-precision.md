# Raw Thread: DVRS UI Validation And Precision

## Overview
This thread covered two closely related UI quality improvements:

1. Make evaluation failures more actionable when the backend rejects invalid inputs.
2. Make the post-evaluation system summary preserve the same decimal precision the user entered.

## Conversation

### User
With `mobile_TX_Low` of `799.16875` and `mobile_TX_high` of `804.84375` and `country = United States`, the API returns an error. Please examine this error, and update the UI to provide a more useful explanation of what error occurred.

### Assistant
Started by tracing where the API request was built and where the UI handled failures. The initial investigation searched the repository for frequency, country, and error handling logic, then fell back from `rg` to PowerShell-native file search because `rg.exe` could not be executed in the environment.

The repository scan found:
- Backend files: `dvrs_tool/api.py`, `dvrs_tool/engine.py`, `dvrs_tool/exceptions.py`, `dvrs_tool/models.py`, `dvrs_tool/plan_data.py`
- Frontend files: `dvrs_tool/static/app.js`, `index.html`, `styles.css`
- Tests: `tests/test_engine.py`

Key findings during the first pass:
- The API already returned structured errors for `DVRSBaseError`.
- The engine contained several structured validation and rule-violation paths.
- The frontend error handling in `app.js` collapsed backend errors into a simple message string.

The assistant then read:
- `dvrs_tool/static/app.js`
- `dvrs_tool/api.py`
- `dvrs_tool/engine.py`
- `tests/test_engine.py`

Notable code observations:
- `app.js` threw a generic `Error` using only `error.message` plus a limited details fallback.
- `api.py` handled project exceptions and unexpected exceptions, but not FastAPI `RequestValidationError`.
- `engine.py` already validated mobile TX/RX ranges, positivity, decimal precision, band detection, and plan feasibility.

### User
The user interrupted the previous turn and clarified the real issue:

> I found the error. The Actual DVRS RX High field was set to 0 instead of being blank. Look at the API, calculation engine, and UI, and add a test to ensure that this type of error is evaluated. In the UI, if an optional field contains a numeric value that does not fit any of the possible plans, either return an error that suggests that the user confirm the inputs are correct, or make a suggestion of an alternate message that assists the user in correcting the invalid input.

### Assistant
Refocused the work around the actual root cause:
- `0` in an optional numeric field
- poor UI explanation of the resulting validation failure
- need for backend and test coverage, not just frontend wording

The assistant then reviewed:
- `dvrs_tool/models.py`
- `dvrs_tool/exceptions.py`
- `dvrs_tool/plan_data.py`

This established:
- optional licensed DVRS TX/RX fields existed on `CalculationRequest`
- technical plan windows were defined in `TECHNICAL_PLANS`
- there was no dedicated validation that optional licensed DVRS values had to fit any possible plan window

## Implemented Changes

### 1. API validation handler
The assistant added a FastAPI `RequestValidationError` handler in `dvrs_tool/api.py`.

Behavior introduced:
- converts request-body validation failures into the project’s structured `"status": "error"` response shape
- includes per-field validation details
- adds a special hint for optional numeric fields:
  - “If this optional field is not known, leave it blank instead of entering 0.”

This specifically addresses cases where fields like `actual_licensed_dvrs_rx_high_mhz` are supplied as `0`, which violates the Pydantic `gt=0` constraint before the engine runs.

### 2. Engine-side optional-range validation
The assistant added new validation in `dvrs_tool/engine.py` after band detection:
- `_validate_optional_licensed_ranges`
- `_validate_optional_range_pair`
- `_validate_optional_range_matches_plan`

New engine rules:
- optional licensed DVRS TX/RX ranges must have both low and high values together
- low must be below high
- if supplied, the range must fit within at least one supported plan window for the detected band

New error codes introduced:
- `INCOMPLETE_OPTIONAL_RANGE`
- `INVALID_OPTIONAL_RANGE`
- `OPTIONAL_RANGE_OUTSIDE_SUPPORTED_PLANS`

New corrective messaging emphasized:
- confirm the licensed frequencies are correct
- or clear the optional field / leave it blank until known

### 3. Frontend error messaging
The assistant updated `dvrs_tool/static/app.js` to render backend errors more helpfully.

Changes included:
- mapping field keys to readable labels such as:
  - `Actual DVRS RX High`
  - `Actual DVRS TX`
  - `Mobile TX Low`
- introducing `buildUserFriendlyError(error)`
- including field-level hints and rule-violation messages in the UI
- appending an explicit correction suggestion for invalid optional licensed DVRS fields

As a result, the UI no longer surfaces only a vague generic API failure for these cases.

### 4. Tests
The assistant added two regression tests in `tests/test_engine.py`:

- `test_optional_actual_licensed_range_must_fit_supported_plan_window`
  - verifies that an invalid optional licensed DVRS RX range raises `OPTIONAL_RANGE_OUTSIDE_SUPPORTED_PLANS`

- `test_api_returns_structured_error_for_optional_zero_value`
  - verifies that posting `actual_licensed_dvrs_rx_high_mhz = 0` returns a structured API error with a helpful hint

## Testing And Iteration

### Initial targeted test run
The assistant ran targeted tests:

```text
python -m unittest tests.test_engine.DVRSCalculationEngineTests.test_optional_actual_licensed_range_must_fit_supported_plan_window tests.test_engine.DVRSCalculationEngineTests.test_api_returns_structured_error_for_optional_zero_value tests.test_engine.DVRSCalculationEngineTests.test_cli_run_returns_json_payload_for_valid_request tests.test_engine.DVRSCalculationEngineTests.test_invalid_band_raises_structured_error
```

Result:
- one API test errored because `fastapi.testclient` required `httpx`, which was not installed locally

### Adjustment
The API test was changed to skip cleanly when `fastapi.testclient` or its runtime support was unavailable:
- handled `ImportError`
- handled `RuntimeError` from missing `httpx`

### Broader test run and regression
The assistant then ran:

```text
python -m unittest discover -s tests -p 'test_*.py'
```

This exposed a regression:
- `test_engine_rejects_more_than_five_decimal_places_with_exact_reason` failed
- cause: an edit accidentally displaced the engine’s existing positivity/decimal-place validation loop, making it unreachable

### Fix
The assistant moved the original validation loop back into `_validate_request` and removed the unreachable block from below `_validate_optional_range_matches_plan`.

### Final test result for validation work
The assistant reran:

```text
python -m unittest discover -s tests -p 'test_*.py'
```

Final result:

```text
Ran 20 tests in 0.100s

OK (skipped=1)
```

The skipped test was the API-client regression test in the environment lacking `httpx`.

## File Locations Gathered During The Thread
- `dvrs_tool/api.py:66` for `handle_request_validation_error`
- `dvrs_tool/engine.py:34` for `_validate_optional_licensed_ranges` call site
- `dvrs_tool/engine.py:146` for `_validate_optional_licensed_ranges`
- `dvrs_tool/engine.py:185` for `INCOMPLETE_OPTIONAL_RANGE`
- `dvrs_tool/engine.py:214` for `INVALID_OPTIONAL_RANGE`
- `dvrs_tool/engine.py:260` for `OPTIONAL_RANGE_OUTSIDE_SUPPORTED_PLANS`
- `dvrs_tool/static/app.js:84` for field-label formatting
- `dvrs_tool/static/app.js:101` for `buildUserFriendlyError`
- `tests/test_engine.py:170` for optional-range validation test
- `tests/test_engine.py:315` for API zero-value test

## Follow-up Request In The Same Thread

### User
The post-evaluation system summary should display frequencies to the same number of decimal places as were entered in the input section.

### Assistant
Identified that `app.js` always rendered ranges using:

```javascript
toFixed(4)
```

That meant:
- user-entered five-decimal values were truncated to four decimals
- user-entered trailing zeros could also be lost if only numeric payload values were used

The assistant decided to preserve raw form-input precision rather than infer precision from numeric values.

## Precision-Preservation Implementation

### Frontend change in `dvrs_tool/static/app.js`
Added:
- `latestInputPrecision`
- `decimalPlacesFromInput(value)`
- `captureInputPrecision(formData)`
- updated `formatRange(range, precision = null)`

Changed `buildPayload()` so it records input precision before coercing values to numbers.

Updated `renderSystemSummary(summary)` so:
- Mobile TX uses the original Mobile TX precision
- Mobile RX uses manual Mobile RX precision if present, otherwise falls back to Mobile TX precision
- System RX uses Mobile TX precision
- System TX uses Mobile RX precision when supplied, otherwise Mobile TX precision

The assistant explicitly kept the scope limited:
- only the post-evaluation system summary was changed
- plan cards, ordering summary, legends, and axes retained existing fixed formatting

## Sanity Check
After patching `app.js`, the assistant ran a quick code-level search to verify the new references:

```text
Select-String -Path 'dvrs_tool\static\app.js' -Pattern 'latestInputPrecision|captureInputPrecision|renderSystemSummary|formatRange\('
```

This confirmed the new precision-capture and system-summary rendering hooks were in place.

## Final State
- Optional numeric validation errors are clearer in the API and UI.
- Optional licensed DVRS fields are validated more meaningfully in the engine.
- Regression tests were added for invalid optional values and API body validation.
- The test suite passes with one environment-specific skip.
- The post-evaluation system summary now preserves the number of decimal places entered in the input fields.

