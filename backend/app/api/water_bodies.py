"""Water bodies management routes"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.water_body import WaterBodyCreate, WaterBodyResponse
from app.models.water_body import WaterBody, User
from app.services.email_service import EmailService
from app.core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

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
    
    # Check if encroachment status is changing
    is_encroached_changing = False
    was_encroached = water_body.is_encroached
    new_is_encroached = water_body_data.dict().get("is_encroached", water_body.is_encroached)
    
    # If marking as encroached and wasn't before, flag it
    if new_is_encroached and not was_encroached:
        is_encroached_changing = True
    
    # Update water body fields
    for field, value in water_body_data.dict().items():
        setattr(water_body, field, value)
    
    # Set encroached_at timestamp when marking as encroached
    if new_is_encroached and not water_body.encroached_at:
        water_body.encroached_at = datetime.utcnow()
    
    db.commit()
    db.refresh(water_body)
    
    # Send encroachment alert if status changed to encroached
    if is_encroached_changing:
        try:
            # Get list of recipient emails
            recipient_emails = []
            
            # Add all active users
            active_users = db.query(User).filter(User.is_active == True).all()
            for user in active_users:
                if user.email:
                    recipient_emails.append(user.email)
            
            if recipient_emails:
                # Send alerts
                encroachment_details = {
                    "name": water_body.name,
                    "type": water_body.body_type or "Unknown",
                    "area": water_body.area_sq_km,
                    "detected_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                stats = EmailService.send_bulk_encroachment_alert(
                    recipient_emails=recipient_emails,
                    water_body_name=water_body.name,
                    encroachment_details=encroachment_details,
                )
                
                logger.info(f"Encroachment notification sent for {water_body.name}: "
                           f"{stats['sent']} successful, {stats['failed']} failed")
        except Exception as e:
            logger.error(f"Failed to send encroachment notification: {str(e)}")
    
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


@router.post("/{water_body_id}/alert-encroachment")
async def send_encroachment_alert(
    water_body_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send encroachment alert email for a water body.
    Sends to the current user's email and all administrators.
    """
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water body not found",
        )
    
    # Get list of recipient emails
    recipient_emails = []
    
    # Add current user if they have email
    if current_user.email:
        recipient_emails.append(current_user.email)
    
    # Add all admin users
    admin_users = db.query(User).filter(User.role == "admin").all()
    for admin in admin_users:
        if admin.email and admin.email not in recipient_emails:
            recipient_emails.append(admin.email)
    
    if not recipient_emails:
        return {
            "message": "No email recipients configured",
            "water_body_id": water_body_id,
            "water_body_name": water_body.name,
        }
    
    # Prepare encroachment details
    encroachment_details = {
        "name": water_body.name,
        "type": getattr(water_body, 'body_type', 'Unknown'),
    }
    
    # Send alerts
    stats = EmailService.send_bulk_encroachment_alert(
        recipient_emails=recipient_emails,
        water_body_name=water_body.name,
        encroachment_details=encroachment_details,
    )
    
    return {
        "message": "Encroachment alert emails sent",
        "water_body_id": water_body_id,
        "water_body_name": water_body.name,
        "recipients_sent": stats["sent"],
        "recipients_failed": stats["failed"],
        "status": "success" if stats["sent"] > 0 else "partial_failure",
    }
