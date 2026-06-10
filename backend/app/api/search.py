from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import SearchRequest, SearchResponse
from app.services.search import search_chunks

router = APIRouter()


@router.post("", response_model=SearchResponse)
def search_documents(request: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    results = search_chunks(db, request.query, matter_id=request.matter_id, limit=request.limit)
    return SearchResponse(query=request.query, results=results)
