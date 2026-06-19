from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, analytics, audit, custodians, documents, entities, evaluation, graph, matters, search
from app.core.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
