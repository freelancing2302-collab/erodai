"""Pydantic schemas for API request/response validation"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: str
    role: str = "user"


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class WaterBodyBase(BaseModel):
    """Base water body schema"""
    name: str
    body_type: Optional[str] = "lake"
    description: Optional[str] = None
    area_sq_km: float


class WaterBodyCreate(WaterBodyBase):
    """Water body creation schema"""
    pass


class WaterBodyResponse(WaterBodyBase):
    """Water body response schema"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MonitoringRecordResponse(BaseModel):
    """Monitoring record response schema"""
    id: int
    water_body_id: int
    satellite_image: str
    captured_at: datetime
    processed_at: datetime
    ndvi_value: Optional[float] = None
    water_area_sq_km: Optional[float] = None
    change_detected: bool
    
    class Config:
        from_attributes = True


class EncroachmentResponse(BaseModel):
    """Encroachment response schema"""
    id: int
    water_body_id: int
    area_sq_km: float
    severity: str
    detected_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Alert response schema"""
    id: int
    water_body_id: int
    alert_type: str
    severity: str
    message: str
    created_at: datetime
    is_resolved: bool
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    environment: str
