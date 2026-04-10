# DVRS In-Band Planning Web App

## 1. Constitution

### 1.1 Purpose
Build a web-based application that helps a public-safety radio planner evaluate Futurecom DVR-LX 700 MHz and 800 MHz standard in-band configurations from minimal user input, then present:

- technically valid DVR-LX TX/RX ranges
- configurations that are not technically feasible
- configurations that may be technically feasible but not realistically licensable in the selected country
- a quote/order-style summary that mirrors the intent of the supplemental ordering form

### 1.2 Product Principles

1. Accuracy before convenience.
The app must never imply that a technically valid frequency plan is automatically licensable.

2. Explainability over black-box output.
Every result must show why a plan passed or failed: band window, spacing rule, passband rule, pairing rule, or regulatory policy rule.

3. Regulatory humility.
The app is a planning aid, not legal advice and not a replacement for FCC/ISED coordination, APCO/IMS A, or Futurecom review.

4. Vendor-faithful logic.
Technical plan evaluation must follow the Futurecom ordering guide and in-band-operation guidance first, then layer country-specific regulatory checks on top.

5. Modular rules engine.
Technical validation and regulatory validation must be separate modules so rules can evolve independently.

6. Ordering-guide fixed ranges first.
When the Futurecom ordering guide lists fixed DVRS TX/RX ranges for a standard plan, those published ranges control the plan definition. The app should recommend the feasible DVRS sub-range inside the published plan range that satisfies the plan rules. Technical validity for that plan means at least one paired DVRS channel inside the published fixed range can satisfy the plan rules.

7. Return the surviving compliant sub-range.
For every plan, whether it uses a fixed ordering-guide range or only a broader allowed window, the engine must search for the remaining paired DVRS sub-range that still satisfies that plan's spacing, window, and pairing rules. If the nominal DVRS window is close to, partially overlaps, or would otherwise conflict with the system frequencies, the app must shrink the recommendation to the surviving compliant sub-range instead of rejecting the plan solely because the full nominal range would not fit. Reject the plan only when no compliant paired sub-range remains.

8. Conservative classification.
When the app cannot determine licensability with high confidence, it must say "coordination required" rather than "valid."

9. Ordering workflow alignment.
The final output must look usable by radio technicians and procurement staff, not just developers.

### 1.3 Scope
In scope:

- Futurecom DVR-LX standard 700 MHz and 800 MHz in-band configurations
- country toggle for `United States` and `Canada`
- user input of low/high mobile transmit frequencies
- inferred 700 MHz / 800 MHz band detection where possible
- mixed 700 MHz and 800 MHz system evaluation
- computed system TX/RX summary
- proposed DVRS TX/RX ranges for each standard plan
  For fixed-range plans, these should be the recommended feasible sub-range inside the ordering-guide plan range, not a range that overlaps the system frequencies in violation of the plan spacing rules.
  For all plans, if only part of the nominal DVRS range remains spacing-compliant, return that surviving compliant sub-range rather than failing the plan.
- final-entry fields for actual licensed DVRS frequencies
- plan-by-plan feasibility and regulatory status

Out of scope for v1:

- VHF technical plan support
- UHF technical plan support
- direct FCC ULS or ISED license lookups
- automatic frequency coordination
- custom Futurecom filtering plans
- cross-band configuration recommendation as the main output
- final legal certification that a channel is assignable

### 1.4 Output States
Each configuration must end in one of these states:

- `Technically valid + regulatorily plausible`
- `Technically valid + coordination required`
- `Technically invalid`
- `Technically valid but outside likely public-safety band plan`

## 2. Specification

### 2.1 Source Constraints Taken From the Attached PDFs

The app must encode the following Futurecom guidance:

- Only standard frequency plans are standard offerings; anything else is custom.
- In-band filters are mechanically tuned and cannot be re-tuned in the field.
- In-band MSU transmit power must not exceed 50 W in DVRS-enabled modes.
- 700/800 in-band plans use a maximum DVR-LX passband of 1 MHz in the 2019 guidance, while the newer ordering guide expands certain 800 MHz plan windows; the rules engine should version the plan definitions explicitly and default to the latest ordering guide used by the project.
- The supplemental-ordering-form layout is the right model for the final summary panel.

### 2.2 User Inputs

Required inputs:

- `Country`: `United States` or `Canada`
- `Lowest mobile transmit frequency (MHz)`
- `Highest mobile transmit frequency (MHz)`

Derived inputs:

- detected band family
- detected mobile TX passband
- candidate mobile RX range, where the offset is deterministic for 700 MHz and 800 MHz plans

Conditional inputs:

- `Manual mobile receive override`
Use only when the project later expands beyond deterministic 700 MHz and 800 MHz pairing rules.

Optional inputs:

- `Use latest ordering-guide ruleset` toggle, default `true`
- `Agency notes`
- `Actual licensed DVRS low/high TX`
- `Actual licensed DVRS low/high RX`

