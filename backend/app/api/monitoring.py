"""Satellite monitoring and analysis routes"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.satellite import SatelliteProcessor, SentinelAPI
from app.models.water_body import MonitoringRecord, Encroachment, Alert, WaterBody
from pydantic import BaseModel

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Pydantic models
class MonitoringRecordResponse(BaseModel):
    id: int
    water_body_id: int
    satellite_image: str
    captured_at: datetime
    processed_at: datetime
    ndvi_value: float
    water_area_sq_km: float
    change_detected: bool
    
    class Config:
        from_attributes = True


class EncroachmentResponse(BaseModel):
    id: int
    water_body_id: int
    location: str
    area_sq_km: float
    severity: str
    detected_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    water_body_id: int
    alert_type: str
    severity: str
    message: str
    created_at: datetime
    is_resolved: bool
    
    class Config:
        from_attributes = True


class UrbanizationAnalysisResponse(BaseModel):
    location: dict
    urbanization_level: float
    risk_assessment: str
    recommendation: str


class SatelliteAnalysisRequest(BaseModel):
    water_body_id: int
    force_reanalysis: bool = False


@router.post("/analyze-urbanization")
async def analyze_urbanization(
    lat: float,
    lng: float,
    db: Session = Depends(get_db)
) -> UrbanizationAnalysisResponse:
    """
    Analyze urbanization level at a specific location
    Returns urbanization level (0-1) and risk assessment
    """
    processor = SatelliteProcessor()
    urbanization_level = processor.estimate_urbanization_level(lat, lng)
    
    # Risk assessment based on urbanization
    if urbanization_level > 0.7:
        risk = "High"
        recommendation = "Increased monitoring recommended. High encroachment risk."
    elif urbanization_level > 0.4:
        risk = "Medium"
        recommendation = "Regular monitoring advised. Moderate encroachment risk."
    else:
        risk = "Low"
        recommendation = "Standard monitoring sufficient."
    
    return UrbanizationAnalysisResponse(
        location={"latitude": lat, "longitude": lng},
        urbanization_level=urbanization_level,
        risk_assessment=risk,
        recommendation=recommendation
    )


@router.post("/search-satellite-images")
async def search_satellite_images(
    water_body_id: int,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Search for available satellite images for a water body
    Returns list of available images from the past N days
    """
    water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water body not found"
        )
    
    # Parse location
    import json
    try:
        location_data = json.loads(water_body.location)
        coords = location_data.get("coordinates", [0, 0])
        lng, lat = coords[0], coords[1]
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid water body location"
        )
    
    # Search for images
    sentinel_api = SentinelAPI()
    date_end = datetime.now().date()
    date_start = date_end - timedelta(days=days_back)
    
    search_results = sentinel_api.search_images(
        lat=lat,
        lng=lng,
        date_start=date_start.isoformat(),
        date_end=date_end.isoformat()
    )
    
    return {
        "water_body_id": water_body_id,
        "search_parameters": search_results["query"],
        "available_images": search_results["results_count"],
        "images": search_results["images"]
    }


