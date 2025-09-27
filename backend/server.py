from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import base64
from io import BytesIO

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing - using hashlib for simplicity in MVP
import hashlib
security = HTTPBearer()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Vehicle Conspicuity Management System")
api_router = APIRouter(prefix="/api")

# Models
class UserRole:
    ADMIN = "admin"
    DISTRIBUTOR = "distributor"
    RETAILER = "retailer"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    role: str
    company_name: Optional[str] = None
    contact_number: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    company_name: Optional[str] = None
    contact_number: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class VehicleDetails(BaseModel):
    registration_no: str
    chassis_no: str
    vehicle_make: str
    vehicle_model: str
    registration_year: int
    engine_no: str

class OwnerDetails(BaseModel):
    owner_name: str
    contact_number: str

class FitmentDetails(BaseModel):
    # Conspicuity Tapes 20MM
    red_20mm: float = 0.0
    white_20mm: float = 0.0
    yellow_20mm: float = 0.0
    # Conspicuity Tapes 50MM
    red_50mm: float = 0.0
    white_50mm: float = 0.0
    yellow_50mm: float = 0.0
    # Rear Marketing Plates
    c3_plates: int = 0
    c4_plates: int = 0

class Certificate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    certificate_no: str = Field(default_factory=lambda: f"CERT{str(uuid.uuid4())[:8].upper()}")
    retailer_id: str
    dealer_name: str
    dealer_license: str
    vehicle_details: VehicleDetails
    owner_details: OwnerDetails
    fitment_details: FitmentDetails
    fitment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    images: Dict[str, str] = Field(default_factory=dict)  # {"front": "base64_data", ...}
    status: str = "draft"  # draft, submitted
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CertificateCreate(BaseModel):
    dealer_name: str
    dealer_license: str
    vehicle_details: VehicleDetails
    owner_details: OwnerDetails
    fitment_details: FitmentDetails
    status: str = "draft"

class CertificateUpdate(BaseModel):
    dealer_name: Optional[str] = None
    dealer_license: Optional[str] = None
    vehicle_details: Optional[VehicleDetails] = None
    owner_details: Optional[OwnerDetails] = None
    fitment_details: Optional[FitmentDetails] = None
    status: Optional[str] = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Routes
@api_router.get("/")
async def root():
    return {"message": "Vehicle Conspicuity Management System API"}

@api_router.post("/auth/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    current_user: Optional[User] = Depends(get_current_user)
):
    # Check if user already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Role-based registration logic
    if user_data.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create admin users through registration"
        )
    elif user_data.role == UserRole.DISTRIBUTOR:
        if not current_user or current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create distributors"
            )
    elif user_data.role == UserRole.RETAILER:
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.DISTRIBUTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins or distributors can create retailers"
            )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict(exclude={"password"})
    user_obj = User(**user_dict)
    
    if current_user:
        user_obj.created_by = current_user.id
    
    # Store user with hashed password
    user_doc = user_obj.dict()
    user_doc["password_hash"] = hashed_password
    
    await db.users.insert_one(user_doc)
    
    # Create distributor-retailer relationship if applicable
    if user_data.role == UserRole.RETAILER and current_user and current_user.role == UserRole.DISTRIBUTOR:
        relationship = {
            "distributor_id": current_user.id,
            "retailer_id": user_obj.id,
            "created_at": datetime.now(timezone.utc)
        }
        await db.relationships.insert_one(relationship)
    
    return user_obj

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    user_obj = User(**user)
    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DISTRIBUTOR]))):
    if current_user.role == UserRole.ADMIN:
        # Admin can see all users
        users = await db.users.find().to_list(length=None)
    else:
        # Distributors can only see retailers under them
        relationships = await db.relationships.find({"distributor_id": current_user.id}).to_list(length=None)
        retailer_ids = [rel["retailer_id"] for rel in relationships]
        users = await db.users.find({"id": {"$in": retailer_ids}}).to_list(length=None)
    
    return [User(**user) for user in users]

@api_router.post("/certificates", response_model=Certificate)
async def create_certificate(
    cert_data: CertificateCreate,
    current_user: User = Depends(require_roles([UserRole.RETAILER]))
):
    cert_dict = cert_data.dict()
    cert_dict['retailer_id'] = current_user.id
    cert_obj = Certificate(**cert_dict)
    
    await db.certificates.insert_one(cert_obj.dict())
    return cert_obj

