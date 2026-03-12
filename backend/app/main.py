import logging
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse

from app.core.config import settings
from app.core.database import engine
from app.core.logging import configure_logging, log_startup_banner, log_startup_checks
from app.utils.excel import generate_excel
from app.utils.pdf import render_pdf


configure_logging(settings)
logger = logging.getLogger(__name__)
APP_TITLE = "Quick Estimate"
app = FastAPI(title=APP_TITLE, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Retry-After"],
)


from app.api import (
    admin,
    analytics,
    auth,
    clients,
    estimates,
    notes,
    templates,
    user,
    versions,
)


# API
app.include_router(auth.router, prefix="/api/auth")
app.include_router(user.router, prefix="/api/users")
app.include_router(admin.router, prefix="/api/admin")
app.include_router(estimates.router, prefix="/api/estimates")
app.include_router(templates.router, prefix="/api/templates")
app.include_router(clients.router, prefix="/api/clients")
app.include_router(versions.router, prefix="/api/versions")
app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(notes.router, prefix="/api/notes")


def _is_test_env() -> bool:
    return str(settings.APP_ENV).strip().lower() in {"test", "testing"}


def _check_configuration_loaded() -> bool:
    config_source_ok = (
        settings.CONFIG_FILE is None
        or (Path(settings.CONFIG_FILE).exists() and Path(settings.CONFIG_FILE).is_file())
    )
    fields_ok = all(
        [
            bool(str(settings.APP_ENV).strip()),
            bool(str(settings.APP_VERSION).strip()),
            bool(str(settings.DATABASE_URL).strip()),
            bool(str(settings.SERVER_HOST).strip()),
            settings.SERVER_PORT > 0,
        ]
    )
    db_url_ok = "://" in settings.DATABASE_URL
    return config_source_ok and fields_ok and db_url_ok


def _check_api_initialized() -> bool:
    api_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/")
    ]
    if not api_routes:
        return False

    required_prefixes = (
        "/api/auth",
        "/api/estimates",
        "/api/templates",
        "/api/clients",
    )
    has_required_prefixes = all(
        any(route.path.startswith(prefix) for route in api_routes) for prefix in required_prefixes
    )
    if not has_required_prefixes:
        return False

    try:
        openapi_schema = app.openapi()
    except Exception:
        return False

    return bool(openapi_schema.get("paths"))


def _check_export_subsystem() -> bool:
    template_path = Path(__file__).resolve().parent / "templates" / "estimate_pdf.html"
    pdf_ready = callable(render_pdf) and template_path.exists()
    excel_ready = callable(generate_excel)
    wkhtmltopdf_ready = shutil.which("wkhtmltopdf") is not None
    return pdf_ready and excel_ready and wkhtmltopdf_ready


async def _check_database_connection() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database connectivity check failed")
        return False


@app.get("/api/health/live")
async def live_health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health/ready")
async def readiness_health() -> JSONResponse:
    skip_heavy_checks = _is_test_env()
    checks = {
        "configuration": _check_configuration_loaded(),
        "api": _check_api_initialized(),
        "exports": True if skip_heavy_checks else _check_export_subsystem(),
        "database": True if skip_heavy_checks else await _check_database_connection(),
    }
    ready = all(checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "checks": checks,
        },
    )


async def _run_startup_checks() -> None:
    log_startup_banner(settings)
    skip_heavy_checks = _is_test_env()

    config_ready = _check_configuration_loaded()
    api_ready = _check_api_initialized()
    export_ready = True if skip_heavy_checks else _check_export_subsystem()

    db_ready = True if skip_heavy_checks else await _check_database_connection()

    checks = [
        ("Configuration loaded", config_ready),
        ("API initialized", api_ready),
        ("Export subsystem initialized", export_ready),
        ("Database connection established", db_ready),
    ]

    log_startup_checks(checks, footer=None)

    failed_checks = [label for label, ok in checks if not ok]
    if failed_checks:
        raise RuntimeError(f"Startup checks failed: {', '.join(failed_checks)}")


@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    await _run_startup_checks()
    yield


app.router.lifespan_context = app_lifespan


# Path to built frontend (dist)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
index_file = os.path.join(frontend_path, "index.html")

if os.path.exists(index_file):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc):
        if isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
            if getattr(exc, "detail", None) and exc.detail != "Not Found":
                return await http_exception_handler(request, exc)
        if request.url.path.startswith("/api"):
            return JSONResponse(status_code=404, content={"detail": "API route not found"})
        if os.path.splitext(request.url.path)[1]:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return FileResponse(index_file)
