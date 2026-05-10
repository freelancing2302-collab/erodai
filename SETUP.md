# Watery - Water Bodies Monitoring System

## Development Setup

This document provides step-by-step instructions to set up the development environment for the Watery project.

### Prerequisites

Before starting, ensure you have:
- Git
- Python 3.11 or higher
- Flutter 3.0 or higher
- Docker and Docker Compose
- Supabase account (free tier available)
- Google account for Earth Engine

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file and fill in your configuration:
   - Database connection details
   - Supabase credentials
   - Google Earth Engine project ID
   - JWT secrets

5. **Run with Docker Compose (recommended)**
   ```bash
   docker-compose up -d
   ```
   This starts:
   - PostgreSQL with PostGIS
   - Redis
   - FastAPI backend

6. **Database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Verify backend is running**
   ```
   http://localhost:8000/health
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Get Flutter dependencies**
   ```bash
   flutter pub get
   ```

3. **Generate code (freezed models, etc.)**
   ```bash
   flutter pub run build_runner build
   ```

4. **Run the app**
   ```bash
   flutter run
   ```

### Running Tests

**Backend tests:**
```bash
cd backend
pytest tests/
```

**Frontend tests:**
```bash
cd frontend
flutter test
```

### Development Workflow

**Backend:**
- FastAPI with automatic reload when files change
- SwaggerUI available at `http://localhost:8000/docs`
- ReDoc at `http://localhost:8000/redoc`

**Frontend:**
- Hot reload enabled during development
- Use `flutter run -v` for verbose output

### Environment Variables

Key environment variables to configure:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/watery_db

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=anon_key

# JWT
JWT_SECRET=your-secret-key

# Google Earth Engine
GEE_PROJECT_ID=your-project-id
```

### Troubleshooting

**Backend issues:**
- Check Docker is running: `docker ps`
- View logs: `docker-compose logs -f backend`
- Reset database: `docker-compose down -v`

**Frontend issues:**
- Clean build: `flutter clean && flutter pub get`
- Check Flutter setup: `flutter doctor`
- Update dependencies: `flutter pub upgrade`

### Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Flutter Documentation](https://flutter.dev/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Google Earth Engine](https://earthengine.google.com/)
- [PostgreSQL PostGIS](https://postgis.net/)
