import csv
from datetime import UTC, date, datetime, time
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response
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
    custodian_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> AnalyticsSnapshot:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return build_analytics_dashboard(
        db,
        matter_id=matter_id,
        matter_ids=matter_ids,
        custodian_id=custodian_id,
        date_from=_start_of_day(date_from),
        date_to=_end_of_day(date_to),
    ).snapshot


@router.get("/dashboard", response_model=AnalyticsDashboard)
def analytics_dashboard(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    custodian_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> AnalyticsDashboard:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    return build_analytics_dashboard(
        db,
        matter_id=matter_id,
        matter_ids=matter_ids,
        custodian_id=custodian_id,
        date_from=_start_of_day(date_from),
        date_to=_end_of_day(date_to),
    )


@router.get("/export.csv")
def analytics_export_csv(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    custodian_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Response:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor) if matter_id is None else None
    dashboard = build_analytics_dashboard(
        db,
        matter_id=matter_id,
        matter_ids=matter_ids,
        custodian_id=custodian_id,
        date_from=_start_of_day(date_from),
        date_to=_end_of_day(date_to),
    )
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["section", "label", "count", "extra"])
    writer.writerow(["snapshot", "documents", dashboard.snapshot.document_count, ""])
    writer.writerow(["snapshot", "entities", dashboard.snapshot.entity_count, ""])
    writer.writerow(["snapshot", "relationships", dashboard.snapshot.relationship_count, ""])
    for section, buckets in (
        ("file_type", dashboard.file_type_distribution),
        ("document_type", dashboard.document_type_distribution),
        ("entity_type", dashboard.entity_type_distribution),
        ("relationship_type", dashboard.relationship_type_distribution),
        ("custodian", dashboard.top_custodians),
    ):
        for bucket in buckets:
            writer.writerow([section, bucket.label, bucket.count, ""])
    for point in dashboard.document_timeline:
        writer.writerow(["timeline", point.date, point.document_count, ""])
    for pair in dashboard.communication_pairs:
        writer.writerow([
            "communication_pair",
            f"{pair.source_entity_name} -> {pair.target_entity_name}",
            pair.message_count,
            " ".join(str(document_id) for document_id in pair.document_ids),
        ])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="analytics-export.csv"'},
    )


def _start_of_day(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.min, tzinfo=UTC)


def _end_of_day(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.max, tzinfo=UTC)
