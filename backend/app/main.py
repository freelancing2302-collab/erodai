"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, water_bodies, monitoring
from app.api.monitoring_realtime import router as monitoring_realtime_router
from app.api import map as map_api
from app.api import gee_analysis

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
app.include_router(map_api.router)


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
