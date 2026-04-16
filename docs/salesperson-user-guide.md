# DVRS Planner User Guide for Sales

## Purpose

This guide explains how a salesperson should use the DVRS Planner to screen standard Motorola Solutions DVR-LX in-band DVRS options for a customer opportunity.

The tool is intended to help you:

- enter the customer system frequencies that already exist
- identify which standard plans appear technically valid
- see when a result is likely to require coordination or additional engineering review
- produce an ordering-summary style output that supports quoting and internal follow-up

The tool is not a final authority on licensing, coordination, or custom engineering approval.

## Source Basis

The current planner workflow is based primarily on these bundled project references:

- `dvr-lx-ordering-guide-1 (1).pdf`
- `Introduction to  In-Band Operation-v1_2019-06-19.pdf`
- `supplemental-ordering-form-b2bf88f7.pdf`
- `dvrs-web-app-design.md`

The development history in `docs/dev-log.md` and `docs/dev-history/` further explains how the current planning rules and workflow were implemented.

## What The Tool Covers

The current release is focused on standard in-band DVRS planning for:

- `United States`
- `Canada`
- `700 only` system frequency configurations
- `800 only` system frequency configurations
- mixed `700 and 800` system frequency configurations

The current release does not provide active VHF or UHF planning support, direct regulator lookup, automatic licensing approval, or custom filter-plan design.

## When To Use This Tool

Use the DVRS Planner when you need an early answer to questions such as:

- "Which standard DVRS plans are worth discussing for this customer?"
- "Does the customer's current system frequency layout appear compatible with a standard plan?"
- "Do we appear to have a straightforward standard recommendation, or do we need engineering support?"

This is a planning and qualification tool. It helps narrow the conversation, but it does not replace Motorola Solutions presales engineering review, regulatory coordination, or final design approval.

## Information You Should Gather First

Before running the tool, collect the most accurate customer information you can. The output quality depends heavily on the quality of the input.

At minimum, confirm:

- country: `United States` or `Canada`
- whether the customer system is `700 only`, `800 only`, or `700 and 800`
- the customer's existing `Mobile TX Frequency` low and high values for the applicable band or bands

If available, also collect:

- exact proposed or existing `DVRS TX` and `DVRS RX`
- agency name
- quote date
- mobile radio type
- control head type
- MSU antenna type
- any agency notes that may matter for quoting or engineering review

If you are unsure whether the customer frequencies are accurate, pause and verify them before relying on the result.

## Basic Workflow

1. Open the DVRS Planner web or desktop application.
2. Select the country.
3. Select the system frequency configuration:
   - `700 only`
   - `800 only`
   - `700 and 800`
4. Enter the customer's existing `Mobile TX Frequency` range for the relevant band or bands.
5. Add optional exact `DVRS TX` and `DVRS RX` values only if you already know them and want the planner to test that exact setup.
6. Add optional quote details if you want the ordering summary to be more complete.
7. Run the evaluation.
8. Review the `System`, `Plans`, and `Quote Draft` sections together before making a recommendation.

## How To Read The Results

The planner separates technical fit from regulatory confidence. That distinction matters.

### Technical Status

- `TECHNICALLY_VALID`: the encoded standard-plan rules found a compliant technical fit
- `TECHNICALLY_INVALID`: the planner could not find a compliant technical fit for that standard plan

### Regulatory Status

- `LIKELY_LICENSABLE`: the result appears to align with the encoded country-specific guidance
- `COORDINATION_REQUIRED`: the result may still be possible, but additional review or coordination is needed
- `LIKELY_NOT_LICENSABLE`: the result appears unlikely to succeed under the encoded guidance
- `NOT_EVALUATED`: the planner did not make a regulatory determination for that case

### Practical Sales Reading

- A technically valid result gives you a candidate standard path to discuss.
- A coordination-required result is not a stop sign. It means the opportunity probably needs additional technical or regulatory review before you treat it as straightforward.
- A technically invalid result means the tested standard plan should not be presented as a clean fit based on the information currently entered.

## Recommended Salesperson Workflow

### If One Or More Standard Plans Are Technically Valid

Use the result to guide the next internal and customer conversation:

- identify the technically valid standard plan candidates
- note any warnings or coordination-related messages
- capture the proposed DVRS TX and DVRS RX shown by the planner
- use the `Quote Draft` summary and PDF export to support quote preparation and internal review
- avoid describing the result as final licensing approval

### If The Tool Shows Only `COORDINATION_REQUIRED` Regulatory Outcomes

Treat the result as a qualified lead, not a final answer.

Your next step should usually be to:

- keep the technically valid candidate in scope
- note that coordination or additional review is still required
- involve Motorola Solutions presales engineering if the opportunity needs confirmation before quoting

### If The Tool Cannot Find A Technically Valid Plan

Do not assume the opportunity is dead based on the first pass.

Follow this sequence:

1. Confirm that the information provided is accurate.
2. Re-check the country, band selection, and entered customer system frequencies.
3. If exact `DVRS TX` and `DVRS RX` were entered, confirm those values are correct and intended.
4. After confirming the information, contact Motorola Solutions presales engineering for additional support.

Motorola Solutions presales engineering may involve the DVRS product management and development engineering teams to:

- make additional recommendations
- validate a custom design for that customer

This escalation path is especially important when:

- the customer may need something outside a standard plan
- the source frequency information may be incomplete or inconsistent
- the opportunity appears close to a workable design but the tool still rejects all standard options
- the customer wants a custom or highly constrained solution

## Common Mistakes To Avoid

- Do not enter desired DVRS frequencies in place of the customer's existing system frequencies unless the workflow specifically asks for exact `DVRS TX` and `DVRS RX`.
- Do not treat a technically valid result as automatic licensing approval.
- Do not assume a technically invalid result means there is no possible path forward without first verifying the inputs.
- Do not promise a custom solution unless Motorola Solutions presales engineering has reviewed it.
- Do not overlook warnings, coordination notes, or rule-based failure reasons in the result cards.

## How To Use The Quote Draft

The `Quote Draft` section is designed to support internal sales and quoting workflows.

Use it to:

- capture the customer system summary
- capture the proposed DVRS frequencies from the selected plan
- preserve optional opportunity details such as agency name and radio/control-head selections
- export a PDF summary for internal circulation or quote preparation

The generated PDF is an ordering-summary style document. It is useful for planning and communication, but it is not a final approved Motorola Solutions ordering artifact by itself.

## What To Say Externally

The safest external positioning is:

- the planner identified standard options that appear technically compatible based on the information provided
- some cases may still require coordination or engineering confirmation
- if a standard configuration cannot be confirmed from the current inputs, Motorola Solutions presales engineering can review the opportunity and determine whether additional recommendations or a custom design review are appropriate

## Summary

The DVRS Planner helps sales quickly screen standard DVR-LX in-band opportunities, organize the result, and decide when to escalate.

Use it to narrow the conversation, not to replace engineering judgment.

When the tool cannot find a technically valid plan, first confirm the information is accurate, then contact Motorola Solutions presales engineering. That team may bring in DVRS product management and development engineering to recommend next steps or validate a customer-specific design.

## Maintenance Note

This guide and `docs/salesperson-quick-reference.md` should be reviewed during documentation passes whenever repository changes affect supported workflow, inputs, outputs, statuses, or escalation guidance.
