from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas import (
    ChatCreate, ChatUpdate, ChatResponse, ChatDetailResponse,
    PaginatedChatResponse, PaginationParams
)
from services.chat_service import ChatService

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(chat_data: ChatCreate, db: Session = Depends(get_db)):
    """Create a new chat."""
    chat = ChatService.create_chat(db, chat_data)
    return ChatResponse.model_validate(chat)


@router.get("/", response_model=PaginatedChatResponse)
def get_chats(
    page: Optional[int] = Query(None, ge=1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    """Get list of chats with optional pagination."""
    pagination = None
    if page is not None or page_size is not None:
        pagination = PaginationParams(
            page=page or 1,
            page_size=page_size or 20
        )
    
    chats, total = ChatService.get_chats(db, pagination)
    
    if pagination:
        total_pages = PaginatedChatResponse.calculate_total_pages(total, pagination.page_size)
        return PaginatedChatResponse(
            items=[ChatResponse.model_validate(chat) for chat in chats],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )
    else:
        # Return as paginated response even without pagination params
        return PaginatedChatResponse(
            items=[ChatResponse.model_validate(chat) for chat in chats],
            total=total,
            page=1,
            page_size=total if total > 0 else 1,
            total_pages=1 if total > 0 else 0
        )


@router.get("/{chat_id}", response_model=ChatDetailResponse)
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific chat."""
    chat_data = ChatService.get_chat_detail(db, chat_id)
    if not chat_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with id {chat_id} not found"
        )
    
    return ChatDetailResponse(**chat_data)


@router.put("/{chat_id}", response_model=ChatResponse)
def update_chat(chat_id: int, chat_data: ChatUpdate, db: Session = Depends(get_db)):
    """Update a chat."""
    chat = ChatService.update_chat(db, chat_id, chat_data)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with id {chat_id} not found"
        )
    return ChatResponse.model_validate(chat)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    """Delete a chat (cascades to all messages)."""
    success = ChatService.delete_chat(db, chat_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat with id {chat_id} not found"
        )

