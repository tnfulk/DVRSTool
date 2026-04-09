"""FastAPI wrapper for the DVRS calculation engine."""

from pathlib import Path
from typing import Any

from .engine import DVRSCalculationEngine
from .exceptions import DVRSBaseError, MissingDependencyError
from .models import CalculationRequest, Country
from .pdf_export import build_ordering_summary_pdf


def create_app():
    try:
        from fastapi import Body, FastAPI, Request
        from fastapi.responses import JSONResponse, RedirectResponse, Response
        from fastapi.staticfiles import StaticFiles
        from pydantic import BaseModel, Field
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
        mobile_tx_low_mhz: float = Field(..., gt=0)
        mobile_tx_high_mhz: float = Field(..., gt=0)
        mobile_rx_low_mhz: float | None = Field(default=None, gt=0)
        mobile_rx_high_mhz: float | None = Field(default=None, gt=0)
        use_latest_ordering_ruleset: bool = True
        agency_notes: str | None = None
        actual_licensed_dvrs_tx_low_mhz: float | None = Field(default=None, gt=0)
        actual_licensed_dvrs_tx_high_mhz: float | None = Field(default=None, gt=0)
        actual_licensed_dvrs_rx_low_mhz: float | None = Field(default=None, gt=0)
        actual_licensed_dvrs_rx_high_mhz: float | None = Field(default=None, gt=0)

    @app.exception_handler(DVRSBaseError)
    async def handle_dvrs_error(_: Request, exc: DVRSBaseError):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": exc.to_dict(),
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
