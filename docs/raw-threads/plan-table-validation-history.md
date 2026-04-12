# Raw Thread: DVRS Plan Table Reconciliation And Validation Audit

## Overview
This thread centered on correcting the encoded 700/800 plan table, reconciling it with user-approved values, fixing engine validation that still relied on legacy analog-plan substitutions, and adding documentation and guardrails so future table edits are intentional.

## Conversation

### User
Asked for each plan's name and the actual frequency ranges on file for that plan.

### Assistant
Inspected the workspace, found the relevant source files, and identified `dvrs_tool/plan_data.py` as the main source of plan definitions. `rg` was unavailable in the environment, so PowerShell-native search was used instead.

### Assistant findings
Read:
- `dvrs_tool/plan_data.py`
- `dvrs_tool/models.py`
- `dvrs_tool/engine.py`

The encoded plans initially contained:
- DVRS RX/TX windows
- active mobile TX/RX windows
- fixed DVRS RX/TX ranges

The assistant returned a first compact listing of all on-file plan ranges.

### User
Asked to check whether the fixed DVRS ranges matched the DVRS windows and to fix them if they were flipped.

### Assistant
Determined that the fixed TX/RX fields were aligned by type, but several values were narrower than the corresponding windows. The assistant updated `plan_data.py` so the fixed ranges matched the intended windows.

### Iteration
An edit accidentally applied `800-C` values to `800-A2`. That mistake was caught during verification and corrected immediately.

### User
Asked for a compact, usable table showing plan name and actual ranges on file.

### Assistant
Returned a table of plan name plus:
- DVRS RX window
- DVRS TX window
- active mobile TX
- active mobile RX
- fixed DVRS RX
- fixed DVRS TX

### User
Clarified that each plan should explicitly have:
- DVRS RX
- DVRS TX
- 700 RX
- 700 TX
- 800 RX
- 800 TX
- Fixed DVRS RX
- Fixed DVRS TX

Exceptions:
- `700-A` only needs DVRS RX/TX, 800 RX/TX, and fixed DVRS RX/TX
- `800-C` only needs DVRS RX/TX, 800 RX/TX, and fixed DVRS RX/TX

The user asked that missing data be filled using pages 8 and 9 of `dvr-lx-ordering-guide-1 (1).pdf` if possible, and asked to see all changed fields for confirmation.

### Assistant
Tried to extract text from the PDF:
- `PyPDF2` was not installed
- `pypdf` was available and used instead
- layout extraction only revealed sparse text, including the page 9 note:
  - for in-band Plans B and C, if 700 MHz or 800 MHz is not in use in the system, placeholder frequency values should be entered that satisfy the plan

Because the numeric table could not be cleanly recovered from the PDF text layer, the assistant used the engine's plan-variant mappings to infer the missing 700/800 system ranges and added explicit fields to `TechnicalPlan` in `dvrs_tool/models.py`:
- `system_700_rx_range`
- `system_700_tx_range`
- `system_800_rx_range`
- `system_800_tx_range`

Those fields were then populated in `dvrs_tool/plan_data.py`.

### User corrections to table values
The user then iteratively corrected several values:

1. `700-B` and `700-C` had `700 RX` and `700 TX` reversed
2. `800-A1`:
   - `700 RX = 764.0-775.0`
   - `700 TX = 794.0-805.0`
3. `800-A2`:
   - `700 RX = 764.0-775.0`
   - `700 TX = 794.0-804.0`
4. `800-B`:
   - `700 RX = 764.0-775.0`
   - `700 TX = 794.0-805.0`

The assistant patched those values and re-verified the plan data.

### User correction to 700 plan DVRS ranges
The user specified:
- `700-B` DVRS TX should be `769.0-772.0`
- `700-B` DVRS RX should be `799.0-802.0`
- `700-C` DVRS TX should be `772.0-775.0`
- `700-C` DVRS RX should be `802.0-805.0`

### Assistant
The first patch landed on the wrong duplicated block and accidentally changed `700-A`. The assistant re-read the file, restored `700-A`, and correctly updated `700-B` and `700-C`.

### User
Asked to redisplay the full table, then observed that the `800 RX` and `800 TX` columns were reversed and should be swapped.

### Assistant
Swapped all `system_800_rx_range` and `system_800_tx_range` values across the table, then redisplayed the table.

### User
Further corrected:
- `700-A` was correct
- `700-B` should have `800 RX = 851.0-869.0` and `800 TX = 806.0-824.0`
- `700-C` should have `800 RX = 851.0-869.0` and `800 TX = 806.0-824.0`
- `800-A1`, `800-A2`, `800-B`, and `800-C` were correct

### Assistant
Patched `700-B` and `700-C` so their 800-band system ranges matched `700-A`, then reprinted the full table.

### User
Asked for a rule to be enforced that prevents changing the table without explicitly confirming that the change is intended.

### Assistant
Implemented a repo-level guard:
- created `dvrs_tool/plan_table_guard.py`
  - stores explicit confirmation metadata
  - stores a stable SHA-256 hash of the approved user-facing plan table fields
- created `tests/test_plan_table_guard.py`
  - fails if the current table hash does not match the approved hash
  - requires confirmation metadata fields such as confirmer, date, and reason

The guard was verified with:

```powershell
python -m unittest tests.test_plan_table_guard
```