@router.post("/process-satellite-image")
async def process_satellite_image(
    request: SatelliteAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process satellite imagery for a water body
    Analyzes water area, detects changes and encroachments
    """
    water_body = db.query(WaterBody).filter(WaterBody.id == request.water_body_id).first()
    if not water_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Water body not found"
        )
    
    # Add background task to process satellite data
    background_tasks.add_task(
        process_satellite_data_task,
        water_body.id,
        db
    )
    
    return {
        "status": "processing",
        "water_body_id": request.water_body_id,
        "message": "Satellite imagery analysis started. Results will be available shortly."
    }


@router.get("/water-body/{water_body_id}/monitoring-records", response_model=List[MonitoringRecordResponse])
async def get_monitoring_records(
    water_body_id: int,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get monitoring records for a water body
    """
    records = db.query(MonitoringRecord).filter(
        MonitoringRecord.water_body_id == water_body_id
    ).order_by(MonitoringRecord.captured_at.desc()).limit(limit).all()
    
    return records


@router.get("/water-body/{water_body_id}/encroachments", response_model=List[EncroachmentResponse])
async def get_encroachments(
    water_body_id: int,
    status_filter: str = "all",
    db: Session = Depends(get_db)
):
    """
    Get encroachment records for a water body
    status_filter: all, pending, confirmed, resolved
    """
    query = db.query(Encroachment).filter(Encroachment.water_body_id == water_body_id)
    
    if status_filter != "all":
        query = query.filter(Encroachment.status == status_filter)
    
    encroachments = query.order_by(Encroachment.detected_at.desc()).all()
    return encroachments


@router.get("/water-body/{water_body_id}/alerts", response_model=List[AlertResponse])
async def get_alerts(
    water_body_id: int,
    unresolved_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get alerts for a water body
    """
    query = db.query(Alert).filter(Alert.water_body_id == water_body_id)
    
    if unresolved_only:
        query = query.filter(Alert.is_resolved == False)
    
    alerts = query.order_by(Alert.created_at.desc()).all()
    return alerts


@router.post("/alert/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    resolution_note: str = "",
    db: Session = Depends(get_db)
):
    """
    Mark an alert as resolved
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    if alert.metadata_info is None:
        alert.metadata_info = {}
    alert.metadata_info["resolution_note"] = resolution_note
    
    db.commit()
    db.refresh(alert)
    
    return {
        "status": "resolved",
        "alert_id": alert.id,
        "resolved_at": alert.resolved_at
    }


@router.post("/encroachment/{encroachment_id}/confirm")
async def confirm_encroachment(
    encroachment_id: int,
    db: Session = Depends(get_db)
):
    """
    Confirm an encroachment detection
    """
    encroachment = db.query(Encroachment).filter(Encroachment.id == encroachment_id).first()
    if not encroachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encroachment not found"
        )
    
    encroachment.status = "confirmed"
    encroachment.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(encroachment)
    
    return {
        "status": "confirmed",
        "encroachment_id": encroachment.id,
        "confirmed_at": encroachment.confirmed_at
    }


@router.get("/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get overall monitoring dashboard statistics
    """
    total_water_bodies = db.query(WaterBody).count()
    active_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
    pending_encroachments = db.query(Encroachment).filter(Encroachment.status == "pending").count()
    monitoring_records_today = db.query(MonitoringRecord).filter(
        MonitoringRecord.processed_at >= datetime.utcnow().date()
    ).count()
    
    # Calculate average urbanization
    water_bodies = db.query(WaterBody).all()
    avg_urbanization = sum([wb.urbanization_level or 0 for wb in water_bodies]) / max(len(water_bodies), 1)
    
    return {
        "total_water_bodies": total_water_bodies,
        "active_alerts": active_alerts,
        "pending_encroachments": pending_encroachments,
        "monitoring_records_today": monitoring_records_today,
        "average_urbanization_level": avg_urbanization,
        "timestamp": datetime.utcnow().isoformat()
    }


# Background task for processing satellite data
def process_satellite_data_task(water_body_id: int, db: Session):
    """Background task to process satellite imagery"""
    try:
        water_body = db.query(WaterBody).filter(WaterBody.id == water_body_id).first()
        if not water_body:
            return
        
        processor = SatelliteProcessor()
        
        # Create mock monitoring record
        record = MonitoringRecord(
            water_body_id=water_body_id,
            satellite_image="sentinel-2-mock",
            captured_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            ndvi_value=0.5,
            water_area_sq_km=water_body.area_sq_km,
            change_detected=False,
            metadata_info={"status": "processed"}
        )
        
        db.add(record)
        
        # Update last monitored timestamp
        water_body.last_monitored = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        print(f"Error processing satellite data: {str(e)}")


@router.post("/trigger-analysis/{water_body_id}")
async def trigger_analysis(
    water_body_id: int,
    db: Session = Depends(get_db),
):
    """Trigger satellite image analysis for a water body"""
    # This will be implemented to:
    # 1. Fetch latest satellite data from Google Earth Engine
    # 2. Process the image with TensorFlow models
    # 3. Detect changes and encroachments
    # 4. Store results in database
    # 5. Generate alerts if needed
    
    return {
        "message": "Analysis triggered",
        "water_body_id": water_body_id,
        "status": "processing",
    }
