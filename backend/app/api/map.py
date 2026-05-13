"""
Map API endpoints for water body monitoring
Provides GeoJSON data and map configuration for Leaflet
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.services.osm_service import OSMService, ERODE_DISTRICT
from app.services.seasonal_service import SeasonalService
from app.services.image_processing import ImageProcessingService
from app.services.email_service import EmailService
from app.core.database import get_db
from app.models.water_body import WaterBody, MonitoringRecord, User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/map",
    tags=["map"]
)


@router.get("/water-bodies-geojson")
async def get_water_bodies_geojson(db: Session = Depends(get_db)):
    """
    Get all water bodies in GeoJSON format for Leaflet
    Includes Erode district water bodies with encroachment status from database
    """
    # Get OSM water bodies
    water_bodies = OSMService.get_erode_water_bodies()
    geojson = OSMService.create_geojson_features(water_bodies)
    
    # Fetch encroachment status from database
    db_water_bodies = db.query(WaterBody).all()
    encroachment_map = {
        wb.name: {
            "is_encroached": wb.is_encroached,
            "encroached_at": wb.encroached_at.isoformat() if wb.encroached_at else None
        }
        for wb in db_water_bodies
    }
    
    # Merge encroachment status into GeoJSON features
    for feature in geojson.get("features", []):
        body_name = feature["properties"].get("name")
        if body_name in encroachment_map:
            feature["properties"]["is_encroached"] = encroachment_map[body_name]["is_encroached"]
            feature["properties"]["encroached_at"] = encroachment_map[body_name]["encroached_at"]
            # Keep encroached for backward compatibility
            feature["properties"]["encroached"] = encroachment_map[body_name]["is_encroached"]
    
    return geojson


@router.get("/erode-district")
async def get_erode_district_info():
    """Get Erode district information and boundaries"""
    return {
        "name": ERODE_DISTRICT["name"],
        "state": ERODE_DISTRICT["state"],
        "center": {
            "lat": ERODE_DISTRICT["center_lat"],
            "lon": ERODE_DISTRICT["center_lon"]
        },
        "bounds": {
            "north": ERODE_DISTRICT["north"],
            "south": ERODE_DISTRICT["south"],
            "east": ERODE_DISTRICT["east"],
            "west": ERODE_DISTRICT["west"]
        },
        "zoom_level": 11,
        "water_bodies_count": len(OSMService.get_erode_water_bodies())
    }


@router.get("/tile-layer/{provider}")
async def get_tile_layer(provider: str = "openstreetmap"):
    """
    Get tile layer URL for Leaflet
    Supports multiple free providers:
    - openstreetmap
    - satellite-openstreetmap
    - dark
    - toner
    """
    url = OSMService.get_tile_layer_url(provider)
    if not url:
        raise HTTPException(status_code=400, detail="Invalid tile provider")
    
    return {
        "provider": provider,
        "url": url,
        "attribution": "© OpenStreetMap contributors, © Stadia Maps"
    }


@router.get("/satellite/{lat}/{lon}")
async def get_satellite_image(lat: float, lon: float, zoom: int = 14):
    """
    Get satellite image for a specific location
    Completely free using OpenStreetMap
    """
    try:
        image = OSMService.get_free_satellite_tile(lat, lon, zoom)
        mask, percentage = OSMService.detect_water_from_color(image)
        
        # Save image temporarily and encode
        from io import BytesIO
        import base64
        
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
        
        return {
            "lat": lat,
            "lon": lon,
            "zoom": zoom,
            "water_percentage": round(percentage, 2),
            "image_base64": f"data:image/png;base64,{img_base64}",
            "timestamp": "2024-01-01T00:00:00Z"  # Replace with actual timestamp
        }
    except Exception as e:
        logger.error(f"Error fetching satellite image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{body_id}")
async def compare_water_areas(
    body_id: int,
    db: Session = Depends(get_db)
):
    """
    Compare satellite images over time for a water body with seasonal awareness.
    Distinguishes between natural seasonal variation and actual encroachment.
    
    Args:
        body_id: ID of water body to analyze
        db: Database session
    
    Returns:
        Detailed comparison with seasonal classification
    """
    try:
        # Get water body from database
        water_body = db.query(WaterBody).filter(WaterBody.id == body_id).first()
        if not water_body:
            raise HTTPException(status_code=404, detail="Water body not found")
        
        # Get last two monitoring records for this water body
        records = db.query(MonitoringRecord)\
            .filter(MonitoringRecord.water_body_id == body_id)\
            .order_by(MonitoringRecord.captured_at.desc())\
            .limit(2).all()
        
        # If we have less than 2 records, fetch from OSM and create simulation
        if len(records) < 2:
            water_bodies = OSMService.get_erode_water_bodies()
            body_data = next(
                (b for b in water_bodies if b["name"].lower() == water_body.name.lower()),
                None
            )
            if not body_data:
                raise HTTPException(status_code=404, detail="Water body not found in OSM")
            
            # Fetch satellite image
            current_image = OSMService.get_free_satellite_tile(
                body_data["lat"],
                body_data["lon"]
            )
            mask_current, water_area_current = OSMService.detect_water_from_color(current_image)
            
            # Simulate previous mask (in production, fetch from database)
            previous_image = OSMService.get_free_satellite_tile(
                body_data["lat"],
                body_data["lon"]
            )
            mask_previous, water_area_previous = OSMService.detect_water_from_color(previous_image)
        else:
            # Get current and previous records
            curr_record = records[0]
            prev_record = records[1]
            
            # In production, load actual masks from stored images
            # For now, we simulate by refetching
            water_bodies = OSMService.get_erode_water_bodies()
            body_data = next(
                (b for b in water_bodies if b["name"].lower() == water_body.name.lower()),
                None
            )
            
            current_image = OSMService.get_free_satellite_tile(
                body_data["lat"],
                body_data["lon"]
            )
            mask_current, water_area_current = OSMService.detect_water_from_color(current_image)
            
            previous_image = OSMService.get_free_satellite_tile(
                body_data["lat"],
                body_data["lon"]
            )
            mask_previous, water_area_previous = OSMService.detect_water_from_color(previous_image)
        
        # Detect current season
        current_season = SeasonalService.get_current_season()
        
        # Compare with seasonal awareness
        comparison = OSMService.compare_water_areas(
            mask1=mask_previous,
            mask2=mask_current,
            water_body_type=water_body.body_type or "lake",
            is_seasonal=water_body.is_seasonal,
            current_season=current_season
        )
        
        # Detect urbanization (encroachment)
        urbanization = ImageProcessingService.detect_urbanization_change(
            prev_image=previous_image,
            curr_image=current_image,
            water_boundary=mask_current
        )
        
        # Get seasonal thresholds and recommendations
        season_threshold = SeasonalService.get_seasonal_threshold(
            current_season,
            water_body.body_type or "lake"
        )
        recommendation = SeasonalService.get_monitoring_recommendation(
            current_season,
            water_body.body_type or "lake"
        )
        
        # Update water body with monitoring data
        water_body.last_monitored = datetime.utcnow()
        water_body.last_monitoring_season = current_season
        water_body.last_water_loss_percent = comparison["change_percent"]
        
        # Determine final encroachment status
        is_encroached = comparison["encroached"]
        
        # If urbanization detected, mark as encroached
        if urbanization.get("likely_urbanization"):
            is_encroached = True
        
        # Track if this is a NEW encroachment detection
        was_encroached_before = water_body.is_encroached
        
        # Update encroachment status
        water_body.is_encroached = is_encroached
        if is_encroached and not water_body.encroached_at:
            from datetime import datetime
            water_body.encroached_at = datetime.utcnow()
        
        db.commit()
        
        # Send email alert if NEW encroachment detected (changed from False to True)
        if is_encroached and not was_encroached_before:
            try:
                # Get all active users to send emails
                active_users = db.query(User).filter(User.is_active == True).all()
                recipient_emails = [user.email for user in active_users if user.email]
                
                if recipient_emails:
                    # Prepare encroachment details
                    encroachment_details = {
                        "water_body": water_body.name,
                        "type": water_body.body_type or "Unknown",
                        "area": f"{water_body.area_sq_km} sq km",
                        "water_loss": f"{comparison['change_percent']:.1f}%",
                        "threshold": f"{comparison['threshold_applied']:.1f}%",
                        "reason": comparison.get("reason", "Exceeds seasonal threshold"),
                        "classification": comparison.get("classification", "encroachment"),
                        "detected_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # If urbanization was detected, add that info
                    if urbanization.get("likely_urbanization"):
                        encroachment_details["urbanization"] = urbanization.get("encroachment_type", "Unknown")
                    
                    # Send bulk alert emails
                    stats = EmailService.send_bulk_encroachment_alert(
                        recipient_emails=recipient_emails,
                        water_body_name=water_body.name,
                        encroachment_details=encroachment_details,
                    )
                    
                    logger.info(f"✉️  Encroachment alert sent for '{water_body.name}': "
                               f"{stats['sent']} emails sent, {stats['failed']} failed")
            except Exception as e:
                logger.error(f"❌ Failed to send encroachment email alert: {str(e)}")
                # Don't fail the API call if email fails - just log it
        
        return {
            "water_body_id": body_id,
            "water_body_name": water_body.name,
            "body_type": water_body.body_type,
            "is_seasonal": water_body.is_seasonal,
            "current_season": current_season,
            "season_name": SeasonalService.get_season_name(current_season),
            "comparison": {
                "change_percent": comparison["change_percent"],
                "threshold_applied": comparison["threshold_applied"],
                "classification": comparison["classification"],
                "reason": comparison["reason"],
                "is_seasonal_variation": comparison["is_seasonal_variation"],
                "encroached": comparison["encroached"]
            },
            "urbanization": {
                "urban_growth": urbanization["urban_growth"],
                "likely_urbanization": urbanization["likely_urbanization"],
                "encroachment_type": urbanization["encroachment_type"]
            },
            "status": "encroached" if is_encroached else "normal",
            "recommendation": recommendation,
            "area_sq_km": water_body.area_sq_km
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing water areas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
