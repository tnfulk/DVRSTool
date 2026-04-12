# DVRS System-Frequency UI And Single-Band Submodel Evaluation

## 1. Context
This thread extended the DVRS planner so standard plans can be evaluated against single-band system inputs in addition to mixed 700/800 systems. The work started in the rules engine and then moved up into the web UI and product specification so users can enter only the system frequencies they actually have.

## 2. Problem Statement
The tool previously treated several standard plans as if they only applied to one system-band scenario, which blocked valid evaluations for customers who had only 700 MHz or only 800 MHz system frequencies. The UI also framed the input model around internal mobile-TX terminology and a limited `System Bands` selector, which did not match how planners think about customer systems or how the engine was evolving. In addition, the design documentation needed to explicitly state that plan names are based on the DVRS band, not the system band.

## 3. Key Decisions
- Decision: Add internal single-band and mixed-system submodels to parent plans, but keep only the parent plans visible in the UI.
  - Rationale: This preserves a clean user-facing plan list while allowing the engine to support more realistic deployment scenarios.
  - Alternatives considered (if any): Exposing subplans directly in the UI was discussed conceptually and rejected in favor of keeping the interface simpler.

- Decision: Support `700-B`, `700-C`, `800-A1`, `800-A2`, and `800-B` as parent plans that can internally evaluate against multiple system-frequency models.
  - Rationale: These were the plans identified as requiring additional single-band behavior while still participating in mixed-system evaluation.
  - Alternatives considered (if any): Leaving them mixed-only or band-native-only would have preserved simpler logic but failed the user’s example scenarios.

- Decision: Introduce an explicit `700 only` system-frequency configuration alongside `800 only` and `700 and 800`.
  - Rationale: The UI and API needed a direct way to express the user’s actual system inventory rather than forcing inference from partial inputs or mixed-mode defaults.
  - Alternatives considered (if any): Relying only on auto-detection for single-band entries was not sufficient once the UI needed to clearly communicate the user’s intent.

- Decision: Update the product spec to define system-frequency input modes and explicitly document that plan naming is based on the DVRS band, not the system band.
  - Rationale: This was a core conceptual rule behind the new evaluation paths and needed to be captured in the charter/spec rather than left implicit in code.
  - Alternatives considered (if any): Keeping the rule as implementation-only behavior would have made future maintenance and UI copy inconsistent.

- Decision: Reframe the web UI around “system frequencies the customer already has.”
  - Rationale: This matches the user’s requested mental model and reduces confusion around internal `mobile_tx_*` field names that remain in the backend model.
  - Alternatives considered (if any): Keeping the old field labels and simply adding more logic behind the scenes would have made the behavior harder to understand.

## 4. Implementation Summary
The engine was updated so `700-B` and `700-C` each evaluate `700-system-only`, `800-system-only`, and `700-and-800-system` submodels while returning a single parent result. The same pattern was then applied to `800-A1`, `800-A2`, and `800-B`, including candidate-plan expansion for the user-specified single-band scenarios. The backend added an explicit `SystemBandHint.BAND_700_ONLY` value and corresponding candidate-plan selection rules for `700 only`, `800 only`, and mixed-system input.

The UI was then reworked so the user chooses a `System Frequency Configuration` of `Only 700 MHz system frequencies`, `Only 800 MHz system frequencies`, or `Both 700 MHz and 800 MHz system frequencies`. The form now hides or shows only the relevant frequency inputs, relabels single-band fields dynamically, clears stale values when the configuration changes, and uses “system frequency” wording throughout. The result summaries and visualizations were also updated to refer to `System RX` and `System TX` rather than exposing the internal mobile-TX naming.

The product specification in `dvrs-web-app-design.md` was updated to document the new input model, the required plan mappings for each configuration, the parent-plan/submodel behavior, and the DVRS-band naming rule. Regression coverage in `tests/test_engine.py` was expanded to cover explicit `700 only` behavior, the expanded parent-plan candidate sets, and the single-band pass cases for the newly supported parent plans.

## 5. Challenges & Iterations
The first phase of the thread focused on engine support for `700-B` and `700-C`, including a failed initial test run that revealed incorrect expectations and one real selection issue around system-model mismatch handling. The implementation had to be refined so inapplicable submodels would not drive actual-DVRS matching or parent-plan result selection. When the same pattern was extended to `800-A1`, `800-A2`, and `800-B`, the first analog mapping for `800-A1`’s 700-only submodel turned out to be too restrictive and had to be remapped after inspecting actual evaluation behavior.

On the UI side, the backend still only recognized `800 only` and `700 and 800` at the start of the work, so the explicit `700 only` mode had to be added before the form could be updated. Another refinement was needed to avoid leaking internal “submodel mirrors” implementation notes into user-visible plan notes; those messages were rewritten to simple user-facing statements like “Evaluated using the 700 MHz-only system model.”

## 6. Final Outcome
The final solution supports the requested system-frequency-driven workflow across the engine, spec, and UI. Users can now explicitly enter only 700 MHz system frequencies, only 800 MHz system frequencies, or both, and the planner selects the correct parent plans and internal submodels accordingly. The visible plan list remains at the parent-plan level, while the engine preserves the system ranges from whichever submodel actually passed. The design documentation now explicitly states that band-plan naming is based on the DVRS band rather than the system band.

## 7. Open Questions / Follow-ups
- The backend data model still uses `mobile_tx_*` field names internally even though the UI and spec now speak in terms of system frequencies; a future cleanup could rename or alias those fields more consistently.
- The UI changes were not browser-verified during this thread; a manual UX pass would be useful to confirm field-switching behavior and wording clarity.
- The analog-plan mappings used for the single-band submodels were derived iteratively from the requested examples and engine behavior; they may merit explicit documentation in plan data if they continue to expand.

## 8. Affected Files / Components
- `dvrs-web-app-design.md`
- `dvrs_tool/models.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `tests/test_engine.py`
- Git commit created during the thread:
  - `Align planner UI with system-frequency input model and add single-band submodel evaluation`
