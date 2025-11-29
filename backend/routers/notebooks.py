from fastapi import APIRouter, HTTPException, status
from typing import List
from services.rag import rag_service

router = APIRouter(prefix="/api/notebooks", tags=["notebooks"])

@router.get("/", response_model=List[str])
async def get_notebooks():
    """
    Get list of available notebooks (RAG collections).
    """
    try:
        return rag_service.list_notebooks()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
