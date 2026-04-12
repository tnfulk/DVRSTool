# Raw Thread: Windows Desktop Runtime And Packaging Path

## Overview
This thread started with a feasibility question about turning the DVRS tool into a Windows executable that includes its own runtime dependencies and avoids registry edits or admin-level installation steps. It then shifted into implementation work on the current branch to create a dedicated desktop application window, an internal production server startup path, and packaging support for future Windows builds. The thread concluded by requesting durable documentation of the work.

## Conversation

### User
Asked whether the contents of the master repo and the current branch could be used to build a Windows executable containing everything needed to run the application as a single installed file, ideally without registry edits or elevated permissions. The user explicitly asked not to build anything yet, only to answer whether it was possible and, if not, what would be needed on the branch.

### Assistant
Inspected the repository to understand the current architecture before answering. The repository was identified as a Python project containing:
- A DVRS calculation engine
- A FastAPI API wrapper
- A static frontend under `dvrs_tool/static`
- A handwritten PDF export helper
- No packaging metadata or build configuration

The assistant also documented an environment note:
- `rg.exe` could not be executed in the environment due to an access error
- PowerShell-native file inspection was used instead

### Assistant Work Log
Key repository findings from the feasibility pass:

- `README.md` documented only:
  - dependency installation via `python -m pip install -r requirements.txt`
  - API startup via `uvicorn dvrs_tool.api:app --reload`
  - opening the UI at `http://127.0.0.1:8000/`
  - CLI usage via `python -m dvrs_tool`
- `requirements.txt` contained:
  - `fastapi`
  - `uvicorn`
  - `pydantic`
- `dvrs_tool/api.py` showed:
  - static files served from `dvrs_tool/static`
  - `/` redirecting to `/static/index.html`
  - `/v1/evaluate`
  - `/v1/order-summary.pdf`
- `dvrs_tool/static/app.js` showed:
  - direct file mode is intentionally unsupported for actual API use
  - the UI expects a localhost-served backend
  - users are told to open `http://127.0.0.1:8000/` when not served over HTTP
- `dvrs_tool/pdf_export.py` showed the PDF output is generated directly in Python and does not depend on external PDF tools
- No `pyproject.toml`, `setup.py`, `setup.cfg`, `MANIFEST.in`, PyInstaller spec, or workflow files were present

### Assistant
Feasibility conclusion:
- Yes, the application was a good candidate for packaging because the core logic and PDF export were already self-contained.
- No, the branch was not ready to produce a no-admin Windows executable as-is.

The assistant explained that the main missing pieces were:
- a launcher
- a desktop shell or embedded app window
- packaging/build configuration
- a self-contained production server startup path

The assistant identified two delivery patterns:
- A simpler browser-launching executable that starts the internal server and opens the default browser
- A fuller desktop-shell approach that keeps everything inside its own application window

For the second option, the assistant noted that an embedded desktop wrapper such as `pywebview`, Tauri, or another shell would be needed.

### User
Requested implementation of the second option. The user explicitly asked for:
- a dedicated application window
- no user-visible localhost or browser workflow
- a self-contained production server startup mode inside the tool
- any missing requirements to be added on this branch for future compiles
- notification if any approval or extra details were needed
- a note about what, if anything, should later be moved into `main`

### Assistant
Outlined the implementation plan:
- inspect the branch state and current entrypoints
- add a desktop launcher with an embedded local server and native application window
- add packaging/build configuration
- verify what could be verified without actually building the executable

### Assistant Work Log
Branch inspection showed:
- a clean working tree before the new changes
- existing `run_tests.py`
- no desktop launcher yet

Implementation decisions made during the thread:
- reuse the existing FastAPI + static frontend architecture
- wrap the app in a desktop window instead of launching a browser
- use PySide6 with Qt WebEngine for the embedded desktop window
- start `uvicorn` programmatically inside the desktop runtime
- add PyInstaller packaging support for future Windows compiles

Files added or changed:

