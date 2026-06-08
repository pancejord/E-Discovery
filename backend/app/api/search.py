from fastapi import APIRouter

from app.models.schemas import SearchRequest, SearchResponse

router = APIRouter()


@router.post("", response_model=SearchResponse)
def search_documents(request: SearchRequest) -> SearchResponse:
    return SearchResponse(query=request.query, results=[])
