"""
Script to send emails to all users in the database
Usage: python send_emails_to_all_users.py
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.water_body import User
from app.services.email_service import EmailService
from app.core.config import settings


def send_test_email_to_all_users():
    """Send a test email to all active users in the database"""
    
    print("=" * 70)
    print("📧 WATERY - BULK EMAIL TO ALL USERS")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check SMTP configuration
    print("🔍 Checking SMTP Configuration...")
    if not settings.smtp_user or not settings.smtp_pass:
        print("⚠️  WARNING: SMTP credentials not fully configured!")
        print(f"   SMTP Host: {settings.smtp_host}")
        print(f"   SMTP Port: {settings.smtp_port}")
        print(f"   SMTP User: {settings.smtp_user}")
        print()
        response = input("Continue anyway? (emails will be logged to console) [y/N]: ").strip().lower()
        if response != 'y':
            print("❌ Cancelled.")
            return
    else:
        print(f"✅ SMTP Configured:")
        print(f"   Host: {settings.smtp_host}:{settings.smtp_port}")
        print(f"   User: {settings.smtp_user}")
        print(f"   From: {settings.smtp_from_name}")
    print()
    
    # Connect to database
    db = SessionLocal()
    try:
        # Get all active users
        print("📊 Fetching users from database...")
        users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            print("❌ No active users found in the database!")
            return
        
        print(f"✅ Found {len(users)} active user(s):")
        print()
        
        # Display users
        for idx, user in enumerate(users, 1):
            print(f"   {idx}. {user.full_name or user.username:<30} | {user.email:<40} | Role: {user.role}")
        
        print()
        print("=" * 70)
        
        # Ask for confirmation
        response = input(f"Send test email to all {len(users)} user(s)? [y/N]: ").strip().lower()
        if response != 'y':
            print("❌ Cancelled.")
            return
        
        print()
        print("📨 Sending emails...")
        print("-" * 70)
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        # Send email to each user
        for idx, user in enumerate(users, 1):
            try:
                # Create test message
                encroachment_details = {
                    "percentage": "15%",
                    "type": "Test Alert",
                    "detected_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "location": "Test Water Body"
                }
                
                success = EmailService.send_encroachment_alert(
                    recipient_email=user.email,
                    water_body_name="Test Water Body (Monitoring Alert)",
                    encroachment_details=encroachment_details
                )
                
                if success:
                    print(f"✅ [{idx}/{len(users)}] Email sent to: {user.email} ({user.full_name or user.username})")
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
        
        if failed_emails:
            print()
            print("   Failed email addresses:")
            for email in failed_emails:
                print(f"      - {email}")
        
        print()
        print("=" * 70)
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    try:
        send_test_email_to_all_users()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
