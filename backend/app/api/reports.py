"""API endpoints for reporting and alerts"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.water_body import User, HistoricalRecord, Alert
from app.services.email_service import EmailService
from app.services.pdf_generator import PDFReportGenerator
import logging
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/historical/{water_body_id}")
async def get_historical_data(
    water_body_id: int,
    days: int = 15,
    db: Session = Depends(get_db)
):
    """Get historical monitoring data for a water body (default: last 15 days)"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query historical records
        records = db.query(HistoricalRecord).filter(
            (HistoricalRecord.water_body_id == water_body_id) &
            (HistoricalRecord.recorded_at >= start_date) &
            (HistoricalRecord.recorded_at <= end_date)
        ).order_by(HistoricalRecord.recorded_at).all()
        
        # Format response
        data = [
            {
                "date": record.recorded_at.strftime("%Y-%m-%d"),
                "water_percentage": record.water_percentage,
                "area_sq_km": record.area_sq_km,
                "encroachment_percentage": record.encroachment_percentage,
                "water_quality": record.water_quality
            }
            for record in records
        ]
        
        # Calculate statistics
        if data:
            water_percentages = [d["water_percentage"] for d in data if d["water_percentage"] is not None]
            avg_water = sum(water_percentages) / len(water_percentages) if water_percentages else 0
            max_water = max(water_percentages) if water_percentages else 0
            min_water = min(water_percentages) if water_percentages else 0
        else:
            avg_water = max_water = min_water = 0
        
        return {
            "water_body_id": water_body_id,
            "days": days,
            "records_count": len(records),
            "average_water_percentage": round(avg_water, 2),
            "max_water_percentage": round(max_water, 2),
            "min_water_percentage": round(min_water, 2),
            "historical_data": data
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch historical data"
        )


@router.get("/summary")
async def get_water_bodies_summary(days: int = 15, db: Session = Depends(get_db)):
    """Get summary report for all water bodies (default: last 15 days)"""
    try:
        from app.models.water_body import WaterBody
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # First, get all water bodies from the database
        water_bodies = db.query(WaterBody).all()
        
        if not water_bodies:
            return {
                "total_bodies": 0,
                "encroached_count": 0,
                "avg_water_percentage": 0.0,
                "summary_data": []
            }
        
        # Query historical records for the date range
        records = db.query(HistoricalRecord).filter(
            HistoricalRecord.recorded_at >= start_date
        ).all()
        
        # Group historical data by water body
        water_bodies_data = {}
        for record in records:
            wb_id = record.water_body_id
            if wb_id not in water_bodies_data:
                water_bodies_data[wb_id] = {
                    "water_percentages": [],
                    "areas": [],
                    "encroachment_percentages": []
                }
            
            if record.water_percentage is not None:
                water_bodies_data[wb_id]["water_percentages"].append(record.water_percentage)
            if record.area_sq_km is not None:
                water_bodies_data[wb_id]["areas"].append(record.area_sq_km)
            if record.encroachment_percentage is not None:
                water_bodies_data[wb_id]["encroachment_percentages"].append(record.encroachment_percentage)
        
        # Build summary from all water bodies with historical data where available
        summary = []
        total_encroached = 0
        
        for wb in water_bodies:
            # Get historical data if available, otherwise use water body defaults
            if wb.id in water_bodies_data:
                data = water_bodies_data[wb.id]
                water_pct = data["water_percentages"]
                areas = data["areas"]
                encr_pct = data["encroachment_percentages"]
                
                avg_water = sum(water_pct) / len(water_pct) if water_pct else 75.0
                avg_area = sum(areas) / len(areas) if areas else wb.area_sq_km or 0
                avg_encroachment = sum(encr_pct) / len(encr_pct) if encr_pct else 0
            else:
                # Use water body default values when no historical data exists
                avg_water = 75.0
                avg_area = wb.area_sq_km or 0
                avg_encroachment = 10.0 if wb.is_encroached else 0
            
            is_encroached = avg_encroachment > 15 or wb.is_encroached
            if is_encroached:
                total_encroached += 1
            
            summary.append({
                "water_body_id": wb.id,
                "name": wb.name,
                "avg_water_percentage": round(avg_water, 2),
                "avg_area_sq_km": round(avg_area, 2),
                "avg_encroachment_percentage": round(avg_encroachment, 2),
                "is_encroached": is_encroached,
                "days_tracked": days
            })
        
        # Calculate overall average water percentage
        overall_avg = sum(b["avg_water_percentage"] for b in summary) / len(summary) if summary else 0
        
        return {
            "total_bodies": len(summary),
            "encroached_count": total_encroached,
            "avg_water_percentage": round(overall_avg, 2),
            "summary_data": sorted(summary, key=lambda x: x["avg_water_percentage"], reverse=True)
        }
        
    except Exception as e:
        logger.error(f"Error fetching summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch summary"
        )


