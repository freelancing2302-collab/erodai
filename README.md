# Water Bodies Monitoring System - Project Root

## Quick Start

This is a full-stack satellite imagery-based monitoring system for detecting changes and encroachments in water bodies.

### Components
- **Backend**: FastAPI (Python) - `/backend`
- **Frontend**: Flutter (Dart) - `/frontend`
- **Documentation**: Project guides - `/docs`

### Prerequisites
- Python 3.11+
- Flutter 3.0+
- Docker & Docker Compose
- Supabase account
- Google Earth Engine access

### Quick Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
cp .env.example .env
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
flutter pub get
flutter run
```

### Documentation
See `/docs/README.md` for comprehensive project documentation.

### API Endpoints
- Health: `http://localhost:8000/health`
- Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Services
- FastAPI Backend: Port 8000
- PostgreSQL: Port 5432
- Redis: Port 6379

For detailed setup and development guide, refer to the documentation.
