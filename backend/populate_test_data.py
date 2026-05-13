"""Script to populate test data for water bodies monitoring"""
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.water_body import WaterBody, HistoricalRecord, User, MonitoringRecord
import json

# Create all tables
Base.metadata.create_all(bind=engine)

# Test data for 30 water bodies in Erode District, Tamil Nadu
TEST_WATER_BODIES = [
    {
        "name": "Bhavani River",
        "body_type": "River",
        "description": "Major river flowing through Erode",
        "location": json.dumps({"type": "Point", "coordinates": [77.7542, 11.3392]}),
        "area_sq_km": 2.5,
        "urbanization_level": 0.5,
        "is_encroached": False,
    },
    {
        "name": "Noyyal River",
        "body_type": "River",
        "description": "Tributary of Bhavani River",
        "location": json.dumps({"type": "Point", "coordinates": [77.5625, 11.2875]}),
        "area_sq_km": 1.8,
        "urbanization_level": 0.45,
        "is_encroached": False,
    },
    {
        "name": "Pongalur Lake",
        "body_type": "Lake",
        "description": "Small reservoir in Pongalur",
        "location": json.dumps({"type": "Point", "coordinates": [77.8234, 11.4567]}),
        "area_sq_km": 0.8,
        "urbanization_level": 0.35,
        "is_encroached": False,
    },
    {
        "name": "Siddhapudur Lake",
        "body_type": "Lake",
        "description": "Historic water body in Siddhapudur",
        "location": json.dumps({"type": "Point", "coordinates": [77.6875, 11.3125]}),
        "area_sq_km": 1.2,
        "urbanization_level": 0.40,
        "is_encroached": False,
    },
    {
        "name": "Periyar Reservoir",
        "body_type": "Reservoir",
        "description": "Artificial reservoir for irrigation",
        "location": json.dumps({"type": "Point", "coordinates": [77.4567, 11.1234]}),
        "area_sq_km": 3.5,
        "urbanization_level": 0.55,
        "is_encroached": True,
    },
    {
        "name": "Kalingarayan Canal",
        "body_type": "Canal",
        "description": "Irrigation canal system",
        "location": json.dumps({"type": "Point", "coordinates": [77.6234, 11.2567]}),
        "area_sq_km": 0.6,
        "urbanization_level": 0.25,
        "is_encroached": False,
    },
    {
        "name": "Valparai Dam",
        "body_type": "Reservoir",
        "description": "Dam reservoir in Valparai",
        "location": json.dumps({"type": "Point", "coordinates": [77.3456, 11.5432]}),
        "area_sq_km": 2.0,
        "urbanization_level": 0.30,
        "is_encroached": False,
    },
    {
        "name": "Thadapalli Lake",
        "body_type": "Lake",
        "description": "Small seasonal water body - UNDER ENCROACHMENT",
        "location": json.dumps({"type": "Point", "coordinates": [77.8765, 11.0987]}),
        "area_sq_km": 0.5,
        "urbanization_level": 0.65,
        "is_encroached": True,
    },
    {
        "name": "Kumbakarai Falls",
        "body_type": "Waterfall",
        "description": "Seasonal waterfall in Western Ghats",
        "location": json.dumps({"type": "Point", "coordinates": [77.2345, 11.6789]}),
        "area_sq_km": 0.3,
        "urbanization_level": 0.15,
        "is_encroached": False,
    },
    {
        "name": "Mettupalayam Tank",
        "body_type": "Tank",
        "description": "Agricultural storage tank",
        "location": json.dumps({"type": "Point", "coordinates": [77.5678, 11.4123]}),
        "area_sq_km": 0.4,
        "urbanization_level": 0.28,
        "is_encroached": False,
    },
    {
        "name": "Anthiyur Dam",
        "body_type": "Reservoir",
        "description": "Historic dam providing water supply",
        "location": json.dumps({"type": "Point", "coordinates": [77.8567, 11.2134]}),
        "area_sq_km": 1.5,
        "urbanization_level": 0.48,
        "is_encroached": False,
    },
    {
        "name": "Solanatharupathi Lake",
        "body_type": "Lake",
        "description": "Village lake with agricultural importance",
        "location": json.dumps({"type": "Point", "coordinates": [77.7234, 11.1567]}),
        "area_sq_km": 0.7,
        "urbanization_level": 0.52,
        "is_encroached": True,
    },
    {
        "name": "Kodiveri Falls",
        "body_type": "Waterfall",
        "description": "Scenic waterfall in Nilgiris",
        "location": json.dumps({"type": "Point", "coordinates": [77.2156, 11.5234]}),
        "area_sq_km": 0.2,
        "urbanization_level": 0.12,
        "is_encroached": False,
    },
    {
        "name": "Thekkampatti Lake",
        "body_type": "Lake",
        "description": "Community water body",
        "location": json.dumps({"type": "Point", "coordinates": [77.4234, 11.3567]}),
        "area_sq_km": 0.9,
        "urbanization_level": 0.50,
        "is_encroached": True,
    },
    {
        "name": "Uppundi Lake",
        "body_type": "Lake",
        "description": "Private water body",
        "location": json.dumps({"type": "Point", "coordinates": [77.3456, 11.2890]}),
        "area_sq_km": 0.6,
        "urbanization_level": 0.35,
        "is_encroached": False,
    },
    {
        "name": "Chinnar River",
        "body_type": "River",
        "description": "Tributary in western region",
        "location": json.dumps({"type": "Point", "coordinates": [77.1234, 11.5890]}),
        "area_sq_km": 1.3,
        "urbanization_level": 0.28,
        "is_encroached": False,
    },
    {
        "name": "Varathanaryar River",
        "body_type": "River",
        "description": "Seasonal river",
        "location": json.dumps({"type": "Point", "coordinates": [77.6890, 11.1234]}),
        "area_sq_km": 0.9,
        "urbanization_level": 0.32,
        "is_encroached": False,
    },
    {
        "name": "Amaravati Lake",
        "body_type": "Lake",
        "description": "Religious and recreational importance",
        "location": json.dumps({"type": "Point", "coordinates": [77.2890, 11.4234]}),
        "area_sq_km": 1.1,
        "urbanization_level": 0.42,
        "is_encroached": False,
    },
    {
        "name": "Karikal Canal",
        "body_type": "Canal",
        "description": "Main irrigation artery",
        "location": json.dumps({"type": "Point", "coordinates": [77.7890, 11.3456]}),
        "area_sq_km": 0.5,
        "urbanization_level": 0.58,
        "is_encroached": True,
    },
    {
        "name": "Gomukhi Tank",
        "body_type": "Tank",
        "description": "Historical tank system",
        "location": json.dumps({"type": "Point", "coordinates": [77.4567, 11.2567]}),
        "area_sq_km": 0.35,
        "urbanization_level": 0.35,
        "is_encroached": False,
    },
    {
        "name": "Puliyancholai Waterfall",
        "body_type": "Waterfall",
        "description": "Lesser-known seasonal cascade",
        "location": json.dumps({"type": "Point", "coordinates": [77.1567, 11.6234]}),
        "area_sq_km": 0.15,
        "urbanization_level": 0.10,
        "is_encroached": False,
    },
    {
        "name": "Sathiyar Thoppu",
        "body_type": "Lake",
        "description": "Habitat conservation area",
        "location": json.dumps({"type": "Point", "coordinates": [77.5234, 11.0645]}),
        "area_sq_km": 0.55,
        "urbanization_level": 0.18,
        "is_encroached": False,
    },
    {
        "name": "Moolanatham Lake",
        "body_type": "Lake",
        "description": "Cultural heritage water body",
        "location": json.dumps({"type": "Point", "coordinates": [77.8234, 11.3789]}),
        "area_sq_km": 0.8,
        "urbanization_level": 0.62,
        "is_encroached": True,
    },
    {
        "name": "Kethanur Anicut",
        "body_type": "Reservoir",
        "description": "Irrigation barrage",
        "location": json.dumps({"type": "Point", "coordinates": [77.5789, 11.2456]}),
        "area_sq_km": 0.7,
        "urbanization_level": 0.38,
        "is_encroached": False,
    },
    {
        "name": "Kottaimalai Pond",
        "body_type": "Tank",
        "description": "Seasonal water storage",
        "location": json.dumps({"type": "Point", "coordinates": [77.2567, 11.1890]}),
        "area_sq_km": 0.3,
        "urbanization_level": 0.25,
        "is_encroached": False,
    },
    {
        "name": "Suranam Lake",
        "body_type": "Lake",
        "description": "Community recreational area",
        "location": json.dumps({"type": "Point", "coordinates": [77.6234, 11.4890]}),
        "area_sq_km": 1.0,
        "urbanization_level": 0.45,
        "is_encroached": False,
    },
    {
        "name": "Bhavani Sagar Lake",
        "body_type": "Reservoir",
        "description": "Major water supply reservoir",
        "location": json.dumps({"type": "Point", "coordinates": [77.7056, 11.5012]}),
        "area_sq_km": 2.8,
        "urbanization_level": 0.68,
        "is_encroached": False,
    },
    {
        "name": "Tirumurthy Dam",
        "body_type": "Reservoir",
        "description": "Hydroelectric project",
        "location": json.dumps({"type": "Point", "coordinates": [77.3234, 11.0567]}),
        "area_sq_km": 1.6,
        "urbanization_level": 0.32,
        "is_encroached": False,
    },
    {
        "name": "Orathupalayam Lake",
        "body_type": "Lake",
        "description": "Urban water body",
        "location": json.dumps({"type": "Point", "coordinates": [77.6123, 11.2345]}),
        "area_sq_km": 0.65,
        "urbanization_level": 0.72,
        "is_encroached": True,
    },
    {
        "name": "Ammapalayam Weir",
        "body_type": "Canal",
        "description": "Water regulation structure",
        "location": json.dumps({"type": "Point", "coordinates": [77.5456, 11.3123]}),
        "area_sq_km": 0.4,
        "urbanization_level": 0.30,
        "is_encroached": False,
    },
]


