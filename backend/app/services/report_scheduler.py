"""
Background task scheduler for automatic encroachment reports
Runs scheduled tasks to send reports automatically
"""
import asyncio
from datetime import datetime, time
import logging
from app.core.database import SessionLocal
from app.models.water_body import User, WaterBody
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Handles scheduled sending of encroachment reports"""
    
    def __init__(self):
        self.running = False
        self.task = None
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("📅 Encroachment report scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("📅 Encroachment report scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Check if it's time to send the report
                # Default: Send at 9:00 AM every day
                now = datetime.now()
                current_time = now.time()
                
                # Send report at 09:00 every day
                target_time = time(9, 0, 0)
                
                if current_time.hour == target_time.hour and current_time.minute == target_time.minute:
                    logger.info("⏰ Scheduled time reached - sending encroachment reports")
                    await self._send_reports()
                    # Wait 60 seconds to avoid duplicate sends
                    await asyncio.sleep(60)
                else:
                    # Check every 5 minutes
                    await asyncio.sleep(300)
                    
            except Exception as e:
                logger.error(f"Error in report scheduler: {str(e)}")
                await asyncio.sleep(300)
    
    @staticmethod
    async def _send_reports():
        """Send encroachment reports to all users"""
        db = SessionLocal()
        try:
            logger.info("🔍 Fetching encroached water bodies...")
            
            # Get encroached water bodies
            encroached_bodies = db.query(WaterBody).filter(WaterBody.is_encroached == True).all()
            
            if not encroached_bodies:
                logger.info("No encroached water bodies found")
                return
            
            # Format data
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
            
            # Get active users
            users = db.query(User).filter(User.is_active == True).all()
            
            if not users:
                logger.warning("No active users found")
                return
            
            logger.info(f"Sending report to {len(users)} users...")
            
            sent = 0
            failed = 0
            
            for user in users:
                try:
                    success = EmailService.send_encroachment_report(
                        recipient_email=user.email,
                        water_bodies_data=water_bodies_data
                    )
                    if success:
                        sent += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Error sending to {user.email}: {str(e)}")
                    failed += 1
            
            logger.info(f"📊 Report send completed: {sent} sent, {failed} failed")
            
        except Exception as e:
            logger.error(f"Error sending scheduled reports: {str(e)}")
        finally:
            db.close()


# Global scheduler instance
scheduler = ReportScheduler()
