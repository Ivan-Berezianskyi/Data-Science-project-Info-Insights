from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Enumeration of valid message roles."""
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


# Chat Schemas
class ChatBase(BaseModel):
    """Base schema for chat operations."""
    name: Optional[str] = Field(None, max_length=255, description="Chat name/title")
    notebooks: List[str] = Field(default_factory=list, description="Array of notebook identifiers")


class ChatCreate(ChatBase):
    """Schema for creating a new chat."""
    pass


class ChatUpdate(BaseModel):
    """Schema for updating a chat."""
    name: Optional[str] = Field(None, max_length=255, description="Chat name/title")
    notebooks: Optional[List[str]] = Field(None, description="Array of notebook identifiers")


class ChatResponse(ChatBase):
    """Schema for chat response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatDetailResponse(ChatResponse):
    """Schema for detailed chat response with messages count."""
    messages_count: int = Field(default=0, description="Total number of messages in the chat")


# Message Schemas
class MessageBase(BaseModel):
    """Base schema for message operations."""
    role: MessageRole
    content: str = Field(..., min_length=1, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    chat_id: int


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: Optional[str] = Field(None, min_length=1)
    role: Optional[MessageRole] = None


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    chat_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Pagination Schemas
class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        from config import settings
        if v > settings.max_page_size:
            return settings.max_page_size
        return v


class PaginatedResponse(BaseModel):
    """Base schema for paginated responses."""
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def calculate_total_pages(cls, total: int, page_size: int) -> int:
        """Calculate total number of pages."""
        return (total + page_size - 1) // page_size if total > 0 else 0


class PaginatedChatResponse(PaginatedResponse):
    """Schema for paginated chat list response."""
    items: List[ChatResponse]


class PaginatedMessageResponse(PaginatedResponse):
    """Schema for paginated message list response."""
    items: List[MessageResponse]

