"""Water bodies management routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.water_body import WaterBodyCreate, WaterBodyResponse
from app.models.water_body import WaterBody

router = APIRouter(prefix="/water-bodies", tags=["water bodies"])


@router.post("/", response_model=WaterBodyResponse)
async def create_water_body(
    water_body: WaterBodyCreate, db: Session = Depends(get_db)
):
    """Create a new water body entry"""
    db_water_body = WaterBody(**water_body.dict())
    db.add(db_water_body)
    db.commit()
    db.refresh(db_water_body)
    return db_water_body


@router.get("/", response_model=List[WaterBodyResponse])
async def get_water_bodies(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Get all water bodies"""
    water_bodies = db.query(WaterBody).offset(skip).limit(limit).all()
    return water_bodies


@router.get("/{water_body_id}", response_model=WaterBodyResponse)
async def get_water_body(water_body_id: int, db: Session = Depends(get_db)):
    """Get a specific water body"""
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water body not found",
        )
    
    return water_body


@router.put("/{water_body_id}", response_model=WaterBodyResponse)
async def update_water_body(
    water_body_id: int,
    water_body_data: WaterBodyCreate,
    db: Session = Depends(get_db),
):
    """Update a water body"""
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water body not found",
        )
    
    for field, value in water_body_data.dict().items():
        setattr(water_body, field, value)
    
    db.commit()
    db.refresh(water_body)
    return water_body


@router.delete("/{water_body_id}")
async def delete_water_body(water_body_id: int, db: Session = Depends(get_db)):
    """Delete a water body"""
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water body not found",
        )
    
    db.delete(water_body)
    db.commit()
    return {"message": "Water body deleted successfully"}
