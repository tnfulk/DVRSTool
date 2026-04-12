# Raw Thread: DVRS Actual Frequency Evaluation Refinement

## Overview
This thread covered two closely related development passes:

1. Replace the optional DVRS low/high range inputs with single-frequency `DVRS TX` and `DVRS RX` fields, then use those fields to drive plan evaluation and UI filtering.
2. Refine that implementation so exact frequencies determine technical validity, while a `+/-0.5 MHz` widened check becomes advisory only.

It concludes with a request to convert the thread into reusable documentation.

## User Request 1
The user asked for the calculation engine and API wrapper to replace:

- `Actual DVRS TX Low`
- `Actual DVRS TX High`
- `Actual DVRS RX Low`
- `Actual DVRS RX High`

with:

- `DVRS TX`
- `DVRS RX`

The requested behavior was:

- Treat these as the actual frequencies used for the DVRS.
- If provided, they must fall inside the computed DVRS TX and RX ranges.
- If included, use the actual frequency with `+/-0.5 MHz` as the DVRS TX and RX ranges, and evaluate plans against that setup.
- In the UI, when a DVRS frequency is provided, only show cards for plans that work with that frequency setup.
- If no plans work, show all possible plans and their errors.
- In the quote section, recommend consulting a Motorola Presale Engineer before proceeding when no plan fits.

## Assistant Investigation
The assistant inspected the repository structure and searched for the relevant calculation, API, UI, and test files. Important locations identified during the thread included:

- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/cli.py`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/index.html`
- `tests/test_engine.py`

The assistant also noted that the git worktree already contained unrelated edits in many of the same files and explicitly chose to work carefully on top of them instead of reverting anything.

## Initial Design Decisions
Before editing, the assistant outlined a coordinated plan:

1. Rename the request/API/UI inputs from low/high ranges to single-frequency DVRS TX/RX fields.
2. Shift validation into per-plan evaluation instead of rejecting the full request up front.
3. Use supplied actual DVRS frequencies to narrow the UI to only valid plans when possible.
4. Preserve fallback visibility by showing all plans with errors when no plan fits.
5. Add a quote-summary recommendation to consult a Motorola Presale Engineer when supplied DVRS frequencies do not fit any standard plan.

## Implementation Pass 1

### Model and API Changes
The assistant changed the request model from four optional DVRS range fields to two single-frequency fields:

- `actual_dvrs_tx_mhz`
- `actual_dvrs_rx_mhz`

In the API wrapper:

- The FastAPI request model was updated to use these new fields.
- Compatibility aliases were added so legacy request payloads using older DVRS field names could still map into the new model.
- Optional-field validation guidance was updated so blank values are preferred over `0`.

### Engine Changes
The engine was reworked to stop rejecting requests early based on optional DVRS range mismatches. Instead, it now:

- computes plan proposals first,
- checks whether supplied actual DVRS frequencies fall inside the computed plan ranges,
- marks individual plans invalid when the supplied actual frequencies do not fit,
- preserves the full plan list so the UI can still display all plans and their failure reasons if no plan works.

In the first implementation, the assistant then:

- converted supplied actual DVRS frequencies into `+/-0.5 MHz` ranges,
- validated those forced widened ranges against plan windows, spacing requirements, and pairing rules,
- used the widened ranges for plan validity and regulatory evaluation.

### UI Changes
The web UI was updated to:

- replace the four DVRS low/high inputs with two inputs labeled `DVRS TX (MHz)` and `DVRS RX (MHz)`,
- send `actual_dvrs_tx_mhz` and `actual_dvrs_rx_mhz` in the request payload,
- rename display labels and user-facing error messages accordingly,
- filter the displayed plan cards so only technically valid plans are shown when actual DVRS frequencies are supplied,
- fall back to showing all plans when no technically valid plan remains,
- show the no-fit presales recommendation in the ordering summary through backend-supplied notes.

