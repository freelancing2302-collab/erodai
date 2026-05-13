#!/usr/bin/env python3
"""
Database migration script to update schema with new columns
"""
from app.core.database import engine, Base
from app.models import water_body

# Create or update all tables
Base.metadata.create_all(bind=engine)
print("Database tables created/updated successfully!")
