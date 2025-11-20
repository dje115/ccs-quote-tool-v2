#!/usr/bin/env python3
"""
Quote Prompt History model
Stores history of prompts used for quote generation
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Boolean, Integer, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .base import Base, BaseModel


class QuotePromptHistory(BaseModel):
    """Quote Prompt History model"""
    __tablename__ = "quote_prompt_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Prompt information
    prompt_text = Column(Text, nullable=False)  # The actual prompt text sent to AI
    prompt_variables = Column(JSON, nullable=False, default=dict)  # Variables used in prompt
    
    # AI generation metadata
    ai_model = Column(String(100), nullable=True)
    ai_provider = Column(String(100), nullable=True)
    temperature = Column(Numeric(3, 2), nullable=True)
    max_tokens = Column(Integer, nullable=True)
    
    # Results
    generation_successful = Column(Boolean, default=False, nullable=False)
    generation_error = Column(Text, nullable=True)
    generated_quote_data = Column(JSON, nullable=True)  # The full AI response
    
    # Created by
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    quote = relationship("Quote", foreign_keys=[quote_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<QuotePromptHistory {self.id} for Quote {self.quote_id}>"