def populate_water_bodies(db: Session):
    """Populate water bodies table with seasonal data"""
    print("📊 Populating water bodies...")
    
    # Clear existing water bodies (optional - for fresh data)
    print("  🗑️  Clearing existing water bodies...")
    db.query(WaterBody).delete()
    db.commit()
    
    # Mark seasonal water bodies
    SEASONAL_BODIES = {
        "Kumbakarai Falls",
        "Thadapalli Lake",
        "Varathanaryar River",
        "Puliyancholai Waterfall",
        "Kottaimalai Pond",
    }
    
    # Expected baseline areas for seasonal bodies (sq km)
    SEASONAL_BASELINES = {
        "Kumbakarai Falls": {"monsoon": 0.3, "summer": 0.05, "post_monsoon": 0.15},
        "Thadapalli Lake": {"monsoon": 0.5, "summer": 0.15, "post_monsoon": 0.3},
        "Varathanaryar River": {"monsoon": 0.9, "summer": 0.2, "post_monsoon": 0.5},
        "Puliyancholai Waterfall": {"monsoon": 0.15, "summer": 0.02, "post_monsoon": 0.08},
        "Kottaimalai Pond": {"monsoon": 0.3, "summer": 0.1, "post_monsoon": 0.2},
    }
    
    for wb_data in TEST_WATER_BODIES:
        water_body = WaterBody(**wb_data)
        water_body.created_at = datetime.utcnow()
        water_body.updated_at = datetime.utcnow()
        
        # Set seasonal flags
        is_seasonal = wb_data["name"] in SEASONAL_BODIES
        water_body.is_seasonal = is_seasonal
        
        # Set baseline areas for seasonal bodies
        if is_seasonal and wb_data["name"] in SEASONAL_BASELINES:
            baselines = SEASONAL_BASELINES[wb_data["name"]]
            water_body.baseline_monsoon_area = baselines.get("monsoon", 0)
            water_body.baseline_summer_area = baselines.get("summer", 0)
            water_body.baseline_post_monsoon_area = baselines.get("post_monsoon", 0)
        else:
            # For non-seasonal bodies, set all baselines to current area
            water_body.baseline_monsoon_area = wb_data["area_sq_km"] * 0.95
            water_body.baseline_summer_area = wb_data["area_sq_km"] * 0.85
            water_body.baseline_post_monsoon_area = wb_data["area_sq_km"] * 0.90
        
        if water_body.is_encroached:
            water_body.encroached_at = datetime.utcnow() - timedelta(days=5)
        
        db.add(water_body)
        seasonal_marker = " (SEASONAL)" if is_seasonal else ""
        print(f"  ✓ Added {wb_data['name']}{seasonal_marker}")
    
    db.commit()
    print(f"✅ Water bodies populated successfully ({len(TEST_WATER_BODIES)} total)\n")


