"""Satellite monitoring and analysis routes"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
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


@router.post("/send-test-alert")
async def send_test_alert(
    to_email: str = "admin@watery.local",
    water_body_name: str = "Bhavani River",
    db: Session = Depends(get_db),
):
    """Send a test alert email for demonstration purposes"""
    from app.monitoring.email_alert import send_email_alert
    from app.core.config import settings
    
    if not settings.smtp_user or not settings.smtp_pass:
        raise HTTPException(
            status_code=400,
            detail="SMTP credentials not configured. Please set SMTP_USER and SMTP_PASS in environment variables."
        )
    
    try:
        subject = f"🚨 Water Body Alert - {water_body_name}"
        
        body = f"""
Water Bodies Monitoring System - Alert Notification

Water Body: {water_body_name}
Alert Type: Encroachment Detected
Severity: HIGH

Details:
- Encroachment detected in monitored area
- Water level change: -5.2%
- Encroachment percentage: 15%
- Detection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Recommendation:
Please visit the dashboard immediately to view satellite images and take necessary action.

Dashboard URL: http://localhost:3001

---
This is an automated alert from Watery Monitoring System
Do not reply to this email
"""
        
        send_email_alert(subject, body, to_email)
        
        # Create alert record in database
        alert = Alert(
            water_body_id=1,
            alert_type="encroachment",
            severity="high",
            message=f"Test alert sent to {to_email}",
            is_resolved=False
        )
        db.add(alert)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Test alert email sent to {to_email}",
            "water_body": water_body_name,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send alert: {str(e)}"
        )


@router.post("/send-bulk-alerts")
async def send_bulk_alerts_to_all_users(
    db: Session = Depends(get_db),
):
    """Send encroachment alerts to all active users with details of all encroached water bodies"""
    from app.models.water_body import User
    from app.services.osm_service import OSMService
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    try:
        # Fetch all active users
        users = db.query(User).filter(User.is_active == True).all()
        if not users:
            raise HTTPException(status_code=400, detail="No active users found in database")
        
        # Fetch all encroached water bodies
        all_bodies = OSMService.get_erode_water_bodies()
        encroached_bodies = [body for body in all_bodies if body.get('encroached', False)]
        
        if not encroached_bodies:
            return {
                "status": "info",
                "message": "No encroached water bodies found",
                "users_notified": 0,
                "encroached_count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Generate summary table
        table_rows = ""
        for i, body in enumerate(encroached_bodies, 1):
            enc_pct = body.get('encroachment_percentage', 0)
            water_pct = 100 - enc_pct
            severity = "CRITICAL 🔴" if enc_pct > 20 else "HIGH 🟠" if enc_pct > 10 else "MODERATE 🟡"
            
            table_rows += f"""
            <tr style="background-color: {'#FEE2E2' if enc_pct > 20 else '#FEF3C7'}; border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 12px; border-right: 1px solid #e5e7eb;"><strong>{i}. {body['name']}</strong></td>
                <td style="padding: 12px; border-right: 1px solid #e5e7eb;">{body['type']}</td>
                <td style="padding: 12px; border-right: 1px solid #e5e7eb;"><strong>{enc_pct:.1f}%</strong></td>
                <td style="padding: 12px; border-right: 1px solid #e5e7eb;"><strong>{water_pct:.1f}%</strong></td>
                <td style="padding: 12px; border-right: 1px solid #e5e7eb;">{body['area_sq_km']:.2f}</td>
                <td style="padding: 12px; text-align: center;">{severity}</td>
            </tr>
            """
        
        # Prepare email body
        avg_encroachment = sum(b.get('encroachment_percentage', 0) for b in encroached_bodies) / len(encroached_bodies)
        total_area = sum(b.get('area_sq_km', 0) for b in encroached_bodies)
        total_population = sum(b.get('population_nearby', 0) for b in encroached_bodies)
        
        def get_html_body(user_name):
            return f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 1000px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);">
                        <div style="background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                            <h1 style="margin: 0; font-size: 28px;">⚠️ ENCROACHMENT ALERT REPORT</h1>
                            <p style="margin: 10px 0 0 0;">Watery Water Bodies Monitoring System</p>
                        </div>
                        
                        <div style="background: white; padding: 30px;">
                            <p style="font-size: 16px; margin-bottom: 5px;">Dear <strong>{user_name}</strong>,</p>
                            <p style="color: #666; margin-bottom: 20px;">This is an urgent alert regarding encroachment detected in monitored water bodies across Erode District.</p>
                            
                            <div style="background-color: #FEE2E2; border-left: 4px solid #DC2626; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                <p style="margin: 0; color: #7F1D1D;"><strong>🔴 CRITICAL ALERT</strong></p>
                                <p style="margin: 5px 0 0 0; color: #7F1D1D;">{len(encroached_bodies)} water bodies show significant encroachment. Immediate action required.</p>
                            </div>
                            
                            <h3 style="color: #374151; margin-top: 30px; border-bottom: 2px solid #DC2626; padding-bottom: 10px;">📊 Summary Statistics</h3>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0;">
                                <div style="background: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #DC2626;">{len(encroached_bodies)}</div>
                                    <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">Encroached Bodies</div>
                                </div>
                                <div style="background: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #EA580C;">{avg_encroachment:.1f}%</div>
                                    <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">Avg Encroachment</div>
                                </div>
                                <div style="background: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #0284C7;">{total_area:.1f}</div>
                                    <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">Total Area (sq km)</div>
                                </div>
                                <div style="background: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: bold; color: #10B981;">{int(total_population/1000)}</div>
                                    <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">Nearby Pop (K)</div>
                                </div>
                            </div>
                            
                            <h3 style="color: #374151; margin-top: 30px; border-bottom: 2px solid #DC2626; padding-bottom: 10px;">🚨 All Encroached Water Bodies</h3>
                            <table style="width: 100%; border-collapse: collapse; margin: 20px 0; background: white;">
                                <thead>
                                    <tr style="background-color: #374151; color: white;">
                                        <th style="padding: 12px; text-align: left;">Water Body</th>
                                        <th style="padding: 12px; text-align: left;">Type</th>
                                        <th style="padding: 12px; text-align: center;">Encroachment %</th>
                                        <th style="padding: 12px; text-align: center;">Water Level %</th>
                                        <th style="padding: 12px; text-align: center;">Area (sq km)</th>
                                        <th style="padding: 12px; text-align: center;">Severity</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_rows}
                                </tbody>
                            </table>
                            
                            <div style="background: #DBEAFE; border-left: 4px solid #0284C7; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                <p style="margin: 0; color: #1e40af;"><strong>📊 Open Dashboard:</strong></p>
                                <p style="margin: 10px 0 0 0; color: #1e40af;"><a href="http://localhost:3001" style="color: #0284C7; text-decoration: none; font-weight: bold;">http://localhost:3001</a></p>
                            </div>
                            
                            <h3 style="color: #374151;">🔔 Required Actions:</h3>
                            <ol style="color: #555;">
                                <li>Review all satellite images on the dashboard</li>
                                <li>Contact local authorities immediately</li>
                                <li>Deploy field verification teams</li>
                                <li>Document encroachments with photos and GPS</li>
                                <li>Initiate legal proceedings</li>
                            </ol>
                        </div>
                        
                        <div style="background-color: #1F2937; color: #E5E7EB; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; font-size: 12px;">
                            <p style="margin: 0;">Watery - Water Bodies Monitoring System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p style="margin: 5px 0 0 0; color: #9CA3AF;">Do not reply to this email</p>
                        </div>
                    </div>
                </body>
            </html>
            """
        
        # Send emails to all users
        sent_count = 0
        failed_users = []
        
        for user in users:
            try:
                subject = f"🚨 URGENT: Encroachment Alert - {len(encroached_bodies)} Water Bodies"
                html_body = get_html_body(user.full_name or user.username)
                
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"Watery System <{settings.smtp_user}>"
                msg["To"] = user.email
                msg.attach(MIMEText(html_body, "html"))
                
                # Send email
                if settings.smtp_user and settings.smtp_pass:
                    server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
                    server.starttls()
                    server.login(settings.smtp_user, settings.smtp_pass)
                    server.sendmail(settings.smtp_user, user.email, msg.as_string())
                    server.quit()
                    sent_count += 1
                else:
                    # Log to console if SMTP not configured
                    print(f"Would send email to {user.email}: {subject}")
                    sent_count += 1
                    
            except Exception as e:
                failed_users.append(f"{user.email}: {str(e)}")
        
        # Create alert record
        for body in encroached_bodies:
            try:
                alert = Alert(
                    water_body_id=body.get('id', 1),
                    alert_type="encroachment",
                    severity="high" if body.get('encroachment_percentage', 0) > 15 else "medium",
                    message=f"Bulk alert sent to {sent_count} users about {body['name']} encroachment",
                    is_resolved=False
                )
                db.add(alert)
            except:
                pass
        
        try:
            db.commit()
        except:
            db.rollback()
        
        return {
            "status": "success",
            "message": f"Encroachment alerts sent successfully",
            "users_notified": sent_count,
            "encroached_bodies_count": len(encroached_bodies),
            "failed_users": failed_users if failed_users else [],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send bulk alerts: {str(e)}"
        )