#### `dvrs_tool/desktop.py`
Added a new desktop runtime module that:
- defines `DesktopRuntime`
- reserves a localhost port
- starts the FastAPI app via `uvicorn.Config` and `uvicorn.Server`
- waits for `/health` before opening the UI
- creates a PySide6 `QWebEngineView` window pointed at the embedded server
- reports missing desktop dependencies through `MissingDependencyError`
- shuts down the internal server when the app exits
- sets Qt WebEngine environment variables to keep packaged runs quieter and reduce frozen-build sandbox issues

#### `run_desktop.py`
Added as a top-level desktop entrypoint that imports and runs `dvrs_tool.desktop.main()`.

#### `requirements-desktop.txt`
Added to collect desktop and packaging requirements:
- `-r requirements.txt`
- `PySide6>=6.8,<7.0`
- `PyInstaller>=6.10,<7.0`

#### `dvrs_desktop.spec`
Added a PyInstaller spec file that:
- targets `run_desktop.py`
- collects the static frontend assets under `dvrs_tool/static`
- adds hidden imports for:
  - `PySide6.QtWebEngineWidgets`
  - `PySide6.QtWebEngineCore`
  - relevant `uvicorn` submodules
- builds a windowed executable named `DVRSPlanner`

#### `build_windows.ps1`
Added a Windows build helper that:
- optionally removes `build` and `dist` when `-Clean` is provided
- installs `requirements-desktop.txt`
- runs `python -m PyInstaller --noconfirm dvrs_desktop.spec`

#### `README.md`
Expanded to document:
- desktop dependency installation
- launching the desktop app via `python run_desktop.py`
- the fact that the launcher starts the API internally and opens the planner in an embedded application window
- the Windows build helper and expected output path `dist\DVRSPlanner.exe`

### Assistant
Reported verification work:
- Existing unit tests were run with `python run_tests.py`
- The test suite failed, but the failures were in pre-existing engine tests unrelated to the new desktop files
- A `py_compile` attempt hit a Windows bytecode-cache access error in `__pycache__`
- A narrower import-level verification then succeeded:
  - `python -B -c "import run_desktop; import dvrs_tool.desktop; print('desktop-import-ok')"`
  - output: `desktop-import-ok`

The assistant explicitly noted:
- the executable was not built
- the full desktop launch path was not run because `PySide6` was not installed in the environment yet
- the internal localhost server remains an implementation detail, but the intended user experience hides it behind the desktop window

### Assistant
Summarized the implementation result:
- The branch now contains a desktop runtime path that launches the existing DVRS app in its own embedded window.
- Users should not need to start `uvicorn` or open a browser manually.
- Packaging support is now present for future Windows compiles.
- The likely candidates to move into `main` later are:
  - `run_desktop.py`
  - `dvrs_tool/desktop.py`
  - `requirements-desktop.txt`
  - `dvrs_desktop.spec`
  - `build_windows.ps1`
  - the desktop documentation in `README.md`

The assistant also called out residual considerations:
- The desktop bundle will be larger because of Qt WebEngine.
- Windows SmartScreen and code signing are separate concerns from admin rights or registry edits.
- The exact long-term packaging toolchain may still change.

### User
Requested that the conversation be converted into reusable project documentation with:
- a summary file under `docs/dev-history/<thread-slug>-summary.md`
- a full cleaned raw thread under `docs/raw-threads/<thread-slug>.md`
- a 3-5 sentence addition to `docs/dev-log.md`

The user also required:
- a short kebab-case filesystem-safe slug
- no invented information
- clear documentation of abandoned versus final approaches when relevant
- a professional engineering tone

## Outcome Captured For Future Engineers
- The DVRS tool is packageable for Windows, but the original branch lacked the runtime and packaging pieces needed for a desktop executable.
- The final implementation on this branch uses an embedded server plus a PySide6 Qt WebEngine window rather than a user-visible browser session.
- Packaging support was added with a dedicated desktop requirements file, a PyInstaller spec, and a Windows build helper.
- Verification was limited by environment state: import-level checks passed, but the full engine suite was already red in unrelated areas and no executable was built in this thread.
