# DVRS Actual Frequency Evaluation Refinement

## 1. Context
This thread refined how the DVRS calculation engine, API wrapper, and web UI handle user-supplied actual DVRS frequencies. The work started from a request to replace four optional "Actual DVRS TX/RX Low/High" inputs with two single-frequency fields and to use those frequencies to narrow plan selection in the UI.

## 2. Problem Statement
The existing flow treated optional DVRS inputs as explicit ranges and validated them too early at the request level. That created two problems:

- The inputs no longer matched the desired UX of entering a single actual DVRS TX and RX frequency.
- The engine could reject requests before returning plan-by-plan failures, which prevented the UI from showing all candidate plans and their errors when no plan fit the supplied DVRS setup.

After the first implementation, a second problem was identified: the exact frequency should be the hard technical pass/fail check, while the earlier `+/-0.5 MHz` expansion should only be advisory when exact spacing passes but the widened window would not.

## 3. Key Decisions
- Decision: Replace the four DVRS low/high inputs with `actual_dvrs_tx_mhz` and `actual_dvrs_rx_mhz`.
  - Rationale: The user wanted the engine and API to accept a single actual DVRS TX and RX frequency instead of separate range endpoints.
  - Alternatives considered (if any): Backward-compatible aliases were kept in the API model for older request payloads, but the canonical schema was changed to single-frequency fields.

- Decision: Move DVRS-frequency fit checks out of request-level validation and into per-plan evaluation.
  - Rationale: This allows the system to return all plans with specific failure reasons instead of rejecting the whole request when no standard plan fits.
  - Alternatives considered (if any): The abandoned approach was the earlier request-level validation that required the optional DVRS values to fit some supported plan window before any results were returned.

- Decision: When actual DVRS frequencies are supplied, filter the UI to only technically valid plans; if none are valid, show all plans plus their errors.
  - Rationale: This matches the planner behavior requested by the user while still preserving diagnostic visibility when the supplied DVRS setup does not fit any standard plan.
  - Alternatives considered (if any): Always showing all plans was rejected because it did not narrow the UI to the usable configurations when an actual setup was known.

- Decision: Add a quote-summary recommendation to consult a Motorola Presale Engineer when actual DVRS frequencies are provided and no standard plan fits.
  - Rationale: The user explicitly requested this fallback guidance for no-fit scenarios.
  - Alternatives considered (if any): None discussed.

- Decision: Use exact supplied DVRS frequencies as the hard technical validation point; treat `+/-0.5 MHz` as advisory only.
  - Rationale: The user clarified that if spacing works with the exact frequency, the plan should remain technically valid even if a widened advisory window would fail.
  - Alternatives considered (if any): The abandoned approach was the first iteration that forced a `+/-0.5 MHz` DVRS TX/RX range and could invalidate plans that only failed after widening.

- Decision: When exact-frequency validation passes but the advisory `+/-0.5 MHz` check would reduce spacing below the normal margin, keep the plan valid and add explanatory notes with the actual spacing achieved.
  - Rationale: This preserves the user's requested exact-frequency behavior while still surfacing the tighter margin as engineering context.
  - Alternatives considered (if any): Hard-failing on the widened window was explicitly removed.

## 4. Implementation Summary
- Updated the request model to use `actual_dvrs_tx_mhz` and `actual_dvrs_rx_mhz`.
- Updated the FastAPI request schema and validation hints to reflect the new single-frequency fields, while preserving compatibility aliases for legacy field names.
- Updated the CLI to expose `--dvrs-tx` and `--dvrs-rx`.
- Reworked the engine so actual DVRS frequencies are validated per plan instead of during top-level request validation.
- Added logic to:
  - confirm each supplied actual DVRS frequency falls inside the computed plan range,
  - evaluate technical validity against the exact supplied DVRS frequency,
  - optionally compute an advisory `+/-0.5 MHz` spacing note without making it a hard requirement.
- Updated the ordering summary so no-fit scenarios with supplied DVRS frequencies add a Motorola Presale Engineer recommendation.
- Updated the web UI to:
  - rename the form inputs to `DVRS TX` and `DVRS RX`,
  - send the new payload shape,
  - show only working cards when actual DVRS frequencies are provided,
  - fall back to all cards with failure reasons when no plan fits.
- Expanded unit coverage for:
  - actual-frequency interoperability selection,
  - no-fit fallback behavior,
  - exact-frequency-valid / advisory-window-fails behavior,
  - API validation for optional zero values,
  - CLI help text changes.

## 5. Challenges & Iterations
- The first implementation forced supplied DVRS frequencies into `+/-0.5 MHz` ranges and used those widened ranges as hard constraints. That satisfied the original reading of the request but was later refined after the user clarified that exact-frequency spacing should control validity.
- Early engine edits had to be applied carefully because the repository worktree already contained unrelated modifications in several of the same files.
- Some initial test fixtures assumed that certain interoperability examples would remain valid under the widened-window model. Once the exact/advisory distinction was introduced, the fixtures were revised to match the real spacing boundaries encoded by the engine.
- A specific regression test had to be discovered by probing plan boundaries until a real exact-pass / advisory-fail case was found. The final fixture used 800 MHz Plan B at the exact spacing threshold.

## 6. Final Outcome
The final implementation accepts single actual DVRS TX/RX frequencies throughout the request path, evaluates plan fit against the exact supplied frequencies, and narrows the UI to technically valid plans when possible. If no plan fits, the UI still shows all candidate plans with their errors and the ordering summary recommends consulting a Motorola Presale Engineer. Advisory `+/-0.5 MHz` spacing concerns are now reported in plan notes rather than causing technical failure when the exact frequency itself is valid.

## 7. Open Questions / Follow-ups
- The API still accepts legacy aliases for older DVRS input field names; the team may want to decide later whether to keep or remove that compatibility path.
- The UI currently renders exact DVRS frequencies through the same range formatter used elsewhere, which effectively displays point ranges. A future UI pass could decide whether to present these as single values instead.
- If PDF output should explicitly distinguish exact DVRS frequencies from advisory windows, that was not changed in this thread and may be worth revisiting.

## 8. Affected Files / Components
- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/cli.py`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `tests/test_engine.py`
- `docs/dev-log.md`
