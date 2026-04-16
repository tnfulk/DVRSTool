# Windows Package Rebuild Guard And Runtime Fix

## User Request
The user asked for the Windows packaged executable startup failure to be fixed, for safeguards to be added so similar failures are caught before future rebuilds, and for repository-specific workflow guidance that prompts rebuilds when significant application changes occur. The user then asked for the resulting `0.1.0` Windows build and all pending source changes to be packaged, committed, and pushed.

## Assistant Work Summary

### 1. Investigated the packaged startup failure
- Reproduced the packaged launcher behavior and reviewed the runtime stack trace.
- Confirmed the crash occurred before the web UI loaded, during embedded uvicorn startup.
- Identified the root cause as uvicorn's default logging bootstrap calling formatter logic that expects `sys.stderr` and `sys.stdout` to exist in a PyInstaller `console=False` executable.

### 2. Implemented the runtime fix
- Updated `dvrs_tool/desktop.py` so the embedded uvicorn server starts with `log_config=None`.
- Added a standard-stream fallback for packaged windowed runs so missing `stdout` or `stderr` are safely replaced with `os.devnull`.
- Added packaged-runtime file logging to the temp directory using `dvrs_planner.log` so startup issues can still be inspected without a console.

### 3. Added regression coverage
- Created `tests/test_desktop.py`.
- Added tests to verify:
  - uvicorn config disables the default console logging setup
  - missing standard streams are repaired
  - frozen builds use file logging
  - normal console runs do not unnecessarily enable file logging
- Ran `python run_tests.py` and confirmed the updated suite passed.

### 4. Added repository workflow reminders
- Created `.github/workflows/windows-package-reminder.yml`.
- Configured it to warn maintainers when significant application files change so the Windows package can be rebuilt and published through GitHub Releases.
- Updated `codex.md` to mirror that repo-specific rule for local Codex work.

### 5. Updated documentation
- Expanded `README.md` with desktop-packaging notes, packaged-runtime logging guidance, and the new rebuild reminder workflow.
- Added `docs/release-process.md` with step-by-step GitHub Releases instructions, exact `gh` commands, and suggested Codex prompts for editors who are less familiar with release publishing.
- Added a structured development-history summary for the change.
- Added this raw-thread archive entry.

### 6. Rebuilt and verified the Windows package
- Rebuilt the Windows executable as DVRS Planner `0.1.0`.
- Verified the rebuilt `dist-release/DVRSPlanner.exe` launched and stayed running through startup.
- Cleaned the packaging footprint so `dist-release/` is treated as a local build and release-asset output rather than a normal Git-tracked artifact.

## Key Decisions
- The startup issue was fixed at the uvicorn logging configuration layer rather than by asking users to run as administrator.
- The repo now treats `dist-release/DVRSPlanner.exe` as a local release asset that is published through GitHub Releases instead of committed to normal Git history.
- The reminder mechanism was implemented both in repository automation and local project instructions so it is visible in normal editing and CI workflows, with explicit release prompts documented for editors.

## Final State
- Source-level desktop runtime fix implemented
- Desktop regression tests added and passing
- Repo reminder workflow added
- Docs updated
- `0.1.0` Windows executable rebuilt successfully