The user then asked for a warning comment to be added to the plan table definition itself, and the assistant added a warning above `TECHNICAL_PLANS` in `dvrs_tool/plan_data.py` pointing maintainers to the guard.

### User bug report
The user then reported a runtime inconsistency:
- entered mobile low `810`, high `822`
- expected the values to be in range for `700-C`
- tool instead returned:
  - `Mobile TX range falls outside the plan's supported active mobile TX window. Mobile TX=810.00000-822.00000 MHz; allowed window=806.00000-821.00000 MHz.`

### Assistant diagnosis
The assistant traced this to the engine:
- `700-C` under `800 only` was still being evaluated via `_build_analog_800_variant(plan, "800-B")`
- the active mobile window validator used `active_mobile_tx_window` and `active_mobile_rx_window`
- those windows came from the analog 800 plan rather than the newly approved explicit table ranges

In other words, the plan table had been corrected, but the engine was still validating against stale analog-substituted windows.

### User
Asked to look at all range rules that compare a value to an explicit range in the table and correct any rules that do not validate correctly to that table.

### Assistant fix 1: explicit table-based active window validation
The assistant updated `dvrs_tool/engine.py` so active mobile TX/RX validation prefers:
- `system_700_tx_range` / `system_700_rx_range` for 700-system evaluation
- `system_800_tx_range` / `system_800_rx_range` for 800-system evaluation

and falls back to legacy `active_mobile_tx_window` / `active_mobile_rx_window` only when the explicit table field is missing.

Regression coverage was added in `tests/test_engine.py` for the `700-C` on `800 only` case that had been mis-rejected.

Targeted tests passed.

### User
Requested an audit for any remaining issues.

### Assistant audit findings
The assistant identified that cross-band variant generation still used legacy analog-plan substitutions:
- `_build_analog_800_variant(...)`
- `_build_analog_700_variant(...)`

Those helpers were still replacing the parent plan's:
- band family
- DVRS RX/TX windows
- fixed DVRS RX/TX ranges
- spacing and pairing behavior

with the analog plan's values, even after the table had been corrected. This caused incorrect end-to-end behavior such as:
- `700-B` on `800 only` proposing `800-C`-like DVRS frequencies
- `700-C` on `800 only` proposing `800-B`-like DVRS frequencies
- `800-A1` and `800-A2` on `700 only` proposing `700-B`-like DVRS frequencies

Concrete engine outputs were sampled to confirm that the wrong DVRS ranges were still being proposed.

### Assistant fix 2: remove analog substitution behavior
The assistant replaced the analog substitution helpers with a cleaner cross-band variant builder:
- kept the parent plan's own approved DVRS and fixed ranges
- derived only the placement needed for the selected system model

This required:
- updating `engine.py`
- updating regression tests to cover:
  - `700-B` on `800 only`
  - `700-C` on `800 only`
  - `800-A1` on `700 only`
  - `800-A2` on `700 only`

Afterward, the now-unused legacy analog builder functions were removed completely and a single `_build_cross_band_variant(...)` helper was used instead.

One regression test initially still referenced the deleted helper and had to be updated. The targeted suite then passed.

### User
Asked to check the API and UI layers as well, and requested that analog substitutions be removed completely unless doing so would break something.

### Assistant
Audited:
- `dvrs_tool/api.py`
- `dvrs_tool/static/app.js`
- `dvrs_tool/cli.py`

Findings:
- the API simply returns `response.to_dict()` from the engine
- the UI renders engine responses and does not independently reinterpret the plan table
- the inconsistency was not in API or UI logic

The assistant then removed the remaining analog-substitution scaffolding from `engine.py` because the previous fix had already made those analog plan IDs functionally unnecessary.

Verification used targeted tests:

```powershell
python -m unittest tests.test_engine.DVRSCalculationEngineTests.test_active_mobile_window_validation_prefers_explicit_table_ranges tests.test_engine.DVRSCalculationEngineTests.test_700_c_800_only_uses_table_dvrs_ranges_instead_of_analog_800_ranges tests.test_engine.DVRSCalculationEngineTests.test_700_b_800_only_uses_table_dvrs_ranges_instead_of_analog_800_ranges tests.test_engine.DVRSCalculationEngineTests.test_800_a1_700_only_uses_table_dvrs_ranges_instead_of_analog_700_ranges tests.test_engine.DVRSCalculationEngineTests.test_800_a2_700_only_uses_table_dvrs_ranges_instead_of_analog_700_ranges tests.test_engine.DVRSCalculationEngineTests.test_ordering_guide_windows_are_encoded_exactly_for_core_700_800_plans tests.test_plan_table_guard
```

All targeted tests passed.

### Final state reached in thread
- the plan table now explicitly stores DVRS ranges, per-band system RX/TX ranges, and fixed DVRS ranges
- the table values were manually reconciled with the user's approved values
- direct system-window validation uses explicit table ranges
- cross-band plan evaluation no longer swaps in other plans' DVRS/fixed ranges
- a guard now blocks silent plan-table edits unless the confirmation record is updated
- API and UI were audited and found to consume engine output rather than reinterpret the table independently

## Files Mentioned Or Modified
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/plan_table_guard.py`
- `tests/test_engine.py`
- `tests/test_plan_table_guard.py`
- `dvrs_tool/api.py`
- `dvrs_tool/static/app.js`
- `dvrs_tool/cli.py`
- `docs/dev-log.md`
- `dvr-lx-ordering-guide-1 (1).pdf`
