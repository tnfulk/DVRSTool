# Project Guide Instructions Alignment

## User Message
Take a look at the `Project Guide.pdf` doc in the repo. Using the project instructions in the guide as a target, evaluate the `dvrs-web-app-design.md` and `codex.md` files and consider if there are areas that the current instructions do not capture that are recommended or required by the project guide doc. Report any suggestions around changes that might improve these documents to incorporate closing the gaps found.

## Assistant Response
Reviewed the project guide alongside both Markdown files and identified the main gaps. The strongest missing areas were:

- `dvrs-web-app-design.md` lacked an explicit problem statement in the guide's format.
- `dvrs-web-app-design.md` did not include a dedicated project plan section or an ordered task list with acceptance criteria.
- `dvrs-web-app-design.md` described current implementation well but did not fully reflect the guide's emphasis on incremental delivery and MVP framing.
- `codex.md` strongly emphasized documentation but did not explicitly require the guide's build cycle of spec, run, test, commit, and repeat.
- `codex.md` also needed clearer spec-first rules, acceptance-criteria awareness, and context-recovery guidance.

Recommended updates included adding a problem statement, user workflow, MVP definition, plan section, and task/acceptance-criteria section to the specification, plus adding spec-first execution, verification, testing, incremental delivery, commit checkpoint, and secret-handling rules to the Codex instruction file.

## User Message
go ahead and defind the concrete edits and patch the files.

## Assistant Response
Patched both files directly.

Changes made in `dvrs-web-app-design.md`:

- added `## 0. Problem Statement`
- added `### 2.11 User Workflow`
- expanded testing expectations with incremental-run and explanation-quality requirements
- added `### 2.14 Acceptance-Oriented Verification Targets`
- added `## 5. Plan` with architecture plan and MVP definition
- added `## 6. Tasks` with ordered task sequence and acceptance criteria
- renumbered later top-level sections accordingly

Changes made in `codex.md`:

- added `## Spec-First Execution`
- added `## Required Development Cycle`
- added `## Incremental Delivery Rules`
- added `## Verification and Testing`
- added `## Acceptance Criteria`
- added `## Commit Checkpoints`
- added `## Project Memory and Context Recovery`
- added `## Security and Secret Handling`

The updated files were then read back to confirm the new sections fit cleanly and did not conflict with the pre-existing documentation and Windows release rules.

## User Message
Thanks for the updates. this task is complete, please document, then stage, commit, and push to github

## Assistant Response
Documented the thread in the repository history, prepared a scoped commit that excludes the unrelated untracked `Project guide.pdf`, and then staged, committed, and pushed the documentation changes to GitHub.
