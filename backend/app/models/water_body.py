"""Database models for SQLAlchemy ORM"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, LargeBinary
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # admin, officer, user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WaterBody(Base):
    """Water body model"""
    __tablename__ = "water_bodies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    body_type = Column(String)  # lake, pond, river, etc.
    description = Column(String)
    location = Column(String)  # Store coordinates as JSON string: {"type": "Point", "coordinates": [lng, lat]}
    area_sq_km = Column(Float)
    urbanization_level = Column(Float, default=0.0)  # 0-1 scale, urbanization around water body
    last_monitored = Column(DateTime(timezone=True))  # Last satellite monitoring timestamp
    alert_threshold = Column(Float, default=0.1)  # Alert threshold in sq km
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MonitoringRecord(Base):
    """Monitoring record model"""
    __tablename__ = "monitoring_records"
    
    id = Column(Integer, primary_key=True, index=True)
    water_body_id = Column(Integer)
    satellite_image = Column(String)  # URL or path to satellite image
    captured_at = Column(DateTime(timezone=True))
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    ndvi_value = Column(Float)  # Normalized Difference Vegetation Index
    water_area_sq_km = Column(Float)
    change_detected = Column(Boolean, default=False)
    metadata_info = Column(JSON)  # Additional metadata
    image_data = Column(LargeBinary)  # Satellite image binary


class Encroachment(Base):
    """Encroachment detection model"""
    __tablename__ = "encroachments"
    
    id = Column(Integer, primary_key=True, index=True)
    water_body_id = Column(Integer)
    monitoring_record_id = Column(Integer)
    location = Column(String)  # Store point as JSON string: {"type": "Point", "coordinates": [lng, lat]}
    area_sq_km = Column(Float)
    severity = Column(String)  # low, medium, high
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    status = Column(String, default="pending")  # pending, confirmed, resolved
    details = Column(JSON)


class Alert(Base):
    """Alert model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    water_body_id = Column(Integer)
    encroachment_id = Column(Integer)
    alert_type = Column(String)  # encroachment, pollution, etc.
    severity = Column(String)  # low, medium, high, critical
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    is_resolved = Column(Boolean, default=False)
    metadata_info = Column(JSON)