def populate_historical_records(db: Session):
    """Populate historical records for the past 15 days"""
    print("📈 Populating historical records (last 15 days)...")
    
    water_bodies = db.query(WaterBody).all()
    
    if not water_bodies:
        print("  ⚠️  No water bodies found. Create water bodies first.")
        return
    
    # Clear existing records
    print("  🗑️  Clearing existing historical records...")
    db.query(HistoricalRecord).delete()
    db.commit()
    
    # Generate 15 days of data
    for day in range(15):
        date = datetime.utcnow() - timedelta(days=day)
        
        for wb in water_bodies:
            # Simulate realistic water percentage (60-90%)
            base_water = 75.0 if not wb.is_encroached else 65.0
            variance = (day % 3) * 5  # Add some variance
            water_percentage = base_water + variance - (3 if wb.is_encroached else 0)
            water_percentage = max(40, min(95, water_percentage))
            
            # Calculate actual water area
            area = wb.area_sq_km
            
            # Encroachment percentage (higher for encroached bodies)
            if wb.is_encroached:
                encroachment_pct = 25 + (day % 5) * 2
            else:
                encroachment_pct = max(0, 5 - (day % 3))
            
            record = HistoricalRecord(
                water_body_id=wb.id,
                water_body_name=wb.name,
                water_percentage=water_percentage,
                area_sq_km=area,
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
    total_records = db.query(HistoricalRecord).count()
    print(f"✅ Generated {total_records} historical records\n")


def create_test_user(db: Session):
    """Create a test user for alerts"""
    print("👤 Creating test user...")
    
    existing = db.query(User).filter(User.email == "testuser@watery.app").first()
    if existing:
        print("  ✓ Test user already exists")
        return
    
    user = User(
        email="testuser@watery.app",
        username="testuser",
        full_name="Test User",
        hashed_password="$2b$12$hash",  # Mock hash
        is_active=True,
        role="admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(user)
    db.commit()
    print("  ✓ Test user created")
    print("✅ Test user created successfully\n")


def main():
    """Main function to populate all test data"""
    print("\n" + "="*60)
    print("🌊 WATERY - Test Data Population Script")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        create_test_user(db)
        populate_water_bodies(db)
        populate_historical_records(db)
        
        # Verify data
        total_bodies = db.query(WaterBody).count()
        total_records = db.query(HistoricalRecord).count()
        
        print("📊 Summary:")
        print(f"  • Water Bodies: {total_bodies}")
        print(f"  • Historical Records: {total_records}")
        
        print("\n" + "="*60)
        print("✅ All test data populated successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