### CLI and Tests
The CLI was updated to accept:

- `--dvrs-tx`
- `--dvrs-rx`

The test suite was updated to reflect:

- the new request shape,
- interoperability selection using supplied actual DVRS values,
- no-fit request behavior without top-level rejection,
- updated API validation names,
- updated CLI help text.

### Validation and Debugging
The assistant ran:

```powershell
python -m unittest tests.test_engine -v
```

This initially failed because several test fixtures assumed widened-range behavior that did not match the actual plan calculations. The assistant inspected failing plan results with small inline Python probes and revised the fixtures until the suite passed.

## User Request 2
After the first implementation, the user clarified the intended rule:

- Remove the forced `+/-0.5 MHz` requirement as a hard validity check.
- If the exact supplied DVRS frequency passes spacing, the plan should be technically valid.
- If the exact frequency passes but the widened `+/-0.5 MHz` version would have failed, keep the plan valid and note the actual spacing achieved.

## Implementation Pass 2

### Revised Engine Behavior
The assistant changed the engine so that:

- exact supplied DVRS frequencies become the hard technical pass/fail input,
- exact DVRS frequencies are represented as point ranges during technical evaluation,
- the widened `+/-0.5 MHz` range is still computed, but only for an advisory check,
- if the exact setup passes and the advisory widened version would reduce spacing below the normal margin, the plan stays valid and gets a note describing the actual spacing.

This required:

- changing the "apply actual DVRS frequencies" helper to support both exact-point and widened-range modes,
- using exact-point mode during normal plan evaluation,
- adding a new advisory-note path that checks the widened setup after exact validation succeeds,
- generating spacing notes such as actual mobile TX-to-DVRS RX or mobile RX-to-DVRS TX separation when those exact separations still satisfy the plan.

### Revised Test Coverage
The assistant updated tests so exact DVRS results are now expected to appear as point ranges rather than `+/-0.5 MHz` ranges. It also added a new regression test for the exact-pass / advisory-fail case.

To find a real fixture for that scenario, the assistant probed candidate plan/frequency combinations and identified 800 MHz Plan B at the exact spacing threshold as a valid case. The final note-based regression used:

- mobile TX: `806.0-807.0`
- actual DVRS TX: `855.0`
- actual DVRS RX: `810.0`

In that case:

- exact spacing is valid,
- the widened `+/-0.5 MHz` version would have reduced spacing below the margin,
- the plan remains valid and receives an advisory note.

The assistant reran:

```powershell
python -m unittest tests.test_engine -q
```

and confirmed the suite passed, with one API test skipped when the FastAPI test client was unavailable.

## Final Functional State Captured in the Thread
At the end of the engineering work, the solution behaved as follows:

- The engine, API, CLI, and UI use single-frequency DVRS TX/RX inputs.
- Supplied DVRS frequencies are evaluated per plan rather than at request-validation time.
- The exact frequency determines technical validity.
- The widened `+/-0.5 MHz` check is advisory only.
- When actual DVRS frequencies are supplied:
  - the UI shows only technically valid plans, if any exist,
  - otherwise it shows all plans with their errors.
- If no plan fits the supplied DVRS setup, the ordering summary recommends consulting a Motorola Presale Engineer.

## User Request 3: Documentation Conversion
The final user request asked for the thread itself to be converted into project documentation:

- create a structured summary in `docs/dev-history/<thread-slug>-summary.md`,
- create a cleaned raw-thread transcript in `docs/raw-threads/<thread-slug>.md`,
- append a short summary of the thread to `docs/dev-log.md`.

## Files Mentioned or Modified During the Thread
- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/cli.py`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/index.html`
- `tests/test_engine.py`
- `docs/dev-history/dvrs-actual-frequency-evaluation-refinement-summary.md`
- `docs/raw-threads/dvrs-actual-frequency-evaluation-refinement.md`
- `docs/dev-log.md`
