# Backend Service - Vehicle Conspicuity Management System

This FastAPI service powers the Vehicle Conspicuity Management System.

## Key Features
- JWT authentication (admin, distributor, retailer roles)
- Hierarchical user creation (admin → distributor → retailer)
- Certificate creation and management with fitment & vehicle details
- Image upload (stored as base64 in MongoDB for MVP)
- Role-based dashboard statistics
- Secure password hashing (bcrypt / passlib)
- Health check endpoint (`/health`) for uptime monitoring

## Quick Start (Windows PowerShell)
```powershell
# From repository root
cd backend

# (Recommended) Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the API (reload for dev)
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Then open: http://localhost:8000/api for base API root

Interactive docs: http://localhost:8000/docs

Health check (unauthenticated): http://localhost:8000/health

## Environment Variables
You can create a `.env` file inside `backend/` (auto-loaded).

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | change-me-in-prod | JWT signing key (replace in production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token lifetime in minutes |
| `MONGO_URL` | mongodb://localhost:27017 | MongoDB connection string |
| `DB_NAME` | vehicle_conspicuity | Database name |
| `CORS_ORIGINS` | * | Comma-separated list of allowed origins |

Example `.env`:
```
SECRET_KEY=super-secret-key
MONGO_URL=mongodb://localhost:27017
DB_NAME=vehicle_conspicuity
CORS_ORIGINS=http://localhost:3000
```

## Default Admin
On startup, if no admin exists, the service creates:
- Username: `admin`
- Password: `admin123`

Change this immediately in production (add a password update endpoint or update directly in DB with a new hash from `passlib`).

## Password Hashing
New users use bcrypt via passlib. Legacy SHA256 hashes (if any) are still accepted on login for backward compatibility. To migrate, re-save users with `get_password_hash()` output.

## Project Structure (Backend)
```
backend/
  server.py         # FastAPI application
  requirements.txt  # Python dependencies
  README.md         # This file
```

## API Overview (Selected)
- POST `/api/auth/login` → JWT token
- POST `/api/auth/register` → Create user (requires appropriate role)
- GET `/api/auth/me` → Current user info
- GET `/api/users` → List users (admin/distributor scoped)
- POST `/api/certificates` → Create certificate (retailer)
- GET `/api/certificates` → List certificates (role scoped)
- GET `/api/certificates/{id}` → Certificate detail (access controlled)
- PUT `/api/certificates/{id}` → Update certificate (retailer owner)
- POST `/api/certificates/{id}/upload-image?image_type=front` → Upload image
- GET `/api/dashboard/stats` → Role-dependent statistics

## Image Upload
Images are stored base64-encoded per certificate under `images.{front|back|side1|side2}`. For production, replace with object storage (S3, etc.) and store URLs only.

## Health & Readiness
`/health` responds with `{ "app": "ok", "db": "ok|degraded" }`.

## Running Tests
Current `backend_test.py` targets a deployed preview URL. To adapt for local testing, change the base_url in its constructor to `http://localhost:8000/api`.

## Future Enhancements
- Password reset / update flow
- Refresh tokens & revocation
- Pagination & filtering for list endpoints
- Replace base64 image storage with external object storage
- Add Pydantic model versioning / response models with `response_model_exclude_none`
- Add structured logging & tracing

## Troubleshooting
| Issue | Possible Cause | Fix |
|-------|----------------|-----|
| Import errors | Virtualenv not activated | Activate env, reinstall requirements |
| Cannot login admin | Admin not created yet | Check logs; ensure Mongo running |
| 401 on protected endpoints | Missing/expired JWT | Re-login to obtain new token |
| Slow startup | Mongo unreachable | Verify `MONGO_URL` & connectivity |

Feel free to extend and harden this service. Pull requests welcome.
