"""Authentication routes"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.water_body import UserCreate, UserResponse, LoginRequest
from app.models.water_body import User
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send welcome email
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from app.core.config import settings
        
        subject = "Welcome to Watery Water Bodies Monitoring System"
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="background-color: #f0f4f8; padding: 20px; border-radius: 8px;">
                    <div style="background-color: white; padding: 20px; border-radius: 8px;">
                        <h1 style="color: #0284C7;">Welcome to Watery! 🌊</h1>
                        
                        <p>Hello <strong>{db_user.full_name or db_user.username}</strong>,</p>
                        
                        <p>Thank you for registering with <strong>Watery Water Bodies Monitoring System</strong>.</p>
                        
                        <div style="background-color: #EFF6FF; padding: 15px; border-left: 4px solid #0284C7; margin: 15px 0; border-radius: 4px;">
                            <h3 style="margin-top: 0; color: #0284C7;">Your Account Details:</h3>
                            <ul style="margin: 10px 0;">
                                <li><strong>Username:</strong> {db_user.username}</li>
                                <li><strong>Email:</strong> {db_user.email}</li>
                                <li><strong>Role:</strong> {db_user.role}</li>
                                <li><strong>Registration Date:</strong> {db_user.created_at.strftime('%Y-%m-%d %H:%M:%S') if db_user.created_at else 'Today'}</li>
                            </ul>
                        </div>
                        
                        <h3 style="color: #0284C7;">What's Next?</h3>
                        <p>You will now receive real-time notifications about:</p>
                        <ul>
                            <li>🚨 <strong>Encroachment Alerts</strong> - When water bodies are detected as encroached</li>
                            <li>💧 <strong>Water Level Changes</strong> - Critical changes in monitored water bodies</li>
                            <li>📊 <strong>Monitoring Reports</strong> - Regular water body status updates</li>
                            <li>🌱 <strong>Seasonal Variations</strong> - Important seasonal water patterns</li>
                        </ul>
                        
                        <div style="background-color: #F0FDF4; padding: 15px; border-left: 4px solid #22C55E; margin: 15px 0; border-radius: 4px;">
                            <h3 style="margin-top: 0; color: #16A34A;">Key Features:</h3>
                            <ul style="margin: 10px 0;">
                                <li>✅ Monitor 30+ water bodies in Erode District</li>
                                <li>✅ Satellite-based water area analysis</li>
                                <li>✅ Seasonal-aware encroachment detection</li>
                                <li>✅ Real-time email alerts (just like this one!)</li>
                                <li>✅ Interactive map visualization</li>
                            </ul>
                        </div>
                        
                        <p style="margin-top: 25px;">Questions? Our monitoring system is here to help protect water bodies! 🌍</p>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #666; font-size: 12px; margin-bottom: 5px;">
                                <strong>Watery Monitoring System</strong> © 2026
                            </p>
                            <p style="color: #666; font-size: 12px;">
                                Protecting water bodies through technology
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        if settings.smtp_user and settings.smtp_pass:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
            msg["To"] = db_user.email
            
            text_body = f"Welcome to Watery! You have successfully registered with username: {db_user.username}"
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_pass)
                server.send_message(msg)
            
            logger.info(f"✉️  Welcome email sent to {db_user.email}")
        else:
            logger.info(f"📧 Email service not configured - would send welcome email to {db_user.email}")
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email: {str(e)}")
        # Don't fail the registration if email fails
    
    return db_user


@router.post("/login")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user),
    }
