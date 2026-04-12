# DVRS Mixed-Plan Sub-Range Spec Alignment

## 1. Context
This thread refined how the DVRS planner should evaluate standard plans when the nominal DVRS plan ranges sit close to, or partially conflict with, the system frequency ranges. The work centered on mixed `700 and 800` planning, with a specific user-supplied example intended to validate `700-C` by returning the remaining compliant slice instead of rejecting the plan outright.

## 2. Problem Statement
The planner was reporting no valid standard plan for the user's mixed-band sample:

- `700 Mobile TX`: `799.2125-801.8875 MHz`
- `800 Mobile TX`: `806.0125-822.3875 MHz`

The user pointed out that the product specification should allow a plan to remain valid when a smaller DVRS sub-range still satisfies that plan's separation rules, even if the full nominal DVRS range does not. The implementation also appeared to be evaluating mixed-band `700` plans against the wrong band-specific system ranges.

## 3. Key Decisions
- Decision: Explicitly document that all plans must return the surviving compliant DVRS sub-range before failing.
  - Rationale: The existing spec already leaned toward feasible-sub-range behavior for fixed plans, but the requirement needed to be stated unambiguously for both fixed and non-fixed plans.
  - Alternatives considered (if any): Leaving the existing wording in place and changing only code was rejected because the old wording still allowed narrow interpretations.

- Decision: In mixed `700 and 800` mode, evaluate each candidate plan using that plan's own band-specific mobile/system ranges.
  - Rationale: The spec already stated that mixed-plan evaluation should use the band-specific mobile TX range attached to each candidate plan. The engine was using the opposite band for some mixed-plan summaries, which blocked valid `700-C` proposals.
  - Alternatives considered (if any): Keeping the previous mixed-band mapping and only changing proposal shrinking logic was rejected because it preserved the wrong spacing inputs.

- Decision: Keep plans invalid when their active mobile TX windows are not fully satisfied.
  - Rationale: The user's request targeted proposal generation inside plan windows, not a relaxation of the active-window rules.
  - Alternatives considered (if any): Relaxing active-window validation was not pursued because it was not supported by the current spec discussion in this thread.

- Decision: Add regression coverage for the specific mixed-band `700-C` sub-range scenario.
  - Rationale: The user provided a concrete sequence that should remain valid in future changes, making it a strong regression target.
  - Alternatives considered (if any): Relying only on existing tests was rejected because those tests encoded the old mixed-band assumption.

## 4. Implementation Summary
Three areas were updated:

- The design spec in `dvrs-web-app-design.md` was expanded to state that every plan must search for and return the surviving compliant DVRS sub-range within its fixed range or allowed window, and that mixed `700/800` plan evaluation must use the candidate plan's own band-specific system ranges.
- The engine logic in `dvrs_tool/engine.py` was corrected so mixed-band `700` plans build summaries from the `700` mobile TX range and mixed-band `800` plans use the `800` ranges.
- The test suite in `tests/test_engine.py` was updated to remove expectations based on the old swapped-band behavior and to add a new regression test proving that the sample mixed-band `700-C` case returns a narrowed valid DVRS proposal.

## 5. Challenges & Iterations
- The initial repository inspection showed that the written spec already partially described feasible sub-range behavior for fixed plans, so the issue was not a blank-slate requirements gap. The work became a combination of making the spec more explicit and aligning the engine to it.
- Early engine output for the user's sample showed all plans invalid, with `700-C` failing because no valid DVRS RX remained when compared against the `800` mobile TX block. This exposed that mixed-band plan-specific summaries were using the wrong side of the system.
- Existing tests had been built around that previous behavior, especially for mixed-band `700-B` summary and ordering expectations. Those tests were revised once the corrected spacing inputs made the previous expectations invalid.

## 6. Final Outcome
The final implementation now treats the user's mixed-band sample as having one valid standard plan:

- Valid plan: `700-C`
- Proposed DVRS RX: `804.8875-805.0000 MHz`
- Proposed DVRS TX: `774.8875-775.0000 MHz`

The remaining evaluated plans stayed invalid because they still fail their active-window requirements. The test suite passed after the changes, and the work was committed as Git commit `f717cb1` with message `Refine DVRS sub-range planning for mixed systems`.

## 7. Open Questions / Follow-ups
- The current thread did not revisit whether active mobile TX window validation should ever allow partial-range compliance similar to DVRS proposal shrinking. That remains unchanged and may merit future product clarification.
- Mixed-band ordering-summary behavior still reports the combined mixed system summary when no technically valid plan exists. If future UX work needs more plan-specific summary behavior in failure states, that would require additional design decisions.

## 8. Affected Files / Components
- `dvrs-web-app-design.md`
- `dvrs_tool/engine.py`
- `tests/test_engine.py`
- Mixed-band plan evaluation logic
- Fixed-range and allowed-window DVRS proposal behavior
- Development history and thread documentation in `docs/`
