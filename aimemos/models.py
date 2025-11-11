"""Data models for AI Memos."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MemoBase(BaseModel):
    """Base model for a memo."""
    
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class MemoCreate(MemoBase):
    """Model for creating a new memo."""
    
    pass


class MemoUpdate(BaseModel):
    """Model for updating a memo."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[str]] = None


class Memo(MemoBase):
    """Complete memo model with metadata."""
    
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MemoList(BaseModel):
    """List of memos with pagination info."""
    
    items: list[Memo]
    total: int
    skip: int
    limit: int
