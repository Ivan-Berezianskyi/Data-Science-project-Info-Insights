from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas import (
    MessageCreate, MessageUpdate, MessageResponse,
    PaginatedMessageResponse, PaginationParams
)
from services.message_service import MessageService

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message_data: MessageCreate, db: Session = Depends(get_db)):
    """Create a new message."""
    message = MessageService.create_message(db, message_data)
    return MessageResponse.model_validate(message)


@router.get("/chat/{chat_id}", response_model=PaginatedMessageResponse)
def get_messages_by_chat(
    chat_id: int,
    page: Optional[int] = Query(None, ge=1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a chat, time sorted by createdAt (oldest first).
    Supports optional pagination.
    """
    pagination = None
    if page is not None or page_size is not None:
        pagination = PaginationParams(
            page=page or 1,
            page_size=page_size or 20
        )
    
    messages, total = MessageService.get_messages_by_chat(db, chat_id, pagination)
    
    if pagination:
        total_pages = PaginatedMessageResponse.calculate_total_pages(total, pagination.page_size)
        return PaginatedMessageResponse(
            items=[MessageResponse.model_validate(msg) for msg in messages],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )
    else:
        # Return as paginated response even without pagination params
        return PaginatedMessageResponse(
            items=[MessageResponse.model_validate(msg) for msg in messages],
            total=total,
            page=1,
            page_size=total if total > 0 else 1,
            total_pages=1 if total > 0 else 0
        )


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(message_id: int, db: Session = Depends(get_db)):
    """Get a specific message by ID."""
    message = MessageService.get_message(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {message_id} not found"
        )
    return MessageResponse.model_validate(message)


@router.put("/{message_id}", response_model=MessageResponse)
def update_message(message_id: int, message_data: MessageUpdate, db: Session = Depends(get_db)):
    """Update a message."""
    message = MessageService.update_message(db, message_id, message_data)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {message_id} not found"
        )
    return MessageResponse.model_validate(message)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db)):
    """Delete a message."""
    success = MessageService.delete_message(db, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {message_id} not found"
        )

