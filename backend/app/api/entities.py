from fastapi import APIRouter

from app.models.schemas import EntitySummary

router = APIRouter()


@router.get("", response_model=list[EntitySummary])
def list_entities() -> list[EntitySummary]:
    return []
