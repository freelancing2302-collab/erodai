"""Application configuration settings"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "sqlite:///./watery.db"
    
    # Supabase (optional for local dev)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # API Configuration
    env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    api_title: str = "Water Bodies Monitoring API"
    api_version: str = "1.0.0"
    
    # Security (with defaults for local dev)
    secret_key: str = "local-dev-secret-key-change-in-production"
    jwt_secret: str = "local-dev-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Google Earth Engine
    gee_project_id: Optional[str] = None
    gee_service_account_json: Optional[str] = None
    gee_enabled: bool = False
    gee_use_ndvi: bool = True
    gee_use_ndbi: bool = True
    
    # OpenStreetMap
    osm_enabled: bool = True
    osm_tile_server: str = "https://tile.openstreetmap.org"
    
    # AWS (for image storage)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ap-south-1"
    aws_s3_bucket: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # SMTP Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    smtp_from_name: str = "Watery Monitoring System"
    
    # Processing
    monitoring_interval_hours: int = 24  # How often to fetch new satellite data
    notification_enabled: bool = True
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
