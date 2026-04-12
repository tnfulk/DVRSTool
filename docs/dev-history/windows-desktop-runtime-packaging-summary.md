# Windows Desktop Runtime And Packaging Path

## 1. Context
This thread explored whether the DVRS tool could be delivered as a Windows executable that runs as a self-contained desktop application rather than as a manually launched local web service. After an initial feasibility assessment, the work shifted into implementing the desktop runtime and build scaffolding directly on the current branch.

## 2. Problem Statement
The repository already supported a FastAPI-served web UI and a CLI, but it did not provide a Windows desktop experience. Users would otherwise need to install Python dependencies, start `uvicorn`, and open `http://127.0.0.1:8000/` manually. The goal was to create a branch-local path toward a dedicated desktop window with no user-visible browser workflow and with packaging support for future Windows builds.

## 3. Key Decisions
- Decision: Treat the existing branch as packageable, but not ready for a Windows executable as-is.
  - Rationale: The core engine and PDF export were already self-contained, but there was no launcher, no desktop shell, and no packaging configuration.
  - Alternatives considered (if any): None beyond the yes-with-caveats assessment.
- Decision: Keep the existing FastAPI + static frontend architecture and wrap it in a desktop shell instead of rewriting the UI natively.
  - Rationale: Reusing the current UI reduced risk and implementation time while preserving established backend behavior.
  - Alternatives considered (if any): A browser-based launcher was considered less desirable because the user explicitly wanted a dedicated application window with no visible browser behavior.
- Decision: Use a Qt WebEngine desktop window driven by PySide6.
  - Rationale: This provides a native desktop window with an embedded renderer, keeping the existing HTML/CSS/JS UI while avoiding a separate browser session.
  - Alternatives considered (if any): A pywebview-style approach was considered conceptually, but the final implementation chose a Qt-hosted embedded web view.
- Decision: Start the production server programmatically inside the desktop process instead of requiring `uvicorn` CLI usage.
  - Rationale: The user asked for a self-contained production startup mode. Running `uvicorn` via Python code keeps startup internal to the app.
  - Alternatives considered (if any): Continuing to require `uvicorn dvrs_tool.api:app --reload` was rejected for the desktop workflow.
- Decision: Add a PyInstaller-based build path on this branch.
  - Rationale: The branch needed concrete packaging artifacts for future Windows compiles, even though the executable itself was not built in this thread.
  - Alternatives considered (if any): Other packagers such as Nuitka or installer-based approaches were left as future options.

## 4. Implementation Summary
The thread added a desktop runtime module in `dvrs_tool/desktop.py` that:
- Reserves a local port
- Starts the FastAPI app with `uvicorn` programmatically in a background thread
- Waits for `/health` before opening the UI
- Hosts the existing planner UI inside a PySide6 `QWebEngineView`
- Shuts down the embedded server when the desktop window closes

It also added:
- `run_desktop.py` as a top-level desktop entrypoint
- `requirements-desktop.txt` for desktop and packaging dependencies
- `dvrs_desktop.spec` for PyInstaller
- `build_windows.ps1` as a repeatable Windows build helper
- README documentation for running the desktop app and building the executable

At the end of the thread, the conversation itself was converted into development-history documentation by adding this summary, a raw-thread transcript, and a new `docs/dev-log.md` entry.

## 5. Challenges & Iterations
The first part of the thread was a feasibility analysis rather than implementation. That analysis identified that the app was structurally suitable for packaging but still depended on a localhost-served workflow and lacked any packaging files. During implementation, the main architectural refinement was choosing an embedded desktop shell rather than a browser launcher. Verification also uncovered that the existing unit suite was already failing in engine-related areas not modified by this work, so desktop validation had to be limited to import-level checks rather than a clean full-suite pass.

## 6. Final Outcome
This branch now contains a desktop runtime path for the DVRS planner and the files needed to compile it into a Windows executable in the future. The intended user experience is a dedicated app window with an internally started local server and no need for the user to manually open a browser or launch `uvicorn`. The executable was not built during this thread, but the runtime and packaging scaffolding are now present.

## 7. Open Questions / Follow-ups
- Confirm the final Windows packaging strategy, especially whether PyInstaller remains the preferred long-term tool.
- Decide whether the desktop runtime and packaging files should be promoted from this branch into `main`.
- Validate an end-to-end Windows build once `PySide6` and packaging dependencies are installed in a build environment.
- Consider code signing if the final Windows executable will be distributed broadly.
- Investigate the pre-existing failing engine tests separately, since they were already red during this thread and are unrelated to the desktop additions.

## 8. Affected Files / Components
- `dvrs_tool/desktop.py`
- `run_desktop.py`
- `requirements-desktop.txt`
- `dvrs_desktop.spec`
- `build_windows.ps1`
- `README.md`
- `docs/dev-history/windows-desktop-runtime-packaging-summary.md`
- `docs/raw-threads/windows-desktop-runtime-packaging.md`
- `docs/dev-log.md`
