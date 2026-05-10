# Architecture Documentation

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  Flutter App (iOS, Android, Web, Desktop)                  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST/WebSocket
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    Backend API Layer                        │
│  FastAPI Server (Python)                                   │
│  ├─ Authentication Routes                                   │
│  ├─ Water Bodies Management                                 │
│  ├─ Monitoring & Analysis                                   │
│  └─ Alerts & Notifications                                  │
└────────────────┬──────────────────────────┬─────────────────┘
                 │                          │
                 │                          │
┌────────────────▼────────────┐  ┌──────────▼──────────────────┐
│  Data Processing Layer      │  │  External Services Layer    │
│  ├─ Image Processing        │  │  ├─ Google Earth Engine     │
│  ├─ Change Detection        │  │  ├─ Supabase Auth          │
│  ├─ ML Models               │  │  ├─ Email Notifications    │
│  └─ Geospatial Analysis     │  │  └─ Cloud Storage (AWS S3) │
└────────────────┬────────────┘  └──────────────────────────────┘
                 │
                 │
┌────────────────▼───────────────────────────────────────────┐
│           Data Storage Layer                               │
│  ├─ PostgreSQL + PostGIS (Supabase)                        │
│  │  ├─ Users & Authentication                              │
│  │  ├─ Water Bodies & Geometry                             │
│  │  ├─ Monitoring Records                                  │
│  │  ├─ Encroachments & Alerts                              │
│  │  └─ Analysis Results                                    │
│  │                                                          │
│  ├─ Redis Cache                                            │
│  │  ├─ Session Management                                  │
│  │  ├─ Real-time Alerts Queue                              │
│  │  └─ Task Queue (Celery)                                 │
│  │                                                          │
│  └─ S3/Cloud Storage                                       │
│     └─ Satellite Images & Analysis Results                │
└────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Frontend (Flutter)
- **Purpose**: Cross-platform mobile and web UI
- **Features**:
  - Interactive maps showing water bodies
  - Real-time alerts and notifications
  - Historical data visualization
  - User authentication
  - Offline functionality with Hive storage

#### Backend API (FastAPI)
- **Purpose**: Core application logic and data management
- **Routes**:
  - Authentication endpoints
  - Water bodies CRUD operations
  - Monitoring data retrieval
  - Analysis triggering
  - Alert management

#### Processing Pipeline
- **Image Processing**: Satellite image preprocessing and enhancement
- **Change Detection**: Temporal analysis for detecting changes
- **ML Models**: Deep learning for encroachment classification
- **Geospatial Analysis**: PostGIS queries for spatial analysis

#### Data Sources
- **Google Earth Engine**: Free satellite imagery (Sentinel-2, Sentinel-1)
- **Supabase**: Managed PostgreSQL database with PostGIS
- **Cloud Storage**: AWS S3 for processed images and reports

### Data Flow

#### Satellite Data Analysis Pipeline
```
Google Earth Engine
    │
    ├─ Fetch Sentinel-2 Image
    │
    ▼
FastAPI Backend
    │
    ├─ Image Preprocessing (normalize, resize)
    │
    ├─ Calculate Indices (NDVI, NDWI)
    │
    ├─ Change Detection (compare with previous)
    │
    ├─ ML Model Inference (encroachment detection)
    │
    ├─ Geospatial Analysis (PostGIS queries)
    │
    ▼
Store Results
    │
    ├─ Save to PostgreSQL
    ├─ Upload images to S3
    ├─ Cache in Redis
    │
    ▼
Generate Alerts
    │
    ├─ Check severity levels
    ├─ Create alert records
    ├─ Send notifications
    │
    ▼
Flutter App (Real-time)
    │
    └─ Display on dashboard
```

### Database Schema (PostGIS)

#### Users Table
```sql
- id (Primary Key)
- email (Unique)
- username (Unique)
- hashed_password
- role (admin, officer, user)
- is_active
- created_at, updated_at
```

#### Water Bodies Table
```sql
- id (Primary Key)
- name
- body_type (lake, pond, river, etc.)
- geometry (PostGIS POLYGON)
- area_sq_km
- description
- created_at, updated_at
```

#### Monitoring Records Table
```sql
- id (Primary Key)
- water_body_id (Foreign Key)
- satellite_image (S3 URL)
- captured_at
- processed_at
- ndvi_value (Normalized Difference Vegetation Index)
- ndwi_value (Normalized Difference Water Index)
- water_area_sq_km
- change_detected (Boolean)
- image_data (Binary)
- metadata (JSON)
```

#### Encroachments Table
```sql
- id (Primary Key)
- water_body_id (Foreign Key)
- monitoring_record_id (Foreign Key)
- location (PostGIS POINT)
- area_sq_km
- severity (low, medium, high)
- detected_at
- confirmed_at
- status (pending, confirmed, resolved)
- details (JSON)
```

#### Alerts Table
```sql
- id (Primary Key)
- water_body_id (Foreign Key)
- encroachment_id (Foreign Key)
- alert_type (encroachment, pollution, etc.)
- severity (low, medium, high, critical)
- message
- created_at
- resolved_at
- is_resolved (Boolean)
- metadata (JSON)
```

### API Response Format

Standard JSON response structure:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error response:

```json
{
  "success": false,
  "error": "Error type",
  "message": "Detailed error message",
  "code": 400,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Scalability Considerations

1. **Horizontal Scaling**:
   - Multiple FastAPI instances behind load balancer
   - PostgreSQL read replicas
   - Redis cluster for caching

2. **Processing Optimization**:
   - Celery workers for async processing
   - Image processing pipeline optimization
   - Batch processing for multiple water bodies

3. **Storage Strategy**:
   - Time-based data archival
   - Image compression and optimization
   - CDN for frontend assets

### Security Architecture

1. **Authentication**: JWT tokens with secure storage
2. **Authorization**: Role-based access control (RBAC)
3. **Data Encryption**: HTTPS for all communications
4. **Database Security**: PostGIS with row-level security
5. **API Security**: Rate limiting, CORS, input validation

### Monitoring & Logging

- Application logs: Elasticsearch + Kibana
- Performance monitoring: Prometheus + Grafana
- Error tracking: Sentry
- User analytics: Firebase Analytics
