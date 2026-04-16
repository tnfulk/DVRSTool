# DVRS Planner Sales Quick Reference

## Use Case

Use the DVRS Planner to quickly screen whether a customer's existing system frequencies appear to fit a standard Motorola Solutions DVR-LX in-band DVRS plan.

## Before You Start

Confirm the customer information first:

- country: `United States` or `Canada`
- system frequency configuration:
  - `700 only`
  - `800 only`
  - `700 and 800`
- customer `Mobile TX Frequency` low and high for the applicable band or bands

Optional if known:

- exact `DVRS TX`
- exact `DVRS RX`
- agency and quote details

## Fast Workflow

1. Select the country.
2. Select the system frequency configuration.
3. Enter the customer's existing `Mobile TX Frequency` values.
4. Add exact `DVRS TX` and `DVRS RX` only if you want to test a specific known setup.
5. Run the evaluation.
6. Review the technically valid plans, warnings, and quote draft.

## How To Read The Result

- `TECHNICALLY_VALID`: standard plan appears to fit technically
- `TECHNICALLY_INVALID`: planner could not find a technically compliant standard fit
- `LIKELY_LICENSABLE`: appears aligned with encoded guidance
- `COORDINATION_REQUIRED`: needs additional review or coordination
- `LIKELY_NOT_LICENSABLE`: appears unlikely under encoded guidance

## What To Do Next

If one or more plans are technically valid:

- use the candidate plans to guide the quote conversation
- capture the proposed DVRS TX and DVRS RX
- use the quote draft and PDF summary for internal follow-up
- do not describe the result as final licensing approval

If the result is technically valid but `COORDINATION_REQUIRED`:

- keep the plan in scope
- flag that additional review is needed
- involve Motorola Solutions presales engineering if confirmation is needed before quoting

If the tool cannot find a technically valid plan:

1. Confirm that the information provided is accurate.
2. Re-check the country, band selection, and entered customer frequencies.
3. Re-check exact `DVRS TX` and `DVRS RX` if those were entered.
4. Contact Motorola Solutions presales engineering for additional support.

Motorola Solutions presales engineering may involve the DVRS product management and development engineering teams to make additional recommendations or validate a custom design for that customer.

## Important Limits

- This is a planning aid, not final approval.
- The tool does not replace licensing review, coordination, or engineering signoff.
- Do not promise a custom solution unless Motorola Solutions presales engineering has reviewed it.

## Maintenance Note

This quick-reference guide and the full sales guide in `docs/salesperson-user-guide.md` should be reviewed during documentation passes whenever repository changes affect supported workflow, inputs, outputs, statuses, or escalation guidance.

Documentation review for release `0.1.2`: the current web and packaged desktop experiences carry Motorola Solutions branding assets in the application header and icon surfaces, the footer now shows the current build tag for support and version confirmation, and the release handoff uses versioned Windows build output folders, with no change to the planner workflow described above.

Maintain the matching PDF exports in `docs/salesperson-quick-reference.pdf` and `docs/salesperson-user-guide.pdf` during the same documentation pass.

The repo front page in `README.md` and the release handoff workflow in `docs/release-process.md` both treat these PDF companions as release-ready user documents when they are delivered alongside the Windows executable.
