# DVRS Plan Selection, Mixed-Band Inputs, and Pairing Rules Thread

## Overview
This thread covered a long sequence of DVRS engine and UI refinements centered on:

- 700/800 plan-family selection
- actual licensed DVRS frequency handling
- active-window and spacing validation
- the `System Bands` hint and mixed-band inputs
- UI field visibility and stale asset behavior
- deterministic 700, 800, and UHF pairing logic

## 1. `800-A1` Was Incorrectly Invalid

### User
Provided a concrete 800 MHz case:

- Mobile TX Low: `806.0125`
- Mobile TX High: `813.8375`
- DVRS TX: `862.2125` (later corrected to `863.2125`)
- DVRS RX: `818.2125`

The expectation was that this should be valid for `800-A1`, but the tool returned it as technically invalid.

### Assistant
Traced the engine and plan data, then found:

- `800-A1` was encoded with:
  - `dvrs_tx_window=(851.0, 869.0)`
  - `pair_offset_mhz=35.0`
- The repo’s own 800 MHz plan graphic showed A1 should use:
  - `DVRS TX 861-869`
  - `45 MHz` DVRS TX-above-RX pairing

The invalid result came from the engine computing an A1 DVRS TX range that overlapped the derived mobile RX block, so `_solve_candidate_rx_range` returned no valid candidate.

### User refinement
Corrected the DVRS TX value from `862.2125` to `863.2125` and requested:

- fix the A1 definition
- add tests

### Assistant implementation
Patched `800-A1` in `dvrs_tool/plan_data.py`:

- `dvrs_tx_window=(861.0, 869.0)`
- `pair_offset_mhz=45.0`
- `fixed_dvrs_tx_range=(861.0, 869.0)`

Added tests to verify:

- A1 definition values
- the corrected `863.2125 / 818.2125` case
- the spacing-driven proposed A1 ranges

## 2. Actual DVRS Frequencies Became the Primary Plan Driver

### User
Requested that when DVRS frequencies are provided, the tool should use those provided DVRS frequencies to determine the plan to evaluate, rather than using the mobile TX range first.

### Existing behavior found
The engine:

- computed a plan range from the mobile TX system
- then rejected supplied DVRS values if they were outside that computed range

This behavior was controlled by the `ACTUAL_DVRS_FREQUENCY_OUTSIDE_COMPUTED_RANGE` check.

### Assistant implementation
Removed the computed-range rejection step and changed the flow so:

- exact DVRS TX/RX values are applied first
- then the engine validates them against:
  - allowed windows
  - spacing
  - pairing

### Test updates
Reworked tests so actual DVRS values:

- can validate a plan even if they lie outside the solver’s default subrange
- still fail when they violate plan windows or spacing rules

## 3. Wrong Plans Were Surviving Because Active Windows Were Ignored

### User
Raised a case where:

- `Mobile TX = 806.0125 to 818.2125`
- `DVRS TX/RX = 770 / 800`

Expected result:

- use `700-A`

Observed result:

- `800-A2` and `800-C` were showing

The user also noted that `800-A2` and `800-C` should require 700 MHz channels not currently included in the input model, and that `800-C` should not be valid in the cited scenario.

### Assistant investigation
Found that:

- the engine did encode `active_mobile_tx_window` and `active_mobile_rx_window`
- but those active windows were not actually enforced during evaluation

### Assistant implementation
Added active mobile TX/RX window validation.

This caused:

- `700-B` and `700-C` to be rejected correctly when their active windows were not met
- `700-A` to win the `770 / 800` case on an 800 system

Tests were added to ensure:

- `700-A` is preferred for an 800 system when the native DVRS pair is a 700 MHz layout
- active windows limit plan validity

## 4. Added `System Bands` Hint

### User
Requested a new input:

- dropdown called `System Bands`
- choices:
  - `VHF`
  - `UHF`
  - `700 only`
  - `800 only`
  - `700 and 800`

Requested behavior:

- use this hint to help determine which band plans to evaluate
- continue to use actual DVRS frequencies as the strongest plan driver when present
- for `700 and 800`, explicitly evaluate:
  - `700-B`
  - `700-C`
  - `800-A1`
  - `800-A2`
  - `800-A3` (later corrected to `800-B`)
- `800-C` should only be used when `800 only` is selected
- `700-A` should be used when the DVRS frequencies are in the 700 MHz plan but the system frequencies are in the 800 MHz band

### Assistant implementation
Added:

- `SystemBandHint` enum in `models.py`
- `system_band_hint` in the API request model
- `System Bands` dropdown to the web form

The engine was updated so:

- actual DVRS native matching is still primary
- if no actual DVRS pair is provided, the hint controls which plan families or plan subsets are evaluated

Later correction:

- `800-A3` was acknowledged as a mistake
- `800-B` was added to the mixed `700 and 800` plan set instead

### Tests added
Tests now cover:

- mixed `700 and 800` candidate plan limits
- `800-C` only appearing under `800 only`
- actual DVRS native matching overriding the `System Bands` hint when appropriate

## 5. Mixed `700 and 800` Needed Separate 700/800 Mobile TX Inputs

### User
Provided a mixed-band example:

- `mobile tx low = 773`
- `mobile tx high = 803`
- `system bands = 700 and 800`
- `DVRS TX/RX = 770 / 800`

Expected:

- `700-B`

