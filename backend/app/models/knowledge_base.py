#!/usr/bin/env python3
"""
Knowledge Base models
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
import enum
import uuid
from .base import Base, BaseModel, TimestampMixin


class ArticleStatus(enum.Enum):
    """Article status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class KnowledgeBaseArticle(BaseModel):
    """Knowledge Base Article model"""
    __tablename__ = "knowledge_base_articles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Article details
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=list)  # List of tags
    
    # Status
    status = Column(String(20), default=ArticleStatus.PUBLISHED.value, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    view_count = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", backref="knowledge_base_articles")
    linked_tickets = relationship("KnowledgeBaseTicketLink", back_populates="article", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeBaseArticle {self.title}>"
    
    __table_args__ = (
        Index('idx_kb_article_tenant_status', 'tenant_id', 'status'),
        Index('idx_kb_article_category', 'category'),
    )


class KnowledgeBaseTicketLink(Base, TimestampMixin):
    """Link between tickets and knowledge base articles"""
    __tablename__ = "knowledge_base_ticket_links"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(String(36), ForeignKey("knowledge_base_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Link metadata
    link_type = Column(String(20), default="suggested", nullable=False)  # "suggested", "linked", "resolved"
    relevance_score = Column(Integer, nullable=True)  # 0-100
    
    # Relationships
    tenant = relationship("Tenant")
    ticket = relationship("Ticket", backref="kb_links")
    article = relationship("KnowledgeBaseArticle", back_populates="linked_tickets")
    
    def __repr__(self):
        return f"<KnowledgeBaseTicketLink ticket={self.ticket_id} article={self.article_id}>"
    
    __table_args__ = (
        Index('idx_kb_link_ticket_article', 'ticket_id', 'article_id'),
    )

