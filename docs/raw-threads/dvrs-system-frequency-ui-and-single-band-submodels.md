# DVRS System-Frequency UI And Single-Band Submodels

## Overview
This thread added single-band parent-plan evaluation support for several mixed-band-related DVRS plans, then updated the product spec and web UI so users enter the system frequencies they actually have. It concluded with a git commit after the user approved the proposed commit message.

## Participants
- User
- Assistant

## Conversation

### 1. Add Single-Band Submodels For `700-B` And `700-C`

**User**

Requested an engine update for `700 MHz` plans `B` and `C`:
- Create subplans for all three possibilities:
  - `700 System only`
  - `800 System only`
  - `700 and 800 system`
- Keep the same spacing/layout as the parent plan.
- Each submodel should only expect the relevant system frequencies.
- If any submodel passes, the parent plan passes.
- Only the parent plan should be presented to the UI.

**Assistant**

Inspected the repository and found the relevant files:
- `dvrs_tool/plan_data.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/models.py`
- `tests/test_engine.py`

Notable observations:
- `rg` was unavailable in the environment, so PowerShell file search was used instead.
- The engine already had a variant-evaluation path that could be extended for parent/submodel logic.

**Implementation details discussed and applied**

- Enabled auto-detection of `700-only` systems instead of rejecting them.
- Added multi-variant evaluation for `700-B` and `700-C` in `dvrs_tool/engine.py`.
- Preserved only the parent plan in the user-facing results.
- Added system-model mismatch handling for inapplicable variants.
- Ensured parent selection preferred real evaluated variants over mismatch placeholders.
- Attached the selected submodel’s system ranges to the returned parent result.
- Expanded candidate-plan behavior so `700-B` and `700-C` participate correctly in single-band and mixed scenarios.

**Testing and iteration**

- Initial test run failed on several expectations:
  - Some expected DVRS ranges were too broad.
  - Actual-DVRS matching was incorrectly including variants that were not applicable to the current request shape.
  - Parent selection sometimes returned a mismatch result instead of a relevant evaluated result.
- The assistant updated:
  - actual-plan matching to consider only request-applicable variants
  - selection logic to prefer non-mismatch evaluated results
  - tests to reflect the new valid single-band outcomes

**Result**

- `python -m unittest tests.test_engine` passed.

### 2. Extend The Same Pattern To `800-A1`, `800-A2`, And `800-B`

**User**

Requested the same internal submodel treatment for:
- `800-A1`
- `800-A2`
- `800-B`

**Assistant**

Extended the same parent/submodel approach:
- Added three internal variants for those parent plans.
- Added 700-only analog evaluation for the 800 plans.
- Expanded candidate-plan sets for explicit and detected single-band scenarios.

**Implementation details discussed and applied**

- Added internal variants for:
  - `800-A1`
  - `800-A2`
  - `800-B`
- Added helper logic to build analog 700-side variants for those plans.
- Extended the base-plan sets used by:
  - variant request-model matching
  - variant system-summary selection
- Expanded detected `700-only` candidate plans.

**Testing and iteration**

- The first mapping for `800-A1`’s 700-only analog was too restrictive and resulted in an invalid outcome.
- The assistant inspected actual outputs with small Python snippets and remapped `800-A1`’s 700-only analog to a profile that actually passed.
- The `800 only` candidate set was also expanded to include:
  - `800-A1`
  - `800-A2`
  - `800-B`

**Result**

- `python -m unittest tests.test_engine` passed with the updated behavior.

### 3. UI/UX Suggestions For Making The New Logic Intuitive

**User**

Asked for UI suggestions so users can input only the system frequencies they have:
- only 800 MHz
- only 700 MHz
- both 700 and 800 MHz

Provided explicit interpretation examples:
1. `800 only` should evaluate:
   - `700A`
   - `700B (800 MHz only)`
   - `700C (800 MHz only)`
   - `800C`
2. `700 only` should evaluate:
   - `700B (700 MHz only)`
   - `700C (700 MHz only)`
   - `800A1 (700 MHz only)`
   - `800A2 (700 MHz only)`
   - `800B (700 MHz only)`
3. If both 700 and 800 are provided, the current mixed evaluation path is correct.

**Assistant**

Suggested a top-level user-facing selector driven by what system frequencies the customer actually has:
- `Only 800 MHz system frequencies`
- `Only 700 MHz system frequencies`
- `Both 700 MHz and 800 MHz system frequencies`

Suggested hiding/showing only the relevant fields for each selection and keeping the submodels hidden from the UI. Also recommended documenting that plan names are based on the DVRS band, not the system band.

### 4. Update The Spec And Implement The UI / Configuration Changes

**User**

Asked for two things:
1. Update `dvrs-web-app-design.md` to reflect:
   - the new concept and plan
   - the fact that plan naming is based on the DVRS band, not the system band
2. Implement the proposed UI and configuration changes

The user also explicitly confirmed:
- Excluding `700-A` from the `700 only` example list was correct.
- Reason: that model only supports system frequencies in the `800 MHz` band.