Observed:

- error due ambiguous or unsupported band detection

### Initial investigation
The engine still ran auto-detect on one combined mobile TX range and threw `UNSUPPORTED_OR_AMBIGUOUS_BAND`.

There was discussion of simply relaxing validation when mixed-band channel detail was missing, but the user explicitly redirected the approach:

> Instead of fixing the block of missing channel detail fields, if `700 and 800` is selected, have the page dynamically request both the `700 Mobile TX` range and the `800 Mobile TX` range, then use both sets of frequencies to determine if a valid plan exists. Spacing between DVRS TX/RX and mobile TX/RX remains the primary constraint.

### Assistant implementation
Added new mixed-band fields:

- `mobile_tx_700_low_mhz`
- `mobile_tx_700_high_mhz`
- `mobile_tx_800_low_mhz`
- `mobile_tx_800_high_mhz`

The web UI was updated so these fields appear only for `700 and 800`.

The engine was updated so:

- in mixed mode, separate 700-side and 800-side TX ranges are required
- plan evaluation uses the two ranges differently

The final mixed-band logic:

- uses one side to identify the plan slot
- uses the opposite side to validate spacing

This allowed the case:

- `700 Mobile TX = 802-803`
- `800 Mobile TX = 806-807`
- `DVRS TX/RX = 770 / 800`

to resolve correctly to `700-B`

### Tests added
Added a mixed-band regression test proving the above case selects `700-B` as the best plan.

## 6. UI Field Visibility and Stale Asset Issues

### User
Asked whether the 700/800 mixed inputs could be hidden unless `System Bands = 700 and 800`.

### Assistant
Implemented dynamic UI logic intended to:

- hide the original single `Mobile TX Low/High` fields when mixed mode is active
- show the dedicated `700 Mobile TX` and `800 Mobile TX` fields only in mixed mode

### Follow-up from user
Reported that:

- with `auto-detect`, the `700 Mobile` and `800 Mobile` fields were still visible
- with `700 and 800`, the original `Mobile TX` fields were still visible

### Assistant investigation
Reviewed the code and found the toggle logic was already present, so likely causes were:

- stale browser assets
- weak hide/show behavior relying only on `hidden`

### Assistant implementation
Performed several UI hardening steps:

- bumped static asset versions in `index.html`
- added stronger frontend toggling logic
- later added:
  - `[hidden], .is-hidden { display: none !important; }` in CSS
  - explicit `.is-hidden` toggling in JavaScript
- disabled inactive fields in addition to hiding them

The assistant also noted that if the issue persisted after this, a stale running server or a different static file source was likely involved.

## 7. Explicit Pairing Rules for 700, 800, and UHF

### User
Specified explicit pairing rules:

- 700 MHz systems: `TX - 30 = RX`
  - example: `TX = 794`, `RX = 764`
- 800 MHz systems: `TX + 45 = RX`
  - example: `TX = 811`, `RX = 856`
- UHF 380-430 systems: always `5 MHz` split, but direction depends on plan
  - `A1` and `A3`: `TX - 5 = RX`
  - `A2` and `A4`: `TX + 5 = RX`

The user asked for the calculations to be adjusted accordingly and requested UI/input changes if needed for UHF.

### Assistant findings
For 700 and 800:

- the numeric formulas already matched the requested examples once the system band was fixed
- the missing capability was that explicit hints like `700 only` were not being honored when the mobile TX input fell outside the previous auto-detect windows

For UHF 380:

- plans still used manual RX inference
- the engine needed plan-specific deterministic pairing

### Assistant implementation
Updated system-band resolution so explicit hints can force:

- `BandFamily.BAND_700`
- `BandFamily.BAND_800`
- `BandFamily.VHF`
- `BandFamily.UHF`

Updated UHF 380 plan data so plans now use deterministic 5 MHz offsets and directions:

- `A1`, `A3`, `B1`, `B3`, `C`: `tx_above_rx`, `pair_offset_mhz=5.0`
- `A2`, `A4`, `B2`, `B4`, `D`: `tx_below_rx`, `pair_offset_mhz=5.0`

Removed the blanket `requires_mobile_rx_range=True` dependency for UHF 380 plans and added plan-specific pairing inference in the engine.

No new UHF UI fields were added because the engine could now derive the paired side automatically.

### Tests added
Added tests for:

- `700 only` using `794 -> 764`
- `800 only` using `811 -> 856`
- UHF 380 `A1` deriving `TX - 5 = RX`
- UHF 380 `A2` deriving `TX + 5 = RX`

## 8. Final State at End of Thread

By the end of the thread:

- `800-A1` had been corrected
- actual DVRS frequencies were the primary native plan driver
- active windows were enforced
- `System Bands` existed in UI and API
- mixed `700 and 800` used separate 700-side and 800-side TX inputs
- mixed-band plan evaluation used both system ranges
- UI field visibility was hardened
- explicit 700-only and 800-only hints could drive pairing logic
- UHF 380 pairing became deterministic and plan-specific
- the test suite grew significantly and remained green

## Files Mentioned or Modified During the Thread

- `dvrs_tool/engine.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/models.py`
- `dvrs_tool/api.py`
- `dvrs_tool/static/index.html`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `tests/test_engine.py`
- `docs/dev-log.md`
- `docs/dev-history/*`
- `docs/raw-threads/*`
