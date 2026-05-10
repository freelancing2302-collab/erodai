# Watery - Water Bodies Monitoring System

Automated satellite imagery-based monitoring system for detecting changes and encroachments in water bodies.

## Project Overview

This project implements a comprehensive water body monitoring system that uses:
- **Satellite Imagery**: Google Earth Engine for continuous data collection
- **Machine Learning**: TensorFlow for change detection and encroachment identification
- **Real-time Analysis**: FastAPI backend with Celery for asynchronous processing
- **Mobile App**: Flutter frontend for cross-platform access
- **Database**: Supabase (PostgreSQL + PostGIS) for geospatial data

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with PostGIS extension (via Supabase)
- **Geospatial**: GDAL, Rasterio, Geopandas, Shapely
- **Image Processing**: OpenCV, scikit-image, PIL
- **ML/AI**: TensorFlow, PyTorch
- **Task Queue**: Celery + Redis
- **API Documentation**: Swagger/OpenAPI

### Frontend
- **Framework**: Flutter
- **State Management**: Riverpod
- **Maps**: Google Maps Flutter
- **Navigation**: GoRouter
- **Database**: Hive (local storage)
- **API Client**: Dio + Retrofit

### Data Sources
- **Satellite Imagery**: Google Earth Engine, Sentinel-2, Sentinel-1
- **Geospatial Data**: OpenStreetMap, Natural Earth

### Deployment
- **Backend**: Docker + Docker Compose
- **Database**: Supabase Cloud
- **Frontend**: Firebase Hosting / Google Play / App Store

## Project Structure

```
watery/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration, security, database
│   │   ├── api/           # API routes and endpoints
│   │   ├── models/        # SQLAlchemy database models
│   │   ├── schemas/       # Pydantic schemas for validation
│   │   ├── services/      # Business logic and integrations
│   │   └── main.py        # FastAPI application
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/
│   ├── lib/
│   │   ├── core/          # Core configuration and services
│   │   ├── features/      # Feature modules (auth, monitoring, etc.)
│   │   ├── shared/        # Shared models and widgets
│   │   └── main.dart
│   ├── pubspec.yaml
│   └── analysis_options.yaml
└── docs/
    └── README.md
```

## Getting Started

### Backend Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker**
   ```bash
   docker-compose up
   ```

4. **Database Migrations**
   ```bash
   alembic upgrade head
   ```

### Frontend Setup

1. **Install Flutter** (if not installed)
   ```bash
   flutter pub global activate fvm
   fvm install
   ```

2. **Get Dependencies**
   ```bash
   cd frontend
   flutter pub get
   ```

3. **Generate Code**
   ```bash
   flutter pub run build_runner build
   ```

4. **Run Application**
   ```bash
   flutter run
   ```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login

### Water Bodies
- `GET /api/v1/water-bodies` - Get all water bodies
- `POST /api/v1/water-bodies` - Create water body
- `GET /api/v1/water-bodies/{id}` - Get specific water body
- `PUT /api/v1/water-bodies/{id}` - Update water body
- `DELETE /api/v1/water-bodies/{id}` - Delete water body

### Monitoring
- `GET /api/v1/monitoring/records/{water_body_id}` - Get monitoring records
- `GET /api/v1/monitoring/encroachments/{water_body_id}` - Get encroachments
- `GET /api/v1/monitoring/alerts/{water_body_id}` - Get alerts
- `POST /api/v1/monitoring/trigger-analysis/{water_body_id}` - Start analysis

## Key Features

### 1. Satellite Data Integration
- Fetches Sentinel-2 and Sentinel-1 imagery from Google Earth Engine
- Multi-temporal analysis for change detection
- Cloud filtering and data quality checks

### 2. Water Body Monitoring
- Tracks water area changes using NDVI and NDWI indices
- Detects encroachments on protected water bodies
- Monitors pollution and vegetation changes

### 3. Change Detection
- Compares satellite images over time
- Identifies structural changes in water boundaries
- Calculates affected area and severity levels

### 4. Real-time Alerts
- Automatic notifications for detected encroachments
- Multi-level severity classification (low, medium, high)
- Configurable alert thresholds

### 5. Dashboard & Visualization
- Interactive maps with water body boundaries
- Historical trend analysis
- Alert management interface
- Performance metrics and statistics

## Database Schema

### Core Tables
- **users**: User accounts and roles
- **water_bodies**: Water body geographic data
- **monitoring_records**: Satellite imagery analysis results
- **encroachments**: Detected encroachment events
- **alerts**: System alerts and notifications

All geographic data uses PostGIS geometry types for spatial queries.

## Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/watery_db

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Google Earth Engine
GEE_PROJECT_ID=your-gee-project-id

# API Security
JWT_SECRET=your-jwt-secret
SECRET_KEY=your-secret-key

# Storage
AWS_S3_BUCKET=your-bucket
AWS_REGION=ap-south-1
```

## Development Workflow

### Backend Development
```bash
# Start development server
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black app/

# Lint
flake8 app/
```

### Frontend Development
```bash
# Run in debug mode
flutter run

# Run tests
flutter test

# Build release
flutter build apk  # Android
flutter build ios  # iOS
```

## Deployment

### Backend Deployment
- Uses Docker for containerization
- PostgreSQL database on Supabase
- Can be deployed to AWS, GCP, or Azure
- Environment-specific configurations

### Frontend Deployment
- Web: Firebase Hosting
- Mobile: Google Play Store (Android), App Store (iOS)
- Desktop: GitHub Releases

## Testing

### Backend Tests
```bash
pytest tests/
```

### Frontend Tests
```bash
flutter test
```

## Future Enhancements

1. **Advanced ML Models**
   - Real-time video stream processing
   - Semantic segmentation for encroachment types
   - Object detection for specific pollutants

2. **Mobile Features**
   - Offline map viewing
   - Geofencing for alerts
   - Photo-based reporting

3. **Integration**
   - Government agency APIs
   - Weather data integration
   - Water quality sensors

4. **Scalability**
   - Distributed processing
   - Multi-region deployment
   - Advanced caching strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Acknowledgments

- Google Earth Engine for satellite data
- Supabase for database infrastructure
- Flutter and FastAPI communities for excellent documentation
