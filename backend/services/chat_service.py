from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from models import Chat
from schemas import ChatCreate, ChatUpdate, ChatResponse, ChatDetailResponse, PaginationParams
from fastapi import HTTPException, status


class ChatService:
    """Service for chat-related database operations."""
    
    @staticmethod
    def create_chat(db: Session, chat_data: ChatCreate) -> Chat:
        """Create a new chat."""
        chat = Chat(
            name=chat_data.name,
            notebooks=chat_data.notebooks
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    
    @staticmethod
    def get_chat(db: Session, chat_id: int) -> Optional[Chat]:
        """Get a chat by ID."""
        return db.query(Chat).filter(Chat.id == chat_id).first()
    
    @staticmethod
    def get_chat_detail(db: Session, chat_id: int) -> Optional[dict]:
        """Get a chat with message count. Returns dict with chat data and messages_count."""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return None
        
        # Get message count efficiently
        from models import Message
        message_count = db.query(func.count(Message.id)).filter(
            Message.chat_id == chat_id
        ).scalar()
        
        # Return dict with messages_count attribute
        result = {
            "id": chat.id,
            "name": chat.name,
            "notebooks": chat.notebooks,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
            "messages_count": message_count
        }
        return result
    
    @staticmethod
    def get_chats(
        db: Session, 
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[Chat], int]:
        """Get list of chats with optional pagination."""
        query = db.query(Chat)
        total = query.count()
        
        if pagination:
            offset = (pagination.page - 1) * pagination.page_size
            chats = query.order_by(Chat.created_at.desc()).offset(offset).limit(pagination.page_size).all()
        else:
            chats = query.order_by(Chat.created_at.desc()).all()
        
        return chats, total
    
    @staticmethod
    def update_chat(db: Session, chat_id: int, chat_data: ChatUpdate) -> Optional[Chat]:
        """Update a chat."""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return None
        
        update_data = chat_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(chat, field, value)
        
        db.commit()
        db.refresh(chat)
        return chat
    
    @staticmethod
    def delete_chat(db: Session, chat_id: int) -> bool:
        """Delete a chat (cascades to messages)."""
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return False
        
        db.delete(chat)
        db.commit()
        return True
    
    @staticmethod
    def chat_exists(db: Session, chat_id: int) -> bool:
        """Check if a chat exists."""
        return db.query(Chat).filter(Chat.id == chat_id).first() is not None

