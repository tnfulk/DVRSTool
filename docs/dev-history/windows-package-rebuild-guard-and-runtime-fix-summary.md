# Windows Package Rebuild Guard And Runtime Fix

## 1. Context
The repository already included a Windows desktop packaging path for the DVRS planner, but the packaged executable failed at runtime after opening on end-user machines. The repo also lacked a persistent guardrail to remind future editors to rebuild the tracked Windows executable when the application changed.

## 2. Problem Statement
The packaged `DVRSPlanner.exe` crashed during embedded server startup because uvicorn attempted to configure console-aware logging formatters inside a PyInstaller windowed executable where standard streams may be missing. Separately, source changes to the calculation engine, desktop bootstrap path, or UI could be committed without rebuilding the Windows release asset, and the resulting executable was too large to store in normal GitHub Git history.

## 3. Key Decisions
- Decision: Disable uvicorn's default logging configuration for the embedded desktop runtime and replace it with packaged-runtime-safe bootstrap helpers.
- Rationale: The crash was caused by uvicorn formatter initialization touching `sys.stderr.isatty()` in a `console=False` executable. Avoiding that logging config removes the failure at the source.
- Alternatives considered: Running as administrator was tested and rejected because the failure was not permission-related. Leaving uvicorn console logging enabled and only patching stdio was considered too fragile as a primary fix.

- Decision: Add regression tests that specifically cover packaged desktop startup safeguards.
- Rationale: The failure mode only appears in packaged/windowed contexts, so dedicated tests are needed to catch regressions before future rebuilds.
- Alternatives considered: Relying on manual launch testing alone was rejected because it is easy to skip and too late in the process.

- Decision: Publish the Windows executable through GitHub Releases instead of storing the `.exe` in normal Git history, and update the reminder workflow to point editors to the release process.
- Rationale: The packaged Qt WebEngine executable exceeds GitHub's standard file-size limit, while GitHub Releases is a better fit for distributing versioned desktop binaries.
- Alternatives considered: Tracking the executable in Git was abandoned after the push failed due to GitHub's 100 MB limit. Git LFS was considered but not chosen for the initial repo flow because a release-asset model keeps the source repository leaner for contributors.

## 4. Implementation Summary
The desktop launcher in `dvrs_tool/desktop.py` now disables uvicorn's default log config, restores missing `stdout` and `stderr` streams for packaged runs, and writes packaged-runtime logs to a temp-file fallback when appropriate. New regression tests in `tests/test_desktop.py` verify the uvicorn config, missing-stdio repair behavior, and file-logging behavior for frozen builds. The repo now includes `.github/workflows/windows-package-reminder.yml` to warn maintainers when meaningful application files change so the Windows package can be rebuilt and published through GitHub Releases. Documentation in `README.md`, `codex.md`, and `docs/release-process.md` was updated to describe the runtime fix, rebuild expectations, and the GitHub Releases publication flow for the `0.1.0` Windows release.

## 5. Challenges & Iterations
The initial packaging effort produced a working executable file but the packaged runtime still failed immediately when launched on a real machine. The stack trace revealed the real issue was uvicorn logging bootstrap inside a windowed executable, not administrative privileges or application logic. The packaging workflow itself also needed cleanup so only the real release artifact is tracked while temporary PyInstaller files remain ignored.

## 6. Final Outcome
The `0.1.0` Windows release artifact was rebuilt successfully and verified to stay running through startup. The startup crash caused by uvicorn console logging is now fixed in source, covered by tests, and backed by a repo automation and documentation flow that prompts future rebuilds and GitHub Release publication when the application changes.

## 7. Open Questions / Follow-ups
- Consider adding a fuller end-to-end packaged smoke test that exercises the embedded UI and PDF export flow, not just process startup.
- Decide whether future releases should continue tracking the executable in-repo or move to GitHub Releases while keeping the reminder workflow logic.

## 8. Affected Files / Components
- `.github/workflows/windows-package-reminder.yml`
- `.gitignore`
- `README.md`
- `codex.md`
- `docs/release-process.md`
- `dvrs_desktop.spec`
- `dvrs_tool/desktop.py`
- `tests/test_desktop.py`
