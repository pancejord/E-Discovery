from fastapi import APIRouter

from app.models.schemas import AnalyticsSnapshot

router = APIRouter()


@router.get("/snapshot", response_model=AnalyticsSnapshot)
def analytics_snapshot() -> AnalyticsSnapshot:
    return AnalyticsSnapshot(
        document_count=0,
        entity_count=0,
        relationship_count=0,
        file_type_counts={},
        custodian_counts={},
    )