**Assistant**

Inspected the UI and API surface:
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `dvrs_tool/api.py`
- `dvrs_tool/cli.py`
- `dvrs-web-app-design.md`

Key observations before changes:
- The UI still exposed a `System Bands` selector with only:
  - `700 and 800`
  - `800 only`
- Labels still used internal `Mobile TX` wording.
- The backend `SystemBandHint` enum did not yet support `700 only`.

**Spec changes applied**

Updated `dvrs-web-app-design.md` to document:
- explicit system-frequency configuration selection:
  - `700 only`
  - `800 only`
  - `700 and 800`
- user input as customer system frequencies rather than raw mobile-TX terminology
- the naming rule that standard plan names refer to the DVRS band
- required parent-plan mappings for:
  - `700 only`
  - `800 only`
  - `700 and 800`
- the UI expectation that only parent plans are shown

**Backend changes applied**

Updated `dvrs_tool/models.py`:
- Added `SystemBandHint.BAND_700_ONLY = "700 only"`

Updated `dvrs_tool/engine.py`:
- Added explicit support for `700 only` in `_resolve_system_band`
- Added `700 only` candidate-plan mapping:
  - `700-B`
  - `700-C`
  - `800-A1`
  - `800-A2`
  - `800-B`
- Preserved the requested `800 only` mapping and mixed mapping
- Reworded internal submodel notes to user-facing text:
  - `Evaluated using the 700 MHz-only system model.`
  - `Evaluated using the 800 MHz-only system model.`

**UI changes applied**

Updated `dvrs_tool/static/index.html`:
- Reworded the intro text around system frequencies
- Added helper copy explaining that users should enter only the system frequencies they actually have
- Replaced `System Bands` with `System Frequency Configuration`
- Added three user-facing choices:
  - `Only 800 MHz system frequencies`
  - `Only 700 MHz system frequencies`
  - `Both 700 MHz and 800 MHz system frequencies`
- Relabeled fields to `System Frequency Low/High`
- Kept mixed-mode dedicated 700 and 800 frequency fields
- Updated empty-state text to mention selected system configuration

Updated `dvrs_tool/static/app.js`:
- Updated field labels in frontend error formatting
- Updated summary labels from `Mobile TX` to `System RX`
- Updated visualization labels to show:
  - `System RX`
  - `System TX`
  - `700 System RX`
  - `800 System RX`
- Added dynamic relabeling for the single-band frequency fields when the mode changes
- Added mode switching logic to:
  - show/hide mixed fields
  - show/hide single-band fields
  - clear stale values when the configuration changes
- Updated reset/empty-state text to describe the new workflow

Updated `dvrs_tool/static/styles.css`:
- Added styling for the new explanatory section copy

**Tests added/updated**

Updated `tests/test_engine.py` to cover:
- explicit `700 only` candidate selection
- expanded `800 only` candidate selection
- 700-only and 800-only parent-plan pass behavior for:
  - `700-B`
  - `700-C`
  - `800-A1`
  - `800-A2`
  - `800-B`

**Verification**

- Ran `python -m unittest tests.test_engine`
- Final result:
  - all relevant tests passed

**Assistant closing summary**

Reported that:
- the spec, engine, tests, and UI were updated
- `python -m unittest tests.test_engine` passed
- no browser-based manual UI verification had been performed yet

### 5. Commit Request

**User**

Asked the assistant to commit the changes, but first propose a commit comment for approval.

**Assistant**

Suggested commit message:

`Align planner UI with system-frequency input model and add single-band submodel evaluation`

**User**

Approved the message as-is.

### 6. Commit Execution

**Assistant**

Attempted to stage and commit the changes.

Notable issue:
- PowerShell rejected `&&` chaining syntax.
- A subsequent `git add` failed because `.git/index.lock` could not be created without elevated permission in the environment.

The assistant then:
- re-ran `git add` with escalation
- staged:
  - `dvrs-web-app-design.md`
  - `dvrs_tool/models.py`
  - `dvrs_tool/engine.py`
  - `dvrs_tool/static/index.html`
  - `dvrs_tool/static/app.js`
  - `dvrs_tool/static/styles.css`
  - `tests/test_engine.py`
- created the commit with the approved message

**Commit created**

- Branch: `master`
- Commit: `dcdd94c`
- Message:
  - `Align planner UI with system-frequency input model and add single-band submodel evaluation`

## Final State Captured By This Thread

- The engine supports internal single-band and mixed-system submodels for:
  - `700-B`
  - `700-C`
  - `800-A1`
  - `800-A2`
  - `800-B`
- The product spec explicitly defines:
  - system-frequency-driven input
  - parent-plan/submodel behavior
  - the DVRS-band naming rule
- The UI now asks users what system frequencies they have and conditionally shows the right fields
- The backend supports explicit:
  - `700 only`
  - `800 only`
  - `700 and 800`
- The work was committed to git with the approved message above
