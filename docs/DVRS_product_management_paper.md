# DVRS Tool: Product Development Paper

## Introduction

For this project, I built a software tool to help evaluate Motorola Solutions DVR-LX standard in-band DVRS configurations. The practical problem was simple to state but messy to do by hand: given a customer's available system frequencies, determine which standard plans are technically feasible, which are likely to require coordination, and how to present the result in a form that is actually useful to someone doing planning or quoting work.

I chose this problem because it sits in a place where software can genuinely reduce friction. The source material exists, but it is scattered across vendor ordering guides, in-band operation notes, and ordering-form conventions. That means the work is repeatable enough to automate, but detailed enough that a careless tool would be dangerous. I was not trying to replace coordination, licensing review, or Motorola review. I was trying to make the earlier planning step faster, clearer, and less error-prone.

The final repo contains more than code. It includes a constitution and specification in `dvrs-web-app-design.md`, a running development log in `docs/dev-log.md`, raw chat-thread records in `docs/raw-threads`, and summarized engineering history in `docs/dev-history`. That documentation matters because this course project was explicitly about software product development, not just coding. In that sense, the most important result is not only that the tool works, but that the process is visible: how I framed the problem, narrowed scope, made tradeoffs, corrected wrong assumptions, and used an agent in a disciplined way.

## Problem and Context

The problem I solved was early-stage DVRS plan evaluation for public-safety radio systems. The intended users are the people between the customer and the final approved configuration: technicians, planners, procurement staff, and product or presales engineers. They need to answer questions like: given the system frequencies this customer already has, which standard DVRS plans are even worth considering, what DVRS TX/RX ranges remain feasible after applying the spacing rules, and does the result look plausible in the United States or Canada?

This matters because the manual alternative is slow and easy to get wrong. A planner has to interpret plan windows, pairing offsets, spacing rules, and regulatory context from PDFs and then convert that into a usable recommendation. In the repo history, this is exactly where complexity kept showing up: cross-band interpretation, fixed plan windows, mixed 700/800 behavior, and the difference between technical feasibility and regulatory confidence. Those are not impossible tasks, but they are the kind of tasks where a small mistake can send someone down the wrong path early.

The main alternatives were straightforward. One was to keep doing the work manually with the ordering guide and supplemental form. That preserves expert judgment, but it is inconsistent, hard to audit, and not very scalable. Another was a spreadsheet or a lightweight calculator. That would help with arithmetic, but it would still struggle to explain why a plan fails, handle mixed-band cases cleanly, or preserve the distinction between technically valid and regulatorily uncertain. A third alternative was to skip software entirely and rely on a Motorola presales engineer or coordinator from the start. That is still necessary at the end of the process, but it is too heavy to be the first step for every scenario.

My solution differs because it creates a planning layer in the middle. The DVRS tool does not pretend to be the final authority. Instead, it narrows the search space, shows the reasoning, returns the surviving compliant subrange when only part of a plan remains viable, and produces an ordering-form-style summary that fits the workflow the user is already in.

One of the most important product decisions was scope. Earlier iterations touched VHF and UHF, but I deliberately narrowed the active product to 700 MHz, 800 MHz, and mixed 700/800 systems. That decision is documented in `docs/dev-history/repo-maintenance-700-800-scope-and-git-identity-summary.md`. I think that was the right call. The assignment emphasized building something ambitious, but also stressed process and product judgment. For this project, the right move was not "support every band eventually mentioned in the source material." The right move was to build one coherent tool around the part of the problem I could define, test, and defend.

## Product Development Process

The clearest place where I applied the course concepts was at the very beginning: I wrote a constitution and a specification before pushing deeper into implementation. In `dvrs-web-app-design.md`, I defined the purpose of the tool, the user-facing scope, the output states, the major modules, and a set of product principles. Those principles were not filler. They acted like decision filters. The most important ones were accuracy before convenience, explainability over black-box output, regulatory humility, vendor-faithful logic, and modular separation between technical and regulatory validation.

