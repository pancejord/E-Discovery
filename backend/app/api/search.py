from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import Actor, get_actor, require_matter_access
from app.database import get_db
from app.models.schemas import SearchRequest, SearchResponse
from app.services.audit import record_audit_event
from app.services.search import search_chunks

router = APIRouter()


@router.post("", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> SearchResponse:
    require_matter_access(actor, request.matter_id)
    results = search_chunks(db, request.query, matter_id=request.matter_id, limit=request.limit)
    source = results[0].source if results else "local"
    record_audit_event(
        db,
        action="search.run",
        actor=actor.name,
        matter_id=request.matter_id,
        summary=f"Searched for {request.query}",
        details={
            "limit": request.limit,
            "result_count": len(results),
            "source": source,
            "citations": [result.citation for result in results if result.citation],
        },
    )
    return SearchResponse(query=request.query, results=results, source=source)
