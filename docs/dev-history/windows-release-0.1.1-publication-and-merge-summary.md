# Windows Release 0.1.1 Publication And Merge Summary

## Scope

This follow-up documented and completed the publication-preparation flow for DVRS Planner `0.1.1` after the branding, packaging, and release-script updates were already implemented in source.

## What Changed

- regenerated the salesperson-facing PDF companions and refreshed the sales-guide review notes so the documentation freshness checks remained satisfied after the release-playbook changes
- reran the full test suite and confirmed a green result with the existing optional FastAPI client test still skipped
- rebuilt the Windows desktop package successfully with the hardened versioned build flow, producing `dist-release-011\DVRSPlanner.exe`
- smoke-tested the packaged executable and confirmed that it stayed running through startup without packaged-runtime log errors
- created, pushed, and merged the `codex-windows-release-0-1-1` branch into `main` through GitHub
- synced the merged GitHub `main` branch back to the local repository
- ran local `git gc` housekeeping after the merge to pack loose objects and reduce GitGUI maintenance warnings

## Release Outcome

The repository finished this thread with:

- a validated `0.1.1` Windows desktop artifact under `dist-release-011\DVRSPlanner.exe`
- current companion user documents in `docs\salesperson-user-guide.pdf` and `docs\salesperson-quick-reference.pdf`
- merged release-ready source and documentation changes on `main`
- updated release/build documentation that explains versioned output folders, fail-fast packaging behavior, locked-folder retry handling, and the current dependency on `dvrs_tool/api.py` as the version source

## Notes

- The built executable remained intentionally outside normal Git history.
- The release-playbook caveat about eventually switching `build_windows.ps1` to a dedicated version module was preserved in the documentation suite for future maintenance.
