from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from passlib.context import CryptContext
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import base64
from contextlib import asynccontextmanager

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib


from database import (
    get_session,
    UserModel,
    RelationshipModel,
    CertificateModel,
    Base as ORMBase,
    engine as orm_engine,
    AsyncSessionLocal,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

"""FastAPI backend for Vehicle Conspicuity Management System."""

# Security configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Password hashing (secure bcrypt via passlib)
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> tuple[bytes, bytes]:
    password_bytes = password.encode("utf-8")
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, 100000)
    return salt, key


def verify_password(password: str, salt: bytes, stored_key: bytes) -> bool:
    password_bytes = password.encode("utf-8")

    # Recompute the hash with the same salt
    new_key = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, 100000)

    # Compare safely
    return new_key == stored_key


security = HTTPBearer()


# Lifespan placeholder (defined later) will be attached after definition; temporarily create app without lifespan
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
    certificate_no: str = Field(
        default_factory=lambda: f"CERT{str(uuid.uuid4())[:8].upper()}"
    )
    retailer_id: str
    dealer_name: str
    dealer_license: str
    vehicle_details: VehicleDetails
    owner_details: OwnerDetails
    fitment_details: FitmentDetails
    fitment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    images: Dict[str, str] = Field(default_factory=dict)
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await session.execute(
        select(UserModel).where(UserModel.username == username)
    )
    user_row = result.scalar_one_or_none()
    if user_row is None:
        raise credentials_exception
    return User(
        id=user_row.id,
        username=user_row.username,
        role=user_row.role,
        company_name=user_row.company_name,
        contact_number=user_row.contact_number,
        created_by=user_row.created_by,
        created_at=user_row.created_at,
    )


def require_roles(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return role_checker


# Routes
@api_router.get("/")
async def root():
    return {"message": "Vehicle Conspicuity Management System API", "status": "ok"}


@app.get("/health")
async def health_check():
    """Lightweight unauthenticated health check.

    Returns OK if process up; includes basic DB connectivity flag.
    """
    # Simple readiness: attempt lightweight DB interaction (transactionless)
    db_ok = True
    try:
        # Run a trivial select 1
        from sqlalchemy import text

        async with orm_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover
        db_ok = False
    return {"app": "ok", "db": "ok" if db_ok else "degraded"}


@api_router.post("/auth/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    current_user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check if user already exists
    existing = await session.execute(
        select(UserModel).where(UserModel.username == user_data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Role-based registration logic
    if user_data.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create admin users through registration",
        )
    elif user_data.role == UserRole.DISTRIBUTOR:
        if not current_user or current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create distributors",
            )
    elif user_data.role == UserRole.RETAILER:
        if not current_user or current_user.role not in [
            UserRole.ADMIN,
            UserRole.DISTRIBUTOR,
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins or distributors can create retailers",
            )

    # Create user
    salt, hashed_password = hash_password(user_data.password)
    user_dict = user_data.model_dump(exclude={"password"})
    user_obj = User(**user_dict)

    if current_user:
        user_obj.created_by = current_user.id

    # Store user with hashed password
    db_user = UserModel(
        id=user_obj.id,
        username=user_obj.username,
        password_hash=hashed_password,
        role=user_obj.role,
        company_name=user_obj.company_name,
        contact_number=user_obj.contact_number,
        created_by=user_obj.created_by,
        created_at=user_obj.created_at,
        password_salt=salt,
    )
    session.add(db_user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create distributor-retailer relationship if applicable
    if (
        user_data.role == UserRole.RETAILER
        and current_user
        and current_user.role == UserRole.DISTRIBUTOR
    ):
        rel = RelationshipModel(
            distributor_id=current_user.id,
            retailer_id=user_obj.id,
        )
        session.add(rel)
        await session.commit()

    return user_obj


@api_router.post("/auth/login", response_model=Token)
async def login(
    user_credentials: UserLogin, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(UserModel).where(UserModel.username == user_credentials.username)
    )
    user_row = result.scalar_one_or_none()
    if not user_row or not verify_password(
        user_credentials.password, user_row.password_salt, user_row.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_row.username}, expires_delta=access_token_expires
    )

    user_obj = User(
        id=user_row.id,
        username=user_row.username,
        role=user_row.role,
        company_name=user_row.company_name,
        contact_number=user_row.contact_number,
        created_by=user_row.created_by,
        created_at=user_row.created_at,
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}


@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@api_router.get("/users", response_model=List[User])
async def get_users(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DISTRIBUTOR])),
    session: AsyncSession = Depends(get_session),
):
    if current_user.role == UserRole.ADMIN:
        result = await session.execute(select(UserModel))
        rows = result.scalars().all()
    else:
        rels = await session.execute(
            select(RelationshipModel).where(
                RelationshipModel.distributor_id == current_user.id
            )
        )
        retailer_ids = [r.retailer_id for r in rels.scalars().all()]
        if retailer_ids:
            result = await session.execute(
                select(UserModel).where(UserModel.id.in_(retailer_ids))
            )
            rows = result.scalars().all()
        else:
            rows = []
    return [
        User(
            id=u.id,
            username=u.username,
            role=u.role,
            company_name=u.company_name,
            contact_number=u.contact_number,
            created_by=u.created_by,
            created_at=u.created_at,
        )
        for u in rows
    ]


