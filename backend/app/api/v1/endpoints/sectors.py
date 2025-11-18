from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.core.database import get_async_db
from app.models.sector import Sector
from app.schemas.sector import SectorResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[SectorResponse])
async def get_sectors(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all available sectors for lead generation campaigns
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        stmt = select(Sector)
        result = await db.execute(stmt)
        sectors = result.scalars().all()
        return sectors
    except Exception as e:
        logger.error(f"Failed to retrieve sectors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sectors: {str(e)}"
        )

@router.get("/{sector_id}", response_model=SectorResponse)
async def get_sector(
    sector_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific sector by ID
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    stmt = select(Sector).where(Sector.id == sector_id)
    result = await db.execute(stmt)
    sector = result.scalar_one_or_none()
    if not sector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sector not found"
        )
    return sector
