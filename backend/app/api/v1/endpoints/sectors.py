from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.models.sector import Sector
from app.schemas.sector import SectorResponse

router = APIRouter()

@router.get("/", response_model=List[SectorResponse])
def get_sectors(
    db: Session = Depends(get_db)
):
    """Get all available sectors for lead generation campaigns"""
    try:
        sectors = db.query(Sector).all()
        return sectors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sectors: {str(e)}"
        )

@router.get("/{sector_id}", response_model=SectorResponse)
def get_sector(
    sector_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific sector by ID"""
    sector = db.query(Sector).filter(Sector.id == sector_id).first()
    if not sector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sector not found"
        )
    return sector