That first step reflects the strategy and vision part of the course. I had to decide what kind of product this actually was. It was not a generic radio-planning app. It was not a compliance oracle. It was a planning aid for a narrow workflow, and the spec says that directly. That framing drove later choices. For example, I explicitly kept the tool conservative when licensing certainty was unclear. The product principle there was simple: if confidence is low, say "coordination required," not "valid." That was a product-management decision shaped by stakeholder risk, not just a coding detail.

The project also reflects the course emphasis on moving from needs to requirements to implementation. The need started vague: help someone figure out what DVRS plans are possible. I translated that into specific inputs, derived values, output states, and UI panes. The spec defines required fields, system-band configurations, how system TX/RX should be derived, how candidate plans should be selected, how fixed DVRS ranges should be handled, and how regulatory status should be classified. That decomposition became the architecture. The functional breakdown in the spec maps directly to the code organization in `dvrs_tool/models.py`, `dvrs_tool/plan_data.py`, `dvrs_tool/engine.py`, `dvrs_tool/api.py`, and the frontend.

Design tradeoffs came up constantly. The biggest one was accuracy versus usability. I wanted the tool to be useful enough to help someone move quickly, but not so "helpful" that it hid uncertainty. That tension shows up all over the repo. A good example is the shift in the engine toward spacing-first logic. In `docs/dev-history/dvrs-engine-api-spacing-rules-summary.md`, the engine moves through several interpretations of the ordering guide: first a looser modeled-window approach, then stricter guide-window alignment, then a more nuanced spacing-first solver that still respects fixed plan boundaries. That was a real tradeoff. If I enforced guide windows too rigidly, I would reject cases where a compliant subrange still exists. If I loosened the model too far, I would risk inventing false positives. The final design tries to split that difference in a way that stays useful without becoming reckless.

Another important tradeoff was simplicity versus capability. The tool initially carried broader band support, but that made the product harder to explain and harder to validate. Narrowing the scope to 700/800 only was a product decision rooted in feasibility, not just convenience. The same was true of the UI shift toward "system frequencies the customer actually has." In the raw thread archive for the system-frequency UI work, my instructions were very direct: users should be able to enter only 800, only 700, or both, and the tool should evaluate the right parent plans behind the scenes. That is a good example of product thinking shaping the interface. The user should not need to think in terms of internal submodels just because the engine does.

Benchmarking in this project was mostly artifact and workflow benchmarking rather than competitor benchmarking. I repeatedly compared the product to the Motorola ordering guide, the in-band operation document, and the supplemental ordering form. Those sources acted as the external baseline. I also treated the target workflow itself as a benchmark: if the final result did not look usable to a planner or procurement-oriented user, the product had missed the point. That is why the ordering-form summary and PDF export matter. They are evidence that I was not only trying to compute a correct answer; I was trying to package the answer in a form that fits the job to be done.

The project also followed the engineering-discipline requirements from the assignment closely. I wrote the specification first, built incrementally, used version control throughout, tested repeatedly, and maintained project context for the agent. The archived thread summaries make that especially visible. Rather than relying on one long opaque conversation, I turned major work streams into reusable records in `docs/raw-threads`, `docs/dev-history`, and `docs/dev-log.md`. That was partly for organization, but it also became a product-development tool. The better the project memory got, the better the agent performed.

## Technical Approach

The technical approach ended up being modular and layered, which matches both the domain and the course emphasis on functional decomposition. At the center is a data-driven rules engine. `dvrs_tool/models.py` defines the main domain objects. `dvrs_tool/plan_data.py` stores the encoded technical plans and the regulatory classification helpers. `dvrs_tool/engine.py` handles validation, system-band resolution, deterministic pairing, candidate-plan selection, technical evaluation, and ordering-summary assembly. `dvrs_tool/api.py` exposes the engine through FastAPI. The web UI in `dvrs_tool/static/` provides the user-facing workflow. `dvrs_tool/pdf_export.py` creates the ordering-form-style export. Later, I added `dvrs_tool/desktop.py`, `run_desktop.py`, and `dvrs_desktop.spec` so the same product could be delivered in a desktop wrapper.

