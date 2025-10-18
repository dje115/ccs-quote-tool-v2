from pydantic import BaseModel
from typing import Optional

class SectorResponse(BaseModel):
    id: int
    sector_name: str
    prompt_ready_replacement_line: str
    example_keywords: str
    example_companies: Optional[str] = None

    class Config:
        from_attributes = True


