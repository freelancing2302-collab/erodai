# 🚀 Quick Start Guide - Watery Monitoring System

## **Get Started in 3 Steps**

### **Step 1: Start Backend**
```bash
cd ~/Documents/watery/backend
source ../venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
✅ Wait for: `Application startup complete`

### **Step 2: Start Web Server**
```bash
cd ~/Documents/watery
python3 -m http.server 3000
```
✅ Wait for: `Serving HTTP on 0.0.0.0 port 3000`

### **Step 3: Open in Browser**
```
http://localhost:3000/index.html
```
✅ See the interactive map!

---

## **What You'll See**

### **Interactive Map Features**
- 🗺️ **Left Sidebar**: All 10 water bodies listed
  - Click any to zoom and view details
  - Color-coded status (✅ Normal or ⚠️ Encroached)
  - Area information for each body

- 📍 **Map Center**: Interactive Leaflet map
  - Blue markers = Normal water bodies
  - Red markers = Encroached areas
  - Click markers to open details

- 📊 **Right Panel**: Water body details
  - Type, Area, Location (GPS coordinates)
  - Status indicator
  - "🛰️ Refresh Satellite Image" button
  - Description

---

## **10 Real Water Bodies in Erode District**

| # | Name | Type | Area | Status |
|---|------|------|------|--------|
| 1 | Bhavani River | River | 2.5 sq km | ✅ |
| 2 | Noyyal River | River | 1.8 sq km | ✅ |
| 3 | Pongalur Lake | Lake | 0.8 sq km | ✅ |
| 4 | Siddhapudur Lake | Lake | 1.2 sq km | ✅ |
| 5 | Periyar Reservoir | Reservoir | 3.5 sq km | ⚠️ |
| 6 | Kalingarayan Canal | Canal | 0.6 sq km | ✅ |
| 7 | Valparai Dam | Reservoir | 2.0 sq km | ✅ |
| 8 | Thadapalli Lake | Lake | 0.5 sq km | ✅ |
| 9 | Kumbakarai Falls | Waterfall | 0.3 sq km | ✅ |
| 10 | Mettupalayam Tank | Tank | 0.4 sq km | ✅ |

---

## **Test the System**

### **API Testing**
```bash
# View all water bodies (GeoJSON)
curl http://localhost:8000/api/v1/map/water-bodies-geojson | jq

# Get district info
curl http://localhost:8000/api/v1/map/erode-district | jq

# Get satellite for a location
curl http://localhost:8000/api/v1/map/satellite/11.3392/77.7542 | jq
```

### **Web UI Testing**
1. Open http://localhost:3000/index.html
2. Click "Periyar Reservoir" in sidebar (shows ⚠️ ENCROACHED)
3. View satellite imagery and location
4. Scroll through all 10 water bodies
5. Note the legend: **10 Water Bodies | 1 Encroached**

---

## **Technology Stack** (100% FREE & OPEN SOURCE)

```
Frontend Layer
├─ Leaflet.js (Free mapping library)
├─ OpenStreetMap (Free map data)
└─ HTML5 + CSS3

Backend Layer
├─ FastAPI (Python web framework)
├─ SQLite (Local database)
├─ SQLAlchemy (ORM)
└─ Python image processing (Pillow, scikit-image)

Services
├─ OSMService (Water body management)
├─ Image processing (Water detection)
├─ Email alerts (SMTP - configurable)
└─ JWT Authentication (python-jose, bcrypt)
```

---

## **Key Advantages**

✅ **No API Keys Required** - No Microsoft Azure, Google, or Bing Maps subscriptions  
✅ **Zero Cost** - Completely free and open-source  
✅ **Real Water Bodies** - All 10 are actual locations in Erode District, Tamil Nadu  
✅ **Real-time Monitoring** - Live satellite image analysis  
✅ **Encroachment Detection** - 5% water loss threshold alert  
✅ **Email Alerts** - Ready to configure (SMTP)  
✅ **Mobile Ready** - Flutter app interface included  
✅ **Fully Documented** - API docs at http://localhost:8000/docs  

---

## **Understanding the Map**

### **Color Legend**
- 🔵 **Blue Marker** = Normal, healthy water body
- 🔴 **Red Marker** = ENCROACHED (water loss detected)
- 🟦 **Light Blue Boundary** = Erode District boundaries

### **Map Controls**
- **+/−** buttons = Zoom in/out
- **Click Marker** = Open popup with details
- **Scroll Sidebar** = View all 10 water bodies
- **Click Item** = Select and zoom to that water body

---

## **Real-time Monitoring Workflow**

```
1. SELECT WATER BODY
   └─> Click on sidebar item or map marker

