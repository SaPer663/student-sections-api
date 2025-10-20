import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.db.init_db import initialize_database
from app.db.session import async_session_maker
from app.seed_demo_data import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.

    При запуске инициализирует БД с ролями и первым админом.
    """
    print("Application starting up...")

    async with async_session_maker() as session:
        try:
            await initialize_database(session)

            if settings.application.is_development:
                await seed_demo_data(session)
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")

    yield

    print("Application shutting down...")


app = FastAPI(
    title=settings.application.APP_NAME,
    version=settings.application.APP_VERSION,
    description="REST API for managing students and sections with role-based access control",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Обработчик кастомных исключений приложения."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error": exc.__class__.__name__,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обработчик ошибок валидации Pydantic."""

    errors = []
    for error in exc.errors():
        error_dict = {
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        if "input" in error:
            error_dict["input"] = str(error["input"])
        if error.get("ctx"):
            ctx = error["ctx"]
            if isinstance(ctx, dict):
                error_dict["ctx"] = {k: str(v) for k, v in ctx.items()}

        errors.append(error_dict)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Validation error", "errors": errors},
    )


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Check if the application is running",
)
async def health_check():
    """Health check endpoint."""

    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "version": settings.application.APP_VERSION,
    }


app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.application.APP_NAME,
        "version": settings.application.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "message": "Welcome to Student Sections API",
    }
