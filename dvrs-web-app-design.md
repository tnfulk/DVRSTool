# DVRS In-Band Planning Web App

## 1. Constitution

### 1.1 Purpose
Build a web-based application that helps a public-safety radio planner evaluate Futurecom DVR-LX standard in-band configurations from minimal user input, then present:

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

6. Conservative classification.
When the app cannot determine licensability with high confidence, it must say "coordination required" rather than "valid."

7. Ordering workflow alignment.
The final output must look usable by radio technicians and procurement staff, not just developers.

### 1.3 Scope
In scope:

- Futurecom DVR-LX standard in-band configurations
- country toggle for `United States` and `Canada`
- user input of low/high mobile transmit frequencies
- inferred band detection where possible
- computed system TX/RX summary
- proposed DVRS TX/RX ranges for each standard plan
- final-entry fields for actual licensed DVRS frequencies
- plan-by-plan feasibility and regulatory status

Out of scope for v1:

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
- VHF and UHF plans use much narrower DVRS passbands than 700/800 plans.
- The supplemental-ordering-form layout is the right model for the final summary panel.

### 2.2 User Inputs

Required inputs:

- `Country`: `United States` or `Canada`
- `Lowest mobile transmit frequency (MHz)`
- `Highest mobile transmit frequency (MHz)`

Derived inputs:

- detected band family
- detected mobile TX passband
- candidate mobile RX range, where the offset is deterministic

Conditional inputs:

- `Manual mobile receive override`
Use only when the app cannot safely infer the system receive/transmit pair structure from the transmit inputs alone, especially in VHF or 380-430 MHz edge cases.

Optional inputs:

- `Use latest ordering-guide ruleset` toggle, default `true`
- `Agency notes`
- `Actual licensed DVRS low/high TX`
- `Actual licensed DVRS low/high RX`

### 2.3 Band Detection

The app should infer candidate band families from the user-entered mobile TX range:

- `700 MHz`: 799-805 MHz mobile TX
- `800 MHz`: 806-824 MHz mobile TX
- `VHF`: 136-174 MHz mobile TX
- `UHF 380-430`: 380-430 MHz mobile TX
- `UHF 450-470`: 450-470 MHz mobile TX

If the input spans multiple band families or falls outside all supported families, the app must stop and show an input error.

### 2.4 System Frequency Computation

The app must compute and display:

- `System RX` = entered mobile TX range
- `System TX` = paired mobile receive range inferred from the band plan when deterministic

Deterministic defaults:

- `700 MHz`: system TX = mobile TX - 30 MHz
- `800 MHz`: system TX = mobile TX + 45 MHz
- `450-470 MHz`: default paired system TX = mobile TX - 5 MHz

Non-deterministic or jurisdiction-sensitive cases:

- `VHF`
- `380-430 MHz`

For those cases, the app should:

- attempt a rule-based pairing inference only when the entered channels match a known standard split pattern
- otherwise request or enable a manual receive-range override
- label the output `Computed from manual pairing assumption`

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
- `notes`

Planned standard in-band coverage for v1:

- 700 MHz: Plans `A`, `B`, `C`
- 800 MHz: Plans `A1`, `A2`, `B`, `C`
- VHF duplex: Plans `A`, `B`
- VHF simplex: Plans `D1`, `D2`, `E1`, `E2`
- UHF 380-430: Plans `A1`, `A2`, `A3`, `A4`, `B1`, `B2`, `B3`, `B4`, `C`, `D`
- UHF 450-470: Plans `A`, `B`

For each plan, evaluate:

1. Is the system band compatible with the plan?
2. Does the mobile TX/RX block fit the plan's allowed windows?
3. Are minimum separations met?
4. Is the maximum DVRS passband respected?
5. Is required channel spacing or duplex split respected?

Return:

- boolean pass/fail
- list of failures
- resulting valid DVRS TX window
- resulting valid DVRS RX window

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
- `VHF`: treat only portions of 150-174 MHz as generally public-safety-plausible; note that not all of 136-174 is public safety.
- `VHF mobile repeater note`: highlight the FCC public-safety mobile repeater channels at 173.2375, 173.2625, 173.2875, and 173.3125 MHz as especially relevant to the Futurecom VHF in-band narrative.
- `380-430 MHz`: treat as likely not licensable for typical non-federal U.S. public-safety applicants except specialized or federal contexts; default to red unless the project later adds a federal profile.
- `450-470 MHz`: treat as coordination-required, not automatically green, because public safety has assignable channels there but not across the full band.

#### Canada rules for v1

Use a similarly conservative model:

- `768-776 / 798-806 MHz`: treat as public-safety-capable.
- `821-824 / 866-869 MHz`: treat as specifically public-safety-capable in 800 MHz.
- `806-821 / 851-866 MHz`: treat as broader land-mobile spectrum that may be used depending on sub-allocation and coordination; mark coordination-required unless a later ruleset refines it by channel block.
- `VHF 148-174 MHz`: treat as coordination-required because it is widely used for land mobile, including public safety, but not uniformly reserved for public safety.
- `136-148 MHz`: treat as mostly not suitable for ordinary public-safety licensing in v1 unless a later ruleset adds a governmental/federal profile.
- `406.1-430 MHz`: treat as land-mobile/coordinated and therefore coordination-required.
- `380-406.1 MHz`: treat as likely not licensable in v1.
- `450-470 MHz`: treat as coordination-required.

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
- App should support future addition of `federal`, `rail`, or `utility` licensing profiles without rewriting the core engine.

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
- Add unit tests for each standard plan family.

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
2. The app should target typical state, provincial, county, municipal, and agency public-safety users, not federal-only licensing profiles, in v1.
3. The app should classify uncertain licensability as `coordination required`.
4. The app should support manual receive-range override because transmit-only input is insufficient for every VHF and 380-430 scenario.

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
