"""
Script to send comprehensive encroachment alert report to all users
Usage: python send_encroachment_report.py
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.water_body import User, WaterBody
from app.services.email_service import EmailService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_encroached_water_bodies():
    """Fetch all encroached water bodies from database with details"""
    db = SessionLocal()
    try:
        # Query encroached water bodies
        encroached = db.query(WaterBody).filter(WaterBody.is_encroached == True).all()
        
        water_bodies_data = []
        for wb in encroached:
            # Determine severity based on encroachment percentage
            encroach_pct = wb.last_water_loss_percent or 0
            if encroach_pct >= 20:
                severity = 'CRITICAL'
            else:
                severity = 'HIGH'
            
            water_body = {
                'name': wb.name or 'Unknown',
                'type': wb.body_type or 'Unknown',
                'description': wb.description or 'N/A',
                'encroachment_percent': encroach_pct,
                'water_level_percent': 100 - encroach_pct,  # Approximation
                'area': wb.area_sq_km or 0,
                'severity': severity,
                'water_quality': 'Fair',  # Default, can be extended with actual data
                'nearby_population': f"{int(wb.urbanization_level * 100000)}" if wb.urbanization_level else '0',
                'ndvi_index': '0.50',  # Placeholder
                'ndbi_index': '0.28',  # Placeholder
            }
            water_bodies_data.append(water_body)
        
        return water_bodies_data
        
    finally:
        db.close()


def send_report_to_all_users():
    """Send encroachment report to all active users"""
    
    print("=" * 70)
    print("📧 ENCROACHMENT ALERT REPORT - BULK SEND")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get encroached water bodies
    print("🔍 Fetching encroached water bodies...")
    water_bodies = get_encroached_water_bodies()
    
    if not water_bodies:
        print("❌ No encroached water bodies found in the database!")
        return
    
    print(f"✅ Found {len(water_bodies)} encroached water body/bodies:")
    for idx, wb in enumerate(water_bodies, 1):
        print(f"   {idx}. {wb['name']} - {wb['encroachment_percent']:.1f}% encroached ({wb['severity']})")
    
    print()
    
    # Get all active users
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            print("❌ No active users found in the database!")
            return
        
        print(f"📊 Found {len(users)} active user(s):")
        for idx, user in enumerate(users, 1):
            print(f"   {idx}. {user.full_name or user.username:<30} | {user.email:<40}")
        
        print()
        print("=" * 70)
        
        # Ask for confirmation
        response = input(f"Send encroachment report to all {len(users)} user(s)? [y/N]: ").strip().lower()
        if response != 'y':
            print("❌ Cancelled.")
            return
        
        print()
        print("📨 Sending encroachment reports...")
        print("-" * 70)
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        # Send report to each user
        for idx, user in enumerate(users, 1):
            try:
                success = EmailService.send_encroachment_report(
                    recipient_email=user.email,
                    water_bodies_data=water_bodies
                )
                
                if success:
                    print(f"✅ [{idx}/{len(users)}] Report sent to: {user.email} ({user.full_name or user.username})")
                    sent_count += 1
                else:
                    print(f"❌ [{idx}/{len(users)}] Failed to send to: {user.email}")
                    failed_count += 1
                    failed_emails.append(user.email)
                    
            except Exception as e:
                print(f"❌ [{idx}/{len(users)}] Error sending to {user.email}: {str(e)}")
                failed_count += 1
                failed_emails.append(user.email)
        
        print("-" * 70)
        print()
        print("📋 SUMMARY:")
        print(f"   ✅ Successfully sent: {sent_count}/{len(users)}")
        print(f"   ❌ Failed: {failed_count}/{len(users)}")
        print(f"   📊 Water bodies in report: {len(water_bodies)}")
        
        if failed_emails:
            print()
            print("   Failed email addresses:")
            for email in failed_emails:
                print(f"      - {email}")
        
        print()
        print("=" * 70)
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
    finally:
        db.close()


if __name__ == "__main__":
    try:
        send_report_to_all_users()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