One key design decision was to keep the plan logic in data, not hard-coded in the UI. This project is fundamentally a rules problem. If the rules are buried in the frontend, every correction becomes harder to audit and test. By keeping plan definitions in `plan_data.py`, I could revise windows, guard bands, and fixed ranges without rewriting the user interface. This also made the system more testable and easier to extend later.

Another important decision was to keep technical validity and regulatory status separate. The constitution called for modular rules engines, and I followed that. A plan can be technically valid and still require coordination. That distinction matters because the product is trying to help with planning, not certify assignability. It would have been simpler to collapse everything into a single green/yellow/red output, but that would have made the product less honest and less useful.

I also made a deliberate choice to reuse the core engine across multiple surfaces. The same underlying logic supports the CLI, API, web UI, PDF export, and desktop runtime. That gave me a cleaner architecture and a more realistic product story. Different users may want different entry points, but the planning logic should stay consistent. The desktop wrapper is a good example of pragmatic product engineering. Instead of rewriting the app natively for Windows, I kept the FastAPI-plus-static-frontend architecture and wrapped it in a Qt WebEngine shell. That was faster, lower risk, and good enough for the intended audience.

The plan-table guard is probably the most product-specific technical safeguard in the repo. In `dvrs_tool/plan_table_guard.py` and `tests/test_plan_table_guard.py`, I added a hash-based confirmation mechanism so changes to the approved plan table require explicit acknowledgment. I added that because the repo history showed repeated corrections to the encoded ranges. In a domain like this, configuration drift is not a minor cleanup issue. It changes the product's behavior in ways that could be hard to notice. That guard is a small but important example of encoding product governance into the codebase.

Working with the agent was effective when I gave it tightly scoped, evidence-backed tasks. The raw threads show that my prompts usually worked best when they were concrete: update the engine to treat the passband rule this way, add these internal submodels but only expose the parent plans, run the full test suite and fix the failures without changing the approved plan table, remove VHF/UHF from active scope but keep them on the roadmap. In those cases, the agent was very productive because the task had clear boundaries and a way to check whether the result was right.

Where the agent was less reliable was in situations where the source material was ambiguous or the environment itself was the problem. The repo history shows several examples: interpreting the ordering guide, dealing with cached frontend assets, diagnosing GitHub CLI failures that turned out to be proxy issues, and tracing failed commits to Windows ACLs on `.git`. In those cases, the agent still helped, but only after I pushed it back toward concrete evidence. My main takeaway is that the agent did not replace product judgment. It made product judgment more necessary.

## Testing and Validation

My testing strategy centered on the rules engine first, then the interfaces built around it. At the time of writing, `python run_tests.py` passes with `52` tests and `1` skipped test. The skipped case is environment-specific: the FastAPI test client is not installed. I think that is a healthy result for this stage of the project, but the more important point is what the tests are actually doing.

The tests are not just smoke tests. They cover band detection, candidate-plan selection, mixed-band behavior, fixed-range handling, surviving compliant subranges, actual licensed DVRS frequency matching, structured API errors, CLI output, PDF export, and the plan-table confirmation guard. That means the tests are aimed at the high-risk parts of the product, not just the easiest code paths.

More importantly, the test suite caught real problems. In `docs/dev-history/dvrs-test-failures-cross-band-fix-summary.md`, a full regression run exposed incorrect behavior around cross-band variants, actual-frequency matching, and active mobile window enforcement. The fix stayed in `dvrs_tool/engine.py` specifically because I had already decided the approved plan table should not move. That is a good example of the tests doing more than confirming behavior after the fact. They forced a more precise understanding of where the defect really lived.

