# Security Guidelines for Erodai Project

## 🔒 Critical Security Information

This document provides guidance on securely setting up credentials and environment variables for the Erodai water monitoring system. **Never commit sensitive information to version control.**

## Environment Setup

### 1. Backend Environment Variables

Create a `.env` file in the `backend/` directory with the following template:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./watery.db
# For production, use: postgresql://user:password@host:5432/watery_db

# FastAPI Configuration
ENV=development
DEBUG=False  # Set to False in production
API_PREFIX=/api/v1
SECRET_KEY=your-very-secure-random-key-here
JWT_SECRET=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Google Earth Engine Configuration
GEE_PROJECT_ID=your-gee-project-id
GEE_SERVICE_ACCOUNT_JSON=path/to/your/service-account.json
GEE_ENABLED=false

# Supabase Configuration (optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AWS Configuration (optional for image storage)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your-bucket-name

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# SMTP Configuration (for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password  # Use App Password, not your main password!
SMTP_FROM_NAME=Erodai Monitoring System

# OSM Configuration
OSM_ENABLED=true
OSM_TILE_SERVER=https://tile.openstreetmap.org
```

**DO NOT commit `.env` file to version control. Use `.env.example` as a template.**

### 2. Backend - Generating Secure Keys

Generate strong random keys for `SECRET_KEY` and `JWT_SECRET`:

```bash
# Linux/Mac
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Windows
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Google Earth Engine Setup

1. Create a service account on [Google Cloud Console](https://console.cloud.google.com)
2. Download the JSON key file
3. Set `GEE_SERVICE_ACCOUNT_JSON` to the path of this file
4. **Never commit this JSON file**; add it to `.gitignore`
5. Enable the Earth Engine API in your GCP project

### 4. SMTP Configuration

For Gmail:
1. Enable 2-Factor Authentication on your Google Account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use this App Password in `SMTP_PASS` (not your regular password)
4. **Never commit this password**

For other email providers:
- Contact your provider for SMTP credentials
- Use app-specific passwords when available

### 5. Frontend (Flutter) OAuth Setup

The mobile app has placeholders for OAuth credentials:

**File:** `watery_mobile/lib/screens/login_screen.dart`

```dart
// Replace these placeholders:
final String googleClientId = 'YOUR_GOOGLE_CLIENT_ID';
final String facebookAppId = 'YOUR_FACEBOOK_APP_ID';
```

#### Google OAuth Setup:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new OAuth 2.0 Client ID (Web Application)
3. Add authorized redirect URI: `http://localhost:8000/auth/google/callback`
4. Copy the Client ID into the code

#### Facebook OAuth Setup:

1. Create an app on [Facebook Developers](https://developers.facebook.com)
2. Add Facebook Login product
3. Set valid OAuth redirect URIs: `http://localhost:8000/auth/facebook/callback`
4. Copy the App ID into the code

### 6. Backend OAuth Handlers

Ensure the following callbacks are configured in `backend/app/api/auth.py`:

```python
# Google OAuth callback (already configured in code)
@router.get("/auth/google/callback")
async def google_callback(code: str):
    # Handle Google OAuth token exchange

# Facebook OAuth callback (already configured in code)
@router.get("/auth/facebook/callback")
async def facebook_callback(code: str):
    # Handle Facebook OAuth token exchange
```

## File Exclusions

The `.gitignore` file automatically excludes:

- All `.env*` files
- `*.key`, `*.pem`, `*.p8` certificate files
- `serviceAccountKey.json` and similar credential files
- Build artifacts and dependencies
- IDE configuration files
- Database files
- Logs

**Verify sensitive files are excluded before pushing to GitHub:**

```bash
git status  # Check no sensitive files are staged
git diff --cached  # Review all staged changes before commit
```

## Credential Security Best Practices

1. **Never commit credentials** - Always use environment variables
2. **Use `.env.example`** - Provide template without real values
3. **Rotate credentials regularly** - Especially API keys and database passwords
4. **Use strong random keys** - Generate with `secrets.token_urlsafe()`
5. **Restrict file permissions** - `.env` should be readable only by application user
6. **Use service accounts** - For Google Earth Engine, not personal accounts
7. **Use app passwords** - For email services, not main passwords
8. **Document setup steps** - Help others set up securely without credentials in docs
9. **Monitor access logs** - Watch for unauthorized API usage
10. **Update dependencies** - Keep libraries patched for security fixes

## Local Development Setup

1. Clone the repository
2. Create `.env` file in `backend/` from `.env.example` template
3. Fill in your actual credentials (see sections above)
4. For Flutter apps, update the placeholder OAuth IDs
5. Run `python backend/app/main.py` to start backend
6. Run `flutter run` for mobile app or `flutter run -d chrome` for web

## Production Deployment

⚠️ **Before deploying to production:**

1. Update all credentials with production values
2. Set `DEBUG=False` in `.env`
3. Set `ENV=production` in `.env`
4. Use strong database passwords
5. Set up HTTPS/TLS certificates
6. Configure proper CORS origins (not `*`)
7. Enable database backups
8. Set up monitoring and logging
9. Use environment-specific deployment configurations
10. Document all credential sources and rotation schedules

## Credential Rotation Schedule

- **API Keys**: Every 90 days
- **Database passwords**: Every 6 months
- **Service account keys**: Every 1 year or on compromise
- **JWT secrets**: Review and rotate on major updates
- **SMTP passwords**: When changed at provider

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do not** create a public GitHub issue
2. Contact the security team privately
3. Include detailed steps to reproduce
4. Allow time for patching before public disclosure

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [Flutter Security](https://flutter.dev/docs/testing/best-practices)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Last Updated:** 2024  
**Version:** 1.0  
**Maintainer:** Erodai Team
