"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api import auth, water_bodies, monitoring, reports
from app.api.monitoring_realtime import router as monitoring_realtime_router
from app.api import map as map_api
from app.api import gee_analysis
from app.models.water_body import WaterBody, HistoricalRecord, User
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Automated Water Bodies Monitoring System using Satellite Imagery",
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(water_bodies.router, prefix=settings.api_prefix)
app.include_router(monitoring.router, prefix=settings.api_prefix)
app.include_router(monitoring_realtime_router, prefix=settings.api_prefix)
app.include_router(gee_analysis.router, prefix=settings.api_prefix)
app.include_router(reports.router)
app.include_router(map_api.router)


def initialize_test_data():
    """Initialize test data if database is empty"""
    try:
        db = SessionLocal()
        
        # Check if water bodies already exist
        existing_bodies = db.query(WaterBody).count()
        if existing_bodies > 0:
            logger.info(f"Database already initialized with {existing_bodies} water bodies")
            db.close()
            return
        
        logger.info("Initializing test data...")
        
        # Test water bodies
        TEST_WATER_BODIES = [
            {
                "name": "Pichola Lake",
                "body_type": "Lake",
                "description": "Historic lake in Udaipur, Rajasthan",
                "location": json.dumps({"type": "Point", "coordinates": [73.8231, 24.5854]}),
                "area_sq_km": 2.5,
                "urbanization_level": 0.7,
                "is_encroached": True,
            },
            {
                "name": "Loktak Lake",
                "body_type": "Lake",
                "description": "Largest freshwater lake in Northeast India",
                "location": json.dumps({"type": "Point", "coordinates": [94.7611, 24.7153]}),
                "area_sq_km": 236.2,
                "urbanization_level": 0.4,
                "is_encroached": False,
            },
            {
                "name": "Chilika Lake",
                "body_type": "Lagoon",
                "description": "Largest coastal lagoon in India",
                "location": json.dumps({"type": "Point", "coordinates": [85.3738, 19.6667]}),
                "area_sq_km": 1165.0,
                "urbanization_level": 0.3,
                "is_encroached": True,
            },
            {
                "name": "Dal Lake",
                "body_type": "Lake",
                "description": "Central lake in Srinagar, Kashmir",
                "location": json.dumps({"type": "Point", "coordinates": [75.5769, 34.1526]}),
                "area_sq_km": 18.0,
                "urbanization_level": 0.8,
                "is_encroached": True,
            },
            {
                "name": "Wular Lake",
                "body_type": "Lake",
                "description": "Largest freshwater lake in India",
                "location": json.dumps({"type": "Point", "coordinates": [75.3333, 34.5833]}),
                "area_sq_km": 212.5,
                "urbanization_level": 0.35,
                "is_encroached": False,
            },
            {
                "name": "Vembanad Lake",
                "body_type": "Lagoon",
                "description": "Longest lake in India",
                "location": json.dumps({"type": "Point", "coordinates": [76.5, 9.5]}),
                "area_sq_km": 2033.0,
                "urbanization_level": 0.5,
                "is_encroached": False,
            },
            {
                "name": "Koleru Lake",
                "body_type": "Lake",
                "description": "Second largest brackish water lake in India",
                "location": json.dumps({"type": "Point", "coordinates": [82.0333, 16.7667]}),
                "area_sq_km": 308.0,
                "urbanization_level": 0.45,
                "is_encroached": True,
            },
            {
                "name": "Tsomgo Lake",
                "body_type": "Alpine Lake",
                "description": "High altitude glacial lake in Sikkim",
                "location": json.dumps({"type": "Point", "coordinates": [88.3, 27.9833]}),
                "area_sq_km": 1.09,
                "urbanization_level": 0.2,
                "is_encroached": False,
            },
            {
                "name": "Sukhna Lake",
                "body_type": "Manmade Lake",
                "description": "Reservoir in Chandigarh",
                "location": json.dumps({"type": "Point", "coordinates": [76.8167, 30.75]}),
                "area_sq_km": 25.0,
                "urbanization_level": 0.6,
                "is_encroached": True,
            },
            {
                "name": "Sarvsar Lake",
                "body_type": "Lake",
                "description": "Lake in Nashik, Maharashtra",
                "location": json.dumps({"type": "Point", "coordinates": [73.8, 19.8]}),
                "area_sq_km": 5.0,
                "urbanization_level": 0.55,
                "is_encroached": False,
            },
        ]
        
        # Add water bodies
        for wb_data in TEST_WATER_BODIES:
            water_body = WaterBody(**wb_data)
            water_body.created_at = datetime.utcnow()
            water_body.updated_at = datetime.utcnow()
            if water_body.is_encroached:
                water_body.encroached_at = datetime.utcnow() - timedelta(days=5)
            db.add(water_body)
        
        db.commit()
        
        # Add historical records
        water_bodies = db.query(WaterBody).all()
        for day in range(15):
            date = datetime.utcnow() - timedelta(days=day)
            
            for wb in water_bodies:
                base_water = 75.0 if not wb.is_encroached else 65.0
                variance = (day % 3) * 5
                water_percentage = base_water + variance - (3 if wb.is_encroached else 0)
                water_percentage = max(40, min(95, water_percentage))
                
                if wb.is_encroached:
                    encroachment_pct = 25 + (day % 5) * 2
                else:
                    encroachment_pct = max(0, 5 - (day % 3))
                
                record = HistoricalRecord(
                    water_body_id=wb.id,
                    water_body_name=wb.name,
                    water_percentage=water_percentage,
                    area_sq_km=wb.area_sq_km,
                    water_quality="Good" if water_percentage > 70 else "Fair",
                    encroachment_percentage=encroachment_pct,
                    recorded_at=date,
                    metadata_info={
                        "urbanization_level": wb.urbanization_level,
                        "ndvi_value": 0.5 + (water_percentage / 100) * 0.3,
                    }
                )
                db.add(record)
        
        db.commit()
        
        # Create test user for alerts
        existing_user = db.query(User).filter(User.email == "testuser@watery.app").first()
        if not existing_user:
            user = User(
                email="testuser@watery.app",
                username="testuser",
                full_name="Test User",
                hashed_password="$2b$12$hash",
                is_active=True,
                role="admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
        
        logger.info(f"✅ Test data initialized: {len(TEST_WATER_BODIES)} water bodies, 15 days of historical data")
        db.close()
        
    except Exception as e:
        logger.error(f"Error initializing test data: {str(e)}")
        db.close()


@app.on_event("startup")
async def startup_event():
    """Initialize test data and scheduler on startup"""
    initialize_test_data()
    
    # Initialize and start the report scheduler
    try:
        from app.services.report_scheduler import scheduler
        await scheduler.start()
        logger.info("✅ Report scheduler initialized and started")
    except Exception as e:
        logger.error(f"Failed to start report scheduler: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        from app.services.report_scheduler import scheduler
        await scheduler.stop()
        logger.info("✅ Report scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Water Bodies Monitoring API",
        "version": settings.api_version,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "environment": settings.env},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
