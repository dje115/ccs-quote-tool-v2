from sqlalchemy import Column, Integer, String, Text
from .base import Base

class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, index=True)
    sector_name = Column(String(255), nullable=False, unique=True, index=True)
    prompt_ready_replacement_line = Column(Text, nullable=False)
    example_keywords = Column(Text, nullable=False)
    example_companies = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Sector(id={self.id}, name='{self.sector_name}')>"