# DVRS In-Band Planning Service

## Files

- `dvrs_tool/engine.py`: calculation engine
- `dvrs_tool/api.py`: FastAPI wrapper
- `tests/test_engine.py`: unit tests
- `run_tests.py`: test runner
- `requirements.txt`: API dependencies

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

## Build a Windows executable

This branch now includes a PyInstaller spec for a windowed desktop build:

```powershell
.\build_windows.ps1
```

The packaged executable will be written under `dist\DVRSPlanner.exe`.

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
