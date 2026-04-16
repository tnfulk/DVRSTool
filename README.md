# DVRS In-Band Planning Service

## Files

- `dvrs_tool/engine.py`: calculation engine
- `dvrs_tool/api.py`: FastAPI wrapper
- `dvrs_tool/desktop.py`: embedded desktop launcher and packaged-runtime safeguards
- `docs/salesperson-user-guide.md`: full salesperson-facing usage guide
- `docs/salesperson-quick-reference.md`: short salesperson quick reference
- `tests/test_engine.py`: engine, API, CLI, and PDF unit tests
- `tests/test_desktop.py`: packaged desktop launcher regression tests
- `tests/test_documentation.py`: documentation freshness and maintenance checks
- `run_tests.py`: test runner
- `requirements.txt`: API dependencies

## Sales documentation

- Full guide (Markdown): `docs/salesperson-user-guide.md`
- Full guide (PDF): `docs/salesperson-user-guide.pdf`
- Quick reference (Markdown): `docs/salesperson-quick-reference.md`
- Quick reference (PDF): `docs/salesperson-quick-reference.pdf`

These sales documents should be reviewed and updated during the documentation pass whenever changes to the tool affect supported workflow, inputs, outputs, statuses, or escalation guidance.

When these user documents are part of a release handoff, regenerate the PDFs with `python .\tools\generate_sales_doc_pdfs.py` and include the updated PDF companions in the normal source commit. The Windows release workflow in `docs/release-process.md` now treats these files as companion release materials when they are updated for delivery alongside the executable.

## Run tests

```powershell
python run_tests.py
```

## Run the API

Install dependencies first:

```powershell
python -m pip install -r requirements.txt
```

Start the service:

```powershell
uvicorn dvrs_tool.api:app --reload
```

Then open the draft planner UI:

```text
http://127.0.0.1:8000/
```

## Run the desktop app

Install the desktop runtime dependencies first:

```powershell
python -m pip install -r requirements-desktop.txt
```

Launch the planner in its own desktop window:

```powershell
python run_desktop.py
```

The desktop launcher starts the API server internally and opens the planner in an embedded application window. Users do not need to start `uvicorn` manually or use a browser.

For packaged windowed builds, the launcher disables uvicorn's default console logging configuration and falls back to file logging when standard streams are unavailable. This prevents the `Unhandled exception in script` startup failure that can occur when a PyInstaller `console=False` executable tries to configure terminal-aware formatters.

## Build a Windows executable

This branch now includes a PyInstaller spec for a windowed desktop build:

```powershell
.\build_windows.ps1
```

The packaged executable will be written under `dist-release\DVRSPlanner.exe`.

The local build artifact is `dist-release\DVRSPlanner.exe`. This file is intentionally not committed to normal Git history because the packaged WebEngine-based desktop binary is larger than GitHub's standard file-size limit. Publish the executable through GitHub Releases instead.

## Desktop packaging notes

- The desktop executable is built as a windowed PyInstaller app, so it may not have usable `stdout` or `stderr` streams at runtime.
- The embedded uvicorn server must not use uvicorn's default logging config in that environment. The desktop launcher now passes `log_config=None` when starting the embedded server.
- Packaged runtime warnings and errors can be written to the temporary log file `dvrs_planner.log` in the current user's temp directory.
- `python run_tests.py` now includes regression coverage for the packaged desktop bootstrap path so missing-stdio startup failures are caught before future rebuilds.
- The repository includes a GitHub Actions reminder workflow that warns maintainers when significant application files change so the Windows package can be rebuilt and published through GitHub Releases.

## Publish a Windows release

Use the documented playbook in `docs/release-process.md` when you need to publish a Windows executable for a tagged release such as DVRS Planner `0.1.0`.

## Troubleshooting packaged startup

If `DVRSPlanner.exe` opens with an `Unhandled exception in script` error before the UI appears:

- confirm the build includes the current `dvrs_tool/desktop.py` changes that disable uvicorn's default log config
- inspect the packaged desktop log file in the system temp directory for the underlying exception
- rebuild the executable after running `python run_tests.py` to ensure the desktop bootstrap regression tests still pass

## Use GitHub CLI in this workspace

This Codex environment may inject invalid proxy variables that break `gh` API calls. Use the repo-local wrapper to clear those variables just for the command:

```powershell
.\gh-safe.ps1 auth status
.\gh-safe.ps1 pr status
.\gh-safe.ps1 pr create
```

The wrapper restores the original PowerShell environment after `gh` exits, so it is safe to use for normal GitHub auth, push, PR, and Actions workflows.

## Use the CLI

Run the tool directly from PowerShell:

```powershell
python -m dvrs_tool --country "United States" --mobile-tx-low 806.0 --mobile-tx-high 809.0
```

Example with optional manual RX override:

```powershell
python -m dvrs_tool --country Canada --mobile-tx-low 151.0 --mobile-tx-high 151.2 --mobile-rx-low 156.0 --mobile-rx-high 156.2
```

Show argument help plus the returned JSON shape:

```powershell
python -m dvrs_tool --help
```
