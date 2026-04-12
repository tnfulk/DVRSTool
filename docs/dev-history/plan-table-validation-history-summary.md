# DVRS Plan Table Reconciliation And Validation Audit

## 1. Context
This thread focused on reconciling the encoded 700 MHz and 800 MHz standard-plan table in the DVRS planner with the intended ordering-guide values and then aligning engine validation behavior with that approved table.

## 2. Problem Statement
The project had drift between the plan data on file, the user-approved plan table, and the engine logic that validated plans. Specific problems included:
- missing explicit `700 RX`, `700 TX`, `800 RX`, and `800 TX` fields in the plan dataset
- incorrect or reversed values in several plan rows
- fixed DVRS ranges that did not match the intended on-file windows
- engine validation still using legacy analog-plan substitutions and stale active-window values instead of the approved table
- risk of accidental future edits to the approved table without clear confirmation

## 3. Key Decisions
- Decision: add explicit per-plan `system_700_rx_range`, `system_700_tx_range`, `system_800_rx_range`, and `system_800_tx_range` fields to `TechnicalPlan`
  - Rationale: the approved table required explicit system-band ranges rather than implicit analog mappings
  - Alternatives considered (if any): continue deriving these ranges from legacy analog-plan substitutions; this was rejected because it caused silent drift from the approved table

- Decision: treat the user-approved plan table as the source of truth and iteratively correct the encoded values to match it
  - Rationale: the thread established the table values by repeated user confirmation
  - Alternatives considered (if any): keep some legacy ordering-guide-derived values; rejected when they conflicted with the approved table

- Decision: add a guard that requires explicit confirmation when the plan table changes
  - Rationale: repeated corrections showed that this data is easy to accidentally drift
  - Alternatives considered (if any): rely on comments or process only; rejected as too weak

- Decision: update active mobile TX/RX validation to prefer explicit `700/800 RX/TX` table ranges before falling back to legacy `active_mobile_*` windows
  - Rationale: direct validation was incorrectly rejecting plans even when the approved table allowed them
  - Alternatives considered (if any): continue using `active_mobile_*` as primary validation fields; rejected because those fields were stale for several cross-band cases

- Decision: remove legacy analog substitutions from cross-band plan evaluation
  - Rationale: those substitutions were still replacing parent-plan DVRS and fixed ranges with other plans, even after the table had been corrected
  - Alternatives considered (if any): keep the analog helpers and patch them piecemeal; rejected in favor of a cleaner cross-band variant builder that preserves the parent plan's approved ranges

## 4. Implementation Summary
The thread added explicit 700/800 system range fields to `TechnicalPlan` and populated them in `plan_data.py` for all core 700/800 plans. The plan table was corrected several times based on user review:
- fixed DVRS ranges were aligned with approved plan windows
- `700-B` and `700-C` DVRS windows and fixed ranges were corrected to their narrower split values
- `700-B` and `700-C` 700-band and 800-band system ranges were corrected
- `800-A1`, `800-A2`, and `800-B` 700-band ranges were corrected
- all `800 RX` and `800 TX` columns were swapped to the intended orientation, then `700-B` and `700-C` were further corrected to use `851.0-869.0` for `800 RX` and `806.0-824.0` for `800 TX`

The engine was then updated so active-window validation uses explicit table ranges first. A broader audit found that cross-band variants still replaced parent-plan DVRS/fixed windows with analog-plan data, so the analog substitution path was removed and replaced with a cross-band variant builder that preserves the parent plan's table-defined behavior while deriving only the placement needed for the selected system model.

Finally, a plan-table guard was added:
- `dvrs_tool/plan_table_guard.py` stores explicit confirmation metadata and an approved table hash
- `tests/test_plan_table_guard.py` fails if the table changes without updating the confirmation record
- a warning comment was added above `TECHNICAL_PLANS` in `plan_data.py`

## 5. Challenges & Iterations
- The first attempt to read the ordering-guide PDF could only recover the note on page 9, not a clean numeric table, so some values were initially inferred from existing engine mappings.
- One edit accidentally applied `800-C` fixed ranges to `800-A2`; this was caught immediately and corrected.
- A later patch accidentally narrowed `700-A` while trying to update `700-B` and `700-C`; the file was re-read and corrected.
- The first engine fix only corrected active-window validation. A second audit revealed that cross-band variant generation was still replacing parent-plan DVRS and fixed ranges with analog-plan values.
- After removing the analog helpers, one regression test still referenced the deleted method and had to be updated to the new cross-band helper.

## 6. Final Outcome
The approved 700/800 plan table is now explicitly encoded in `plan_data.py`, guarded by a confirmation hash, and used by the engine for direct range validation. Cross-band evaluation no longer swaps in other plans' DVRS or fixed windows. The API and UI layers were audited and found to be consumers of engine output rather than independent sources of range interpretation.

## 7. Open Questions / Follow-ups
- Run the full test suite for a broader regression pass beyond the targeted tests executed in this thread.
- Consider whether the legacy `active_mobile_tx_window` and `active_mobile_rx_window` fields should eventually be removed or formally deprecated now that explicit `system_700_*` and `system_800_*` fields drive validation.
- Consider whether the API or UI should surface the approved plan-table fields directly for operator visibility or diagnostics.

## 8. Affected Files / Components
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/plan_table_guard.py`
- `tests/test_engine.py`
- `tests/test_plan_table_guard.py`
- `dvrs_tool/api.py`
- `dvrs_tool/static/app.js`
- `docs/dev-log.md`
- `dvr-lx-ordering-guide-1 (1).pdf`