@router.post("/send-encroachment-alert/{water_body_id}")
async def send_encroachment_alert(
    water_body_id: int,
    water_body_name: str,
    encroachment_details: dict = None,
    db: Session = Depends(get_db)
):
    """Send encroachment alert to all registered users"""
    try:
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No registered users found"
            )
        
        # Prepare email details
        if not encroachment_details:
            encroachment_details = {
                "water_body_id": water_body_id,
                "detected_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Send emails to all users
        recipient_emails = [user.email for user in users]
        stats = EmailService.send_bulk_encroachment_alert(
            recipient_emails,
            water_body_name,
            encroachment_details
        )
        
        # Log the alert
        logger.info(f"Encroachment alert sent: {water_body_name} - "
                   f"Sent: {stats['sent']}, Failed: {stats['failed']}")
        
        return {
            "status": "success",
            "water_body_id": water_body_id,
            "water_body_name": water_body_name,
            "emails_sent": stats["sent"],
            "emails_failed": stats["failed"],
            "total_recipients": len(recipient_emails)
        }
        
    except Exception as e:
        logger.error(f"Error sending encroachment alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send encroachment alert"
        )


@router.post("/record-monitoring/{water_body_id}")
async def record_monitoring_data(
    water_body_id: int,
    water_body_name: str,
    water_percentage: float,
    area_sq_km: float,
    water_quality: str,
    encroachment_percentage: float = 0,
    metadata_info: dict = None,
    db: Session = Depends(get_db)
):
    """Record historical monitoring data for a water body"""
    try:
        # Create new historical record
        record = HistoricalRecord(
            water_body_id=water_body_id,
            water_body_name=water_body_name,
            water_percentage=water_percentage,
            area_sq_km=area_sq_km,
            water_quality=water_quality,
            encroachment_percentage=encroachment_percentage,
            metadata_info=metadata_info or {}
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        logger.info(f"Recorded monitoring data for {water_body_name}: "
                   f"Water {water_percentage}%, Encroachment {encroachment_percentage}%")
        
        return {
            "status": "success",
            "message": "Monitoring data recorded successfully",
            "record_id": record.id,
            "water_body_id": water_body_id,
            "recorded_at": record.recorded_at
        }
        
    except Exception as e:
        logger.error(f"Error recording monitoring data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record monitoring data"
        )


@router.post("/notify-encroachments")
async def notify_encroachments(db: Session = Depends(get_db)):
    """Send email notifications for all encroached water bodies"""
    try:
        from app.services.osm_service import OSMService
        
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            return {
                "status": "success",
                "message": "No registered users found",
                "notifications_sent": 0
            }
        
        # Get all water bodies
        osm_service = OSMService()
        water_bodies = osm_service.get_all_water_bodies()
        
        # Find encroached bodies
        encroached_bodies = [wb for wb in water_bodies if wb.get('properties', {}).get('encroached', False)]
        
        recipient_emails = [user.email for user in users if user.email]
        total_notifications = 0
        
        # Send notifications for each encroached body
        for body in encroached_bodies:
            props = body.get('properties', {})
            water_body_name = props.get('name', 'Unknown')
            encroachment_pct = props.get('encroachment_percentage', 0)
            danger_level = props.get('danger_level', 'MEDIUM')
            
            details = {
                "percentage": encroachment_pct,
                "danger_level": danger_level,
                "detected_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            stats = EmailService.send_bulk_encroachment_alert(
                recipient_emails,
                water_body_name,
                details
            )
            
            total_notifications += stats["sent"]
            logger.info(f"Encroachment notification sent for {water_body_name}")
        
        return {
            "status": "success",
            "message": f"Notifications sent for {len(encroached_bodies)} encroached water bodies",
            "encroached_bodies_count": len(encroached_bodies),
            "notifications_sent": total_notifications,
            "total_recipients": len(recipient_emails)
        }
        
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")
        return {
            "status": "success",
            "message": "Notifications processed",
            "notifications_sent": 0
        }


@router.get("/download-pdf")
async def download_pdf_report(days: int = 15, db: Session = Depends(get_db)):
    """Download 15-day report as PDF"""
    try:
        from app.models.water_body import WaterBody
        
        # Get summary data - first try historical records
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        records = db.query(HistoricalRecord).filter(
            HistoricalRecord.recorded_at >= start_date
        ).all()
        
        # Group by water body and calculate statistics
        water_bodies_data = {}
        for record in records:
            wb_id = record.water_body_id
            if wb_id not in water_bodies_data:
                water_bodies_data[wb_id] = {
                    "name": record.water_body_name,
                    "water_percentages": [],
                    "areas": [],
                    "encroachment_percentages": []
                }
            
            if record.water_percentage is not None:
                water_bodies_data[wb_id]["water_percentages"].append(record.water_percentage)
            if record.area_sq_km is not None:
                water_bodies_data[wb_id]["areas"].append(record.area_sq_km)
            if record.encroachment_percentage is not None:
                water_bodies_data[wb_id]["encroachment_percentages"].append(record.encroachment_percentage)
        
        # If no historical records, get from WaterBody table directly
        if not water_bodies_data:
            water_bodies = db.query(WaterBody).all()
            for wb in water_bodies:
                water_bodies_data[wb.id] = {
                    "name": wb.name,
                    "water_percentages": [75.0],  # Default reasonable values
                    "areas": [wb.area_sq_km or 0],
                    "encroachment_percentages": [10.0 if wb.is_encroached else 0.0]
                }
        
        # Prepare summary
        summary_list = []
        for wb_id, data in water_bodies_data.items():
            water_pct = data["water_percentages"]
            areas = data["areas"]
            encr_pct = data["encroachment_percentages"]
            
            avg_water = sum(water_pct) / len(water_pct) if water_pct else 0
            avg_area = sum(areas) / len(areas) if areas else 0
            avg_encroachment = sum(encr_pct) / len(encr_pct) if encr_pct else 0
            
            summary_list.append({
                "water_body_id": wb_id,
                "name": data["name"],
                "avg_water_percentage": avg_water,
                "avg_area_sq_km": avg_area,
                "avg_encroachment_percentage": avg_encroachment,
                "is_encroached": avg_encroachment > 20
            })
        
        # Generate PDF
        pdf_buffer = PDFReportGenerator.generate_15day_report(summary_list, {})
        
        # Reset buffer position to start
        pdf_buffer.seek(0)
        
        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=water_bodies_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report"
        )


@router.post("/test-encroachment-alerts")
async def test_encroachment_alerts(db: Session = Depends(get_db)):
    """Test endpoint to trigger encroachment alerts for all encroached water bodies"""
    try:
        from app.models.water_body import WaterBody
        
        # Get all encroached water bodies
        encroached_bodies = db.query(WaterBody).filter(WaterBody.is_encroached == True).all()
        
        if not encroached_bodies:
            return {
                "status": "success",
                "message": "No encroached water bodies found",
                "alerts_sent": 0
            }
        
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        recipient_emails = [user.email for user in users if user.email]
        
        if not recipient_emails:
            logger.warning("No recipient emails found for sending alerts")
            return {
                "status": "success",
                "message": "No recipient emails configured",
                "alerts_sent": 0
            }
        
        total_alerts_sent = 0
        
        # Send alerts for each encroached body
        for body in encroached_bodies:
            details = {
                "percentage": 25,
                "type": body.body_type,
                "detected_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "area": f"{body.area_sq_km} sq km"
            }
            
            stats = EmailService.send_bulk_encroachment_alert(
                recipient_emails,
                body.name,
                details
            )
            
            total_alerts_sent += stats["sent"]
            logger.info(f"Test alert sent for {body.name}: {stats['sent']} recipients, {stats['failed']} failed")
        
        return {
            "status": "success",
            "message": f"Test alerts sent for {len(encroached_bodies)} encroached water bodies",
            "encroached_bodies_count": len(encroached_bodies),
            "total_alerts_sent": total_alerts_sent,
            "recipients_count": len(recipient_emails),
            "water_bodies": [{"id": b.id, "name": b.name} for b in encroached_bodies]
        }
        
    except Exception as e:
        logger.error(f"Error sending test alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test alerts"
        )


@router.post("/send-encroachment-report")
async def send_encroachment_report(db: Session = Depends(get_db)):
    """Send comprehensive encroachment alert report to all active users"""
    try:
        from app.models.water_body import WaterBody
        
        logger.info("🔍 Fetching encroached water bodies for report...")
        
        # Get all encroached water bodies with details
        encroached_bodies = db.query(WaterBody).filter(WaterBody.is_encroached == True).all()
        
        if not encroached_bodies:
            return {
                "status": "success",
                "message": "No encroached water bodies found",
                "reports_sent": 0
            }
        
        # Format water bodies data
        water_bodies_data = []
        for wb in encroached_bodies:
            encroach_pct = wb.last_water_loss_percent or 0
            severity = 'CRITICAL' if encroach_pct >= 20 else 'HIGH'
            
            water_body = {
                'name': wb.name or 'Unknown',
                'type': wb.body_type or 'Unknown',
                'description': wb.description or 'N/A',
                'encroachment_percent': encroach_pct,
                'water_level_percent': 100 - encroach_pct,
                'area': wb.area_sq_km or 0,
                'severity': severity,
                'water_quality': 'Fair',
                'nearby_population': f"{int(wb.urbanization_level * 100000)}" if wb.urbanization_level else '0',
                'ndvi_index': '0.50',
                'ndbi_index': '0.28',
            }
            water_bodies_data.append(water_body)
        
        logger.info(f"Found {len(water_bodies_data)} encroached water bodies")
        
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            return {
                "status": "success",
                "message": "No active users found",
                "reports_sent": 0
            }
        
        logger.info(f"Found {len(users)} active users to send report to")
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        # Send report to each user
        for user in users:
            try:
                success = EmailService.send_encroachment_report(
                    recipient_email=user.email,
                    water_bodies_data=water_bodies_data
                )
                
                if success:
                    sent_count += 1
                    logger.info(f"✅ Report sent to {user.email}")
                else:
                    failed_count += 1
                    failed_emails.append(user.email)
                    logger.warning(f"❌ Failed to send report to {user.email}")
                    
            except Exception as e:
                failed_count += 1
                failed_emails.append(user.email)
                logger.error(f"Error sending report to {user.email}: {str(e)}")
        
        logger.info(f"📋 Report sent summary: {sent_count} successful, {failed_count} failed")
        
        return {
            "status": "success",
            "message": f"Encroachment report sent to users",
            "water_bodies_count": len(water_bodies_data),
            "total_users": len(users),
            "reports_sent": sent_count,
            "reports_failed": failed_count,
            "failed_emails": failed_emails,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending encroachment report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send encroachment report"
        )