@api_router.post("/certificates", response_model=Certificate)
async def create_certificate(
    cert_data: CertificateCreate,
    current_user: User = Depends(require_roles([UserRole.RETAILER])),
    session: AsyncSession = Depends(get_session),
):
    cert_obj = Certificate(
        retailer_id=current_user.id,
        dealer_name=cert_data.dealer_name,
        dealer_license=cert_data.dealer_license,
        vehicle_details=cert_data.vehicle_details,
        owner_details=cert_data.owner_details,
        fitment_details=cert_data.fitment_details,
        status=cert_data.status,
    )
    db_cert = CertificateModel(
        id=cert_obj.id,
        certificate_no=cert_obj.certificate_no,
        retailer_id=cert_obj.retailer_id,
        dealer_name=cert_obj.dealer_name,
        dealer_license=cert_obj.dealer_license,
        vehicle_details=cert_obj.vehicle_details.model_dump(),
        owner_details=cert_obj.owner_details.model_dump(),
        fitment_details=cert_obj.fitment_details.model_dump(),
        images=cert_obj.images,
        status=cert_obj.status,
        fitment_date=cert_obj.fitment_date,
        created_at=cert_obj.created_at,
        updated_at=cert_obj.updated_at,
    )
    session.add(db_cert)
    await session.commit()
    return cert_obj


