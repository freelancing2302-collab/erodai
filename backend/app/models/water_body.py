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
    is_seasonal = Column(Boolean, default=False)  # Whether water body is seasonal (dries up)
    baseline_summer_area = Column(Float, default=0.0)  # Expected water area in summer (sq km)
    baseline_monsoon_area = Column(Float, default=0.0)  # Expected water area in monsoon (sq km)
    baseline_post_monsoon_area = Column(Float, default=0.0)  # Expected water area in post-monsoon (sq km)
    last_monitoring_season = Column(String, default="unknown")  # Last monitoring season: summer, monsoon, post-monsoon, dry-season
    last_water_loss_percent = Column(Float, default=0.0)  # Last recorded water loss percentage
    is_encroached = Column(Boolean, default=False)  # Encroachment status - set to True by default
    encroached_at = Column(DateTime(timezone=True))  # When encroachment was detected/set
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


class HistoricalRecord(Base):
    """Historical record model for 15-day tracking"""
    __tablename__ = "historical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    water_body_id = Column(Integer, index=True)
    water_body_name = Column(String)
    water_percentage = Column(Float)  # Percentage of water detected
    area_sq_km = Column(Float)  # Area of water detected
    encroachment_percentage = Column(Float, default=0.0)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    water_quality = Column(String)
    metadata_info = Column(JSON)  # Additional monitoring data
