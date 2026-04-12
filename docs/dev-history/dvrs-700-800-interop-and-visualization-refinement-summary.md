# DVRS 700/800 Interoperability And Visualization Refinement

## 1. Context
This thread focused on two related areas of the DVRS planner. The first was extending the 700 MHz and 800 MHz planning logic to support cross-band 700/800 interoperability scenarios that were not handled by the original in-band-only rules. The second was refining the web visualization so evaluated ranges are easier to compare on a shared frequency axis.

## 2. Problem Statement
The planner was marking a U.S. 700 MHz Plan C scenario as technically invalid even when the user expected a valid interoperability pairing using DVRS TX `853.0125` and DVRS RX `808.0125`. Investigation showed that the engine only considered native 700 MHz plan windows once a mobile TX range was classified as 700 MHz. Separately, the chart visualization went through several iterations because the initial display was either too lane-heavy or too cluttered with labels.

## 3. Key Decisions
- Decision: Treat each 700 MHz and 800 MHz plan as having both a native layout and a cross-band interoperability variant.
  - Rationale: The existing engine bound plan selection to the detected mobile TX band family and therefore could not represent valid 700/800 interoperability cases.
  - Alternatives considered: Keeping native-only plan logic and trying to reinterpret user-entered optional licensed values without changing plan evaluation.

- Decision: Allow optional licensed DVRS single-channel entries where `low == high`.
  - Rationale: Real licensed entries may be represented as a single channel center frequency, and rejecting equal low/high values blocked legitimate interoperability examples.
  - Alternatives considered: Requiring users to enter an artificial width around a single licensed channel.

- Decision: Prefer the interoperability variant when optional licensed DVRS channels match that layout better than the native plan.
  - Rationale: This makes plan selection align more closely with the user’s actual licensed channel information instead of always favoring the native band interpretation.
  - Alternatives considered: Always preferring native layouts, even when optional licensed channels clearly matched the interoperable path.

- Decision: Remove the warning that the mobile system TX range is wider than the DVRS passband.
  - Rationale: The user clarified that this is expected in practice and should not be surfaced as a meaningful warning.
  - Alternatives considered: Keeping the warning as informational text.

- Decision: Remove ordering-guide “exact window” wording from 700/800 notes and failure messaging.
  - Rationale: The thread established that the engine should emphasize spacing and supported-frequency constraints rather than repeatedly framing results around example ordering-guide windows.
  - Alternatives considered: Keeping the existing wording but softening it.

- Decision: Move the visualization to a single shared-axis chart with color-coded overlays.
  - Rationale: The user wanted all four components compared on one common line while retaining the existing component color scheme.
  - Alternatives considered: Keeping a lane-based chart, or keeping in-chart labels despite clutter.

- Decision: Remove in-chart labels entirely and place only the frequency scale below the visualization.
  - Rationale: Repeated visualization refinements showed that overlay labels and per-bar value labels created more clutter than value in the chart itself.
  - Alternatives considered: Lane labels, stacked overlay labels, and collision-managed in-chart labels.

## 4. Implementation Summary
The engine was updated so 700 MHz plans can evaluate an 800 MHz DVRS interoperability profile and 800 MHz plans can evaluate a 700 MHz DVRS interoperability profile. Optional licensed DVRS validation now accepts equal low/high values and checks both native and interoperability windows when deciding whether a licensed range fits a supported plan. Regulatory classification was expanded to recognize cross-band interoperability layouts as supported but coordination-dependent.

On the messaging side, non-actionable passband-width warnings were removed, and ordering-guide-specific phrasing was replaced with more general language about spacing and supported-frequency constraints. 700/800 plan notes were rewritten to describe supported layouts without calling them “exact” ordering-guide windows.

The web visualization was then refactored multiple times. It first moved to a common-axis layout, then to a single-axis overlay chart, then briefly added collision-managed overlay labels, and finally removed all in-chart labels. The final chart keeps the color coding for `Mobile TX`, `System TX`, `DVRS RX`, and `DVRS TX`, overlays them on one shared axis line, and places a granular frequency scale below the chart while leaving the legend to identify each series.

## 5. Challenges & Iterations
The first challenge was diagnosing why a seemingly valid interoperability example was marked invalid. The root cause was that a mobile TX range in `799-805 MHz` forced the engine into the `700 MHz` band family, where only native 700 MHz DVRS windows were considered.

Another iteration involved the optional licensed DVRS values. The original backend treated equal low/high inputs as invalid optional ranges, which made single-channel licensed entries unusable even before interoperability logic could be applied.

The visualization also went through several false starts. It evolved from a stacked-lane display to a shared-axis chart, then to a single-axis overlay with in-chart labels, then to collision-managed label stacking, and finally to a cleaner chart with no in-chart labels at all and only an axis scale below the visualization.

One test also had to be revised after interoperability support changed prior invalid outcomes into valid ones. A different failure case was selected so the suite still covered the exact no-solution error path without conflicting with the new functionality.

## 6. Final Outcome
The planner now supports native 700 MHz and 800 MHz plans as well as cross-band 700/800 interoperability layouts. Optional licensed DVRS channels can be entered as single-channel values, and the engine will prefer the interoperable variant when those values clearly align with it.

User-facing messaging is cleaner: expected wide mobile TX spans no longer produce warning noise, and plan notes and failure reasons no longer depend on “exact ordering-guide window” wording. The visualization now presents all four components on a single shared axis with retained color coding, a cleaner legend, and frequency labels below the chart instead of inside it.

## 7. Open Questions / Follow-ups
- The final chart was verified through source inspection and regression tests, but not visually reviewed in a browser during this documentation step.
- The UI still contains a generic checkbox label referencing the “latest ordering-guide ruleset,” which was intentionally left alone because the request focused on plan/window wording rather than that feature label.
- The thread did not introduce browser-based screenshot validation for the latest visualization state.

## 8. Affected Files / Components
- `dvrs_tool/engine.py`
- `dvrs_tool/plan_data.py`
- `tests/test_engine.py`
- `dvrs_tool/static/app.js`
- `dvrs_tool/static/styles.css`
- `docs/dev-log.md`
- `docs/dev-history/dvrs-700-800-interop-and-visualization-refinement-summary.md`
- `docs/raw-threads/dvrs-700-800-interop-and-visualization-refinement.md`
