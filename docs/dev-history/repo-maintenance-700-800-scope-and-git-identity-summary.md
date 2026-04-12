# Repo Maintenance, 700/800 Scope Reduction, and Git Identity Cleanup

## 1. Context
This thread combined repository maintenance work with a product-scope change for the DVRS planning tool. The work started with fixing a Git commit failure, then moved into narrowing the project to 700 MHz and 800 MHz support only, and ended with cleaning up Git author metadata for both future and historical commits.

## 2. Problem Statement
Several distinct problems were addressed:

- Git commits were failing because the repository could not create `.git/index.lock`.
- The project still documented and partially implemented VHF and UHF support even though the desired product scope had shifted to 700 MHz and 800 MHz only.
- Existing tests, UI text, and PDF output still referenced VHF and UHF behavior that was no longer intended to ship.
- Git author metadata was inconsistent with the desired identity, first because of an `author identity unknown` concern and then because the configured email needed to be updated from `k1ld4@local` to `tnfulk@gmail.com`.

## 3. Key Decisions
- Decision: Repair the `.git` permission issue by removing an explicit Windows `DENY` ACL entry on the repository's `.git` directory.
  - Rationale: The commit failure was caused by Windows denying writes inside `.git`, not by Git hooks or missing user identity.
  - Alternatives considered (if any): Hooks and stale lock-file causes were checked first and ruled out.

- Decision: Stage the current tracked changes and commit them as `Project status`.
  - Rationale: The user explicitly asked to stage and commit the current work once the repository commit issue was resolved.
  - Alternatives considered (if any): None beyond verifying the repo could create lock files again before committing.

- Decision: Reduce the documented and implemented product scope to 700 MHz, 800 MHz, and mixed 700/800 systems only.
  - Rationale: The user explicitly directed the project to focus on those bands and to treat VHF/UHF as future roadmap items.
  - Alternatives considered (if any): None; the abandoned path was continuing to carry VHF/UHF support in the live product.

- Decision: Remove VHF/UHF references from the engine, models, technical plan dataset, UI, PDF export, and active tests instead of merely hiding them in the frontend.
  - Rationale: Full removal keeps runtime behavior, documentation, and test coverage aligned and avoids misleading future engineers or users about supported functionality.
  - Alternatives considered (if any): Leaving dormant support in code was implicitly rejected because the request asked for removal, not just UI concealment.

- Decision: Preserve VHF and UHF as explicit roadmap items in the project charter/specification.
  - Rationale: The user wanted those bands deferred, not forgotten.
  - Alternatives considered (if any): Fully deleting mention of VHF/UHF from the design doc was not chosen because future support remained relevant.

- Decision: Set both repo-local and global Git identity settings, then rewrite the repo's existing commit history to replace `k1ld4@local` with `tnfulk@gmail.com`.
  - Rationale: The repo-local fix addressed immediate commit behavior, the global fix prevented future identity failures elsewhere, and the history rewrite cleaned up prior metadata.
  - Alternatives considered (if any): Leaving old commits unchanged was rejected after the user explicitly asked to update existing commits in the repo.

## 4. Implementation Summary
The thread first diagnosed the failed commit flow by checking Git status, hooks, local identity, and dry-run commit behavior. The actual root cause was a Windows ACL problem on `.git`, where an explicit deny rule blocked creation of `.git/index.lock`. That ACL entry was removed with elevated permissions, Git write access was revalidated, and the existing tracked changes were staged and committed as `Project status`.

The product-scope change then updated `dvrs-web-app-design.md` so the charter and specification describe only 700 MHz, 800 MHz, and mixed 700/800 scenarios. VHF and UHF were moved into a roadmap section. In the codebase, VHF/UHF enums and plan families were removed from the domain model and plan dataset. Engine band detection was narrowed to 700/800 windows, UHF-specific pairing logic was dropped, and plan-hint selection was simplified to the remaining supported bands. UI band options and planning notes were updated accordingly, and the PDF export table was simplified to a 700/800-only layout. Obsolete VHF/UHF tests were deleted while retaining regression coverage for 700-only, 800-only, and mixed 700/800 behavior.

Finally, Git identity configuration was inspected and normalized. The repo already had a local identity of `k1ld4 <k1ld4@local>`, so a matching global identity was added first to eliminate `author identity unknown` failures elsewhere. After the user supplied `tnfulk@gmail.com`, both local and global `user.email` settings were updated. The repository history was then rewritten with `git filter-branch` to change existing author and committer emails from `k1ld4@local` to `tnfulk@gmail.com`, using a temporary stash to preserve uncommitted working changes during the rewrite.

## 5. Challenges & Iterations
- The initial commit failure investigation could have pointed to hooks or missing Git identity, but the actual issue was Windows filesystem ACLs on `.git`.
- Removing the explicit deny ACL fixed the repository itself, but validation inside the Codex sandbox still required elevated execution to prove Git could write to `.git`.
- The first attempt to rewrite commit history failed because the repository had unstaged changes, which blocked `git filter-branch`.
- The second rewrite attempt failed because of PowerShell quoting around the `--env-filter` script.
- The final successful rewrite required three coordinated steps: stash the worktree, run `git filter-branch` with a literal filter string, and pop the stash back onto the rewritten history.

## 6. Final Outcome
The repository can commit again, and the previously blocked commit was completed as `Project status`. The active DVRS product scope is now explicitly 700 MHz, 800 MHz, and mixed 700/800 only across documentation, engine behavior, UI, PDF export, and tests. VHF and UHF are now documented as future roadmap items rather than current functionality. Git is configured to use `tnfulk@gmail.com` for future commits, and the repo's existing commits were rewritten so their author and committer metadata also use that email.

## 7. Open Questions / Follow-ups
- If the rewritten history is ever pushed to a remote later, any collaborators or downstream clones would need to reconcile the new commit hashes.
- The current global Git name remains `k1ld4`; only the email was updated to the real address in this thread.
- VHF and UHF support were intentionally removed from the active product surface and may need a deliberate reintroduction plan later if roadmap priorities change.

## 8. Affected Files / Components
- `dvrs-web-app-design.md`
- `dvrs_tool/models.py`
- `dvrs_tool/plan_data.py`
- `dvrs_tool/engine.py`
- `dvrs_tool/pdf_export.py`
- `dvrs_tool/cli.py`
- `dvrs_tool/static/index.html`
- `tests/test_engine.py`
- `.git/config`
- `C:/Users/k1ld4/.gitconfig`
- Git history for `master`