### 2.3 Band Detection

The app should infer candidate band families from the user-entered mobile TX range:

- `700 MHz`: 799-805 MHz mobile TX
- `800 MHz`: 806-824 MHz mobile TX

If the input falls outside the supported 700 MHz or 800 MHz windows, the app must stop and show an input error.

### 2.4 System Frequency Computation

The app must compute and display:

- `System RX` = entered mobile TX range
- `System TX` = paired mobile receive range inferred from the band plan when deterministic

Deterministic defaults:

- `700 MHz`: system TX = mobile TX - 30 MHz
- `800 MHz`: system TX = mobile TX + 45 MHz
- `700 and 800 mixed systems`: plan evaluation must use the band-specific mobile TX range attached to each candidate plan, and any returned DVRS recommendation must be computed from that same candidate plan's band-specific system ranges

### 2.5 Technical Plan Engine

Represent each standard in-band configuration as data, not hard-coded UI logic.

Each plan definition should contain:

- `id`
- `bandFamily`
- `displayName`
- `mountCompatibility`
- `dvrsTxWindow`
- `dvrsRxWindow`
- `requiredDvrsSpacing`
- `requiredMsuSpacing`
- `minSeparationRules`
- `maxDvrsPassband`
- `maxMsuPassband`
- `fixedDvrsTxRange`
- `fixedDvrsRxRange`
- `notes`

Planned standard in-band coverage for v1:

- 700 MHz: Plans `A`, `B`, `C`
- 800 MHz: Plans `A1`, `A2`, `B`, `C`

For each plan, evaluate:

1. Is the system band compatible with the plan?
2. Does the mobile TX/RX block fit the plan's allowed windows?
3. If the ordering guide provides fixed DVRS TX/RX ranges for that plan, use those fixed ranges as the plan boundary and compute the recommended feasible DVRS sub-range inside that published plan range.
4. For fixed-range plans, determine whether at least one paired DVRS channel inside the published fixed range satisfies the spacing, window, and pairing rules.
5. For non-fixed plans, search the allowed windows for the surviving paired DVRS sub-range that satisfies the spacing, window, and pairing rules.
6. The proposed DVRS TX/RX ranges returned to the user must themselves satisfy the selected plan's required separations, even if that means returning only a narrow slice of the nominal plan range.
7. Near-adjacency or partial overlap between the nominal DVRS range and the system range is not by itself a reason to fail a plan; fail only if no compliant paired DVRS sub-range remains after applying the plan rules.
8. Is required channel spacing or duplex split respected?

Return:

- boolean pass/fail
- list of failures
- resulting proposed DVRS TX range
- resulting proposed DVRS RX range

### 2.6 Regulatory Rules Engine

The regulatory engine must be a second pass applied after technical evaluation.

Each result gets:

- `regulatoryStatus`
- `confidence`
- `reasonCodes`
- `humanSummary`

Recommended statuses:

- `LIKELY_LICENSABLE`
- `COORDINATION_REQUIRED`
- `LIKELY_NOT_LICENSABLE`

#### United States rules for v1

Use a conservative model:

- `700 MHz`: treat 769-775 / 799-805 as public-safety-capable.
- `800 MHz`: treat public-safety use as plausible within the 800 public-safety pool and interoperability structure, but note border-area and channel-category constraints.

#### Canada rules for v1

Use a similarly conservative model:

- `768-776 / 798-806 MHz`: treat as public-safety-capable.
- `821-824 / 866-869 MHz`: treat as specifically public-safety-capable in 800 MHz.
- `806-821 / 851-866 MHz`: treat as broader land-mobile spectrum that may be used depending on sub-allocation and coordination; mark coordination-required unless a later ruleset refines it by channel block.

### 2.7 Result Presentation

The app should render three panes:

1. `Input + System Summary`
- country
- detected band
- user-entered mobile TX low/high
- computed or assumed system TX low/high
- warnings about assumptions

2. `Standard Configuration Matrix`
- one card or row per standard in-band plan
- technical status
- regulatory status
- valid proposed DVRS TX range
- valid proposed DVRS RX range
- concise reason text

3. `Ordering Form Summary`
- system TX/RX values
- proposed DVRS TX/RX range
- blank editable fields for actual licensed DVRS TX/RX
- notes area
- export-friendly layout

### 2.8 UX Requirements

- Do not hide rejected plans; show all standard plans for the detected band family.
- Use color plus text labels; color alone is not enough.
- Every failed plan must expose the exact failing rule.
- Every yellow/red regulatory status must show a disclaimer and source basis.
- Show the Futurecom note that custom plans require vendor review.

### 2.9 Non-Functional Requirements