@api_router.get("/certificates", response_model=List[Certificate])
async def get_certificates(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        # Admin can see all certificates
        certificates = await db.certificates.find().to_list(length=None)
    elif current_user.role == UserRole.DISTRIBUTOR:
        # Distributors can see certificates from their retailers
        relationships = await db.relationships.find({"distributor_id": current_user.id}).to_list(length=None)
        retailer_ids = [rel["retailer_id"] for rel in relationships]
        certificates = await db.certificates.find({"retailer_id": {"$in": retailer_ids}}).to_list(length=None)
    else:
        # Retailers can only see their own certificates
        certificates = await db.certificates.find({"retailer_id": current_user.id}).to_list(length=None)
    
    return [Certificate(**cert) for cert in certificates]

@api_router.get("/certificates/{certificate_id}", response_model=Certificate)
async def get_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user)
):
    certificate = await db.certificates.find_one({"id": certificate_id})
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    cert_obj = Certificate(**certificate)
    
    # Check permissions
    if current_user.role == UserRole.RETAILER and cert_obj.retailer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    elif current_user.role == UserRole.DISTRIBUTOR:
        # Check if retailer belongs to this distributor
        relationship = await db.relationships.find_one({
            "distributor_id": current_user.id,
            "retailer_id": cert_obj.retailer_id
        })
        if not relationship:
            raise HTTPException(status_code=403, detail="Access forbidden")
    
    return cert_obj

@api_router.put("/certificates/{certificate_id}", response_model=Certificate)
async def update_certificate(
    certificate_id: str,
    cert_data: CertificateUpdate,
    current_user: User = Depends(require_roles([UserRole.RETAILER]))
):
    certificate = await db.certificates.find_one({"id": certificate_id})
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    if certificate["retailer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    update_data = {k: v for k, v in cert_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.certificates.update_one(
        {"id": certificate_id},
        {"$set": update_data}
    )
    
    updated_cert = await db.certificates.find_one({"id": certificate_id})
    return Certificate(**updated_cert)

@api_router.post("/certificates/{certificate_id}/upload-image")
async def upload_certificate_image(
    certificate_id: str,
    image_type: str,  # front, back, side1, side2
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.RETAILER]))
):
    certificate = await db.certificates.find_one({"id": certificate_id})
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    if certificate["retailer_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    
    if image_type not in ["front", "back", "side1", "side2"]:
        raise HTTPException(status_code=400, detail="Invalid image type")
    
    # Read and encode image
    contents = await file.read()
    encoded_image = base64.b64encode(contents).decode('utf-8')
    
    # Update certificate with image
    await db.certificates.update_one(
        {"id": certificate_id},
        {"$set": {f"images.{image_type}": encoded_image, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Image uploaded successfully", "image_type": image_type}

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.ADMIN:
        total_users = await db.users.count_documents({})
        total_distributors = await db.users.count_documents({"role": UserRole.DISTRIBUTOR})
        total_retailers = await db.users.count_documents({"role": UserRole.RETAILER})
        total_certificates = await db.certificates.count_documents({})
        submitted_certificates = await db.certificates.count_documents({"status": "submitted"})
        
        return {
            "total_users": total_users,
            "total_distributors": total_distributors,
            "total_retailers": total_retailers,
            "total_certificates": total_certificates,
            "submitted_certificates": submitted_certificates,
            "draft_certificates": total_certificates - submitted_certificates
        }
    elif current_user.role == UserRole.DISTRIBUTOR:
        relationships = await db.relationships.find({"distributor_id": current_user.id}).to_list(length=None)
        retailer_ids = [rel["retailer_id"] for rel in relationships]
        total_retailers = len(retailer_ids)
        total_certificates = await db.certificates.count_documents({"retailer_id": {"$in": retailer_ids}})
        submitted_certificates = await db.certificates.count_documents({
            "retailer_id": {"$in": retailer_ids},
            "status": "submitted"
        })
        
        return {
            "total_retailers": total_retailers,
            "total_certificates": total_certificates,
            "submitted_certificates": submitted_certificates,
            "draft_certificates": total_certificates - submitted_certificates
        }
    else:
        total_certificates = await db.certificates.count_documents({"retailer_id": current_user.id})
        submitted_certificates = await db.certificates.count_documents({
            "retailer_id": current_user.id,
            "status": "submitted"
        })
        
        return {
            "total_certificates": total_certificates,
            "submitted_certificates": submitted_certificates,
            "draft_certificates": total_certificates - submitted_certificates
        }

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Create default admin user on startup
@app.on_event("startup")
async def create_default_admin():
    admin_exists = await db.users.find_one({"role": UserRole.ADMIN})
    if not admin_exists:
        admin_user = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password_hash": get_password_hash("admin123"),
            "role": UserRole.ADMIN,
            "company_name": "System Admin",
            "contact_number": None,
            "created_by": None,
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(admin_user)
        logger.info("Default admin user created: username=admin, password=admin123")