from contextlib import asynccontextmanager
import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, ai, analytics, audit, custodians, documents, entities, evaluation, graph, matters, search
from app.core.config import settings
from app.database import SessionLocal, get_db, init_db
from app.services.audit import record_audit_event, purge_expired_audit_events, reset_audit_context, set_audit_context, update_audit_context

logger = logging.getLogger("ediscovery.api")


def _configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), force=True)


_configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.audit_purge_on_startup:
        db = SessionLocal()
        try:
            deleted_count = purge_expired_audit_events(db)
            record_audit_event(
                db,
                action="audit.retention.purge_scheduled",
                actor="system",
                summary="Purged expired audit events at startup",
                details={"retention_days": settings.audit_retention_days, "deleted_count": deleted_count},
            )
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Litigation and eDiscovery analytics API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_request_context(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)

    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    token = set_audit_context(
        request_id=request_id,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        route=request.url.path,
        method=request.method,
        auth_scheme=_request_auth_scheme(request),
    )
    response = None
    try:
        response = await call_next(request)
        update_audit_context(response_status=response.status_code)
        return response
    except Exception:
        update_audit_context(response_status=500)
        raise
    finally:
        status_code = response.status_code if response is not None else 500
        db_generator = app.dependency_overrides.get(get_db, get_db)()
        db = next(db_generator)
        try:
            update_audit_context(response_status=status_code)
            record_audit_event(
                db,
                action="request.completed",
                actor=None,
                summary=f"{request.method} {request.url.path} completed with {status_code}",
                details={"status_code": status_code},
            )
        finally:
            db_generator.close()
    reset_audit_context(token)


@app.middleware("http")
async def structured_request_logging(request: Request, call_next):
    started = perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        status_code = response.status_code if response is not None else 500
        duration_ms = round((perf_counter() - started) * 1000, 2)
        payload = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }
        if settings.structured_logs:
            logger.info(json.dumps(payload, separators=(",", ":")))
        else:
            logger.info(
                "%s %s completed with %s in %.2fms",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )


def _request_auth_scheme(request: Request) -> str | None:
    if request.headers.get("X-API-Key"):
        return "api_key"
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return "bearer"
    return None

app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(matters.router, prefix="/api/matters", tags=["matters"])
app.include_router(custodians.router, prefix="/api/custodians", tags=["custodians"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(entities.router, prefix="/api/entities", tags=["entities"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
