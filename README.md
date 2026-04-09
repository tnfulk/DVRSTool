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
