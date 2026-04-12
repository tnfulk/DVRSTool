# DVRS Engine, API, and Spacing-First Rules Evolution

## 1. Context
This thread covered the evolution of the DVRS planning tool from an initial product and architecture concept into a Python calculation engine, a FastAPI service surface, and a tested rule model for evaluating in-band DVRS configurations. The work relied on the supplied ordering guide, in-band operation guide, and supplemental ordering form, and repeatedly refined the implementation as the technical interpretation became more precise.

## 2. Problem Statement
The project needed a reusable backend that could accept user-entered mobile frequencies and country context, evaluate standard DVRS configurations across supported band plans, and return technically meaningful outputs for a future web UI. The harder problem was deciding how strictly to encode the ordering guide: first as example-window datasets, then as exact guide windows, and finally with stronger emphasis on spacing requirements and weaker dependence on illustrative example ranges.

## 3. Key Decisions
- Decision: Start by producing a constitution, functional specification, and implementation plan before building the engine.
  - Rationale: The PDFs defined a specialized technical domain, so aligning on requirements first reduced the risk of hard-coding the wrong assumptions into the service.
  - Alternatives considered: Implementing the calculator directly from the ordering guide without a design phase.
- Decision: Document a modular web application design in `dvrs-web-app-design.md`.
  - Rationale: The requested application needed both engineering structure and domain interpretation, including regulatory considerations for the United States and Canada.
  - Alternatives considered: Keeping the plan implicit inside code comments or README material.
- Decision: Add a Python calculation engine with a FastAPI wrapper and dedicated tests.
  - Rationale: The user explicitly asked for a backend service that a future UI could call, with test coverage and developer-usable error reporting.
  - Alternatives considered: A script-only tool or a UI-first implementation.
- Decision: Treat the 1.000 MHz passband rule as applying to proposed DVRS TX and RX outputs, not to the mobile input frequencies.
  - Rationale: The user clarified that the passband limitation should not restrict mobile system inputs unless the ordering guide explicitly required it.
  - Alternatives considered: Enforcing passband limits on both the mobile input and the DVRS proposal.
- Decision: Reconcile plan datasets against the ordering guide's exact technical windows.
  - Rationale: The user asked for the encoded datasets to match the guide's band-plan windows rather than loosely modeled approximations.
  - Alternatives considered: Leaving the original generalized windows in place.
- Decision: Increase input precision support to five decimal places and make errors more exact and structured.
  - Rationale: Frequency planning work benefits from precise input handling and machine-readable diagnostics.
  - Alternatives considered: Preserving lower precision and human-only error strings.
- Decision: Add structured `rule_violations` to both plan results and top-level API errors.
  - Rationale: The backend needed to be easier to debug and easier for a UI or developer tool to interpret programmatically.
  - Alternatives considered: Returning only unstructured warning or error messages.
- Decision: Rebuild the engine around spacing requirements rather than relying on example frequency windows as hard validation gates.
  - Rationale: The user emphasized that the guide's critical logic is driven by separations, allowed proposal widths, and relative placement, not by overfitting to example numeric ranges.
  - Alternatives considered: Continuing to reject plans primarily because the active mobile frequencies fell outside the guide's illustrative example windows.

## 4. Implementation Summary
The thread first produced a design artifact, `dvrs-web-app-design.md`, describing the constitution, specification, implementation plan, architecture, and regulatory research notes for a modular web application. That design also captured a key modeling issue: transmit-only input is insufficient for every VHF and 380-430 MHz scenario, so the specification included a manual mobile RX override where needed.

The implementation then introduced or refined the Python backend components in `dvrs_tool/`, including domain models, plan data, exception handling, the calculation engine, and the FastAPI API layer. Test coverage in `tests/test_engine.py` and the `run_tests.py` harness evolved alongside the engine. Later iterations tightened the encoded plan datasets to mirror the ordering guide more closely, added five-decimal precision, improved validation and error detail, and introduced structured `rule_violations` both within per-plan results and at the top-level API error shape.

The final major iteration reworked the engine into a spacing-first solver. Instead of treating the ordering guide's example active windows as hard blockers, the engine now prioritizes required separations, placement relationships, and plan passband limits when proposing DVRS RX and TX ranges. The old active-window checks were demoted to illustrative warnings, and the solver was updated so a proposal can shrink below the plan's maximum width when spacing geometry requires it.

## 5. Challenges & Iterations
The largest technical iteration was the interpretation of the ordering guide itself. The implementation moved through three meaningful phases: generalized modeled windows, then exact guide-window encoding, then a spacing-driven rule system that treated many of those windows as informative examples rather than mandatory operational limits.

Another important refinement came from the passband rule. The earlier engine behavior incorrectly implied that the mobile system inputs might also be width-limited; that was later corrected so the proposal width constraint applies to the DVRS outputs instead.

The thread also corrected precision and developer usability issues. Input handling was expanded to five decimal places, error responses became more verbose and exact, and machine-readable `rule_violations` were added after it became clear that plain messages were not enough for reliable debugging or future UI behavior.

There was also a terminology correction during the 800 MHz comparison work: the guide page being reviewed showed `A1`, `A2`, `B`, and `C`, not an `A3` plan. That clarification fed back into the dataset review work.

## 6. Final Outcome
The project ended this thread with a documented DVRS web-application design and a Python/FastAPI backend that had been iteratively refined to better reflect the ordering guide's intent. The engine supports five-decimal inputs, produces more exact structured diagnostics, returns machine-readable rule violations, and uses spacing-driven proposal logic for plan evaluation. The test suite was kept in step with those refinements and was reported passing after the final spacing-first rebuild.

## 7. Open Questions / Follow-ups
- The thread relied on the ordering guide, in-band guide, and related regulatory research, but future work may still need a deliberate legal review if the tool will be used for production licensing decisions in the United States or Canada.
- The spacing-first rebuild intentionally deprioritized some illustrative guide windows; future engineers should confirm that this interpretation remains aligned with stakeholder expectations and any manufacturer guidance.
- The backend was prepared for a future UI, but the thread did not finish a full production-grade frontend workflow for the latest rule model.
- Any additional band-plan edge cases not covered by the current tests may warrant more explicit regression cases.

## 8. Affected Files / Components
- `dvrs-web-app-design.md`
- `requirements.txt`
- `README.md`
- `run_tests.py`
- `dvrs_tool/__init__.py`
- `dvrs_tool/exceptions.py`
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/api.py`
- `dvrs_tool/cli.py`
- `tests/test_engine.py`
- Source reference PDFs in the repository root:
  - `dvr-lx-ordering-guide-1 (1).pdf`
  - `Introduction to  In-Band Operation-v1_2019-06-19.pdf`
  - `supplemental-ordering-form-b2bf88f7.pdf`

