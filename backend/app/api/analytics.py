from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import AnalyticsDashboard, AnalyticsSnapshot
from app.services.analytics import build_analytics_dashboard

router = APIRouter()


@router.get("/snapshot", response_model=AnalyticsSnapshot)
def analytics_snapshot(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
) -> AnalyticsSnapshot:
    return build_analytics_dashboard(db, matter_id=matter_id).snapshot


@router.get("/dashboard", response_model=AnalyticsDashboard)
def analytics_dashboard(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
) -> AnalyticsDashboard:
    return build_analytics_dashboard(db, matter_id=matter_id)
