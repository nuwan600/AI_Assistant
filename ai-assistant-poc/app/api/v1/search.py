from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_user
from app.models.schema import User
from app.services.retrieval_service import RetrievalService

router = APIRouter()

@router.get("/search")
async def search_documents(
    q: str = Query(..., description="Search query"),
    department: str = Query(None),
    doc_type: str = Query(None),
    alpha: float = Query(0.5, ge=0.0, le=1.0, description="1.0=Dense, 0.0=Sparse"),
    current_user: User = Depends(get_current_user)
):
    results = await RetrievalService.hybrid_search(
        query=q,
        user_role=current_user.role,
        department=department,
        doc_type=doc_type,
        alpha=alpha
    )
    return {
        "user": current_user.username,
        "role": current_user.role,
        "count": len(results),
        "results": results
    }