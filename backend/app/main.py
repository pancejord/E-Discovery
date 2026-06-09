from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import analytics, documents, entities, evaluation, search
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

app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(entities.router, prefix="/api/entities", tags=["entities"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
