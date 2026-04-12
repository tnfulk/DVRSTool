# DVRS 800 A1 and A2 Guard-Band Update

## 1. Context
This thread focused on the 800 MHz mixed-system plan definitions, specifically whether the encoded `800-A1` spacing rules matched the intended ordering-guide interpretation. The work started as a review of the existing spacing behavior and ended with a targeted rule update plus tests and a git commit.

## 2. Problem Statement
The existing engine encoded `800-A1` and `800-A2` with `2.5 MHz` guard bands. The user clarified that for these plans the deterministic `30 MHz` and `45 MHz` pairings should remain where they already were in the engine, but the plan-specific guard bands for both `800-A1` and `800-A2` should be `5 MHz` while preserving the ordering-guide frequency ranges and the `3 MHz` maximum DVRS passband.

## 3. Key Decisions
- Decision: Treat the `30 MHz` 700-side pairing, the `45 MHz` 800 mobile TX/RX pairing, and the `45 MHz` DVRS RX/TX pairing as deterministic outputs rather than plan-specific spacing rules.
  - Rationale: The user explicitly clarified that those relationships come from the regulatory framework and should stay in the existing deterministic-pairing logic.
  - Alternatives considered: Folding those relationships into the per-plan guard-band logic.
- Decision: Keep the ordering-guide windows for `800-A1` and `800-A2` unchanged while only raising their guard bands to `5 MHz`.
  - Rationale: The user wanted the encoded plan windows preserved and only the spacing interpretation corrected.
  - Alternatives considered: Redefining the fixed or active plan windows in addition to the guard band.
- Decision: Update tests to pin the new `5 MHz` rule and adjust A1 sample frequencies that were no longer spacing-compliant.
  - Rationale: Some prior A1 test values only satisfied the older `2.5 MHz` requirement, so they needed to move to remain valid under the corrected rule.
  - Alternatives considered: Leaving tests untouched and accepting failures, or weakening test coverage for exact spacing-sensitive cases.
- Decision: Commit the changes immediately after verification using the message `modified 800A1 and 800A2 to use 5MHz guard band`.
  - Rationale: The user explicitly requested a commit after the rule updates were complete and validated.
  - Alternatives considered: Leaving the changes uncommitted.

## 4. Implementation Summary
The assistant first compared the user's intended `800-A1` layout with the current engine behavior and documented that the deterministic pairings were already modeled separately in the engine, but the plan itself still used `2.5 MHz` spacing. The assistant then updated `dvrs_tool/plan_data.py` so `800-A1` used `5.0 MHz` minimum separation from both mobile TX and mobile RX while retaining its existing ordering-guide windows and `3.0 MHz` max passband.

Because the tighter spacing invalidated one previous A1 sample pair, the assistant updated `tests/test_engine.py` so the exact-frequency A1 cases used a DVRS pair that still met the new guard band. A second pass then applied the same `5.0 MHz` spacing update to `800-A2` and expanded the dataset-oriented test coverage so both A1 and A2 now explicitly assert the corrected guard-band values.

## 5. Challenges & Iterations
The main refinement was conceptual rather than structural. The user clarified that deterministic cross-band and paired-frequency relationships should remain outside the plan-specific logic, which meant only the guard-band fields needed to change rather than the engine's pairing framework.

There was also a test-data iteration for `800-A1`. A previously valid exact DVRS pair no longer satisfied the tighter `5 MHz` requirement, so the assistant replaced it with a spacing-compliant pair instead of changing the preserved ordering-guide windows.

The commit step had a small workflow hiccup because `git add` initially failed inside the sandbox with an `index.lock` permission error, and the first escalated `git commit` ran in parallel before staging had completed. The assistant then retried in sequence, confirmed the staged files, and completed the requested commit successfully.

## 6. Final Outcome
`800-A1` and `800-A2` now both use `5.0 MHz` guard bands on the mobile TX and mobile RX sides. Their ordering-guide windows and `3.0 MHz` maximum DVRS passband remain unchanged, the spacing-sensitive tests were updated accordingly, the full test suite passed, and the work was committed on `master` with the requested message.

## 7. Open Questions / Follow-ups
- The thread did not request similar reevaluation of `800-B` or `800-C`, so their spacing values remain as previously encoded.
- The conceptual distinction between deterministic pairing rules and plan-specific guard bands is now clearer in thread history, but future engineers may still want to document that separation more explicitly in product or technical design docs.

## 8. Affected Files / Components
- `dvrs_tool/plan_data.py`
- `tests/test_engine.py`
- Git repository state on `master`

