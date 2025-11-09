from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from models import Message
from schemas import MessageCreate, MessageUpdate, MessageResponse, PaginationParams
from fastapi import HTTPException, status
from services.chat_service import ChatService


class MessageService:
    """Service for message-related database operations."""
    
    @staticmethod
    def create_message(db: Session, message_data: MessageCreate) -> Message:
        """Create a new message."""
        # Verify chat exists
        if not ChatService.chat_exists(db, message_data.chat_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat with id {message_data.chat_id} not found"
            )
        
        message = Message(
            chat_id=message_data.chat_id,
            role=message_data.role.value,
            content=message_data.content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def get_message(db: Session, message_id: int) -> Optional[Message]:
        """Get a message by ID."""
        return db.query(Message).filter(Message.id == message_id).first()
    
    @staticmethod
    def get_messages_by_chat(
        db: Session,
        chat_id: int,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[Message], int]:
        """
        Get all messages for a chat, time sorted by createdAt.
        Returns messages ordered by creation time (oldest first).
        """
        # Verify chat exists
        if not ChatService.chat_exists(db, chat_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat with id {chat_id} not found"
            )
        
        query = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc())
        total = query.count()
        
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            messages = query.offset(offset).limit(pagination.page_size).all()
        else:
            messages = query.all()
        
        return messages, total
    
    @staticmethod
    def update_message(db: Session, message_id: int, message_data: MessageUpdate) -> Optional[Message]:
        """Update a message."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return None
        
        update_data = message_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "role" and value is not None:
                setattr(message, field, value.value)
            else:
                setattr(message, field, value)
        
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def delete_message(db: Session, message_id: int) -> bool:
        """Delete a message."""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return False
        
        db.delete(message)
        db.commit()
        return True
    
    @staticmethod
    def message_exists(db: Session, message_id: int) -> bool:
        """Check if a message exists."""
        return db.query(Message).filter(Message.id == message_id).first() is not None

