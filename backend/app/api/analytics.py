from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access
from app.database import get_db
from app.models.schemas import AnalyticsDashboard, AnalyticsSnapshot
from app.services.analytics import build_analytics_dashboard

router = APIRouter()


@router.get("/snapshot", response_model=AnalyticsSnapshot)
def analytics_snapshot(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
) -> AnalyticsSnapshot:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return build_analytics_dashboard(db, matter_id=matter_id, matter_ids=matter_ids).snapshot


@router.get("/dashboard", response_model=AnalyticsDashboard)
def analytics_dashboard(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
) -> AnalyticsDashboard:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return build_analytics_dashboard(db, matter_id=matter_id, matter_ids=matter_ids)