2. FETCH SATELLITE IMAGE
   └─> Backend retrieves free OSM satellite tile

3. ANALYZE FOR ENCROACHMENT
   └─> Color detection algorithm identifies water area
   └─> Compare with previous baseline (5% threshold)

4. GENERATE ALERTS
   └─> If water loss > 5% → Alert triggered
   └─> Email notification sent (if configured)

5. UPDATE STATUS
   └─> Map marker changes to red (⚠️ ENCROACHED)
   └─> Details panel shows new status
```

---

## **Database Schema**

### **Users Table**
- id, email, username, password_hash, role, created_at

### **Water Bodies Table**
- id, name, type, location (JSON), area_sq_km, urbanization_level, alert_threshold

### **Monitoring Records Table**
- id, water_body_id, satellite_image, water_area_sq_km, ndvi_value, processed_at

### **Encroachments Table**
- id, water_body_id, detected_at, area_loss_sq_km, confidence_score

### **Alerts Table**
- id, water_body_id, alert_type, severity, sent_to, created_at

---

## **Configuration Examples**

### **Email Alert Configuration**
```bash
# Gmail
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your_email@gmail.com"
export SMTP_PASSWORD="your_app_password"

# Yahoo
export SMTP_SERVER="smtp.mail.yahoo.com"
export SMTP_PORT="587"

# Corporate
export SMTP_SERVER="mail.company.com"
export SMTP_PORT="25"
```

### **Run with Email Alerts**
```bash
export ALERT_EMAIL="district_officer@erode.gov.in"
export FROM_EMAIL="watery-alerts@monitoring.local"
# Then restart backend
```

---

## **API Reference Quick Links**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/map/water-bodies-geojson` | GET | Get all water bodies |
| `/api/v1/map/erode-district` | GET | Get district info |
| `/api/v1/map/satellite/{lat}/{lon}` | GET | Fetch satellite image |
| `/api/v1/map/compare/{body_id}` | GET | Detect encroachment |
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/auth/login` | POST | User login |

Full docs: **http://localhost:8000/docs** (Swagger UI)

---

## **Troubleshooting**

| Problem | Solution |
|---------|----------|
| **Map shows blank** | Internet connection needed for OSM tiles |
| **No water bodies visible** | Check backend is running (`/api/v1/map/water-bodies-geojson`) |
| **Satellite image not loading** | OSM tile service may be slow; try refreshing |
| **Port 3000 already in use** | `lsof -ti:3000 \| xargs kill -9` |
| **API 404 errors** | Verify backend running on port 8000 |

---

## **Next: Advanced Features**

### **To Enable Email Alerts**
1. Configure SMTP credentials (see above)
2. Restart backend
3. System will automatically send alerts when encroachment detected

### **To Add More Water Bodies**
Edit `/backend/app/services/osm_service.py`:
```python
{
    "name": "New Lake Name",
    "type": "lake",
    "lat": 11.XXXX,
    "lon": 77.XXXX,
    "area_sq_km": X.X,
    "description": "Description here"
}
```

### **To Deploy to Production**
```bash
# Build Docker image (coming soon)
docker build -t watery:latest .
docker run -p 8000:8000 -p 3000:3000 watery:latest
```

---

## **Support Resources**

📖 **Full Implementation Guide**: See `IMPLEMENTATION_GUIDE.md`  
📚 **API Documentation**: http://localhost:8000/docs  
🔗 **OpenStreetMap**: https://www.openstreetmap.org  
🔗 **Leaflet.js**: https://leafletjs.com  
🔗 **FastAPI**: https://fastapi.tiangolo.com  

---

## **Success Checklist** ✅

- [ ] Backend running on port 8000
- [ ] Web server running on port 3000
- [ ] Map loads at http://localhost:3000/index.html
- [ ] 10 water bodies visible in sidebar
- [ ] Can click water bodies and see details
- [ ] Periyar Reservoir shows as "ENCROACHED"
- [ ] API endpoints responding at http://localhost:8000/api/v1/...
- [ ] Swagger docs visible at http://localhost:8000/docs

---

**🎉 You're Ready to Monitor Water Bodies in Real-time!**

Start with the 3 steps above and enjoy exploring the system.

Questions? Check `IMPLEMENTATION_GUIDE.md` for detailed information.
