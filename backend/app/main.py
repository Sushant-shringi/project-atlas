"""
Project Atlas - FastAPI Application Main Entrypoint
Configures ASGI application, CORS, middleware, global error handling,
and lifecycle event handlers.
"""

import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.core.config import settings
from app.core.logging_config import logger
from app.services.ingestion import IngestionService

app = FastAPI(
    title="Project Atlas - Report Copilot API",
    description="Deterministic, entitlement-aware market intelligence copilot for CodeIgniter 3 legacy portal.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows CodeIgniter portal and development frontends
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_request_id_header(request: Request, call_next):
    """Adds request ID and process timing headers to all responses."""
    req_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
    start_time = time.time()

    # Pass request_id through request state
    request.state.request_id = req_id

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Process-Time-MS"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler: Prevents unrestricted stack traces from leaking to clients.
    Logs full exception internally and returns a clean, audited error response.
    """
    req_id = getattr(request.state, "request_id", "req-unknown")
    logger.error(
        f"Unhandled application exception: {exc}",
        exc_info=True,
        extra={"request_id": req_id}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the request. Our engineering team has been notified.",
            "request_id": req_id
        }
    )


# Mount routes at root and /api/v1
app.include_router(router)
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initializes collections and indexes seed reports on application startup."""
    logger.info("Project Atlas FastAPI application starting up...")
    try:
        # Ingest reports if reports directory exists
        import os
        if os.path.exists("reports"):
            logger.info("Executing initial report indexing on startup...")
            IngestionService.ingest_directory("reports")
    except Exception as e:
        logger.warning(f"Startup ingestion non-fatal warning: {e}")