The plan-table validation work is another good example. Repeated corrections to the encoded ranges revealed that the dataset itself needed stronger protection. That led to the hash-based confirmation guard. In other words, one lesson from testing here was that not every important risk is a normal functional bug. Some risks come from silent data drift or from future edits that look harmless but materially change the product.

That said, the testing strategy has obvious gaps. Most of the coverage is at the unit and component level. I do not have formal end-to-end browser tests. I do not have usability testing with real planners. I do not have external validation against actual licensing outcomes. The desktop packaging path was also validated at a lighter level than the core engine. So my assessment of quality is positive but bounded. I trust the product as a planning tool within the rules it encodes. I would not present it as a production-grade authority on licensing or as a fully field-validated user experience.

## Reflection

If I were doing this project again, the main thing I would add earlier is direct user validation. I think I did a good job building around a real workflow and using the ordering form as a practical target, but most of the feedback loop still came from documents, tests, and my own interpretation. Even a small number of structured conversations with people who actually do this planning work would have improved prioritization and probably shortened some later iterations.

I would also make the rule-traceability process more explicit. The repo already has strong documentation compared to a typical student project, but some of the most expensive iterations came from ambiguity in the source material. A future version should probably maintain a direct mapping from encoded rules back to the specific guide page, note, or assumption behind them. That would make reviews easier and make it clearer when the issue is in the code versus in the underlying interpretation.

I would also add end-to-end UI automation. The unit tests did a lot of useful work, but some frontend issues, especially caching or rendering confusion, were harder to reason about than they should have been. A small Playwright-style suite for the main evaluation flow would likely pay for itself quickly.

The biggest thing this project changed for me is how I think about working with an agent. Before doing this, it would have been easy to imagine that the value of the agent was mainly speed. After doing this, I think the real value is speed under constraints. The better I defined the product, the better the agent performed. The worse the project memory was, or the looser the task was, the more likely the agent was to head in the wrong direction. In that sense, product management and agentic coding are deeply connected. A good constitution, a clear spec, explicit scope decisions, and strong tests are not overhead. They are what make the tool usable.

More broadly, this project reinforced a product-development lesson that I think the course was trying to teach directly: building something useful is not just about getting software to run. It is about framing the right problem, narrowing the scope when needed, preserving the reasoning behind tradeoffs, and being honest about uncertainty. I think this project was successful because it kept returning to those questions instead of treating implementation as the whole job.

## References

Repository and project artifacts:

- `dvrs-web-app-design.md`
- `docs/dev-log.md`
- `docs/dev-history/dvrs-engine-api-spacing-rules-summary.md`
- `docs/dev-history/dvrs-system-frequency-ui-and-single-band-submodels-summary.md`
- `docs/dev-history/plan-table-validation-history-summary.md`
- `docs/dev-history/repo-maintenance-700-800-scope-and-git-identity-summary.md`
- `docs/dev-history/windows-desktop-runtime-packaging-summary.md`
- `docs/dev-history/dvrs-test-failures-cross-band-fix-summary.md`
- `tests/test_engine.py`
- `tests/test_plan_table_guard.py`
- `project.pdf`

External product-development references consulted during drafting:

- Scrum Guides. *The Scrum Guide*. [https://scrumguides.org](https://scrumguides.org)
- Atlassian Agile resources on product requirements and product management practice. [https://www.atlassian.com/agile/product-management](https://www.atlassian.com/agile/product-management)
- Teresa Torres, resources on opportunity-solution thinking and continuous product discovery. [https://www.producttalk.org](https://www.producttalk.org)

## Appendix A: Specification Document

The project's constitution and specification are maintained in the repository file `dvrs-web-app-design.md`. In the generated submission document, that file is attached as Appendix A after the main paper so the paper body can stay within the target length while still including the full specification required by the assignment.
