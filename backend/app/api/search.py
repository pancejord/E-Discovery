from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access
from app.database import get_db
from app.models.saved_search import SavedSearch
from app.models.schemas import SavedSearchCreate, SavedSearchRead, SavedSearchUpdate, SearchRequest, SearchResponse
from app.services.audit import record_audit_event
from app.services.search import search_chunks

router = APIRouter()


@router.post("", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> SearchResponse:
    require_matter_access(db, actor, request.matter_id)
    matter_ids = accessible_matter_ids(db, actor) if request.matter_id is None else None
    results = search_chunks(
        db,
        request.query,
        matter_id=request.matter_id,
        matter_ids=matter_ids,
        limit=request.limit,
        custodian_id=request.custodian_id,
        document_type=request.document_type,
        file_type=request.file_type,
        processing_status=request.processing_status,
        tag=request.tag,
        issue_code=request.issue_code,
        privilege_flag=request.privilege_flag,
        review_status=request.review_status,
        sender=request.sender,
        recipient=request.recipient,
        sort_by=request.sort_by,
        date_from=request.date_from,
        date_to=request.date_to,
    )
    source = results[0].source if results else "local"
    record_audit_event(
        db,
        action="search.run",
        actor=actor.name,
        matter_id=request.matter_id,
        summary=f"Searched for {request.query}",
        details={
            "limit": request.limit,
            "filters": _search_filters(request),
            "result_count": len(results),
            "source": source,
            "citations": [result.citation for result in results if result.citation],
        },
    )
    return SearchResponse(query=request.query, results=results, source=source)


@router.get("/saved", response_model=list[SavedSearchRead])
def list_saved_searches(
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
    matter_id: int | None = None,
    created_by: str | None = None,
) -> list[SavedSearch]:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor)
    statement = select(SavedSearch).order_by(SavedSearch.created_at.desc(), SavedSearch.id.desc())
    if matter_id is not None:
        statement = statement.where(SavedSearch.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(or_(SavedSearch.matter_id.is_(None), SavedSearch.matter_id.in_(matter_ids)))
    if created_by is not None:
        statement = statement.where(SavedSearch.created_by == created_by)
    elif not actor.is_admin:
        statement = statement.where(or_(SavedSearch.is_shared.is_(True), SavedSearch.created_by == actor.name))
    return list(db.scalars(statement))


@router.post("/saved", response_model=SavedSearchRead)
def create_saved_search(
    request: SavedSearchCreate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> SavedSearch:
    require_matter_access(db, actor, request.matter_id)
    filters = _saved_search_filters(request)
    saved_search = SavedSearch(
        matter_id=request.matter_id,
        name=request.name,
        query=request.query,
        filters=filters,
        created_by=actor.name,
        is_shared=request.is_shared,
    )
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    record_audit_event(
        db,
        action="saved_search.create",
        actor=actor.name,
        matter_id=request.matter_id,
        summary=f"Created saved search {request.name}",
        details={"query": request.query, "filters": filters},
    )
    return saved_search


@router.patch("/saved/{saved_search_id}", response_model=SavedSearchRead)
def update_saved_search(
    saved_search_id: int,
    request: SavedSearchUpdate,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> SavedSearch:
    saved_search = _get_saved_search_for_write(db, actor, saved_search_id)
    updates = request.model_dump(exclude_unset=True)
    if "matter_id" in updates:
        require_matter_access(db, actor, request.matter_id)
        saved_search.matter_id = request.matter_id
    if "name" in updates and request.name is not None:
        saved_search.name = request.name
    if "query" in updates and request.query is not None:
        saved_search.query = request.query
    if "is_shared" in updates and request.is_shared is not None:
        saved_search.is_shared = request.is_shared

    filter_updates = _saved_search_filter_updates(request)
    if filter_updates:
        current_filters = dict(saved_search.filters or {})
        current_filters.update(filter_updates)
        saved_search.filters = {key: value for key, value in current_filters.items() if value is not None}
    db.commit()
    db.refresh(saved_search)
    record_audit_event(
        db,
        action="saved_search.update",
        actor=actor.name,
        matter_id=saved_search.matter_id,
        summary=f"Updated saved search {saved_search.name}",
        details={"saved_search_id": saved_search.id, "updated_fields": sorted(updates)},
    )
    return saved_search


@router.delete("/saved/{saved_search_id}", status_code=204)
def delete_saved_search(
    saved_search_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> None:
    saved_search = _get_saved_search_for_write(db, actor, saved_search_id)
    matter_id = saved_search.matter_id
    name = saved_search.name
    db.delete(saved_search)
    db.commit()
    record_audit_event(
        db,
        action="saved_search.delete",
        actor=actor.name,
        matter_id=matter_id,
        summary=f"Deleted saved search {name}",
        details={"saved_search_id": saved_search_id},
    )


@router.post("/saved/{saved_search_id}/run", response_model=SearchResponse)
def run_saved_search(
    saved_search_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> SearchResponse:
    saved_search = db.get(SavedSearch, saved_search_id)
    if saved_search is None:
        raise HTTPException(status_code=404, detail="Saved search not found")
    require_matter_access(db, actor, saved_search.matter_id)
    filters = saved_search.filters or {}
    matter_ids = accessible_matter_ids(db, actor) if saved_search.matter_id is None else None
    results = search_chunks(
        db,
        saved_search.query,
        matter_id=saved_search.matter_id,
        matter_ids=matter_ids,
        limit=int(filters.get("limit") or 10),
        custodian_id=filters.get("custodian_id"),
        document_type=filters.get("document_type"),
        file_type=filters.get("file_type"),
        processing_status=filters.get("processing_status"),
        tag=filters.get("tag"),
        issue_code=filters.get("issue_code"),
        privilege_flag=filters.get("privilege_flag"),
        review_status=filters.get("review_status"),
        sender=filters.get("sender"),
        recipient=filters.get("recipient"),
        sort_by=filters.get("sort_by") or "relevance",
        date_from=_parse_datetime(filters.get("date_from")),
        date_to=_parse_datetime(filters.get("date_to")),
    )
    source = results[0].source if results else "local"
    record_audit_event(
        db,
        action="saved_search.run",
        actor=actor.name,
        matter_id=saved_search.matter_id,
        summary=f"Ran saved search {saved_search.name}",
        details={"saved_search_id": saved_search.id, "result_count": len(results), "source": source},
    )
    return SearchResponse(query=saved_search.query, results=results, source=source)


def _search_filters(request: SearchRequest) -> dict:
    return {
        key: value
        for key, value in {
            "custodian_id": request.custodian_id,
            "document_type": request.document_type,
            "file_type": request.file_type,
            "processing_status": request.processing_status,
            "tag": request.tag,
            "issue_code": request.issue_code,
            "privilege_flag": request.privilege_flag,
            "review_status": request.review_status,
            "sender": request.sender,
            "recipient": request.recipient,
            "sort_by": request.sort_by,
            "date_from": request.date_from.isoformat() if request.date_from else None,
            "date_to": request.date_to.isoformat() if request.date_to else None,
        }.items()
        if value is not None
    }


def _saved_search_filters(request: SavedSearchCreate) -> dict:
    filters = {
        "custodian_id": request.custodian_id,
        "document_type": request.document_type,
        "file_type": request.file_type,
        "processing_status": request.processing_status,
        "tag": request.tag,
        "issue_code": request.issue_code,
        "privilege_flag": request.privilege_flag,
        "review_status": request.review_status,
        "sender": request.sender,
        "recipient": request.recipient,
        "sort_by": request.sort_by,
        "date_from": request.date_from,
        "date_to": request.date_to,
        "limit": request.limit,
    }
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in filters.items()
        if value is not None
    }


def _saved_search_filter_updates(request: SavedSearchUpdate) -> dict:
    fields = {
        "custodian_id",
        "document_type",
        "file_type",
        "processing_status",
        "tag",
        "issue_code",
        "privilege_flag",
        "review_status",
        "sender",
        "recipient",
        "sort_by",
        "date_from",
        "date_to",
        "limit",
    }
    payload = request.model_dump(exclude_unset=True)
    return {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in payload.items()
        if key in fields
    }


def _get_saved_search_for_write(db: Session, actor: Actor, saved_search_id: int) -> SavedSearch:
    saved_search = db.get(SavedSearch, saved_search_id)
    if saved_search is None:
        raise HTTPException(status_code=404, detail="Saved search not found")
    require_matter_access(db, actor, saved_search.matter_id)
    if not actor.is_admin and saved_search.created_by not in {None, actor.name}:
        raise HTTPException(status_code=403, detail="Saved search owner required")
    return saved_search


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None