- Rules must be data-driven JSON or TypeScript objects.
- Regulatory rules must be versioned separately from technical plan rules.
- Every calculation should be unit-tested.
- App should support future addition of `VHF`, `UHF`, `federal`, `rail`, or `utility` profiles without rewriting the core engine.

## 3. Implementation Plan

### Phase 1. Foundations

- Create a single-page web app using a modular front end such as React + TypeScript.
- Define domain models for `BandFamily`, `TechnicalPlan`, `RegulatoryPolicy`, `EvaluationResult`, and `OrderSummary`.
- Build a source-controlled plan-definition dataset from the Futurecom ordering guide.

Deliverable:

- static plan data and validation interfaces

### Phase 2. Technical Rules Engine

- Implement band detection.
- Implement system TX/RX computation.
- Implement plan-by-plan technical validation.
- Add unit tests for each supported 700/800 standard plan family.

Deliverable:

- deterministic technical evaluator with test coverage

### Phase 3. Regulatory Policy Layer

- Encode U.S. and Canada policy ranges as a separate rules module.
- Add confidence-based results and disclaimers.
- Add source metadata so each rule can point to the supporting reference.

Deliverable:

- country-aware regulatory classifier

### Phase 4. User Interface

- Build the input form.
- Build the configuration matrix.
- Build the ordering-form-style summary panel.
- Add assumption and warning banners.

Deliverable:

- end-to-end interactive planner

### Phase 5. Validation and Expert Review

- test sample cases from the Futurecom in-band-operation guide
- compare results against at least a few known real-world band scenarios
- review edge cases with a radio technician or coordinator

Deliverable:

- validated v1 release candidate

### Phase 6. Nice-to-Have Enhancements

- PDF export of the ordering summary
- saved scenarios
- admin-editable regulatory policy tables
- optional direct license import from FCC ULS or a local CSV
- explicit profile selection such as `state/local public safety`, `federal`, or `other government`

## 4. Recommended Architecture

### Front End

- React + TypeScript
- component groups:
  - `InputForm`
  - `SystemSummary`
  - `PlanResultsTable`
  - `OrderFormPreview`
  - `RuleExplanationDrawer`

### Core Modules

- `bandDetection.ts`
- `pairingInference.ts`
- `technicalPlans.ts`
- `technicalEvaluator.ts`
- `regulatoryPolicies.ts`
- `regulatoryEvaluator.ts`
- `formatters.ts`

### Test Modules

- `technicalEvaluator.test.ts`
- `regulatoryEvaluator.test.ts`
- `fixtures/*.json`

## 5. Important Assumptions

1. The app should prefer the more recent ordering guide logic when the older narrative document and newer ordering guide differ.
   When the ordering guide publishes fixed standard-plan DVRS ranges, those ranges define the allowed recommendation boundary, while the returned proposed DVRS ranges must be a spacing-compliant subset when overlap would otherwise occur.
   The same subset-selection principle applies to non-fixed plans inside their broader allowed windows.
2. The app should target typical state, provincial, county, municipal, and agency public-safety users, not federal-only licensing profiles, in v1.
3. The app should classify uncertain licensability as `coordination required`.
4. The app should preserve a data model flexible enough to add VHF and UHF planning later, even though v1 only evaluates 700 MHz and 800 MHz plans.

## 7. Roadmap

- Add VHF standard-plan support in a future release once the team is ready to reintroduce manual-pairing and narrow-passband workflows.
- Add UHF standard-plan support in a future release once the team is ready to reintroduce the 380-430 MHz and 450-470 MHz technical and regulatory rulesets.

## 6. Research Notes and Source Basis

Attached documents used:

- `dvr-lx-ordering-guide-1 (1).pdf`
- `Introduction to  In-Band Operation-v1_2019-06-19.pdf`
- `supplemental-ordering-form-b2bf88f7.pdf`

Online sources reviewed for regulatory framing:

- Futurecom / Motorola DVR-LX ordering-guide mirror:
  - https://manuals.plus/m/79994c2ed840d6ccd9827e13cfef138ce4c5b89f6275934723d79f50c8dc679b
- FCC Public Safety Pool:
  - https://www.law.cornell.edu/cfr/text/47/90.20
- FCC 800 MHz public-safety pool in non-border areas:
  - https://www.law.cornell.edu/cfr/text/47/90.617
- FCC 700 MHz narrowband public-safety rules:
  - https://www.law.cornell.edu/cfr/text/47/90.531
- Canada SRSP-511 for 768-776 / 798-806 MHz:
  - https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/node/844
- Canada SRSP-502 for 806-824 / 851-869 MHz:
  - https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/standard-radio-system-plans/srsp-502-technical-requirements-land-mobile-and-fixed-radio-services-operating-bands-806-821851-866

Regulatory caution:

- U.S. and Canadian public-safety eligibility is channel-specific, border-sensitive, and coordinator-dependent.
- Because of that, the correct v1 behavior is classification and explanation, not automatic licensing approval.
