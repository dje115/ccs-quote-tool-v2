#!/usr/bin/env python3
"""
Quote document models for multi-part quote system
"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, BaseModel, TimestampMixin


class DocumentType(enum.Enum):
    """Quote document type enumeration"""
    PARTS_LIST = "parts_list"
    TECHNICAL = "technical"
    OVERVIEW = "overview"
    BUILD = "build"


class QuoteDocument(BaseModel):
    """Quote document model for multi-part quotes"""
    __tablename__ = "quote_documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document type: 'parts_list', 'technical', 'overview', 'build'
    document_type = Column(String(50), nullable=False)
    
    # Rich content structure (JSONB for flexibility)
    # Structure: {
    #   "sections": [
    #     {"id": "section1", "title": "Section Title", "content": "...", "order": 1}
    #   ],
    #   "metadata": {"generated_by": "ai", "last_edited_by": "user_id", ...}
    # }
    content = Column(JSON, nullable=False, default=dict)
    
    # Version tracking
    version = Column(Integer, nullable=False, default=1)
    
    # Created by
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    quote = relationship("Quote", foreign_keys=[quote_id])
    creator = relationship("User", foreign_keys=[created_by])
    versions = relationship("QuoteDocumentVersion", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QuoteDocument {self.document_type} v{self.version} for Quote {self.quote_id}>"


class QuoteDocumentVersion(Base, TimestampMixin):
    """Quote document version history - does not need tenant_id (inherited via document)"""
    __tablename__ = "quote_document_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("quote_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Version information
    version = Column(Integer, nullable=False)
    
    # Content snapshot
    content = Column(JSON, nullable=False)
    
    # Change tracking
    changes_summary = Column(Text, nullable=True)
    
    # Created by
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    document = relationship("QuoteDocument", back_populates="versions", foreign_keys=[document_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<QuoteDocumentVersion v{self.version} for Document {self.document_id}>"

