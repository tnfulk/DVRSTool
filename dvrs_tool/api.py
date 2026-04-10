"""FastAPI wrapper for the DVRS calculation engine."""

from pathlib import Path
from typing import Any

from .engine import DVRSCalculationEngine
from .exceptions import DVRSBaseError, MissingDependencyError
from .models import CalculationRequest, Country, SystemBandHint
from .pdf_export import build_ordering_summary_pdf


def create_app():
    try:
        from fastapi import Body, FastAPI, Request
        from fastapi.exceptions import RequestValidationError
        from fastapi.responses import JSONResponse, RedirectResponse, Response
        from fastapi.staticfiles import StaticFiles
        from pydantic import AliasChoices, BaseModel, Field
    except ImportError as exc:
        raise MissingDependencyError(
            code="MISSING_FASTAPI_DEPENDENCY",
            message="FastAPI runtime dependencies are not installed.",
            details={
                "missing_dependency": str(exc),
                "hint": "Install requirements.txt before running the API service.",
            },
        ) from exc

    engine = DVRSCalculationEngine()
    app = FastAPI(
        title="DVRS In-Band Planning API",
        version="0.1.0",
        description="Planning API for Futurecom DVRS standard in-band configurations.",
    )
    static_dir = Path(__file__).with_name("static")

    class CalculationRequestModel(BaseModel):
        country: Country
        mobile_tx_low_mhz: float | None = Field(default=None, gt=0)
        mobile_tx_high_mhz: float | None = Field(default=None, gt=0)
        system_band_hint: SystemBandHint | None = None
        mobile_tx_700_low_mhz: float | None = Field(default=None, gt=0)
        mobile_tx_700_high_mhz: float | None = Field(default=None, gt=0)
        mobile_tx_800_low_mhz: float | None = Field(default=None, gt=0)
        mobile_tx_800_high_mhz: float | None = Field(default=None, gt=0)
        mobile_rx_low_mhz: float | None = Field(default=None, gt=0)
        mobile_rx_high_mhz: float | None = Field(default=None, gt=0)
        use_latest_ordering_ruleset: bool = True
        agency_name: str | None = None
        quote_date: str | None = None
        mobile_radio_type: str | None = None
        control_head_type: str | None = None
        msu_antenna_type: str | None = None
        agency_notes: str | None = None
        actual_dvrs_tx_mhz: float | None = Field(
            default=None,
            gt=0,
            validation_alias=AliasChoices(
                "actual_dvrs_tx_mhz",
                "actual_licensed_dvrs_tx_low_mhz",
            ),
        )
        actual_dvrs_rx_mhz: float | None = Field(
            default=None,
            gt=0,
            validation_alias=AliasChoices(
                "actual_dvrs_rx_mhz",
                "actual_licensed_dvrs_rx_low_mhz",
            ),
        )

    @app.exception_handler(DVRSBaseError)
    async def handle_dvrs_error(_: Request, exc: DVRSBaseError):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": exc.to_dict(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(_: Request, exc: RequestValidationError):
        field_errors = []
        rule_violations = []
        optional_numeric_fields = {
            "mobile_rx_low_mhz",
            "mobile_rx_high_mhz",
            "actual_dvrs_tx_mhz",
            "actual_dvrs_rx_mhz",
        }
        for error in exc.errors():
            location = list(error.get("loc", []))
            field_name = location[-1] if location else "request"
            message = error.get("msg", "Invalid input.")
            error_type = error.get("type", "validation_error")
            input_value = error.get("input")
            hint = None
            if field_name in optional_numeric_fields:
                hint = "If this optional field is not known, leave it blank instead of entering 0."
            field_error = {
                "field": field_name,
                "location": location,
                "message": message,
                "type": error_type,
                "input": input_value,
            }
            if hint:
                field_error["hint"] = hint
            field_errors.append(field_error)
            rule_violation = {
                "code": "INVALID_REQUEST_FIELD",
                "message": f"{field_name}: {message}",
                "details": field_error,
            }
            rule_violations.append(rule_violation)

        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": {
                    "code": "INVALID_REQUEST_BODY",
                    "message": "One or more inputs are invalid. Review the highlighted field guidance and confirm optional numeric fields are blank unless you know the licensed value.",
                    "details": {
                        "field_errors": field_errors,
                        "exception_type": exc.__class__.__name__,
                    },
                    "rule_violations": rule_violations,
                },
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "code": "UNHANDLED_EXCEPTION",
                    "message": "An unexpected server error occurred.",
                    "details": {
                        "exception_type": exc.__class__.__name__,
                        "exception_message": str(exc),
                    },
                    "rule_violations": [
                        {
                            "code": "UNHANDLED_EXCEPTION",
                            "message": "An unexpected server error occurred.",
                            "details": {
                                "exception_type": exc.__class__.__name__,
                                "exception_message": str(exc),
                            },
                        }
                    ],
                },
            },
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @app.get("/", include_in_schema=False)
        async def index() -> RedirectResponse:
            return RedirectResponse(url="/static/index.html")

    @app.post("/v1/evaluate")
    async def evaluate(payload: CalculationRequestModel = Body(...)) -> dict[str, Any]:
        request = CalculationRequest(**payload.model_dump())
        response = engine.evaluate(request)
        return {
            "status": "ok",
            "data": response.to_dict(),
        }

    @app.post("/v1/order-summary.pdf")
    async def order_summary_pdf(payload: CalculationRequestModel = Body(...)) -> Response:
        request = CalculationRequest(**payload.model_dump())
        response = engine.evaluate(request)
        pdf = build_ordering_summary_pdf(response)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="dvrs-ordering-summary.pdf"'},
        )

    return app


app = None
try:
    app = create_app()
except MissingDependencyError:
    app = None