@api_router.get("/certificates", response_model=List[Certificate])
async def get_certificates(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    query = select(CertificateModel)
    if current_user.role == UserRole.ADMIN:
        pass
    elif current_user.role == UserRole.DISTRIBUTOR:
        rels = await session.execute(
            select(RelationshipModel).where(
                RelationshipModel.distributor_id == current_user.id
            )
        )
        retailer_ids = [r.retailer_id for r in rels.scalars().all()]
        if retailer_ids:
            query = query.where(CertificateModel.retailer_id.in_(retailer_ids))
        else:
            return []
    else:
        query = query.where(CertificateModel.retailer_id == current_user.id)

    result = await session.execute(query)
    rows = result.scalars().all()
    return [
        Certificate(
            id=r.id,
            certificate_no=r.certificate_no,
            retailer_id=r.retailer_id,
            dealer_name=r.dealer_name,
            dealer_license=r.dealer_license,
            vehicle_details=VehicleDetails(**r.vehicle_details),
            owner_details=OwnerDetails(**r.owner_details),
            fitment_details=FitmentDetails(**r.fitment_details),
            fitment_date=r.fitment_date,
            images=r.images,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@api_router.get("/certificates/{certificate_id}", response_model=Certificate)
async def get_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(CertificateModel).where(CertificateModel.id == certificate_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Certificate not found")

    cert_obj = Certificate(
        id=r.id,
        certificate_no=r.certificate_no,
        retailer_id=r.retailer_id,
        dealer_name=r.dealer_name,
        dealer_license=r.dealer_license,
        vehicle_details=VehicleDetails(**r.vehicle_details),
        owner_details=OwnerDetails(**r.owner_details),
        fitment_details=FitmentDetails(**r.fitment_details),
        fitment_date=r.fitment_date,
        images=r.images,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )

    # Check permissions
    if (
        current_user.role == UserRole.RETAILER
        and cert_obj.retailer_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Access forbidden")
    elif current_user.role == UserRole.DISTRIBUTOR:
        rel_result = await session.execute(
            select(RelationshipModel).where(
                RelationshipModel.distributor_id == current_user.id,
                RelationshipModel.retailer_id == cert_obj.retailer_id,
            )
        )
        if not rel_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access forbidden")

    return cert_obj


@api_router.put("/certificates/{certificate_id}", response_model=Certificate)
async def update_certificate(
    certificate_id: str,
    cert_data: CertificateUpdate,
    current_user: User = Depends(require_roles([UserRole.RETAILER])),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(CertificateModel).where(CertificateModel.id == certificate_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if r.retailer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    data = cert_data.dict(exclude_unset=True)
    update_fields = {}
    if data.get("dealer_name") is not None:
        update_fields["dealer_name"] = data["dealer_name"]
    if data.get("dealer_license") is not None:
        update_fields["dealer_license"] = data["dealer_license"]
    if data.get("vehicle_details") is not None:
        update_fields["vehicle_details"] = data["vehicle_details"].model_dump()
    if data.get("owner_details") is not None:
        update_fields["owner_details"] = data["owner_details"].model_dump()
    if data.get("fitment_details") is not None:
        update_fields["fitment_details"] = data["fitment_details"].model_dump()
    if data.get("status") is not None:
        update_fields["status"] = data["status"]
    update_fields["updated_at"] = datetime.now(timezone.utc)

    await session.execute(
        update(CertificateModel)
        .where(CertificateModel.id == certificate_id)
        .values(**update_fields)
    )
    await session.commit()

    # Re-fetch
    result = await session.execute(
        select(CertificateModel).where(CertificateModel.id == certificate_id)
    )
    r = result.scalar_one_or_none()
    return Certificate(
        id=r.id,
        certificate_no=r.certificate_no,
        retailer_id=r.retailer_id,
        dealer_name=r.dealer_name,
        dealer_license=r.dealer_license,
        vehicle_details=VehicleDetails(**r.vehicle_details),
        owner_details=OwnerDetails(**r.owner_details),
        fitment_details=FitmentDetails(**r.fitment_details),
        fitment_date=r.fitment_date,
        images=r.images,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@api_router.post("/certificates/{certificate_id}/upload-image")
async def upload_certificate_image(
    certificate_id: str,
    image_type: str,  # front, back, side1, side2
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles([UserRole.RETAILER])),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(CertificateModel).where(CertificateModel.id == certificate_id)
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if r.retailer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    if image_type not in ["front", "back", "side1", "side2"]:
        raise HTTPException(status_code=400, detail="Invalid image type")

    contents = await file.read()
    encoded_image = base64.b64encode(contents).decode("utf-8")
    new_images = dict(r.images or {})
    new_images[image_type] = encoded_image

    await session.execute(
        update(CertificateModel)
        .where(CertificateModel.id == certificate_id)
        .values(images=new_images, updated_at=datetime.now(timezone.utc))
    )
    await session.commit()
    return {"message": "Image uploaded successfully", "image_type": image_type}


@api_router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.role == UserRole.ADMIN:
        total_users = (await session.execute(func.count(UserModel.id))).scalar() or 0
        total_distributors = (
            await session.execute(
                func.count(UserModel.id).filter(UserModel.role == UserRole.DISTRIBUTOR)
            )
        ).scalar() or 0
        total_retailers = (
            await session.execute(
                func.count(UserModel.id).filter(UserModel.role == UserRole.RETAILER)
            )
        ).scalar() or 0
        total_certificates = (
            await session.execute(func.count(CertificateModel.id))
        ).scalar() or 0
        submitted_certificates = (
            await session.execute(
                func.count(CertificateModel.id).filter(
                    CertificateModel.status == "submitted"
                )
            )
        ).scalar() or 0
        return {
            "total_users": total_users,
            "total_distributors": total_distributors,
            "total_retailers": total_retailers,
            "total_certificates": total_certificates,
            "submitted_certificates": submitted_certificates,
            "draft_certificates": total_certificates - submitted_certificates,
        }
    elif current_user.role == UserRole.DISTRIBUTOR:
        rels = await session.execute(
            select(RelationshipModel).where(
                RelationshipModel.distributor_id == current_user.id
            )
        )
        retailer_ids = [r.retailer_id for r in rels.scalars().all()]
        total_retailers = len(retailer_ids)
        if retailer_ids:
            certs_result = await session.execute(
                select(CertificateModel).where(
                    CertificateModel.retailer_id.in_(retailer_ids)
                )
            )
            rows = certs_result.scalars().all()
        else:
            rows = []
        total_certificates = len(rows)
        submitted_certificates = len([r for r in rows if r.status == "submitted"])
        return {
            "total_retailers": total_retailers,
            "total_certificates": total_certificates,
            "submitted_certificates": submitted_certificates,
            "draft_certificates": total_certificates - submitted_certificates,
        }
    else:
        certs_result = await session.execute(
            select(CertificateModel).where(
                CertificateModel.retailer_id == current_user.id
            )
        )
        rows = certs_result.scalars().all()
        total_certificates = len(rows)
        submitted_certificates = len([r for r in rows if r.status == "submitted"])
        return {
            "total_certificates": total_certificates,
            "submitted_certificates": submitted_certificates,
            "draft_certificates": total_certificates - submitted_certificates,
        }


# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    filename="application.log",
    encoding="utf-8",
)
logger = logging.getLogger("vehicle_conspicuity_api")


# Create default admin user on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with orm_engine.begin() as conn:
        await conn.run_sync(ORMBase.metadata.create_all)

    # Create default admin if none exists
    async with AsyncSessionLocal() as session:  # type: ignore
        result = await session.execute(
            select(UserModel).where(UserModel.role == UserRole.ADMIN)
        )
        admin_exists = result.scalar_one_or_none()
        if not admin_exists:
            session.add(
                UserModel(
                    id=str(uuid.uuid4()),
                    username="admin",
                    password_hash=hash_password("admin123"),
                    role=UserRole.ADMIN,
                    company_name="System Admin",
                )
            )
            await session.commit()
            logger.info("Default admin user created: username=admin, password=admin123")
    logger.info("Startup tasks completed (tables ensured, admin checked)")
    yield
    # (Optional) graceful shutdown tasks here


# Recreate app with lifespan so startup logic executes (rebind routers & middleware already added above if needed)
app.router.lifespan_context = lifespan
