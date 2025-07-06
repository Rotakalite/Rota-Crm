import os
import uuid
import logging
import shutil
import re
import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv
import json
from enum import Enum
import re
import jwt
from jwt import PyJWKClient
import httpx
import requests
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Email service import
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from services.email_service import email_service
    logging.info("✅ Email service imported successfully")
except Exception as e:
    logging.error(f"❌ Failed to import Email service: {e}")
    email_service = None

# WhatsApp service - DISABLED
whatsapp_service = None  # WhatsApp service deactivated

# DEFRA Carbon calculation import
try:
    from defra_carbon import calculate_carbon_emissions, get_emission_factor, validate_consumption_data, benchmark_performance
    logging.info("✅ DEFRA Carbon module imported successfully")
except ImportError as e:
    logging.warning(f"⚠️ DEFRA Carbon module import failed: {e}")
    calculate_carbon_emissions = None

# Import MongoDB GridFS service (DISABLED - PROBLEMATIC)
# try:
#     import sys
#     import os
#     sys.path.append(os.path.dirname(__file__))
#     from services.mongo_gridfs import mongo_gridfs
#     logging.info("✅ MongoDB GridFS service imported successfully")
# except Exception as e:
#     logging.error(f"❌ Failed to import MongoDB GridFS service: {e}")
#     mongo_gridfs = None

# Disable GridFS for now
mongo_gridfs = None

# Import Supabase service (backup)
try:
    from services.supabase_storage import supabase_storage
    logging.info("✅ Supabase storage service imported as backup")
except Exception as e:
    logging.error(f"❌ Failed to import Supabase storage service: {e}")
    supabase_storage = None

# Import GCS service (fallback)
try:
    from services.gcs import gcs_service
    logging.info("✅ GCS service imported as fallback")
except Exception as e:
    logging.error(f"❌ Failed to import GCS service: {e}")
    gcs_service = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Clerk configuration
CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
CLERK_JWKS_URL = os.environ.get('CLERK_JWKS_URL')

# Configure FastAPI for large file uploads
app = FastAPI(
    title="Sürdürülebilir Turizm Danışmanlık CRM API",
    description="CRM system for sustainable tourism consulting",
    version="1.0.0"
)

# RAILWAY CORS CONFIGURATION - TÜM VERCEL URL'LERİ İÇİN
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://portal.rotakalitedanismanlik.com",  # PRODUCTION DOMAIN
        "https://rota-a43ap7zfm-rotas-projects-62181e6e.vercel.app",  # Eski Vercel URL
        "https://rota-9asd83vl1-rotas-projects-62181e6e.vercel.app",  # Yeni Vercel URL
        "https://*.vercel.app",  # Tüm Vercel domain'leri  
        "https://eeb7db6e-db39-4d4e-be1b-fe2f8cdcb81a.preview.emergentagent.com",  # Current reported URL
        "https://eeb7db6e-db39-4d4e-be1b-fe2f8cdcb81a.preview.emergentagent.com",  # Current env URL
        "http://localhost:3000",  # Development
        "http://localhost:3001",  # Development
        "*"  # Hepsine izin ver (geliştirme için)
    ],
    allow_credentials=True,  # Vercel için True
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept", 
        "Accept-Language", 
        "Content-Language", 
        "Content-Type", 
        "Authorization", 
        "X-Requested-With", 
        "Origin", 
        "Access-Control-Request-Method", 
        "Access-Control-Request-Headers",
        "Cache-Control",  # Bu eksikti!
        "Pragma",
        "Expires",
        "X-CSRF-Token",
        "*"  # Tüm header'lara izin ver
    ],
    expose_headers=["*"],
    max_age=86400  # 24 saat cache
)

# Set maximum request size to 500MB
app.state.max_request_size = 500 * 1024 * 1024  # 500MB

# SUPER AGGRESSIVE CORS MIDDLEWARE - FORCES CORS ON ALL RESPONSES
@app.middleware("http")
async def ultra_cors_middleware(request, call_next):
    # Handle preflight OPTIONS requests FIRST
    if request.method == "OPTIONS":
        response = Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Cache-Control, Pragma, Expires, X-CSRF-Token",
                "Access-Control-Expose-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",
                "Content-Length": "0"
            }
        )
        return response
    
    # Allow large uploads for upload endpoints
    if request.url.path.endswith("/upload-document"):
        request.state.max_request_size = 500 * 1024 * 1024
    
    # Process normal request
    response = await call_next(request)
    
    # Force CORS headers on ALL responses - ULTRA PERMISSIVE
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Cache-Control, Pragma, Expires, X-CSRF-Token"
    response.headers["Access-Control-Expose-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response

# Create a router with the /api prefix
api_router = APIRouter()

# Additional OPTIONS handler for API routes
@api_router.options("/{full_path:path}")
async def api_options_handler(full_path: str):
    """Handle CORS preflight requests for API routes"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Cache-Control, Pragma, Expires, X-CSRF-Token",
            "Access-Control-Expose-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
            "Content-Length": "0"
        }
    )

# Global OPTIONS handler for non-API routes
@app.options("/{full_path:path}")
async def global_options_handler(full_path: str):
    """Handle CORS preflight requests for all routes"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Cache-Control, Pragma, Expires, X-CSRF-Token",
            "Access-Control-Expose-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
            "Content-Length": "0"
        }
    )

# Security
security = HTTPBearer()

# Rate Limiter for 2FA
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# JWKS client - simple version without cache_ttl
import functools
import time

@functools.lru_cache(maxsize=1)
def get_jwks_client():
    return PyJWKClient(CLERK_JWKS_URL)

jwks_client = get_jwks_client()

# Enums
class ProjectStage(str, Enum):
    STAGE_1 = "I.Aşama"
    STAGE_2 = "II.Aşama"
    STAGE_3 = "III.Aşama"

class ConsumptionType(str, Enum):
    ELECTRICITY = "elektrik"
    WATER = "su"
    NATURAL_GAS = "dogalgaz"
    COAL = "komur"

class ServiceType(str, Enum):
    SITUATION_ANALYSIS = "Mevcut durum analizi"
    TEAM_DETERMINATION = "Çalışma ekibinin belirlenmesi"
    PROJECT_PLANNING = "Proje planının oluşturulması"
    SUSTAINABILITY_PLAN = "Sürdürülebilirlik planı"
    RISK_ASSESSMENT = "Risk değerlendirmesi"
    TRAINING = "Eğitim-Bilinçlendirme faaliyetleri"
    MONITORING = "İzleme, Denetim Kayıtlarının Oluşturulması ve İyileştirme faaliyetleri"
    CERTIFICATION_AUDIT = "Belgelendirme denetimi"

class DocumentType(str, Enum):
    TR1_CRITERIA = "Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)"
    STAGE_1_DOC = "I. Aşama Belgesi"
    STAGE_2_DOC = "II. Aşama Belgesi"
    STAGE_3_DOC = "III. Aşama Belgesi"
    CARBON_REPORT = "Karbon Ayak İzi Raporu"
    SUSTAINABILITY_REPORT = "Sürdürülebilirlik Raporu"

class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"

# Authentication Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clerk_user_id: str
    email: str
    name: str
    role: UserRole = UserRole.CLIENT
    client_id: Optional[str] = None  # For client users, links to their client record
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    clerk_user_id: str
    email: str
    name: str
    role: UserRole = UserRole.CLIENT
    client_id: Optional[str] = None

# Existing Models
class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    hotel_name: str
    contact_person: str
    email: str
    phone: str
    phone_number: Optional[str] = None  # WhatsApp için ek telefon field
    address: str
    current_stage: ProjectStage = ProjectStage.STAGE_1
    services_completed: List[ServiceType] = []
    carbon_footprint: Optional[float] = None
    sustainability_score: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Guest Engagement Models
class GuestEngagementInput(BaseModel):
    guest_name: str
    room_number: str
    eco_actions: List[str] = []  # Completed eco actions
    sustainability_score: int = 0
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None
    client_id: Optional[str] = None

class GuestEngagement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guest_name: str
    room_number: str
    eco_actions: List[str] = []
    sustainability_score: int = 0
    feedback_rating: Optional[int] = None
    feedback_comment: Optional[str] = None
    client_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Consumption Models
class Consumption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    year: int
    month: int  # 1-12
    electricity: float = 0.0  # kWh
    water: float = 0.0        # m³
    natural_gas: float = 0.0  # m³
    coal: float = 0.0         # kg
    # DEFRA Additional Fuel Types
    diesel: float = 0.0       # litre (mazot)
    gasoline: float = 0.0     # litre (benzin)
    lpg: float = 0.0          # litre (LPG)
    fuel_oil: float = 0.0     # litre (fuel oil)
    # DEFRA Refrigerant Gases (F-Gases) - Specific Types
    r134a_gas: float = 0.0   # kg (HFC-134a for Air Conditioning)
    r600a_gas: float = 0.0   # kg (Isobutane for Refrigerators)  
    r410a_gas: float = 0.0   # kg (HFC-410A for Modern AC)
    r32_gas: float = 0.0     # kg (HFC-32 for New Generation AC)
    # DEFRA Fire Suppressants
    co2_fire: float = 0.0    # kg (CO2 fire extinguishers)
    fm200_fire: float = 0.0  # kg (FM200/HFC-227ea fire suppressant)
    accommodation_count: int = 0  # Konaklama sayısı
    # Carbon footprint calculations (auto-calculated)
    total_co2_emissions: Optional[float] = None  # kg CO2
    total_co2_tonnes: Optional[float] = None     # tonnes CO2
    per_person_co2: Optional[float] = None       # kg CO2 per person
    carbon_benchmark: Optional[str] = None       # Performance level
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConsumptionInput(BaseModel):
    year: int
    month: int
    electricity: float = 0.0
    water: float = 0.0  
    natural_gas: float = 0.0
    coal: float = 0.0
    # DEFRA Additional Fuel Types
    diesel: float = 0.0       # litre (mazot)
    gasoline: float = 0.0     # litre (benzin)
    lpg: float = 0.0          # litre (LPG)
    fuel_oil: float = 0.0     # litre (fuel oil)
    # DEFRA Refrigerant Gases (F-Gases) - Specific Types
    r134a_gas: float = 0.0   # kg (HFC-134a for Air Conditioning)
    r600a_gas: float = 0.0   # kg (Isobutane for Refrigerators)  
    r410a_gas: float = 0.0   # kg (HFC-410A for Modern AC)
    r32_gas: float = 0.0     # kg (HFC-32 for New Generation AC)
    # DEFRA Fire Suppressants
    co2_fire: float = 0.0    # kg (CO2 fire extinguishers)
    fm200_fire: float = 0.0  # kg (FM200/HFC-227ea fire suppressant)
    accommodation_count: int = 0
    client_id: Optional[str] = None  # Optional for admin users

class Training(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    name: str  # Eğitimin Adı
    subject: str  # Konusu
    participant_count: int  # Katılımcı Sayısı
    trainer: str  # Eğitimi Kimin Vereceği
    training_date: datetime  # Tarih
    description: str  # Açıklama
    status: str = "planned"  # planned, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TrainingCreate(BaseModel):
    client_id: str
    name: str
    subject: str
    participant_count: int
    trainer: str
    training_date: datetime
    description: str

class TrainingUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    participant_count: Optional[int] = None
    trainer: Optional[str] = None
    training_date: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ClientCreate(BaseModel):
    name: str
    hotel_name: str
    contact_person: str
    email: str
    phone: str
    address: str

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    hotel_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    current_stage: Optional[ProjectStage] = None
    services_completed: Optional[List[ServiceType]] = None
    carbon_footprint: Optional[float] = None
    sustainability_score: Optional[int] = None

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    name: str
    document_type: DocumentType
    stage: ProjectStage
    file_path: Optional[str] = None  # For local/Supabase uploads
    file_id: Optional[str] = None    # For GridFS uploads
    filename: Optional[str] = None   # GridFS filename
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_by: str = "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Upload type flags
    gridfs_upload: Optional[bool] = False
    supabase_upload: Optional[bool] = False
    local_upload: Optional[bool] = False
    mock_upload: Optional[bool] = False
    # Folder structure
    folder_path: Optional[str] = None  # e.g., "Müşteri Adı SYS/Alt Klasör"
    folder_level: Optional[int] = 0    # 0=root, 1=level1, etc.

class Folder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    name: str
    parent_folder_id: Optional[str] = None  # For nested folders
    folder_path: str  # Full path: "Müşteri Adı SYS/Alt Klasör"
    level: int = 0    # 0=root, 1=level1, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentCreate(BaseModel):
    client_id: str
    name: str
    document_type: DocumentType
    stage: ProjectStage
    file_path: str
    file_size: Optional[int] = None

# Waste Management Models (Based on Consumption Structure)
class WasteManagement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    year: int
    month: int  # 1-12
    organic_waste: float = 0.0  # kg
    plastic_waste: float = 0.0  # kg
    glass_waste: float = 0.0    # kg
    paper_waste: float = 0.0    # kg
    metal_waste: float = 0.0    # kg
    electronic_waste: float = 0.0  # kg
    oil_waste: float = 0.0      # litre
    mixed_waste: float = 0.0    # kg
    accommodation_count: int = 1  # For per-person calculations
    # Calculated fields (simplified - removed cost calculations)
    total_waste: float = 0.0    # kg (calculated)
    recycling_rate: float = 0.0 # % (calculated)
    per_person_waste: float = 0.0  # kg per person (calculated)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WasteManagementInput(BaseModel):
    year: int
    month: int
    organic_waste: float = 0.0
    plastic_waste: float = 0.0
    glass_waste: float = 0.0
    paper_waste: float = 0.0
    metal_waste: float = 0.0
    electronic_waste: float = 0.0
    oil_waste: float = 0.0
    mixed_waste: float = 0.0
    accommodation_count: int = 1  # For per-person calculations
    client_id: Optional[str] = None  # For admin users

# Environment Management Models  
class EnvironmentData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    year: int
    month: int
    organic_waste: float = 0.0  # kg
    plastic_waste: float = 0.0  # kg
    glass_waste: float = 0.0  # kg
    paper_waste: float = 0.0  # kg
    metal_waste: float = 0.0  # kg
    electronic_waste: float = 0.0  # kg
    oil_waste: float = 0.0  # litre
    mixed_waste: float = 0.0  # kg
    total_waste: float = 0.0  # kg (calculated)
    recycling_rate: float = 0.0  # % (calculated)
    waste_cost: float = 0.0  # TL (calculated)
    recycling_income: float = 0.0  # TL (calculated)
    net_cost: float = 0.0  # TL (calculated)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EnvironmentInput(BaseModel):
    year: int
    month: int
    organic_waste: float = 0.0
    plastic_waste: float = 0.0
    glass_waste: float = 0.0
    paper_waste: float = 0.0
    metal_waste: float = 0.0
    electronic_waste: float = 0.0
    oil_waste: float = 0.0
    mixed_waste: float = 0.0
    client_id: Optional[str] = None

# 2FA Models
class TwoFACodeRequest(BaseModel):
    email: EmailStr

class TwoFAVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class TwoFACode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    code: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    attempts: int = 0
    verified: bool = False


# Authentication Functions
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        logging.info(f"🔍 TOKEN VERIFICATION START for token ending: ...{token[-10:]}")
        
        # Basic token format validation
        if not token or len(token.split('.')) != 3:
            logging.error(f"❌ Invalid token format: {len(token.split('.'))} segments")
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Get the signing key from Clerk with retry logic
        signing_key = None
        for attempt in range(3):  # Retry up to 3 times
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                logging.info(f"✅ Got signing key from Clerk (attempt {attempt + 1})")
                break
            except Exception as key_error:
                logging.warning(f"⚠️ Attempt {attempt + 1} failed to get signing key: {str(key_error)}")
                if attempt == 2:  # Last attempt
                    logging.error(f"❌ All attempts failed to get signing key")
                    raise HTTPException(status_code=401, detail="Invalid token: could not get signing key")
                import time
                time.sleep(0.1)  # Brief delay before retry
        
        # Decode and verify the token
        try:
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=None,  # Clerk doesn't use audience
                options={"verify_aud": False}
            )
            logging.info(f"✅ JWT decode successful for user: {payload.get('sub', 'unknown')}")
        except jwt.ExpiredSignatureError:
            logging.error("❌ Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            logging.error(f"❌ Invalid token during decode: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Validate payload has required fields
        if not payload.get('sub'):
            logging.error("❌ Token missing required 'sub' field")
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        return payload
        
    except HTTPException:
        # Re-raise HTTP exceptions (already logged)
        raise
    except Exception as e:
        logging.error(f"❌ Unexpected token verification error: {str(e)}")
        raise HTTPException(status_code=401, detail="Token verification failed")

async def get_current_user(payload: dict = Depends(verify_token)):
    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        logging.error("❌ Missing user ID in token payload")
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    logging.info(f"🔍 USER LOOKUP: Looking for user with Clerk ID: {clerk_user_id}")
    
    user = await db.users.find_one({"clerk_user_id": clerk_user_id})
    if not user:
        logging.warning(f"⚠️ User not found in database for clerk_user_id: {clerk_user_id}")
        
        # Extract user info from Clerk token
        user_email = payload.get("email")
        if not user_email:
            # Try alternative email fields
            email_addresses = payload.get("email_addresses", [])
            if email_addresses and isinstance(email_addresses, list) and len(email_addresses) > 0:
                user_email = email_addresses[0].get("email_address", "unknown@example.com")
            else:
                user_email = "unknown@example.com"
        
        # Try to build full name from available fields
        given_name = payload.get("given_name", "")
        family_name = payload.get("family_name", "")
        full_name = payload.get("name", "")
        
        if full_name:
            user_name = full_name
        elif given_name or family_name:
            user_name = f"{given_name} {family_name}".strip()
        else:
            user_name = user_email.split("@")[0].title()  # Use email prefix as name
        
        logging.info(f"👤 CREATING NEW USER - Name: '{user_name}', Email: '{user_email}'")
        
        # Create new user in database
        new_user = {
            "id": str(uuid.uuid4()),
            "clerk_user_id": clerk_user_id,
            "name": user_name,
            "email": user_email,
            "role": "client",  # Default role is CLIENT
            "client_id": "",  # Will be set later via client setup
            "created_at": datetime.utcnow()
        }
        
        await db.users.insert_one(new_user)
        user = new_user
        logging.info(f"✅ NEW USER CREATED: {user['id']} - {user['name']} ({user['email']})")
    else:
        logging.info(f"✅ USER FOUND: {user['id']} - {user['name']} ({user['email']}) - Role: {user['role']}")
    
    # Convert to User object
    return User(
        id=user["id"],
        clerk_user_id=user["clerk_user_id"],
        name=user["name"],
        email=user["email"],
        role=UserRole(user["role"]),
        client_id=user.get("client_id", ""),
        created_at=user["created_at"]
    )

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def verify_admin_token(token: str) -> str:
    """Admin token doğrulama - mevcut verify_token kullanır"""
    # Mevcut verify_token sistemini kullan - bu daha güvenli
    # WhatsApp API'ler için ayrı auth yapmak yerine mevcut sistemi kullanıyoruz
    return token  # Bu fonksiyon şimdilik placeholder - endpoint'de get_admin_user kullanacağız

def get_user_id_from_token(token: str) -> str:
    """Token'dan user ID al - placeholder fonksiyon"""
    # Bu fonksiyon da şimdilik placeholder - endpoint'de get_current_user kullanacağız
    return token

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Rota CRM Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Rota CRM Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
    return {
        "status": "healthy",
        "service": "Rota CRM Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Rota CRM Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }



@api_router.get("/whatsapp/status")
async def get_whatsapp_status(current_user: User = Depends(get_admin_user)):
    """WhatsApp bağlantı durumunu kontrol et"""
    try:
        if not whatsapp_service:
            return {"connected": False, "error": "WhatsApp servis mevcut değil"}
        
        status = await whatsapp_service.get_status()
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/whatsapp/qr")
async def get_whatsapp_qr(current_user: User = Depends(get_admin_user)):
    """WhatsApp QR kodu al"""
    try:
        if not whatsapp_service:
            return {"qr": None, "error": "WhatsApp servis mevcut değil"}
        
        qr_data = await whatsapp_service.get_qr_code()
        return qr_data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp QR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/whatsapp/send")
async def send_whatsapp_message(
    request: dict,
    current_user: User = Depends(get_admin_user)
):
    """Manuel WhatsApp mesajı gönder"""
    try:
        phone_number = request.get("phone_number")
        message = request.get("message")
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="Telefon numarası ve mesaj gerekli")
        
        if not whatsapp_service:
            raise HTTPException(status_code=503, detail="WhatsApp servis mevcut değil")
        
        result = await whatsapp_service.send_message(phone_number, message)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/whatsapp/test")
async def send_test_message(
    request: dict,
    current_user: User = Depends(get_admin_user)
):
    """Test mesajı gönder"""
    try:
        phone_number = request.get("phone_number")
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Telefon numarası gerekli")
        
        if not whatsapp_service:
            raise HTTPException(status_code=503, detail="WhatsApp servis mevcut değil")
        
        result = await whatsapp_service.send_test_message(phone_number)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/whatsapp/status")
async def get_whatsapp_status(current_user: User = Depends(get_admin_user)):
    """WhatsApp bağlantı durumunu kontrol et"""
    try:
        if not whatsapp_service:
            return {"connected": False, "error": "WhatsApp servis mevcut değil"}
        
        status = await whatsapp_service.get_status()
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/whatsapp/qr")
async def get_whatsapp_qr(current_user: User = Depends(get_admin_user)):
    """WhatsApp QR kodu al"""
    try:
        if not whatsapp_service:
            return {"qr": None, "error": "WhatsApp servis mevcut değil"}
        
        qr_data = await whatsapp_service.get_qr_code()
        return qr_data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp QR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/whatsapp/send")
async def send_whatsapp_message(
    request: dict,
    current_user: User = Depends(get_admin_user)
):
    """Manuel WhatsApp mesajı gönder"""
    try:
        phone_number = request.get("phone_number")
        message = request.get("message")
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="Telefon numarası ve mesaj gerekli")
        
        if not whatsapp_service:
            raise HTTPException(status_code=503, detail="WhatsApp servis mevcut değil")
        
        result = await whatsapp_service.send_message(phone_number, message)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/whatsapp/test")
async def send_test_message(
    request: dict,
    current_user: User = Depends(get_admin_user)
):
    """Test mesajı gönder"""
    try:
        phone_number = request.get("phone_number")
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Telefon numarası gerekli")
        
        if not whatsapp_service:
            raise HTTPException(status_code=503, detail="WhatsApp servis mevcut değil")
        
        result = await whatsapp_service.send_test_message(phone_number)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        if not whatsapp_service:
            return {"qr": None, "error": "WhatsApp servis mevcut değil"}
        
        qr_data = await whatsapp_service.get_qr_code()
        return qr_data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp QR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/whatsapp/send")
async def send_whatsapp_message(
    request: dict,
    current_user: User = Depends(get_admin_user)
):
    """Manuel WhatsApp mesajı gönder"""
    try:
        phone_number = request.get("phone_number")
        message = request.get("message")
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="Telefon numarası ve mesaj gerekli")
        
        if not whatsapp_service:
            raise HTTPException(status_code=503, detail="WhatsApp servis mevcut değil")
        
        result = await whatsapp_service.send_message(phone_number, message)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/whatsapp/test")
async def send_test_message(
    request: dict,
    current_user: User = Depends(get_admin_user)
):
    """Test mesajı gönder"""
    try:
        phone_number = request.get("phone_number")
        
        if not phone_number:
            raise HTTPException(status_code=400, detail="Telefon numarası gerekli")
        
        if not whatsapp_service:
            raise HTTPException(status_code=503, detail="WhatsApp servis mevcut değil")
        
        result = await whatsapp_service.send_test_message(phone_number)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WhatsApp test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def create_client_root_folder(client_id: str, client_name: str):
    """Create root folder and sub-folders for a new client"""
    try:
        root_folder_name = f"{client_name} SYS"
        
        # Check if root folder already exists
        existing_folder = await db.folders.find_one({
            "client_id": client_id,
            "level": 0
        })
        
        if existing_folder:
            logging.info(f"📁 Root folder already exists for client: {client_name}")
            # Check if sub-folders exist, if not create them
            await create_column_folders(client_id, existing_folder["id"], root_folder_name)
            return existing_folder
        
        # Create root folder
        root_folder = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "name": root_folder_name,
            "parent_folder_id": None,
            "folder_path": root_folder_name,
            "level": 0,
            "created_at": datetime.utcnow()
        }
        
        await db.folders.insert_one(root_folder)
        logging.info(f"📁 Created root folder: {root_folder_name}")
        
        # Create 4 column sub-folders automatically
        await create_column_folders(client_id, root_folder["id"], root_folder_name)
        
        return root_folder
        
    except Exception as e:
        logging.error(f"❌ Failed to create root folder: {str(e)}")
        return None

async def create_column_folders(client_id: str, root_folder_id: str, root_folder_path: str):
    """Create A, B, C, D column folders under root folder with their sub-folders"""
    try:
        # Define main columns and their sub-folders
        column_structure = {
            "A SÜTUNU": ["A1", "A2", "A3", "A4", "A5", "A7.1", "A7.2", "A7.3", "A7.4", "A8", "A9", "A10"],
            "B SÜTUNU": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
            "C SÜTUNU": ["C1", "C2", "C3", "C4"],
            "D SÜTUNU": ["D1", "D2", "D3"]
        }
        
        # Define Level 3 sub-folders for D column
        d_level3_structure = {
            "D1": ["D1.1", "D1.2", "D1.3", "D1.4"],
            "D2": ["D2.1", "D2.2", "D2.3", "D2.4", "D2.5", "D2.6"],
            "D3": ["D3.1", "D3.2", "D3.3", "D3.4", "D3.5", "D3.6"]
        }
        
        for column_name, sub_folders in column_structure.items():
            # Check if column folder already exists
            existing_column = await db.folders.find_one({
                "client_id": client_id,
                "parent_folder_id": root_folder_id,
                "name": column_name
            })
            
            column_folder_id = None
            
            if existing_column:
                logging.info(f"📁 Column folder already exists: {column_name}")
                column_folder_id = existing_column["id"]
            else:
                # Create column folder
                column_folder_id = str(uuid.uuid4())
                column_folder = {
                    "id": column_folder_id,
                    "client_id": client_id,
                    "name": column_name,
                    "parent_folder_id": root_folder_id,
                    "folder_path": f"{root_folder_path}/{column_name}",
                    "level": 1,
                    "created_at": datetime.utcnow()
                }
                
                await db.folders.insert_one(column_folder)
                logging.info(f"📁 Created column folder: {column_name}")
            
            # Create sub-folders for this column
            for sub_folder_name in sub_folders:
                # Check if sub-folder already exists
                existing_sub_folder = await db.folders.find_one({
                    "client_id": client_id,
                    "parent_folder_id": column_folder_id,
                    "name": sub_folder_name
                })
                
                if existing_sub_folder:
                    logging.info(f"📁 Sub-folder already exists: {sub_folder_name}")
                    
                    # Create Level 3 sub-folders for existing D column folders
                    if column_name == "D SÜTUNU" and sub_folder_name in d_level3_structure:
                        level3_folders = d_level3_structure[sub_folder_name]
                        for level3_folder_name in level3_folders:
                            # Check if Level 3 folder already exists
                            existing_level3_folder = await db.folders.find_one({
                                "client_id": client_id,
                                "parent_folder_id": existing_sub_folder["id"],
                                "name": level3_folder_name
                            })
                            
                            if existing_level3_folder:
                                logging.info(f"📁 Level 3 folder already exists: {level3_folder_name}")
                                continue
                            
                            # Create Level 3 folder
                            level3_folder = {
                                "id": str(uuid.uuid4()),
                                "client_id": client_id,
                                "name": level3_folder_name,
                                "parent_folder_id": existing_sub_folder["id"],
                                "folder_path": f"{root_folder_path}/{column_name}/{sub_folder_name}/{level3_folder_name}",
                                "level": 3,
                                "created_at": datetime.utcnow()
                            }
                            
                            await db.folders.insert_one(level3_folder)
                            logging.info(f"📁 Created Level 3 folder: {column_name}/{sub_folder_name}/{level3_folder_name}")
                    continue
                
                # Create sub-folder
                sub_folder = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "name": sub_folder_name,
                    "parent_folder_id": column_folder_id,
                    "folder_path": f"{root_folder_path}/{column_name}/{sub_folder_name}",
                    "level": 2,
                    "created_at": datetime.utcnow()
                }
                
                await db.folders.insert_one(sub_folder)
                logging.info(f"📁 Created sub-folder: {column_name}/{sub_folder_name}")
                
                # Create Level 3 sub-folders for D column folders
                if column_name == "D SÜTUNU" and sub_folder_name in d_level3_structure:
                    level3_folders = d_level3_structure[sub_folder_name]
                    for level3_folder_name in level3_folders:
                        # Check if Level 3 folder already exists
                        existing_level3_folder = await db.folders.find_one({
                            "client_id": client_id,
                            "parent_folder_id": sub_folder["id"],
                            "name": level3_folder_name
                        })
                        
                        if existing_level3_folder:
                            logging.info(f"📁 Level 3 folder already exists: {level3_folder_name}")
                            continue
                        
                        # Create Level 3 folder
                        level3_folder = {
                            "id": str(uuid.uuid4()),
                            "client_id": client_id,
                            "name": level3_folder_name,
                            "parent_folder_id": sub_folder["id"],
                            "folder_path": f"{root_folder_path}/{column_name}/{sub_folder_name}/{level3_folder_name}",
                            "level": 3,
                            "created_at": datetime.utcnow()
                        }
                        
                        await db.folders.insert_one(level3_folder)
                        logging.info(f"📁 Created Level 3 folder: {column_name}/{sub_folder_name}/{level3_folder_name}")
            
    except Exception as e:
        logging.error(f"❌ Failed to create column folders: {str(e)}")

async def get_client_access(current_user: User = Depends(get_current_user)):
    # Both admin and client can access, but with different permissions
    return current_user

async def update_existing_clients_with_subfolders():
    """Update existing clients to have sub-folders in their column folders"""
    try:
        # Get all clients
        clients = await db.clients.find({}).to_list(length=None)
        logging.info(f"📋 Found {len(clients)} existing clients to update")
        
        for client in clients:
            client_id = client["id"]
            client_name = client["name"]
            
            logging.info(f"🔄 Updating client: {client_name} ({client_id})")
            
            # Find the root folder for this client
            root_folder = await db.folders.find_one({
                "client_id": client_id,
                "level": 0
            })
            
            if not root_folder:
                logging.warning(f"⚠️ No root folder found for client {client_name}")
                continue
            
            # Find column folders
            column_folders = await db.folders.find({
                "client_id": client_id,
                "level": 1
            }).to_list(length=None)
            
            logging.info(f"📁 Found {len(column_folders)} column folders for {client_name}")
            
            # Create sub-folders for each column that doesn't have them
            column_structure = {
                "A SÜTUNU": ["A1", "A2", "A3", "A4", "A5", "A7.1", "A7.2", "A7.3", "A7.4", "A8", "A9", "A10"],
                "B SÜTUNU": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
                "C SÜTUNU": ["C1", "C2", "C3", "C4"],
                "D SÜTUNU": ["D1", "D2", "D3"]
            }
            
            for column_folder in column_folders:
                column_id = column_folder["id"]
                column_name = column_folder["name"]
                column_path = column_folder["folder_path"]
                
                if column_name in column_structure:
                    # Check if this column already has sub-folders
                    existing_subfolders = await db.folders.find({
                        "client_id": client_id,
                        "parent_folder_id": column_id,
                        "level": 2
                    }).to_list(length=None)
                    
                    if len(existing_subfolders) > 0:
                        logging.info(f"📁 Column {column_name} already has {len(existing_subfolders)} sub-folders, skipping")
                        continue
                    
                    # Create sub-folders for this column
                    sub_folders = column_structure[column_name]
                    for sub_folder_name in sub_folders:
                        sub_folder = {
                            "id": str(uuid.uuid4()),
                            "client_id": client_id,
                            "name": sub_folder_name,
                            "parent_folder_id": column_id,
                            "folder_path": f"{column_path}/{sub_folder_name}",
                            "level": 2,
                            "created_at": datetime.utcnow()
                        }
                        
                        await db.folders.insert_one(sub_folder)
                        logging.info(f"📁 Created sub-folder: {column_name}/{sub_folder_name}")
                    
                    logging.info(f"✅ Created {len(sub_folders)} sub-folders for {column_name}")
            
            logging.info(f"✅ Completed updating client: {client_name}")
        
        logging.info("🎉 All existing clients updated with sub-folders!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to update existing clients: {str(e)}")
        return False

# Routes
@api_router.get("/")
async def root():
    return {"message": "Sürdürülebilir Turizm Danışmanlık CRM Sistemi"}

# Authentication Routes
@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"clerk_user_id": user_data.clerk_user_id})
    
    if existing_user:
        # SECURITY FIX: Check if existing client user needs client_id linking
        if existing_user.get("role") == UserRole.CLIENT and not existing_user.get("client_id"):
            # Try to find matching client by email
            matching_client = await db.clients.find_one({"contact_person": existing_user.get("email")})
            if matching_client:
                # Update existing user with client_id
                await db.users.update_one(
                    {"clerk_user_id": user_data.clerk_user_id},
                    {"$set": {"client_id": matching_client["id"], "updated_at": datetime.utcnow()}}
                )
                existing_user["client_id"] = matching_client["id"]
                logging.info(f"🔗 Existing client user linked to client: {matching_client['name']} (ID: {matching_client['id']})")
            else:
                logging.warning(f"⚠️ Existing client user but no matching client found for email: {existing_user.get('email')}")
        
        return User(**existing_user)
    
    user_dict = user_data.dict()
    
    # SECURITY FIX: If registering as client, find matching client record by email
    if user_dict.get("role") == UserRole.CLIENT:
        # Try to find existing client by email
        matching_client = await db.clients.find_one({"contact_person": user_dict.get("email")})
        if matching_client:
            # Link this user to the existing client
            user_dict["client_id"] = matching_client["id"]
            logging.info(f"🔗 New client user linked to existing client: {matching_client['name']} (ID: {matching_client['id']})")
        else:
            # No matching client found - client_id remains None for manual admin assignment
            logging.warning(f"⚠️ New client user registered but no matching client found for email: {user_dict.get('email')}")
    
    user = User(**user_dict)
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.put("/auth/me", response_model=User)
async def update_current_user(
    user_update: dict,
    current_user: User = Depends(get_current_user)
):
    update_data = {k: v for k, v in user_update.items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.users.update_one(
        {"clerk_user_id": current_user.clerk_user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"clerk_user_id": current_user.clerk_user_id})
    return User(**updated_user)

# Client Management (Enhanced for self-registration)
@api_router.post("/clients", response_model=Client)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user)
):
    # Admin can create any client, client users can only create for themselves
    if current_user.role == UserRole.CLIENT and current_user.client_id:
        # If client user already has a client record, return the existing one
        existing_client = await db.clients.find_one({"id": current_user.client_id})
        if existing_client:
            return Client(**existing_client)
        else:
            # If client_id exists but no client record, remove client_id and continue
            await db.users.update_one(
                {"clerk_user_id": current_user.clerk_user_id},
                {"$unset": {"client_id": ""}, "$set": {"updated_at": datetime.utcnow()}}
            )
    
    client_dict = client_data.dict()
    client = Client(**client_dict)
    await db.clients.insert_one(client.dict())
    
    # Create root folder for the new client
    await create_client_root_folder(client.id, client.name)
    
    # If client user is creating their own record, update their user record
    if current_user.role == UserRole.CLIENT:
        await db.users.update_one(
            {"clerk_user_id": current_user.clerk_user_id},
            {"$set": {"client_id": client.id, "updated_at": datetime.utcnow()}}
        )
    
    return client

# Admin endpoint to fix user-client assignments
@api_router.post("/admin/assign-client-to-user")
async def assign_client_to_user(
    user_email: str,
    client_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Admin endpoint to manually assign client_id to a user"""
    try:
        # Find user by email
        user = await db.users.find_one({"email": user_email})
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_email}")
        
        # Verify client exists
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")
        
        # Update user with client_id
        result = await db.users.update_one(
            {"email": user_email},
            {"$set": {"client_id": client_id, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        logging.info(f"🔗 Admin assigned client {client['name']} to user {user_email}")
        
        return {
            "success": True,
            "message": f"User {user_email} assigned to client {client['name']}",
            "user_email": user_email,
            "client_id": client_id,
            "client_name": client['name']
        }
        
    except Exception as e:
        logging.error(f"❌ Error assigning client to user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user)):
    print(f"🚨🚨🚨 SECURITY CHECK: GET /clients called by user: {current_user.role} - {current_user.name} - client_id: {current_user.client_id}")
    logging.error(f"🚨🚨🚨 SECURITY CHECK: GET /clients called by user: {current_user.role} - {current_user.name} - client_id: {current_user.client_id}")
    
    if current_user.role == UserRole.ADMIN:
        clients = await db.clients.find().to_list(1000)
        print(f"🚨 ADMIN USER - returning {len(clients)} clients")
        logging.error(f"🚨 ADMIN USER - returning {len(clients)} clients")
        return [Client(**client) for client in clients]
    else:
        print(f"🚨 CLIENT USER DETECTED - APPLYING SECURITY FILTER")
        logging.error(f"🚨 CLIENT USER DETECTED - APPLYING SECURITY FILTER")
        
        # CLIENT SECURITY: Client users can ONLY see their own client data
        if not current_user.client_id:
            print(f"🚨🚨🚨 CLIENT USER WITHOUT CLIENT_ID: {current_user.name} - BLOCKING ACCESS")
            logging.error(f"🚨🚨🚨 CLIENT USER WITHOUT CLIENT_ID: {current_user.name} - BLOCKING ACCESS")
            raise HTTPException(status_code=403, detail="Client user not properly linked to a client")
        
        # Return only the client record for this specific user
        client = await db.clients.find_one({"id": current_user.client_id})
        if not client:
            print(f"🚨🚨🚨 CLIENT NOT FOUND: {current_user.client_id} for user {current_user.name}")
            logging.error(f"🚨🚨🚨 CLIENT NOT FOUND: {current_user.client_id} for user {current_user.name}")
            raise HTTPException(status_code=404, detail="Client record not found")
        
        print(f"🚨 CLIENT USER SECURITY APPLIED - returning ONLY their client: {client['name']}")
        logging.error(f"🚨 CLIENT USER SECURITY APPLIED - returning ONLY their client: {client['name']}")
        return [Client(**client)]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    logging.info(f"🔍 GET /clients/{client_id} called by user: {current_user.role}")
    
    if current_user.role == UserRole.CLIENT and current_user.client_id != client_id:
        raise HTTPException(status_code=403, detail="Access denied to this client")
    
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return Client(**client)

# ==========================
# CLIENT PHONE NUMBER MANAGEMENT
# ==========================

@api_router.post("/clients/{client_id}/phone")
async def update_client_phone(
    client_id: str,
    request: dict,
    current_user: User = Depends(get_admin_user)
):
    """Müşteri telefon numarasını güncelle (Admin only)"""
    try:
        phone_number = request.get("phone_number")
        if not phone_number:
            raise HTTPException(status_code=400, detail="Telefon numarası gerekli")
        
        # Telefon numarası formatını kontrol et
        clean_phone = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not clean_phone.startswith(("0", "+90", "90")):
            raise HTTPException(status_code=400, detail="Geçersiz Türk telefon numarası formatı")
        
        # Müşteriyi güncelle
        result = await db.clients.update_one(
            {"id": client_id},
            {"$set": {"phone_number": clean_phone, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Client not found")
        
        logging.info(f"✅ Client phone updated: {client_id} -> {clean_phone}")
        return {"message": "Telefon numarası güncellendi", "phone_number": clean_phone}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Client phone update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/clients/{client_id}/phone")
async def get_client_phone(
    client_id: str,
    current_user: User = Depends(get_current_user)
):
    """Müşteri telefon numarasını al"""
    try:
        # Client sadece kendi telefon numarasını görebilir
        if current_user.role == UserRole.CLIENT and current_user.client_id != client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return {"phone_number": client.get("phone_number", "")}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get client phone error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/update-subfolders")
async def update_existing_clients_subfolders(current_user: User = Depends(get_current_user)):
    """Admin-only endpoint to update existing clients with sub-folders"""
    logging.info(f"🔧 POST /admin/update-subfolders called by user: {current_user.role}")
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        success = await update_existing_clients_with_subfolders()
        if success:
            return {"message": "Successfully updated all existing clients with sub-folders", "success": True}
        else:
            return {"message": "Failed to update some clients", "success": False}
    except Exception as e:
        logging.error(f"❌ Error in update-subfolders endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(
    client_id: str,
    client_update: ClientUpdate,
    current_user: User = Depends(get_admin_user)
):
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.clients.update_one(
        {"id": client_id}, 
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    updated_client = await db.clients.find_one({"id": client_id})
    return Client(**updated_client)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: User = Depends(get_admin_user)):
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Document Management
@api_router.post("/documents", response_model=Document)
async def create_document(
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_user)
):
    # Check permissions based on role
    if current_user.role == UserRole.ADMIN:
        # Admin can upload documents for any client
        client = await db.clients.find_one({"id": document_data.client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    else:
        # Client users can only upload documents for themselves
        if current_user.client_id != document_data.client_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot upload documents for other clients")
        
        # Verify the client exists and belongs to this user
        client = await db.clients.find_one({"id": document_data.client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    
    document_dict = document_data.dict()
    document_dict["uploaded_by"] = current_user.clerk_user_id
    document = Document(**document_dict)
    await db.documents.insert_one(document.dict())
    return document

@api_router.get("/documents")
async def get_documents(current_user: User = Depends(get_current_user)):
    """Get documents for email management - CLIENT sees own docs, ADMIN sees all"""
    try:
        logging.info(f"📧 Email Management - GET /documents called by: {current_user.role} - {current_user.name}")
        
        if current_user.role == UserRole.CLIENT:
            # CLIENT users only see their own documents
            client_id = current_user.client_id
            if not client_id:
                logging.warning(f"⚠️ CLIENT user {current_user.name} has no client_id")
                return {"documents": []}
            
            documents_from_db = await db.documents.find({"client_id": client_id}).to_list(length=None)
            
            # Format documents for frontend with client info
            formatted_documents = []
            for doc in documents_from_db:
                if "_id" in doc:
                    del doc["_id"]
                
                formatted_doc = {
                    "id": doc.get("id", str(doc.get("_id", ""))),
                    "title": doc.get("name", doc.get("title", "Untitled Document")),
                    "type": "PDF",  # Default type
                    "category": doc.get("document_type", "General"),
                    "upload_date": doc.get("upload_date", datetime.utcnow().isoformat()),
                    "file_size": doc.get("file_size", "N/A"),
                    "file_path": doc.get("file_path", ""),
                    "client_id": doc.get("client_id", ""),
                    "client_name": current_user.hotel_name or current_user.name or "My Hotel"
                }
                formatted_documents.append(formatted_doc)
            
            logging.info(f"✅ CLIENT user - returning {len(formatted_documents)} own documents")
            return {"documents": formatted_documents}
            
        elif current_user.role == UserRole.ADMIN:
            # ADMIN users see all documents from database
            documents_from_db = await db.documents.find().to_list(length=None)
            
            # Format documents for frontend with client info
            formatted_documents = []
            for doc in documents_from_db:
                if "_id" in doc:
                    del doc["_id"]
                
                # Get client info
                client = await db.clients.find_one({"id": doc.get("client_id", "")})
                client_name = client.get("hotel_name", "Unknown Client") if client else "Unknown Client"
                
                formatted_doc = {
                    "id": doc.get("id", str(doc.get("_id", ""))),
                    "title": doc.get("name", doc.get("title", "Untitled Document")),
                    "type": "PDF",  # Default type
                    "category": doc.get("document_type", "General"),
                    "upload_date": doc.get("upload_date", datetime.utcnow().isoformat()),
                    "file_size": doc.get("file_size", "N/A"),
                    "file_path": doc.get("file_path", ""),
                    "client_id": doc.get("client_id", ""),
                    "client_name": client_name
                }
                formatted_documents.append(formatted_doc)
            
            # If no real documents found, return sample data with client info
            if not formatted_documents:
                documents = [
                    {
                        "id": 1,
                        "title": "Sürdürülebilirlik Rehberi 2025",
                        "type": "PDF",
                        "category": "Training Material",
                        "upload_date": datetime.utcnow().isoformat(),
                        "file_size": "2.5 MB",
                        "file_path": "/docs/sustainability_guide.pdf",
                        "client_id": "paradise-resort",
                        "client_name": "Paradise Resort & Spa"
                    },
                    {
                        "id": 2,
                        "title": "Çevre Politikası Dokümanı",
                        "type": "PDF", 
                        "category": "Policy Document",
                        "upload_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                        "file_size": "1.2 MB",
                        "file_path": "/docs/environment_policy.pdf",
                        "client_id": "green-valley",
                        "client_name": "Green Valley Hotel"
                    }
                ]
                logging.info(f"No real documents found, returning {len(documents)} sample documents")
                return {"documents": documents}
            
            logging.info(f"✅ ADMIN user - returning {len(formatted_documents)} real documents")
            return {"documents": formatted_documents}
        else:
            logging.warning(f"⚠️ Unknown user role: {current_user.role}")
            return {"documents": []}
    except Exception as e:
        logging.error(f"Error getting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/documents/{client_id}", response_model=List[Document])
async def get_client_documents(client_id: str, current_user: User = Depends(get_current_user)):
    """Get documents for a specific client"""
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can access any client's documents
        pass
    else:
        # Client can only access their own documents
        if current_user.client_id != client_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot view other clients' documents")
    
    documents = await db.documents.find({"client_id": client_id}).to_list(1000)
    return [Document(**doc) for doc in documents]

@api_router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: User = Depends(get_admin_user)):
    """Delete a document (Admin only)"""
    # Find the document first
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    result = await db.documents.delete_one({"id": document_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}

# Carbon Footprint Report Upload
@api_router.post("/carbon-report", response_model=Document)
async def upload_carbon_report(
    document_data: DocumentCreate,
    current_user: User = Depends(get_admin_user)
):
    """Upload carbon footprint report (Admin only)"""
    document_dict = document_data.dict()
    document_dict["uploaded_by"] = current_user.clerk_user_id
    document = Document(**document_dict)
    await db.documents.insert_one(document.dict())
    return document

@api_router.get("/carbon-reports/{client_id}", response_model=List[Document])
async def get_client_carbon_reports(client_id: str, current_user: User = Depends(get_current_user)):
    """Get carbon footprint reports for a client"""
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can access any client's carbon reports
        pass
    else:
        # Client can access their own carbon reports
        if current_user.client_id != client_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot view other clients' carbon reports")
    
    documents = await db.documents.find({
        "client_id": client_id, 
        "document_type": "Karbon Ayak İzi Raporu"
    }).to_list(1000)
    return [Document(**doc) for doc in documents]

# Training Management
@api_router.post("/trainings", response_model=Training)
async def create_training(
    training_data: TrainingCreate,
    current_user: User = Depends(get_admin_user)
):
    try:
        logging.info(f"📚 Creating training with data: {training_data}")
        
        # Check if admin can access this client
        client = await db.clients.find_one({"id": training_data.client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        training_dict = training_data.dict()
        training = Training(**training_dict)
        await db.trainings.insert_one(training.dict())
        
        # 📱 WhatsApp bildirimi gönder
        try:
            if whatsapp_service:
                # Müşteri telefon numarası kontrolü
                if client and client.get("phone_number"):
                    # WhatsApp bildirimi gönder
                    await whatsapp_service.send_training_notification(
                        customer_name=client.get("hotel_name", "Değerli Müşterimiz"),
                        customer_phone=client["phone_number"],
                        training_name=training_data.name,
                        participant_count=training_data.participant_count,
                        trainer=training_data.trainer,
                        training_date=training_data.training_date.strftime("%d.%m.%Y"),
                        description=training_data.description or ""
                    )
                    logging.info(f"📱 Eğitim WhatsApp bildirimi gönderildi: {client['hotel_name']}")
                else:
                    logging.warning(f"⚠️ Müşteri telefon numarası bulunamadı: {training_data.client_id}")
            else:
                logging.warning("⚠️ WhatsApp servisi aktif değil")
        except Exception as whatsapp_error:
            logging.error(f"❌ WhatsApp bildirimi hatası: {whatsapp_error}")
            # WhatsApp hatası training create işlemini etkilemesin
        
        return training
    except Exception as e:
        logging.error(f"❌ Error creating training: {str(e)}")
        logging.error(f"❌ Training data received: {training_data}")
        raise

@api_router.get("/trainings/{client_id}", response_model=List[Training])
async def get_client_trainings(client_id: str, current_user: User = Depends(get_client_access)):
    # Check permissions
    if current_user.role != UserRole.ADMIN and current_user.client_id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    trainings = await db.trainings.find({"client_id": client_id}).to_list(1000)
    return [Training(**training) for training in trainings]

@api_router.put("/trainings/{training_id}")
async def update_training_status(
    training_id: str,
    status: str,
    current_user: User = Depends(get_admin_user)
):
    result = await db.trainings.update_one(
        {"id": training_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Training not found")
    return {"message": "Training status updated"}

# Statistics (Role-based)
@api_router.get("/stats")
async def get_statistics(current_user: User = Depends(get_current_user)):
    try:
        if current_user.role == UserRole.ADMIN:
            # Admin sees all statistics
            total_clients = await db.clients.count_documents({})
            stage_1_clients = await db.clients.count_documents({"current_stage": "I.Aşama"})
            stage_2_clients = await db.clients.count_documents({"current_stage": "II.Aşama"})
            stage_3_clients = await db.clients.count_documents({"current_stage": "III.Aşama"})
            total_documents = await db.documents.count_documents({})
            total_trainings = await db.trainings.count_documents({})
            
            return {
                "total_clients": total_clients,
                "stage_distribution": {
                    "stage_1": stage_1_clients,
                    "stage_2": stage_2_clients,
                    "stage_3": stage_3_clients
                },
                "total_documents": total_documents,
                "total_trainings": total_trainings
            }
        else:
            # Client sees only their own statistics - document type distribution
            if not current_user.client_id:
                return {
                    "total_clients": 0,
                    "stage_distribution": {"stage_1": 0, "stage_2": 0, "stage_3": 0},
                    "total_documents": 0,
                    "total_trainings": 0,
                    "document_type_distribution": {
                        "TR1_CRITERIA": 0,
                        "STAGE_1_DOC": 0,
                        "STAGE_2_DOC": 0,
                        "STAGE_3_DOC": 0,
                        "CARBON_REPORT": 0,
                        "SUSTAINABILITY_REPORT": 0
                    }
                }
            
            client = await db.clients.find_one({"id": current_user.client_id})
            client_documents = await db.documents.count_documents({"client_id": current_user.client_id})
            client_trainings = await db.trainings.count_documents({"client_id": current_user.client_id})
            
            # Calculate document type distribution for client
            document_type_counts = {
                "TR1_CRITERIA": 0,
                "STAGE_1_DOC": 0,
                "STAGE_2_DOC": 0,
                "STAGE_3_DOC": 0,
                "CARBON_REPORT": 0,
                "SUSTAINABILITY_REPORT": 0
            }
            
            # Get all documents for this client and count by type
            documents = await db.documents.find({"client_id": current_user.client_id}).to_list(length=None)
            for doc in documents:
                doc_type = doc.get("document_type", "")
                if doc_type == "Türkiye Sürdürülebilir Turizm Programı Kriterleri (TR-I)":
                    document_type_counts["TR1_CRITERIA"] += 1
                elif doc_type == "I. Aşama Belgesi":
                    document_type_counts["STAGE_1_DOC"] += 1
                elif doc_type == "II. Aşama Belgesi":
                    document_type_counts["STAGE_2_DOC"] += 1
                elif doc_type == "III. Aşama Belgesi":
                    document_type_counts["STAGE_3_DOC"] += 1
                elif doc_type == "Karbon Ayak İzi Raporu":
                    document_type_counts["CARBON_REPORT"] += 1
                elif doc_type == "Sürdürülebilirlik Raporu":
                    document_type_counts["SUSTAINABILITY_REPORT"] += 1
            
            current_stage = client.get("current_stage", "I.Aşama") if client else "I.Aşama"
            stage_distribution = {"stage_1": 0, "stage_2": 0, "stage_3": 0}
            
            if current_stage == "I.Aşama":
                stage_distribution["stage_1"] = 1
            elif current_stage == "II.Aşama":
                stage_distribution["stage_2"] = 1
            elif current_stage == "III.Aşama":
                stage_distribution["stage_3"] = 1
            
            return {
                "total_clients": 1,
                "stage_distribution": stage_distribution,
                "total_documents": client_documents,
                "total_trainings": client_trainings,
                "document_type_distribution": document_type_counts
            }
    except Exception as e:
        logging.error(f"Error in get_statistics: {str(e)}")
        return {
            "total_clients": 0,
            "stage_distribution": {"stage_1": 0, "stage_2": 0, "stage_3": 0},
            "total_documents": 0,
            "total_trainings": 0
        }

# File Upload Endpoints with Google Cloud Storage
@api_router.post("/upload-document")
async def upload_document(
    client_id: str = Form(...),
    document_name: str = Form(...),
    document_type: DocumentType = Form(...),
    stage: ProjectStage = Form(...),
    file: UploadFile = File(...),
    folder_id: str = Form(...),  # Required folder selection
    current_user: User = Depends(get_admin_user)  # Only admin can upload
):
    """Upload document file to local storage and save metadata to database (Admin only)"""
    
    logging.info(f"📤 Upload document request - Admin: {current_user.name} - Client: {client_id} - Folder: {folder_id} - File: {file.filename}")
    
    # Check file size (500MB limit)
    if file.size and file.size > 500 * 1024 * 1024:  # 500MB
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 500MB.")
    
    logging.info(f"📦 File size: {file.size / 1024 / 1024:.2f}MB")
    
    # Verify folder exists and belongs to the specified client
    folder = await db.folders.find_one({"id": folder_id, "client_id": client_id})
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found or doesn't belong to specified client")
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can upload documents for any client
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    else:
        # Client users can only upload documents for themselves
        if current_user.client_id != client_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot upload documents for other clients")
        
        # Verify the client exists and belongs to this user
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to MongoDB GridFS (Primary choice)
        if mongo_gridfs and mongo_gridfs.fs:
            logging.info("📤 Using MongoDB GridFS for upload")
            
            try:
                # Create metadata for the file
                file_metadata = {
                    "client_id": client_id,
                    "document_name": document_name,
                    "document_type": document_type,
                    "stage": stage,
                    "uploaded_by": current_user.clerk_user_id
                }
                
                upload_result = await mongo_gridfs.upload_file(
                    file_content=file_content,
                    filename=file.filename,
                    user_id=current_user.clerk_user_id,
                    content_type=file.content_type or "application/octet-stream",
                    metadata=file_metadata
                )
                
                logging.info(f"✅ GridFS upload successful: {upload_result}")
                
                # Create document record in database
                document_data = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "name": document_name,
                    "document_type": document_type,
                    "stage": stage,
                    "file_id": upload_result["file_id"],  # GridFS file ID
                    "filename": upload_result["filename"],
                    "original_filename": upload_result["original_filename"],
                    "file_size": upload_result["file_size"],
                    "uploaded_by": current_user.clerk_user_id,
                    "created_at": datetime.utcnow(),
                    "gridfs_upload": True,
                    "folder_id": folder_id,
                    "folder_path": folder["folder_path"],
                    "folder_level": folder["level"]
                }
                
                await db.documents.insert_one(document_data)
                logging.info(f"✅ Document metadata saved: {document_data['id']}")
                
                # 📱 WhatsApp bildirimi gönder
                try:
                    if whatsapp_service:
                        # Müşteri bilgilerini al
                        client = await db.clients.find_one({"id": client_id})
                        if client and client.get("phone_number"):
                            # WhatsApp bildirimi gönder
                            await whatsapp_service.send_document_notification(
                                customer_name=client.get("hotel_name", "Değerli Müşterimiz"),
                                customer_phone=client["phone_number"],
                                document_name=document_name,
                                folder_name=folder["name"],
                                description=f"{document_type} - {stage}"
                            )
                            logging.info(f"📱 WhatsApp bildirimi gönderildi: {client['hotel_name']}")
                        else:
                            logging.warning(f"⚠️ Müşteri telefon numarası bulunamadı: {client_id}")
                    else:
                        logging.warning("⚠️ WhatsApp servisi aktif değil")
                except Exception as whatsapp_error:
                    logging.error(f"❌ WhatsApp bildirimi hatası: {whatsapp_error}")
                    # WhatsApp hatası upload işlemini etkilemesin
                
                return {
                    "message": "Document uploaded successfully to MongoDB GridFS ✅",
                    "document_id": document_data["id"],
                    "file_id": upload_result["file_id"],
                    "file_size": upload_result["file_size"],
                    "gridfs_upload": True,
                    "storage": "MongoDB GridFS"
                }
                
            except Exception as gridfs_error:
                logging.error(f"❌ GridFS upload failed: {gridfs_error}")
                # Fall through to next option
        
        # Backup: Upload to Supabase Storage
        elif supabase_storage and supabase_storage.client:
            logging.info("📤 Using Supabase Storage for upload (backup)")
            
            upload_result = await supabase_storage.upload_file(
                file_content=file_content,
                filename=file.filename,
                user_id=current_user.clerk_user_id,
                content_type=file.content_type or "application/octet-stream"
            )
            
            # Create document record in database
            document_data = {
                "id": str(uuid.uuid4()),
                "client_id": client_id,
                "name": document_name,
                "document_type": document_type,
                "stage": stage,
                "file_path": upload_result["file_path"],
                "original_filename": upload_result["original_filename"],
                "file_size": upload_result["file_size"],
                "uploaded_by": current_user.clerk_user_id,
                "created_at": datetime.utcnow(),
                "supabase_upload": True
            }
            
            await db.documents.insert_one(document_data)
            
            # 📱 WhatsApp bildirimi gönder
            try:
                if whatsapp_service:
                    # Müşteri bilgilerini al
                    client = await db.clients.find_one({"id": client_id})
                    if client and client.get("phone_number"):
                        # WhatsApp bildirimi gönder
                        await whatsapp_service.send_document_notification(
                            customer_name=client.get("hotel_name", "Değerli Müşterimiz"),
                            customer_phone=client["phone_number"],
                            document_name=document_name,
                            folder_name=folder["name"],
                            description=f"{document_type} - {stage}"
                        )
                        logging.info(f"📱 WhatsApp bildirimi gönderildi: {client['hotel_name']}")
                    else:
                        logging.warning(f"⚠️ Müşteri telefon numarası bulunamadı: {client_id}")
                else:
                    logging.warning("⚠️ WhatsApp servisi aktif değil")
            except Exception as whatsapp_error:
                logging.error(f"❌ WhatsApp bildirimi hatası: {whatsapp_error}")
                # WhatsApp hatası upload işlemini etkilemesin
            
            return {
                "message": "Document uploaded successfully to Supabase",
                "document_id": document_data["id"],
                "file_size": upload_result["file_size"],
                "supabase_upload": True
            }
        
        else:
            # Fallback to local storage
            logging.warning("⚠️ GridFS and Supabase not available, using local storage")
            
            uploads_dir = "/app/backend/uploads"
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            local_filename = f"{file_id}{file_extension}"
            local_path = os.path.join(uploads_dir, local_filename)
            
            # Save file
            with open(local_path, "wb") as f:
                f.write(file_content)
            
            logging.info(f"📁 File saved locally: {local_path}")
            
            # Create document record in database
            document_data = {
                "id": str(uuid.uuid4()),
                "client_id": client_id,
                "name": document_name,
                "document_type": document_type,
                "stage": stage,
                "file_path": local_path,
                "original_filename": file.filename,
                "file_size": len(file_content),
                "uploaded_by": current_user.clerk_user_id,
                "created_at": datetime.utcnow(),
                "local_upload": True,
                "folder_id": folder_id,
                "folder_path": folder["folder_path"],
                "folder_level": folder["level"]
            }
            
            await db.documents.insert_one(document_data)
            
            # 📱 WhatsApp bildirimi gönder
            try:
                if whatsapp_service:
                    # Müşteri bilgilerini al
                    client = await db.clients.find_one({"id": client_id})
                    if client and client.get("phone_number"):
                        # WhatsApp bildirimi gönder
                        await whatsapp_service.send_document_notification(
                            customer_name=client.get("hotel_name", "Değerli Müşterimiz"),
                            customer_phone=client["phone_number"],
                            document_name=document_name,
                            folder_name=folder["name"],
                            description=f"{document_type} - {stage}"
                        )
                        logging.info(f"📱 WhatsApp bildirimi gönderildi: {client['hotel_name']}")
                    else:
                        logging.warning(f"⚠️ Müşteri telefon numarası bulunamadı: {client_id}")
                else:
                    logging.warning("⚠️ WhatsApp servisi aktif değil")
            except Exception as whatsapp_error:
                logging.error(f"❌ WhatsApp bildirimi hatası: {whatsapp_error}")
                # WhatsApp hatası upload işlemini etkilemesin
            
            return {
                "message": f"✅ {file.filename} başarıyla yüklendi! (Yerel Depolama - {len(file_content)} bytes)",
                "document_id": document_data["id"],
                "file_size": len(file_content),
                "local_upload": True
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@api_router.delete("/documents/{document_id}/file")
async def delete_document_file(
    document_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Delete document file from Google Cloud Storage and remove database record"""
    
    # Find the document
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete file from Google Cloud Storage
        if not document.get("mock_upload", False):
            await gcs_service.delete_file(document["file_path"])
        
        # Remove document record from database
        result = await db.documents.delete_one({"id": document_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")

@api_router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get download URL for document (signed URL for private files)"""
    
    logging.info(f"📥 Download request for document: {document_id}")
    
    # Find the document
    document = await db.documents.find_one({"id": document_id})
    if not document:
        logging.error(f"❌ Document not found: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    logging.info(f"📄 Found document: {document.get('name', 'Unknown')}")
    logging.info(f"🔗 Current file_url in DB: {document.get('file_url', 'No URL')}")
    logging.info(f"📁 File path: {document.get('file_path', 'No path')}")
    logging.info(f"🎭 Mock upload: {document.get('mock_upload', False)}")
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can access any document
        pass
    else:
        # Client can only access their own documents
        if current_user.client_id != document["client_id"]:
            raise HTTPException(status_code=403, detail="Access denied: Cannot access other clients' documents")
    
    try:
        # Check if it's a GridFS upload (Primary)
        if document.get("gridfs_upload", False):
            # MongoDB GridFS file download
            if mongo_gridfs and mongo_gridfs.fs:
                logging.info(f"📥 Downloading from MongoDB GridFS: {document.get('file_id')}")
                
                file_content, metadata = await mongo_gridfs.download_file(document.get("file_id"))
                
                from fastapi.responses import Response
                return Response(
                    content=file_content,
                    media_type=metadata.get('content_type', 'application/octet-stream'),
                    headers={
                        "Content-Disposition": f"attachment; filename=\"{metadata.get('original_filename', document.get('name', 'download'))}\""
                    }
                )
            else:
                logging.error("❌ MongoDB GridFS client not available")
                raise HTTPException(status_code=500, detail="Storage service not available")
        
        # Check if it's a Supabase upload (Backup)
        elif document.get("supabase_upload", False):
            # Supabase file download
            if supabase_storage and supabase_storage.client:
                logging.info(f"📥 Downloading from Supabase: {document.get('file_path')}")
                
                file_content = await supabase_storage.download_file(document.get("file_path"))
                
                from fastapi.responses import Response
                return Response(
                    content=file_content,
                    media_type='application/octet-stream',
                    headers={
                        "Content-Disposition": f"attachment; filename=\"{document.get('original_filename', document.get('name', 'download'))}\""
                    }
                )
            else:
                logging.error("❌ Supabase client not available")
                raise HTTPException(status_code=500, detail="Storage service not available")
        
        # Check if it's a local upload (Fallback)
        elif document.get("local_upload", False):
            # Local file download
            import os
            from fastapi.responses import FileResponse
            
            file_path = document.get("file_path")
            if file_path and os.path.exists(file_path):
                logging.info(f"📁 Serving local file: {file_path}")
                return FileResponse(
                    path=file_path,
                    filename=document.get("original_filename", document.get("name", "download")),
                    media_type='application/octet-stream'
                )
            else:
                logging.error(f"❌ Local file not found: {file_path}")
                raise HTTPException(status_code=404, detail="File not found on server")
        
        # GCS fallback (existing logic)
        elif document.get("mock_upload", False) or not gcs_service or not gcs_service.client:
            # For mock uploads or when GCS is not available
            file_url = document.get("file_url", "")
            
            if file_url and file_url.startswith("https://storage.googleapis.com/"):
                # This is a mock upload, create a downloadable file
                logging.info(f"🎭 Mock upload detected, creating downloadable file")
                
                # Create a simple text content for the document
                file_content = f"""
=== DOSYA BİLGİLERİ ===

Dosya Adı: {document.get("name", "Bilinmeyen Dosya")}
Dosya Boyutu: {document.get("file_size", 0)} bytes
Yükleme Tarihi: {document.get("created_at", "Bilinmeyen")}
Müşteri: {document.get("client_id", "Bilinmeyen")}

=== UYARI ===
Bu demo bir dosyadır. Gerçek dosya Google Cloud Storage'da saklanacaktır.

Orijinal URL: {file_url}

=== ROTA KALİTE DANIŞMANLIK ===
Sürdürülebilir Turizm CRM Sistemi
"""
                
                # Create downloadable response
                from io import BytesIO
                import base64
                
                content_bytes = file_content.encode('utf-8')
                content_b64 = base64.b64encode(content_bytes).decode('utf-8')
                
                # Use text/plain instead of data URL to avoid navigation issues
                download_url = f"data:text/plain;charset=utf-8;base64,{content_b64}"
                
                # Better: create a blob URL that can be downloaded
                logging.info(f"🎭 Created downloadable content for: {document.get('name')}")
            else:
                # Use stored URL directly if available
                download_url = file_url or "#"
                logging.info(f"🔗 Using stored URL: {download_url}")
                
        else:
            # Generate signed URL for real GCS files
            try:
                download_url = await gcs_service.get_signed_url(document["file_path"], expiration_hours=24)
                logging.info(f"🔐 Generated signed URL: {download_url[:100]}...")
            except Exception as gcs_error:
                if "File not found" in str(gcs_error) or "NoSuchKey" in str(gcs_error):
                    logging.error(f"📁 File not found in GCS: {document['file_path']}")
                    # Create fallback placeholder for missing files
                    html_content = f'''
                    <!DOCTYPE html>
                    <html>
                    <head><title>Dosya Bulunamadı</title></head>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h1>❌ Dosya Bulunamadı</h1>
                        <p>Aradığınız dosya bulunamadı: <strong>{document.get("name", "Unknown")}</strong></p>
                        <p>Dosya yolu: {document.get("file_path", "Unknown")}</p>
                        <hr>
                        <p>Lütfen dosyanın mevcut olduğundan emin olun.</p>
                    </body>
                    </html>
                    '''
                    import base64
                    encoded_html = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
                    download_url = f"data:text/html;base64,{encoded_html}"
                    logging.info(f"🔄 Created fallback placeholder for missing file")
                else:
                    logging.error(f"🚨 GCS error: {str(gcs_error)}")
                    raise HTTPException(status_code=500, detail=f"Storage access error: {str(gcs_error)}")
        
        final_response = {
            "download_url": download_url,
            "filename": document["name"],
            "file_size": document.get("file_size", 0),
            "document_type": document["document_type"]
        }
        
        logging.info(f"✅ Returning download response for: {final_response['filename']}")
        return final_response
        
    except Exception as e:
        logging.error(f"❌ Download URL generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

# Chunked Upload Endpoints - DEACTIVATED (Using simple upload instead)
# @api_router.post("/upload-chunk")
# async def upload_chunk(
#     file_chunk: UploadFile = File(...),
#     chunk_index: int = Form(...),
#     total_chunks: int = Form(...),
#     upload_id: str = Form(...),
#     original_filename: str = Form(...),
#     client_id: Optional[str] = Form(None),
#     name: Optional[str] = Form(None),
#     document_type: Optional[str] = Form(None),
#     stage: Optional[str] = Form(None),
#     current_user: User = Depends(get_current_user)
# ):
#     """Upload a file chunk"""
#     try:
#         logging.info(f"📦 Chunk upload: {chunk_index + 1}/{total_chunks} for upload_id: {upload_id}")
#         
#         # Create temp directory for chunks if not exists
#         import tempfile
#         temp_dir = f"/tmp/chunks_{upload_id}"
#         os.makedirs(temp_dir, exist_ok=True)
#         
#         # Save chunk to temporary file
#         chunk_path = f"{temp_dir}/chunk_{chunk_index:04d}"
#         with open(chunk_path, "wb") as chunk_file:
#             content = await file_chunk.read()
#             chunk_file.write(content)
#         
#         logging.info(f"✅ Chunk {chunk_index + 1} saved: {len(content)} bytes")
#         
#         # Store chunk metadata in database for tracking
#         chunk_record = {
#             "upload_id": upload_id,
#             "chunk_index": chunk_index,
#             "chunk_path": chunk_path,
#             "chunk_size": len(content),
#             "uploaded_at": datetime.utcnow(),
#             "original_filename": original_filename,
#             "client_id": client_id,
#             "document_name": name,
#             "document_type": document_type,
#             "stage": stage if chunk_index == 0 else None  # Only store metadata in first chunk
#         }
#         
#         await db.upload_chunks.insert_one(chunk_record)
#         
#         return {
#             "message": f"Chunk {chunk_index + 1}/{total_chunks} uploaded successfully",
#             "upload_id": upload_id,
#             "chunk_index": chunk_index
#         }
#         
#     except Exception as e:
#         logging.error(f"❌ Chunk upload failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Chunk upload failed: {str(e)}")

# @api_router.post("/finalize-upload")
# async def finalize_upload(
#     upload_data: dict,
#     current_user: User = Depends(get_current_user)
# ):
#     """Finalize chunked upload by combining chunks"""
#     try:
#         upload_id = upload_data.get("upload_id")
#         total_chunks = upload_data.get("total_chunks")
#         filename = upload_data.get("filename")
#         file_size = upload_data.get("file_size")
#         
#         logging.info(f"🔗 Finalizing upload: {upload_id} with {total_chunks} chunks")
#         
#         # Get all chunks for this upload
#         chunks = await db.upload_chunks.find({
#             "upload_id": upload_id
#         }).sort("chunk_index", 1).to_list(length=total_chunks)
#         
#         if len(chunks) != total_chunks:
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Missing chunks: expected {total_chunks}, got {len(chunks)}"
#             )
#         
#         # Combine chunks into final file
#         temp_dir = f"/tmp/chunks_{upload_id}"
#         final_file_path = f"/tmp/final_{upload_id}_{filename}"
#         
#         with open(final_file_path, "wb") as final_file:
#             for chunk in chunks:
#                 chunk_path = chunk["chunk_path"]
#                 with open(chunk_path, "rb") as chunk_file:
#                     final_file.write(chunk_file.read())
#         
#         # Save final file to local storage instead of GCS
#         uploads_dir = "/app/backend/uploads"
#         os.makedirs(uploads_dir, exist_ok=True)
#         
#         # Generate unique filename for local storage
#         file_id = str(uuid.uuid4())
#         file_extension = os.path.splitext(filename)[1] if '.' in filename else ''
#         local_filename = f"{file_id}{file_extension}"
#         local_final_path = os.path.join(uploads_dir, local_filename)
#         
#         # Move temp file to uploads directory
#         shutil.move(final_file_path, local_final_path)
#         
#         logging.info(f"📁 Chunked file saved to local storage: {local_final_path}")
#         
#         # ⭐ CREATE DOCUMENT RECORD IN DATABASE
#         # Get metadata from first chunk if available
#         first_chunk = chunks[0] if chunks else {}
#         client_id = first_chunk.get("client_id", "")
#         document_name = first_chunk.get("document_name", filename)
#         document_type = first_chunk.get("document_type", "")
#         stage = first_chunk.get("stage", "")
#         
#         # Create document record
#         document_data = {
#             "id": str(uuid.uuid4()),
#             "client_id": client_id,
#             "document_name": document_name,
#             "document_type": document_type,
#             "stage": stage,
#             "file_path": local_final_path,
#             "file_size": file_size,
#             "original_filename": filename,
#             "upload_date": datetime.utcnow(),
#             "upload_method": "chunked"
#         }
#         
#         # Save document to database
#         await db.documents.insert_one(document_data)
#         logging.info(f"📄 Document record created in database: {document_data['id']}")
#         
#         upload_result = {
#             "file_path": local_final_path,
#             "file_size": file_size,
#             "local_upload": True,
#             "document_id": document_data["id"]
#         }
#         
#         # Cleanup temp files
#         shutil.rmtree(temp_dir, ignore_errors=True)
#         
#         # Remove chunk records
#         await db.upload_chunks.delete_many({"upload_id": upload_id})
#         
#         logging.info(f"✅ Chunked upload finalized: {local_final_path}")
#         
#         return {
#             "message": f"✅ {filename} başarıyla yüklendi! (Yerel Depolama - {file_size} bytes)",
#             "document_id": document_data["id"],
#             "file_path": local_final_path,
#             "file_size": file_size,
#             "upload_id": upload_id,
#             "local_upload": True,
#             "storage": "Yerel Depolama"
#         }
#         
#     except Exception as e:
#         logging.error(f"❌ Upload finalization failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Upload finalization failed: {str(e)}")

# Folder Management Endpoints
@api_router.get("/folders")
async def get_folders(current_user: User = Depends(get_current_user)):
    """Get folder tree for current user"""
    try:
        if current_user.role == UserRole.ADMIN:
            # Admin sees all folders
            folders = await db.folders.find({}).to_list(length=None)
        else:
            # Client sees only their own folders
            folders = await db.folders.find({"client_id": current_user.client_id}).to_list(length=None)
        
        # Convert MongoDB documents to JSON-serializable format
        serialized_folders = []
        for folder in folders:
            # Remove MongoDB-specific fields and convert to dict
            folder_dict = {
                "id": folder.get("id"),
                "client_id": folder.get("client_id"),
                "name": folder.get("name"),
                "parent_folder_id": folder.get("parent_folder_id"),
                "folder_path": folder.get("folder_path"),
                "level": folder.get("level", 0),
                "created_at": folder.get("created_at").isoformat() if folder.get("created_at") else None
            }
            serialized_folders.append(folder_dict)
        
        # Sort by level and name
        serialized_folders.sort(key=lambda x: (x.get("level", 0), x.get("name", "")))
        
        return serialized_folders
    except Exception as e:
        logging.error(f"❌ Error fetching folders: {str(e)}")
        return []

@api_router.post("/folders")
async def create_folder(
    folder_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new folder"""
    try:
        # Extract data
        folder_name = folder_data.get("name", "")
        parent_folder_id = folder_data.get("parent_folder_id")
        client_id = folder_data.get("client_id", current_user.client_id)
        
        # Validate permissions
        if current_user.role == UserRole.CLIENT and client_id != current_user.client_id:
            raise HTTPException(status_code=403, detail="Can only create folders for your own client")
        
        # Build folder path
        if parent_folder_id:
            parent_folder = await db.folders.find_one({"id": parent_folder_id})
            if not parent_folder:
                raise HTTPException(status_code=404, detail="Parent folder not found")
            folder_path = f"{parent_folder['folder_path']}/{folder_name}"
            level = parent_folder.get("level", 0) + 1
        else:
            # Root level folder
            client = await db.clients.find_one({"id": client_id})
            client_name = client.get("name", "Unknown") if client else "Unknown"
            folder_path = f"{client_name} SYS"
            level = 0
        
        # Create folder
        folder = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "name": folder_name,
            "parent_folder_id": parent_folder_id,
            "folder_path": folder_path,
            "level": level,
            "created_at": datetime.utcnow()
        }
        
        await db.folders.insert_one(folder)
        logging.info(f"📁 Created folder: {folder_path}")
        
        return folder
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Error creating folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

# Consumption Management Endpoints
@api_router.post("/consumptions")
async def create_consumption(
    consumption_data: ConsumptionInput,
    current_user: User = Depends(get_current_user)
):
    """Create monthly consumption record"""
    
    logging.info(f"🔍 POST /consumptions called by user: {current_user.role} - {current_user.name} - client_id: {current_user.client_id}")
    
    # Check permissions - only admin can create for any client, client can create for themselves
    if current_user.role == UserRole.ADMIN:
        # Admin can specify client_id in request body
        if consumption_data.client_id:
            client_id = consumption_data.client_id
        else:
            # If no client_id specified, use admin's assigned client (backward compatibility)
            client_id = current_user.client_id
            if not client_id:
                raise HTTPException(status_code=400, detail="Admin must specify client_id")
    else:
        # Client users can only create for themselves
        if not current_user.client_id:
            raise HTTPException(status_code=400, detail="Client not assigned to user")
        client_id = current_user.client_id
    
    # Check if consumption already exists for this month/year
    existing = await db.consumptions.find_one({
        "client_id": client_id,
        "year": consumption_data.year,
        "month": consumption_data.month
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Bu ay için tüketim verisi zaten mevcut. Güncelleme yapın.")
    
    # Create consumption record
    consumption_dict = {
        "client_id": client_id,
        "year": consumption_data.year,
        "month": consumption_data.month,
        "electricity": consumption_data.electricity,
        "water": consumption_data.water,
        "natural_gas": consumption_data.natural_gas,
        "coal": consumption_data.coal,
        # DEFRA Additional Fuel Types
        "diesel": consumption_data.diesel,
        "gasoline": consumption_data.gasoline,
        "lpg": consumption_data.lpg,
        "fuel_oil": consumption_data.fuel_oil,
        # DEFRA Refrigerant Gases (F-Gases)
        "r134a_gas": consumption_data.r134a_gas,
        "r600a_gas": consumption_data.r600a_gas,
        "r410a_gas": consumption_data.r410a_gas,
        "r32_gas": consumption_data.r32_gas,
        # DEFRA Fire Suppressants
        "co2_fire": consumption_data.co2_fire,
        "fm200_fire": consumption_data.fm200_fire,
        "accommodation_count": consumption_data.accommodation_count
    }
    
    # Calculate carbon emissions using DEFRA factors
    carbon_data = {}
    if calculate_carbon_emissions:
        try:
            carbon_results = calculate_carbon_emissions(consumption_dict)
            carbon_data = {
                "total_co2_emissions": carbon_results.get("total_co2_emissions"),
                "total_co2_tonnes": carbon_results.get("total_co2_tonnes"),
                "per_person_co2": carbon_results.get("per_person_co2")
            }
            
            # Add benchmark analysis
            if consumption_data.accommodation_count > 0:
                benchmark = benchmark_performance(
                    carbon_results.get("total_co2_emissions", 0),
                    consumption_data.accommodation_count
                )
                carbon_data["carbon_benchmark"] = benchmark.get("performance_level")
            
            logging.info(f"🌍 Carbon calculation successful: {carbon_results.get('total_co2_emissions', 0)} kg CO2")
        except Exception as e:
            logging.warning(f"⚠️ Carbon calculation failed: {e}")
    
    # Create consumption record with carbon data
    consumption = Consumption(
        **consumption_dict,
        **carbon_data
    )
    
    await db.consumptions.insert_one(consumption.dict())
    
    return {"message": "Tüketim verisi başarıyla kaydedildi", "consumption_id": consumption.id}

@api_router.get("/consumptions")
async def get_consumptions(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get consumption records for client"""
    
    logging.info(f"🔍 GET /consumptions called by user: {current_user.role} - client_id param: {client_id}")
    
    # Get client_id based on user role
    if current_user.role == UserRole.ADMIN:
        # Admin can specify client_id or see all data
        if client_id:
            target_client_id = client_id
        else:
            # If no client_id specified, use admin's assigned client (backward compatibility)
            target_client_id = current_user.client_id
    else:
        # Client users can only see their own consumptions
        if not current_user.client_id:
            raise HTTPException(status_code=400, detail="Client not assigned to user")
        target_client_id = current_user.client_id
    
    logging.info(f"📊 Fetching consumptions for client_id: {target_client_id}")
    
    # Build filter
    filter_query = {}
    if target_client_id:
        filter_query["client_id"] = target_client_id
    if year:
        filter_query["year"] = year
    
    # Get consumptions sorted by year and month (newest first)
    consumptions = await db.consumptions.find(filter_query).sort([("year", -1), ("month", -1)]).to_list(length=100)
    
    logging.info(f"✅ Found {len(consumptions)} consumption records")
    
    # Clean data for JSON serialization (remove ObjectId _id field)
    clean_consumptions = []
    for consumption in consumptions:
        # Remove the MongoDB _id field to avoid serialization issues
        consumption.pop('_id', None)
        clean_consumptions.append(consumption)
    
    return clean_consumptions

@api_router.put("/consumptions/{consumption_id}")
async def update_consumption(
    consumption_id: str,
    consumption_data: ConsumptionInput,
    current_user: User = Depends(get_current_user)
):
    """Update consumption record"""
    
    # Find existing consumption
    consumption = await db.consumptions.find_one({"id": consumption_id})
    if not consumption:
        raise HTTPException(status_code=404, detail="Tüketim verisi bulunamadı")
    
    # Check permissions
    if current_user.role == UserRole.CLIENT and current_user.client_id != consumption["client_id"]:
        raise HTTPException(status_code=403, detail="Bu tüketim verisini güncelleme yetkiniz yok")
    
    # Update consumption data and recalculate carbon emissions
    update_data = consumption_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    # Calculate carbon emissions using DEFRA factors
    if calculate_carbon_emissions:
        try:
            carbon_results = calculate_carbon_emissions(update_data)
            update_data.update({
                "total_co2_emissions": carbon_results.get("total_co2_emissions"),
                "total_co2_tonnes": carbon_results.get("total_co2_tonnes"),
                "per_person_co2": carbon_results.get("per_person_co2")
            })
            
            # Add benchmark analysis
            if consumption_data.accommodation_count > 0:
                benchmark = benchmark_performance(
                    carbon_results.get("total_co2_emissions", 0),
                    consumption_data.accommodation_count
                )
                update_data["carbon_benchmark"] = benchmark.get("performance_level")
            
            logging.info(f"🌍 Carbon calculation updated: {carbon_results.get('total_co2_emissions', 0)} kg CO2")
        except Exception as e:
            logging.warning(f"⚠️ Carbon calculation failed during update: {e}")
    
    await db.consumptions.update_one(
        {"id": consumption_id},
        {"$set": update_data}
    )
    
    return {"message": "Tüketim verisi başarıyla güncellendi"}

@api_router.delete("/consumptions/{consumption_id}")
async def delete_consumption(
    consumption_id: str,
    current_user: User = Depends(get_admin_user)  # Only admin can delete
):
    """Delete consumption record"""
    
    logging.info(f"🗑️ DELETE /consumptions/{consumption_id} called by admin user: {current_user.name}")
    
    # Check if consumption exists
    existing = await db.consumptions.find_one({"id": consumption_id})
    if not existing:
        logging.info(f"❌ Consumption not found: {consumption_id}")
        raise HTTPException(status_code=404, detail="Tüketim verisi bulunamadı")
    
    result = await db.consumptions.delete_one({"id": consumption_id})
    if result.deleted_count == 0:
        logging.info(f"❌ Failed to delete consumption: {consumption_id}")
        raise HTTPException(status_code=404, detail="Tüketim verisi silinemedi")
    
    logging.info(f"✅ Consumption deleted successfully: {consumption_id}")
    return {"message": "Tüketim verisi başarıyla silindi"}

@api_router.get("/consumptions/analytics")
async def get_consumption_analytics(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get consumption analytics and comparisons"""
    
    logging.info(f"🔍 GET /consumptions/analytics called by user: {current_user.role} - client_id param: {client_id}")
    
    # Get client_id based on user role
    if current_user.role == UserRole.ADMIN:
        # Admin can specify client_id or see aggregated data for all clients
        if client_id:
            target_client_id = client_id
        else:
            # If no client_id specified, get the first available client for demo
            # In production, this might show aggregated data for all clients
            clients = await db.clients.find().to_list(1)
            if not clients:
                raise HTTPException(status_code=400, detail="No clients available for analytics")
            target_client_id = clients[0]["id"]
            logging.info(f"📊 Admin user - using first available client: {target_client_id}")
    else:
        # Client users can only see their own analytics
        if not current_user.client_id:
            raise HTTPException(status_code=400, detail="Client not assigned to user")
        target_client_id = current_user.client_id
    
    logging.info(f"📊 Generating analytics for client_id: {target_client_id}")
    
    # Default to current year if not specified
    if not year:
        year = datetime.now().year
    
    # Get current year and previous year data
    current_year_data = await db.consumptions.find({
        "client_id": target_client_id,
        "year": year
    }).sort("month", 1).to_list(length=12)
    
    previous_year_data = await db.consumptions.find({
        "client_id": target_client_id,
        "year": year - 1
    }).sort("month", 1).to_list(length=12)
    
    # Calculate monthly comparisons
    monthly_comparison = []
    for month in range(1, 13):
        current_month = next((c for c in current_year_data if c["month"] == month), None)
        previous_month = next((c for c in previous_year_data if c["month"] == month), None)
        
        month_data = {
            "month": month,
            "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][month],
            "current_year": {
                "electricity": current_month["electricity"] if current_month else 0,
                "water": current_month["water"] if current_month else 0,
                "natural_gas": current_month["natural_gas"] if current_month else 0,
                "coal": current_month["coal"] if current_month else 0,
                "accommodation_count": current_month["accommodation_count"] if current_month else 0
            },
            "previous_year": {
                "electricity": previous_month["electricity"] if previous_month else 0,
                "water": previous_month["water"] if previous_month else 0,
                "natural_gas": previous_month["natural_gas"] if previous_month else 0,
                "coal": previous_month["coal"] if previous_month else 0,
                "accommodation_count": previous_month["accommodation_count"] if previous_month else 0
            }
        }
        
        # Calculate per-person consumption
        if month_data["current_year"]["accommodation_count"] > 0:
            month_data["per_person"] = {
                "electricity": month_data["current_year"]["electricity"] / month_data["current_year"]["accommodation_count"],
                "water": month_data["current_year"]["water"] / month_data["current_year"]["accommodation_count"],
                "natural_gas": month_data["current_year"]["natural_gas"] / month_data["current_year"]["accommodation_count"],
                "coal": month_data["current_year"]["coal"] / month_data["current_year"]["accommodation_count"]
            }
        else:
            month_data["per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        if month_data["previous_year"]["accommodation_count"] > 0:
            month_data["previous_year_per_person"] = {
                "electricity": month_data["previous_year"]["electricity"] / month_data["previous_year"]["accommodation_count"],
                "water": month_data["previous_year"]["water"] / month_data["previous_year"]["accommodation_count"],
                "natural_gas": month_data["previous_year"]["natural_gas"] / month_data["previous_year"]["accommodation_count"],
                "coal": month_data["previous_year"]["coal"] / month_data["previous_year"]["accommodation_count"]
            }
        else:
            month_data["previous_year_per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        monthly_comparison.append(month_data)
    
    # Calculate year totals
    current_year_totals = {
        "electricity": sum(c["electricity"] for c in current_year_data),
        "water": sum(c["water"] for c in current_year_data),
        "natural_gas": sum(c["natural_gas"] for c in current_year_data),
        "coal": sum(c["coal"] for c in current_year_data),
        "accommodation_count": sum(c["accommodation_count"] for c in current_year_data)
    }
    
    previous_year_totals = {
        "electricity": sum(c["electricity"] for c in previous_year_data),
        "water": sum(c["water"] for c in previous_year_data),
        "natural_gas": sum(c["natural_gas"] for c in previous_year_data),
        "coal": sum(c["coal"] for c in previous_year_data),
        "accommodation_count": sum(c["accommodation_count"] for c in previous_year_data)
    }
    
    return {
        "year": year,
        "monthly_comparison": monthly_comparison,
        "yearly_totals": {
            "current_year": current_year_totals,
            "previous_year": previous_year_totals
        },
        "yearly_per_person": {
            "current_year": {
                "electricity": current_year_totals["electricity"] / current_year_totals["accommodation_count"] if current_year_totals["accommodation_count"] > 0 else 0,
                "water": current_year_totals["water"] / current_year_totals["accommodation_count"] if current_year_totals["accommodation_count"] > 0 else 0,
                "natural_gas": current_year_totals["natural_gas"] / current_year_totals["accommodation_count"] if current_year_totals["accommodation_count"] > 0 else 0,
                "coal": current_year_totals["coal"] / current_year_totals["accommodation_count"] if current_year_totals["accommodation_count"] > 0 else 0
            },
            "previous_year": {
                "electricity": previous_year_totals["electricity"] / previous_year_totals["accommodation_count"] if previous_year_totals["accommodation_count"] > 0 else 0,
                "water": previous_year_totals["water"] / previous_year_totals["accommodation_count"] if previous_year_totals["accommodation_count"] > 0 else 0,
                "natural_gas": previous_year_totals["natural_gas"] / previous_year_totals["accommodation_count"] if previous_year_totals["accommodation_count"] > 0 else 0,
                "coal": previous_year_totals["coal"] / previous_year_totals["accommodation_count"] if previous_year_totals["accommodation_count"] > 0 else 0
            }
        }
    }

# Carbon Analytics Endpoint
@api_router.get("/analytics/carbon-footprint")
async def get_carbon_analytics(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get carbon footprint analytics and comparisons"""
    
    logging.info(f"🌍 GET /analytics/carbon-footprint called by user: {current_user.role}")
    
    # Get client_id based on user role
    if current_user.role == UserRole.ADMIN:
        if client_id:
            target_client_id = client_id
        else:
            # Admin needs to specify client_id for carbon analytics
            raise HTTPException(status_code=400, detail="Client ID required for carbon analytics")
    else:
        # Client users can only see their own carbon data
        if not current_user.client_id:
            raise HTTPException(status_code=403, detail="Client user not properly linked to a client")
        target_client_id = current_user.client_id
    
    # Default to current year if not specified
    if not year:
        year = datetime.now().year
    
    # Get consumption data for carbon calculation
    filter_query = {"client_id": target_client_id, "year": year}
    consumptions = await db.consumptions.find(filter_query).to_list(length=100)
    
    if not consumptions:
        return {
            "year": year,
            "client_id": target_client_id,
            "total_carbon_emissions": 0,
            "monthly_carbon_data": [],
            "carbon_benchmarks": {},
            "total_emission_sources": {},
            "message": "No consumption data found for carbon analysis"
        }
    
    # Calculate carbon emissions for each month
    monthly_carbon_data = []
    total_yearly_co2 = 0.0
    total_yearly_accommodation = 0
    total_emission_sources = {}
    
    for consumption in consumptions:
        if calculate_carbon_emissions:
            try:
                # Prepare consumption data for carbon calculation
                consumption_data = {
                    "electricity": consumption.get("electricity", 0),
                    "water": consumption.get("water", 0),
                    "natural_gas": consumption.get("natural_gas", 0),
                    "coal": consumption.get("coal", 0),
                    "diesel": consumption.get("diesel", 0),
                    "gasoline": consumption.get("gasoline", 0),
                    "lpg": consumption.get("lpg", 0),
                    "fuel_oil": consumption.get("fuel_oil", 0),
                    # DEFRA F-Gases
                    "r134a_gas": consumption.get("r134a_gas", 0),
                    "r600a_gas": consumption.get("r600a_gas", 0),
                    "r410a_gas": consumption.get("r410a_gas", 0),
                    "r32_gas": consumption.get("r32_gas", 0),
                    "co2_fire": consumption.get("co2_fire", 0),
                    "fm200_fire": consumption.get("fm200_fire", 0),
                    "accommodation_count": consumption.get("accommodation_count", 0)
                }
                
                # Calculate carbon emissions
                carbon_results = calculate_carbon_emissions(consumption_data)
                
                # Accumulate emission sources for total yearly emissions
                emissions_breakdown = carbon_results.get("emissions_breakdown", {})
                for source, source_data in emissions_breakdown.items():
                    if source not in total_emission_sources:
                        total_emission_sources[source] = 0
                    total_emission_sources[source] += source_data.get("co2_emissions", 0)
                
                # Get benchmark analysis
                benchmark_result = {}
                if consumption.get("accommodation_count", 0) > 0:
                    benchmark_result = benchmark_performance(
                        carbon_results.get("total_co2_emissions", 0),
                        consumption.get("accommodation_count", 0)
                    )
                
                monthly_data = {
                    "month": consumption.get("month"),
                    "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][consumption.get("month", 1)],
                    "total_co2_emissions": carbon_results.get("total_co2_emissions", 0),
                    "total_co2_tonnes": carbon_results.get("total_co2_tonnes", 0),
                    "per_person_co2": carbon_results.get("per_person_co2", 0),
                    "accommodation_count": consumption.get("accommodation_count", 0),
                    "emissions_breakdown": emissions_breakdown,
                    "benchmark": benchmark_result
                }
                
                monthly_carbon_data.append(monthly_data)
                total_yearly_co2 += carbon_results.get("total_co2_emissions", 0)
                total_yearly_accommodation += consumption.get("accommodation_count", 0)
                
            except Exception as e:
                logging.error(f"❌ Carbon calculation error for month {consumption.get('month')}: {e}")
    
    # Calculate yearly benchmarks
    yearly_benchmarks = {}
    if total_yearly_accommodation > 0:
        yearly_benchmarks = benchmark_performance(
            total_yearly_co2,
            total_yearly_accommodation,
            nights=365  # Yearly calculation
        )
    
    # Sort monthly data by month
    monthly_carbon_data.sort(key=lambda x: x["month"])
    
    return {
        "year": year,
        "client_id": target_client_id,
        "total_carbon_emissions": round(total_yearly_co2, 3),
        "total_carbon_tonnes": round(total_yearly_co2 / 1000.0, 6),
        "average_per_person_co2": round(total_yearly_co2 / total_yearly_accommodation if total_yearly_accommodation > 0 else 0, 3),
        "total_accommodation_count": total_yearly_accommodation,
        "monthly_carbon_data": monthly_carbon_data,
        "yearly_benchmarks": yearly_benchmarks,
        "total_emission_sources": total_emission_sources,  # Kaynak bazında toplam emisyonlar
        "methodology": "DEFRA 2024 Emission Factors",
        "units": "kg CO2 equivalent"
    }

# Carbon Analytics Endpoint
@api_router.get("/analytics/carbon-footprint")
async def get_carbon_analytics(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get carbon footprint analytics and comparisons"""
    
    logging.info(f"🌍 GET /analytics/carbon-footprint called by user: {current_user.role}")
    
    # Get client_id based on user role
    if current_user.role == UserRole.ADMIN:
        if client_id:
            target_client_id = client_id
        else:
            # Admin needs to specify client_id for carbon analytics
            raise HTTPException(status_code=400, detail="Client ID required for carbon analytics")
    else:
        # Client users can only see their own carbon data
        if not current_user.client_id:
            raise HTTPException(status_code=403, detail="Client user not properly linked to a client")
        target_client_id = current_user.client_id
    
    # Default to current year if not specified
    if not year:
        year = datetime.now().year
    
    # Get consumption data for carbon calculation
    filter_query = {"client_id": target_client_id, "year": year}
    consumptions = await db.consumptions.find(filter_query).to_list(length=100)
    
    if not consumptions:
        return {
            "year": year,
            "client_id": target_client_id,
            "total_carbon_emissions": 0,
            "monthly_carbon_data": [],
            "carbon_benchmarks": {},
            "total_emission_sources": {},
            "message": "No consumption data found for carbon analysis"
        }
    
    # Calculate carbon emissions for each month
    monthly_carbon_data = []
    total_yearly_co2 = 0.0
    total_yearly_accommodation = 0
    total_emission_sources = {}
    
    for consumption in consumptions:
        if calculate_carbon_emissions:
            try:
                # Prepare consumption data for carbon calculation
                consumption_data = {
                    "electricity": consumption.get("electricity", 0),
                    "water": consumption.get("water", 0),
                    "natural_gas": consumption.get("natural_gas", 0),
                    "coal": consumption.get("coal", 0),
                    "diesel": consumption.get("diesel", 0),
                    "gasoline": consumption.get("gasoline", 0),
                    "lpg": consumption.get("lpg", 0),
                    "fuel_oil": consumption.get("fuel_oil", 0),
                    # DEFRA F-Gases
                    "r134a_gas": consumption.get("r134a_gas", 0),
                    "r600a_gas": consumption.get("r600a_gas", 0),
                    "r410a_gas": consumption.get("r410a_gas", 0),
                    "r32_gas": consumption.get("r32_gas", 0),
                    "co2_fire": consumption.get("co2_fire", 0),
                    "fm200_fire": consumption.get("fm200_fire", 0),
                    "accommodation_count": consumption.get("accommodation_count", 0)
                }
                
                # Calculate carbon emissions
                carbon_results = calculate_carbon_emissions(consumption_data)
                
                # Accumulate emission sources for total yearly emissions
                emissions_breakdown = carbon_results.get("emissions_breakdown", {})
                for source, source_data in emissions_breakdown.items():
                    if source not in total_emission_sources:
                        total_emission_sources[source] = 0
                    total_emission_sources[source] += source_data.get("co2_emissions", 0)
                
                # Get benchmark analysis
                benchmark_result = {}
                if consumption.get("accommodation_count", 0) > 0:
                    benchmark_result = benchmark_performance(
                        carbon_results.get("total_co2_emissions", 0),
                        consumption.get("accommodation_count", 0)
                    )
                
                monthly_data = {
                    "month": consumption.get("month"),
                    "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                                 "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][consumption.get("month", 1)],
                    "total_co2_emissions": carbon_results.get("total_co2_emissions", 0),
                    "total_co2_tonnes": carbon_results.get("total_co2_tonnes", 0),
                    "per_person_co2": carbon_results.get("per_person_co2", 0),
                    "accommodation_count": consumption.get("accommodation_count", 0),
                    "emissions_breakdown": emissions_breakdown,
                    "benchmark": benchmark_result
                }
                
                monthly_carbon_data.append(monthly_data)
                total_yearly_co2 += carbon_results.get("total_co2_emissions", 0)
                total_yearly_accommodation += consumption.get("accommodation_count", 0)
                
            except Exception as e:
                logging.error(f"❌ Carbon calculation error for month {consumption.get('month')}: {e}")
    
    # Calculate yearly benchmarks
    yearly_benchmarks = {}
    if total_yearly_accommodation > 0:
        yearly_benchmarks = benchmark_performance(
            total_yearly_co2,
            total_yearly_accommodation,
            nights=365  # Yearly calculation
        )
    
    # Sort monthly data by month
    monthly_carbon_data.sort(key=lambda x: x["month"])
    
    return {
        "year": year,
        "client_id": target_client_id,
        "total_carbon_emissions": round(total_yearly_co2, 3),
        "total_carbon_tonnes": round(total_yearly_co2 / 1000.0, 6),
        "average_per_person_co2": round(total_yearly_co2 / total_yearly_accommodation if total_yearly_accommodation > 0 else 0, 3),
        "total_accommodation_count": total_yearly_accommodation,
        "monthly_carbon_data": monthly_carbon_data,
        "yearly_benchmarks": yearly_benchmarks,
        "total_emission_sources": total_emission_sources,  # Kaynak bazında toplam emisyonlar
        "methodology": "DEFRA 2024 Emission Factors",
        "units": "kg CO2 equivalent"
    }

# Guest Engagement Endpoints
@api_router.post("/guest-engagement")
async def create_guest_engagement(
    guest_data: GuestEngagementInput,
    current_user: User = Depends(get_current_user)
):
    """Create guest engagement record"""
    
    # Determine client_id
    if current_user.role == UserRole.ADMIN:
        if not guest_data.client_id:
            raise HTTPException(status_code=400, detail="Admin must specify client_id")
        client_id = guest_data.client_id
    else:
        client_id = current_user.client_id
    
    # Calculate sustainability score based on eco actions
    score = len(guest_data.eco_actions) * 10  # 10 points per action
    
    guest_dict = {
        **guest_data.dict(exclude={'client_id'}),
        "client_id": client_id,
        "sustainability_score": score,
        "id": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.guest_engagement.insert_one(guest_dict)
    return {"message": "Guest engagement record created", "id": guest_dict["id"], "score": score}

@api_router.get("/guest-engagement")
async def get_guest_engagement(
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get guest engagement records"""
    
    if current_user.role == UserRole.ADMIN:
        if client_id:
            filter_query = {"client_id": client_id}
        else:
            filter_query = {}
    else:
        filter_query = {"client_id": current_user.client_id}
    
    guests = await db.guest_engagement.find(filter_query).to_list(length=100)
    return guests

@api_router.get("/guest-engagement/eco-tips")
async def get_eco_tips():
    """Get sustainability tips for guests"""
    
    eco_tips = [
        {
            "id": 1,
            "category": "energy",
            "icon": "💡",
            "title": "Enerji Tasarrufu",
            "description": "Odadan çıkarken klimayı ve ışıkları kapatmayı unutmayın.",
            "points": 10
        },
        {
            "id": 2,
            "category": "water",
            "icon": "💧",
            "title": "Su Tasarrufu",
            "description": "Dişlerinizi fırçalarken veya ellerinizi yıkarken suyu kapatın.",
            "points": 10
        },
        {
            "id": 3,
            "category": "waste",
            "icon": "♻️",
            "title": "Geri Dönüşüm",
            "description": "Çöplerinizi ayrıştırarak geri dönüşüm kutularına atın.",
            "points": 15
        },
        {
            "id": 4,
            "category": "towel",
            "icon": "🏨",
            "title": "Havlu Tasarrufu",
            "description": "Havlularınızı gereksiz yere değiştirmeyin.",
            "points": 10
        },
        {
            "id": 5,
            "category": "local",
            "icon": "🌿",
            "title": "Yerel Ürünler",
            "description": "Restoranlarımızda yerel ve organik ürünleri tercih edin.",
            "points": 20
        },
        {
            "id": 6,
            "category": "transport",
            "icon": "🚶",
            "title": "Yürüyerek Keşfet",
            "description": "Yakın mesafeleri araç kullanmadan yürüyerek keşfedin.",
            "points": 15
        }
    ]
    
    return {"eco_tips": eco_tips}

@api_router.get("/guest-engagement/leaderboard")
async def get_sustainability_leaderboard(
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get sustainability leaderboard"""
    
    if current_user.role == UserRole.ADMIN:
        if client_id:
            filter_query = {"client_id": client_id}
        else:
            filter_query = {}
    else:
        filter_query = {"client_id": current_user.client_id}
    
    # Get top guests by sustainability score
    pipeline = [
        {"$match": filter_query},
        {"$sort": {"sustainability_score": -1}},
        {"$limit": 10}
    ]
    
    top_guests = await db.guest_engagement.aggregate(pipeline).to_list(length=10)
    return {"leaderboard": top_guests}

# Guest Engagement Endpoints
@api_router.post("/guest-engagement")
async def create_guest_engagement(
    guest_data: GuestEngagementInput,
    current_user: User = Depends(get_current_user)
):
    """Create guest engagement record"""
    
    # Determine client_id
    if current_user.role == UserRole.ADMIN:
        if not guest_data.client_id:
            raise HTTPException(status_code=400, detail="Admin must specify client_id")
        client_id = guest_data.client_id
    else:
        client_id = current_user.client_id
    
    # Calculate sustainability score based on eco actions
    score = len(guest_data.eco_actions) * 10  # 10 points per action
    
    guest_dict = {
        **guest_data.dict(exclude={'client_id'}),
        "client_id": client_id,
        "sustainability_score": score,
        "id": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.guest_engagement.insert_one(guest_dict)
    return {"message": "Guest engagement record created", "id": guest_dict["id"], "score": score}

@api_router.get("/guest-engagement")
async def get_guest_engagement(
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get guest engagement records"""
    
    if current_user.role == UserRole.ADMIN:
        if client_id:
            filter_query = {"client_id": client_id}
        else:
            filter_query = {}
    else:
        filter_query = {"client_id": current_user.client_id}
    
    guests = await db.guest_engagement.find(filter_query).to_list(length=100)
    return guests

@api_router.get("/guest-engagement/eco-tips")
async def get_eco_tips():
    """Get sustainability tips for guests"""
    
    eco_tips = [
        {
            "id": 1,
            "category": "energy",
            "icon": "💡",
            "title": "Enerji Tasarrufu",
            "description": "Odadan çıkarken klimayı ve ışıkları kapatmayı unutmayın.",
            "points": 10
        },
        {
            "id": 2,
            "category": "water",
            "icon": "💧",
            "title": "Su Tasarrufu",
            "description": "Dişlerinizi fırçalarken veya ellerinizi yıkarken suyu kapatın.",
            "points": 10
        },
        {
            "id": 3,
            "category": "waste",
            "icon": "♻️",
            "title": "Geri Dönüşüm",
            "description": "Çöplerinizi ayrıştırarak geri dönüşüm kutularına atın.",
            "points": 15
        },
        {
            "id": 4,
            "category": "towel",
            "icon": "🏨",
            "title": "Havlu Tasarrufu",
            "description": "Havlularınızı gereksiz yere değiştirmeyin.",
            "points": 10
        },
        {
            "id": 5,
            "category": "local",
            "icon": "🌿",
            "title": "Yerel Ürünler",
            "description": "Restoranlarımızda yerel ve organik ürünleri tercih edin.",
            "points": 20
        },
        {
            "id": 6,
            "category": "transport",
            "icon": "🚶",
            "title": "Yürüyerek Keşfet",
            "description": "Yakın mesafeleri araç kullanmadan yürüyerek keşfedin.",
            "points": 15
        }
    ]
    
    return {"eco_tips": eco_tips}

@api_router.get("/guest-engagement/leaderboard")
async def get_sustainability_leaderboard(
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get sustainability leaderboard"""
    
    if current_user.role == UserRole.ADMIN:
        if client_id:
            filter_query = {"client_id": client_id}
        else:
            filter_query = {}
    else:
        filter_query = {"client_id": current_user.client_id}
    
    # Get top guests by sustainability score
    pipeline = [
        {"$match": filter_query},
        {"$sort": {"sustainability_score": -1}},
        {"$limit": 10}
    ]
    
    top_guests = await db.guest_engagement.aggregate(pipeline).to_list(length=10)
    return {"leaderboard": top_guests}

@api_router.get("/guest-engagement/self-assessment/{guest_id}")
async def get_guest_self_assessment(guest_id: str):
    """Get guest's own assessment form"""
    guest = await db.guest_engagement.find_one({"id": guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    return {
        "guest": guest,
        "eco_tips": [
            {
                "id": 1,
                "category": "energy",
                "icon": "💡",
                "title": "Enerji Tasarrufu",
                "description": "Odadan çıkarken klimayı ve ışıkları kapatmayı unutmayın.",
                "points": 10
            },
            {
                "id": 2,
                "category": "water",
                "icon": "💧",
                "title": "Su Tasarrufu",
                "description": "Dişlerinizi fırçalarken veya ellerinizi yıkarken suyu kapatın.",
                "points": 10
            },
            {
                "id": 3,
                "category": "waste",
                "icon": "♻️",
                "title": "Geri Dönüşüm",
                "description": "Çöplerinizi ayrıştırarak geri dönüşüm kutularına atın.",
                "points": 15
            },
            {
                "id": 4,
                "category": "towel",
                "icon": "🏨",
                "title": "Havlu Tasarrufu",
                "description": "Havlularınızı gereksiz yere değiştirmeyin.",
                "points": 10
            },
            {
                "id": 5,
                "category": "local",
                "icon": "🌿",
                "title": "Yerel Ürünler",
                "description": "Restoranlarımızda yerel ve organik ürünleri tercih edin.",
                "points": 20
            },
            {
                "id": 6,
                "category": "transport",
                "icon": "🚶",
                "title": "Yürüyerek Keşfet",
                "description": "Yakın mesafeleri araç kullanmadan yürüyerek keşfedin.",
                "points": 15
            }
        ]
    }

@api_router.put("/guest-engagement/self-assessment/{guest_id}")
async def update_guest_self_assessment(
    guest_id: str,
    assessment_data: dict
):
    """Update guest's self-assessment"""
    guest = await db.guest_engagement.find_one({"id": guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Calculate new sustainability score
    completed_actions = assessment_data.get("eco_actions", [])
    new_score = len(completed_actions) * 10  # 10 points per action
    
    # Update guest record
    update_data = {
        "eco_actions": completed_actions,
        "sustainability_score": new_score,
        "feedback_rating": assessment_data.get("feedback_rating"),
        "feedback_comment": assessment_data.get("feedback_comment"),
        "updated_at": datetime.utcnow()
    }
    
    await db.guest_engagement.update_one(
        {"id": guest_id},
        {"$set": update_data}
    )
    
    return {"message": "Assessment updated successfully", "new_score": new_score}

@api_router.get("/guest-engagement/qr-access/{room_number}")
async def get_guest_by_room(room_number: str, client_id: str):
    """Get guest access by room number for QR code system"""
    guest = await db.guest_engagement.find_one({
        "room_number": room_number,
        "client_id": client_id
    })
    
    if not guest:
        # Create a temporary guest record for QR access
        guest_dict = {
            "id": str(uuid.uuid4()),
            "guest_name": f"Guest Room {room_number}",
            "room_number": room_number,
            "client_id": client_id,
            "eco_actions": [],
            "sustainability_score": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.guest_engagement.insert_one(guest_dict)
        return {"guest_id": guest_dict["id"], "is_new": True}
    
    return {"guest_id": guest["id"], "is_new": False}

@api_router.get("/guest-engagement/self-assessment/{guest_id}")
async def get_guest_self_assessment(guest_id: str):
    """Get guest's own assessment form"""
    guest = await db.guest_engagement.find_one({"id": guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    return {
        "guest": guest,
        "eco_tips": [
            {
                "id": 1,
                "category": "energy",
                "icon": "💡",
                "title": "Enerji Tasarrufu",
                "description": "Odadan çıkarken klimayı ve ışıkları kapatmayı unutmayın.",
                "points": 10
            },
            {
                "id": 2,
                "category": "water",
                "icon": "💧",
                "title": "Su Tasarrufu",
                "description": "Dişlerinizi fırçalarken veya ellerinizi yıkarken suyu kapatın.",
                "points": 10
            },
            {
                "id": 3,
                "category": "waste",
                "icon": "♻️",
                "title": "Geri Dönüşüm",
                "description": "Çöplerinizi ayrıştırarak geri dönüşüm kutularına atın.",
                "points": 15
            },
            {
                "id": 4,
                "category": "towel",
                "icon": "🏨",
                "title": "Havlu Tasarrufu",
                "description": "Havlularınızı gereksiz yere değiştirmeyin.",
                "points": 10
            },
            {
                "id": 5,
                "category": "local",
                "icon": "🌿",
                "title": "Yerel Ürünler",
                "description": "Restoranlarımızda yerel ve organik ürünleri tercih edin.",
                "points": 20
            },
            {
                "id": 6,
                "category": "transport",
                "icon": "🚶",
                "title": "Yürüyerek Keşfet",
                "description": "Yakın mesafeleri araç kullanmadan yürüyerek keşfedin.",
                "points": 15
            }
        ]
    }

@api_router.put("/guest-engagement/self-assessment/{guest_id}")
async def update_guest_self_assessment(
    guest_id: str,
    assessment_data: dict
):
    """Update guest's self-assessment"""
    guest = await db.guest_engagement.find_one({"id": guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Calculate new sustainability score
    completed_actions = assessment_data.get("eco_actions", [])
    new_score = len(completed_actions) * 10  # 10 points per action
    
    # Update guest record
    update_data = {
        "eco_actions": completed_actions,
        "sustainability_score": new_score,
        "feedback_rating": assessment_data.get("feedback_rating"),
        "feedback_comment": assessment_data.get("feedback_comment"),
        "updated_at": datetime.utcnow()
    }
    
    await db.guest_engagement.update_one(
        {"id": guest_id},
        {"$set": update_data}
    )
    
    return {"message": "Assessment updated successfully", "new_score": new_score}

@api_router.get("/guest-engagement/qr-access/{room_number}")
async def get_guest_by_room(room_number: str, client_id: str):
    """Get guest access by room number for QR code system"""
    guest = await db.guest_engagement.find_one({
        "room_number": room_number,
        "client_id": client_id
    })
    
    if not guest:
        # Create a temporary guest record for QR access
        guest_dict = {
            "id": str(uuid.uuid4()),
            "guest_name": f"Guest Room {room_number}",
            "room_number": room_number,
            "client_id": client_id,
            "eco_actions": [],
            "sustainability_score": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.guest_engagement.insert_one(guest_dict)
        return {"guest_id": guest_dict["id"], "is_new": True}
    
    return {"guest_id": guest["id"], "is_new": False}

@api_router.post("/consumptions/waste-data")
async def create_waste_record_via_consumptions(
    env_data: EnvironmentInput,
    current_user: User = Depends(get_current_user)
):
    """Create waste record via consumptions endpoint"""
    try:
        client_id = env_data.client_id if current_user.role == UserRole.ADMIN else current_user.client_id
        if not client_id:
            raise HTTPException(status_code=400, detail="Client ID required")

        # Calculate totals
        recyclable = env_data.plastic_waste + env_data.glass_waste + env_data.paper_waste + env_data.metal_waste
        total = env_data.organic_waste + recyclable + env_data.electronic_waste + env_data.mixed_waste
        recycling_rate = (recyclable / total * 100) if total > 0 else 0
        waste_cost = total * 2.5 + env_data.oil_waste * 15.0
        recycling_income = recyclable * 0.8
        net_cost = waste_cost - recycling_income

        record = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "year": env_data.year,
            "month": env_data.month,
            "organic_waste": env_data.organic_waste,
            "plastic_waste": env_data.plastic_waste,
            "glass_waste": env_data.glass_waste,
            "paper_waste": env_data.paper_waste,
            "metal_waste": env_data.metal_waste,
            "electronic_waste": env_data.electronic_waste,
            "oil_waste": env_data.oil_waste,
            "mixed_waste": env_data.mixed_waste,
            "total_waste": total,
            "recycling_rate": round(recycling_rate, 2),
            "waste_cost": round(waste_cost, 2),
            "recycling_income": round(recycling_income, 2),
            "net_cost": round(net_cost, 2),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await db.environment_data.insert_one(record)
        return {"message": "Waste record created successfully", "id": record["id"]}

    except Exception as e:
        logging.error(f"Error creating waste record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/consumptions/waste-data")
async def get_waste_records_via_consumptions(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get waste records via consumptions endpoint"""
    try:
        query = {}
        
        if current_user.role == UserRole.ADMIN:
            if client_id:
                query["client_id"] = client_id
        else:
            if not current_user.client_id:
                raise HTTPException(status_code=403, detail="Client not linked")
            query["client_id"] = current_user.client_id

        if year:
            query["year"] = year

        records = await db.waste_management.find(query).sort("year", -1).sort("month", -1).to_list(length=None)
        return records

    except Exception as e:
        logging.error(f"Error fetching waste records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Environment Management - Clean Implementation
@api_router.post("/environment")
async def create_environment_record(
    env_data: EnvironmentInput,
    current_user: User = Depends(get_current_user)
):
    """Create environment record"""
    try:
        client_id = env_data.client_id if current_user.role == UserRole.ADMIN else current_user.client_id
        if not client_id:
            raise HTTPException(status_code=400, detail="Client ID required")

        # Calculate totals
        recyclable = env_data.plastic_waste + env_data.glass_waste + env_data.paper_waste + env_data.metal_waste
        total = env_data.organic_waste + recyclable + env_data.electronic_waste + env_data.mixed_waste
        recycling_rate = (recyclable / total * 100) if total > 0 else 0
        waste_cost = total * 2.5 + env_data.oil_waste * 15.0
        recycling_income = recyclable * 0.8
        net_cost = waste_cost - recycling_income

        record = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "year": env_data.year,
            "month": env_data.month,
            "organic_waste": env_data.organic_waste,
            "plastic_waste": env_data.plastic_waste,
            "glass_waste": env_data.glass_waste,
            "paper_waste": env_data.paper_waste,
            "metal_waste": env_data.metal_waste,
            "electronic_waste": env_data.electronic_waste,
            "oil_waste": env_data.oil_waste,
            "mixed_waste": env_data.mixed_waste,
            "total_waste": total,
            "recycling_rate": round(recycling_rate, 2),
            "waste_cost": round(waste_cost, 2),
            "recycling_income": round(recycling_income, 2),
            "net_cost": round(net_cost, 2),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await db.environment_data.insert_one(record)
        return {"message": "Record created successfully", "id": record["id"]}

    except Exception as e:
        logging.error(f"Error creating environment record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/environment")
async def get_environment_records(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get environment records"""
    try:
        query = {}
        
        if current_user.role == UserRole.ADMIN:
            if client_id:
                query["client_id"] = client_id
        else:
            if not current_user.client_id:
                raise HTTPException(status_code=403, detail="Client not linked")
            query["client_id"] = current_user.client_id

        if year:
            query["year"] = year

        records = await db.environment_data.find(query).sort("year", -1).sort("month", -1).to_list(length=None)
        return records

    except Exception as e:
        logging.error(f"Error fetching environment records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Waste Management Endpoints (Based on Consumption Structure)
@api_router.post("/consumptions/waste")
async def create_waste_record(
    waste_data: WasteManagementInput,
    current_user: User = Depends(get_current_user)
):
    """Create monthly waste record (same logic as consumption)"""
    
    logging.info(f"🗑️ POST /consumptions/waste called by user: {current_user.role} - {current_user.name} - client_id: {current_user.client_id}")
    
    # Check permissions - same as consumption logic
    if current_user.role == UserRole.ADMIN:
        if waste_data.client_id:
            client_id = waste_data.client_id
        else:
            client_id = current_user.client_id
            if not client_id:
                raise HTTPException(status_code=400, detail="Admin must specify client_id")
    else:
        if not current_user.client_id:
            raise HTTPException(status_code=400, detail="Client not assigned to user")
        client_id = current_user.client_id

    # Check if record already exists for this month/year (same as consumption)
    existing = await db.waste_management.find_one({
        "client_id": client_id,
        "year": waste_data.year,
        "month": waste_data.month
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Waste record already exists for this month")

    # Calculate totals (simplified - removed cost calculations)
    recyclable_waste = (
        waste_data.plastic_waste + waste_data.glass_waste + 
        waste_data.paper_waste + waste_data.metal_waste
    )
    total_waste = (
        waste_data.organic_waste + recyclable_waste + 
        waste_data.electronic_waste + waste_data.mixed_waste
    )
    recycling_rate = (recyclable_waste / total_waste * 100) if total_waste > 0 else 0
    per_person_waste = (total_waste / waste_data.accommodation_count) if waste_data.accommodation_count > 0 else 0

    waste_dict = {
        "id": str(uuid.uuid4()),
        "client_id": client_id,
        "year": waste_data.year,
        "month": waste_data.month,
        "organic_waste": waste_data.organic_waste,
        "plastic_waste": waste_data.plastic_waste,
        "glass_waste": waste_data.glass_waste,
        "paper_waste": waste_data.paper_waste,
        "metal_waste": waste_data.metal_waste,
        "electronic_waste": waste_data.electronic_waste,
        "oil_waste": waste_data.oil_waste,
        "mixed_waste": waste_data.mixed_waste,
        "accommodation_count": waste_data.accommodation_count,
        "total_waste": total_waste,
        "recycling_rate": round(recycling_rate, 2),
        "per_person_waste": round(per_person_waste, 2),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await db.waste_management.insert_one(waste_dict)
    
    logging.info(f"✅ Waste record created successfully for client: {client_id}, month: {waste_data.month}/{waste_data.year}")
    return {"message": "Waste record created successfully", "id": waste_dict["id"]}

@api_router.get("/consumptions/waste")
async def get_waste_records(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get waste records (same logic as consumption)"""
    
    logging.info(f"🗑️ GET /consumptions/waste called by user: {current_user.role} - client_id param: {client_id}")
    
    # Get client_id based on user role (same as consumption)
    if current_user.role == UserRole.ADMIN:
        if client_id:
            target_client_id = client_id
        else:
            target_client_id = current_user.client_id
    else:
        if not current_user.client_id:
            raise HTTPException(status_code=400, detail="Client not assigned to user")
        target_client_id = current_user.client_id
    
    logging.info(f"🗑️ Fetching waste records for client_id: {target_client_id}")
    
    # Build filter (same as consumption)
    filter_query = {}
    if target_client_id:
        filter_query["client_id"] = target_client_id
    if year:
        filter_query["year"] = year

    # Get records (same as consumption)
    records = await db.waste_management.find(filter_query).sort("year", -1).sort("month", -1).to_list(length=None)
    
    logging.info(f"📊 Found {len(records)} waste records")
    return records

@api_router.get("/consumptions/waste/analytics")
async def get_waste_analytics(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get waste analytics (same structure as consumption analytics)"""
    
    logging.info(f"📊 GET /consumptions/waste/analytics called by user: {current_user.role}")
    
    # Get client_id based on user role (same as consumption)
    if current_user.role == UserRole.ADMIN:
        if client_id:
            target_client_id = client_id
        else:
            target_client_id = current_user.client_id
    else:
        if not current_user.client_id:
            raise HTTPException(status_code=400, detail="Client not assigned to user")
        target_client_id = current_user.client_id

    # Build filter
    filter_query = {}
    if target_client_id:
        filter_query["client_id"] = target_client_id
    if year:
        filter_query["year"] = year

    records = await db.waste_management.find(filter_query).sort("year", 1).sort("month", 1).to_list(length=None)
    
    if not records:
        return {
            "yearly_totals": {},
            "monthly_data": [],
            "waste_breakdown": {},
            "recycling_performance": {}
        }

    # Analytics calculations (simplified - removed cost calculations)
    latest_record = records[-1] if records else {}
    yearly_totals = {
        "total_waste": sum(r.get("total_waste", 0) for r in records),
        "recyclable_waste": sum(
            r.get("plastic_waste", 0) + r.get("glass_waste", 0) + 
            r.get("paper_waste", 0) + r.get("metal_waste", 0) for r in records
        ),
        "organic_waste": sum(r.get("organic_waste", 0) for r in records),
        "oil_waste": sum(r.get("oil_waste", 0) for r in records),
        "avg_recycling_rate": sum(r.get("recycling_rate", 0) for r in records) / len(records) if records else 0,
        "avg_per_person_waste": sum(r.get("per_person_waste", 0) for r in records) / len(records) if records else 0,
        "total_accommodation": sum(r.get("accommodation_count", 0) for r in records)
    }

    # Monthly breakdown (simplified)
    monthly_data = []
    for record in records:
        monthly_data.append({
            "month": record.get("month"),
            "year": record.get("year"),
            "total_waste": record.get("total_waste", 0),
            "recycling_rate": record.get("recycling_rate", 0),
            "per_person_waste": record.get("per_person_waste", 0),
            "accommodation_count": record.get("accommodation_count", 0)
        })

    # Waste type breakdown (latest month)
    waste_breakdown = {
        "organic": latest_record.get("organic_waste", 0),
        "plastic": latest_record.get("plastic_waste", 0),
        "glass": latest_record.get("glass_waste", 0),
        "paper": latest_record.get("paper_waste", 0),
        "metal": latest_record.get("metal_waste", 0),
        "electronic": latest_record.get("electronic_waste", 0),
        "oil": latest_record.get("oil_waste", 0),
        "mixed": latest_record.get("mixed_waste", 0)
    }

    # Recycling performance
    recycling_performance = {
        "current_rate": latest_record.get("recycling_rate", 0),
        "target_rate": 60.0,  # Target 60% recycling rate
        "performance": "Excellent" if latest_record.get("recycling_rate", 0) >= 60 else 
                      "Good" if latest_record.get("recycling_rate", 0) >= 40 else
                      "Needs Improvement"
    }

    return {
        "yearly_totals": yearly_totals,
        "monthly_data": monthly_data,
        "waste_breakdown": waste_breakdown,
        "recycling_performance": recycling_performance
    }

@api_router.post("/environment/analytics")
async def post_waste_data_via_analytics(
    env_data: EnvironmentInput,
    current_user: User = Depends(get_current_user)
):
    """Create waste record via analytics endpoint (POST)"""
    try:
        client_id = env_data.client_id if current_user.role == UserRole.ADMIN else current_user.client_id
        if not client_id:
            raise HTTPException(status_code=400, detail="Client ID required")

        # Calculate totals
        recyclable = env_data.plastic_waste + env_data.glass_waste + env_data.paper_waste + env_data.metal_waste
        total = env_data.organic_waste + recyclable + env_data.electronic_waste + env_data.mixed_waste
        recycling_rate = (recyclable / total * 100) if total > 0 else 0
        waste_cost = total * 2.5 + env_data.oil_waste * 15.0
        recycling_income = recyclable * 0.8
        net_cost = waste_cost - recycling_income

        record = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "year": env_data.year,
            "month": env_data.month,
            "organic_waste": env_data.organic_waste,
            "plastic_waste": env_data.plastic_waste,
            "glass_waste": env_data.glass_waste,
            "paper_waste": env_data.paper_waste,
            "metal_waste": env_data.metal_waste,
            "electronic_waste": env_data.electronic_waste,
            "oil_waste": env_data.oil_waste,
            "mixed_waste": env_data.mixed_waste,
            "total_waste": total,
            "recycling_rate": round(recycling_rate, 2),
            "waste_cost": round(waste_cost, 2),
            "recycling_income": round(recycling_income, 2),
            "net_cost": round(net_cost, 2),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await db.environment_data.insert_one(record)
        return {"message": "Waste record created successfully", "id": record["id"]}

    except Exception as e:
        logging.error(f"Error creating waste record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/environment/analytics")
async def get_environment_analytics(
    year: Optional[int] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get environment analytics"""
    try:
        query = {}
        
        if current_user.role == UserRole.ADMIN:
            if client_id:
                query["client_id"] = client_id
        else:
            if not current_user.client_id:
                raise HTTPException(status_code=403, detail="Client not linked")
            query["client_id"] = current_user.client_id

        if year:
            query["year"] = year

        records = await db.environment_data.find(query).sort("year", 1).sort("month", 1).to_list(length=None)
        
        if not records:
            return {
                "yearly_totals": {},
                "monthly_data": [],
                "waste_breakdown": {},
                "recycling_performance": {}
            }

        # Analytics calculations
        latest = records[-1] if records else {}
        yearly_totals = {
            "total_waste": sum(r.get("total_waste", 0) for r in records),
            "recyclable_waste": sum(
                r.get("plastic_waste", 0) + r.get("glass_waste", 0) + 
                r.get("paper_waste", 0) + r.get("metal_waste", 0) for r in records
            ),
            "organic_waste": sum(r.get("organic_waste", 0) for r in records),
            "oil_waste": sum(r.get("oil_waste", 0) for r in records),
            "total_cost": sum(r.get("net_cost", 0) for r in records),
            "avg_recycling_rate": sum(r.get("recycling_rate", 0) for r in records) / len(records) if records else 0
        }

        monthly_data = []
        for record in records:
            monthly_data.append({
                "month": record.get("month"),
                "year": record.get("year"),
                "total_waste": record.get("total_waste", 0),
                "recycling_rate": record.get("recycling_rate", 0),
                "net_cost": record.get("net_cost", 0)
            })

        waste_breakdown = {
            "organic": latest.get("organic_waste", 0),
            "plastic": latest.get("plastic_waste", 0),
            "glass": latest.get("glass_waste", 0),
            "paper": latest.get("paper_waste", 0),
            "metal": latest.get("metal_waste", 0),
            "electronic": latest.get("electronic_waste", 0),
            "oil": latest.get("oil_waste", 0),
            "mixed": latest.get("mixed_waste", 0)
        }

        recycling_performance = {
            "current_rate": latest.get("recycling_rate", 0),
            "target_rate": 60.0,
            "performance": "Excellent" if latest.get("recycling_rate", 0) >= 60 else 
                          "Good" if latest.get("recycling_rate", 0) >= 40 else
                          "Needs Improvement"
        }

        return {
            "records": records,  # Raw records for listing
            "yearly_totals": yearly_totals,
            "monthly_data": monthly_data,
            "waste_breakdown": waste_breakdown,
            "recycling_performance": recycling_performance
        }

    except Exception as e:
        logging.error(f"Error fetching environment analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Multi-Client Comparison Analytics
@api_router.get("/analytics/multi-client-comparison")
async def get_multi_client_comparison(
    year: Optional[int] = None,
    current_user: User = Depends(get_admin_user)  # Only admin can compare multiple clients
):
    """Get consumption comparison across all clients for a given year"""
    
    logging.info(f"🔍 GET /analytics/multi-client-comparison called by admin user")
    
    # Default to current year if not specified
    if not year:
        year = datetime.now().year
    
    # Get all clients
    clients = await db.clients.find().to_list(1000)
    
    client_comparisons = []
    
    for client in clients:
        client_id = client["id"]
        
        # Get consumption data for this client
        client_consumptions = await db.consumptions.find({
            "client_id": client_id,
            "year": year
        }).sort("month", 1).to_list(length=12)
        
        # Calculate totals
        yearly_totals = {
            "electricity": sum(c["electricity"] for c in client_consumptions),
            "water": sum(c["water"] for c in client_consumptions),
            "natural_gas": sum(c["natural_gas"] for c in client_consumptions),
            "coal": sum(c["coal"] for c in client_consumptions),
            "accommodation_count": sum(c["accommodation_count"] for c in client_consumptions)
        }
        
        # Calculate per-person consumption
        per_person = {
            "electricity": yearly_totals["electricity"] / yearly_totals["accommodation_count"] if yearly_totals["accommodation_count"] > 0 else 0,
            "water": yearly_totals["water"] / yearly_totals["accommodation_count"] if yearly_totals["accommodation_count"] > 0 else 0,
            "natural_gas": yearly_totals["natural_gas"] / yearly_totals["accommodation_count"] if yearly_totals["accommodation_count"] > 0 else 0,
            "coal": yearly_totals["coal"] / yearly_totals["accommodation_count"] if yearly_totals["accommodation_count"] > 0 else 0
        }
        
        client_comparisons.append({
            "client_id": client_id,
            "client_name": client["name"],
            "hotel_name": client["hotel_name"],
            "yearly_totals": yearly_totals,
            "per_person_consumption": per_person,
            "monthly_data": [
                {
                    "month": month,
                    "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                                  "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][month],
                    "electricity": next((c["electricity"] for c in client_consumptions if c["month"] == month), 0),
                    "water": next((c["water"] for c in client_consumptions if c["month"] == month), 0),
                    "natural_gas": next((c["natural_gas"] for c in client_consumptions if c["month"] == month), 0),
                    "coal": next((c["coal"] for c in client_consumptions if c["month"] == month), 0),
                    "accommodation_count": next((c["accommodation_count"] for c in client_consumptions if c["month"] == month), 0)
                }
                for month in range(1, 13)
            ]
        })
    
    return {
        "year": year,
        "clients_comparison": client_comparisons,
        "summary": {
            "total_clients": len(client_comparisons),
            "average_consumption": {
                "electricity": sum(c["yearly_totals"]["electricity"] for c in client_comparisons) / len(client_comparisons) if client_comparisons else 0,
                "water": sum(c["yearly_totals"]["water"] for c in client_comparisons) / len(client_comparisons) if client_comparisons else 0,
                "natural_gas": sum(c["yearly_totals"]["natural_gas"] for c in client_comparisons) / len(client_comparisons) if client_comparisons else 0,
                "coal": sum(c["yearly_totals"]["coal"] for c in client_comparisons) / len(client_comparisons) if client_comparisons else 0
            }
        }
    }

@api_router.get("/analytics/monthly-trends")
async def get_monthly_trends(
    year: Optional[int] = None,
    consumption_type: Optional[str] = None,  # electricity, water, natural_gas, coal
    current_user: User = Depends(get_current_user)
):
    """Get monthly trends for consumption data"""
    
    logging.info(f"🔍 GET /analytics/monthly-trends called by user: {current_user.role}")
    
    # Default to current year if not specified
    if not year:
        year = datetime.now().year
    
    # Get client_id based on user role
    if current_user.role == UserRole.ADMIN:
        # Admin can see trends for all clients combined
        filter_query = {"year": year}
    else:
        # Client users can only see their own trends
        if not current_user.client_id:
            raise HTTPException(status_code=400, detail="Client not assigned to user")
        filter_query = {"client_id": current_user.client_id, "year": year}
    
    consumptions = await db.consumptions.find(filter_query).sort("month", 1).to_list(1000)
    
    # Group by month if admin (multiple clients), or just organize by month if client
    monthly_data = {}
    for month in range(1, 13):
        month_consumptions = [c for c in consumptions if c["month"] == month]
        
        if current_user.role == UserRole.ADMIN:
            # For admin, aggregate all clients for each month
            monthly_data[month] = {
                "month": month,
                "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                              "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][month],
                "electricity": sum(c["electricity"] for c in month_consumptions),
                "water": sum(c["water"] for c in month_consumptions),
                "natural_gas": sum(c["natural_gas"] for c in month_consumptions),
                "coal": sum(c["coal"] for c in month_consumptions),
                "accommodation_count": sum(c["accommodation_count"] for c in month_consumptions),
                "client_count": len(month_consumptions)
            }
        else:
            # For client, just their data
            month_consumption = month_consumptions[0] if month_consumptions else None
            monthly_data[month] = {
                "month": month,
                "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                              "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][month],
                "electricity": month_consumption["electricity"] if month_consumption else 0,
                "water": month_consumption["water"] if month_consumption else 0,
                "natural_gas": month_consumption["natural_gas"] if month_consumption else 0,
                "coal": month_consumption["coal"] if month_consumption else 0,
                "accommodation_count": month_consumption["accommodation_count"] if month_consumption else 0
            }
    
    # Convert to list
    monthly_trends = [monthly_data[month] for month in range(1, 13)]
    
    return {
        "year": year,
        "monthly_trends": monthly_trends,
        "user_role": current_user.role.value
    }



# User-Client Management Endpoint
@api_router.post("/admin/assign-client")
async def assign_client_to_user(
    clerk_user_id: str,
    client_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Assign a client to a user (Admin only)"""
    
    logging.info(f"🔗 Admin assigning client {client_id} to user {clerk_user_id}")
    
    # Check if client exists
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Update user's client_id
    result = await db.users.update_one(
        {"clerk_user_id": clerk_user_id},
        {"$set": {"client_id": client_id, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    logging.info(f"✅ Client assigned successfully")
    return {"message": f"Client {client['hotel_name']} assigned to user"}

@api_router.get("/admin/users-clients")
async def get_users_and_clients(current_user: User = Depends(get_admin_user)):
    """Get all users and clients for admin management"""
    
    users = await db.users.find().to_list(1000)
    clients = await db.clients.find().to_list(1000)
    
    return {
        "users": [
            {
                "clerk_user_id": u["clerk_user_id"],
                "name": u["name"],
                "email": u["email"],
                "role": u["role"],
                "client_id": u.get("client_id"),
                "client_name": next((c["hotel_name"] for c in clients if c["id"] == u.get("client_id")), "No Client")
            }
            for u in users
        ],
        "clients": [
            {
                "id": c["id"],
                "hotel_name": c["hotel_name"],
                "name": c["name"],
                "contact_person": c["contact_person"]
            }
            for c in clients
        ]
    }

# ==================== TRAINING ENDPOINTS ====================


@api_router.get("/trainings")
async def get_trainings(current_user: User = Depends(get_current_user)):
    """Get trainings - Admin sees all, Client sees only their own"""
    logging.info(f"📚 GET /trainings called by user: {current_user.role}")
    
    try:
        if current_user.role == UserRole.ADMIN:
            # Admin sees all trainings
            trainings = await db.trainings.find().to_list(length=None)
        else:
            # Client sees only their own trainings
            trainings = await db.trainings.find({"client_id": current_user.client_id}).to_list(length=None)
        
        # Convert ObjectId to string and format response
        formatted_trainings = []
        for training in trainings:
            if "_id" in training:
                del training["_id"]
            formatted_trainings.append(training)
        
        logging.info(f"📚 Returning {len(formatted_trainings)} trainings")
        return formatted_trainings
        
    except Exception as e:
        logging.error(f"❌ Error fetching trainings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trainings: {str(e)}")

@api_router.get("/trainings/{training_id}", response_model=Training)
async def get_training(training_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific training by ID"""
    logging.info(f"📚 GET /trainings/{training_id} called by user: {current_user.role}")
    
    training = await db.trainings.find_one({"id": training_id})
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    # Check access permissions
    if current_user.role == UserRole.CLIENT and training["client_id"] != current_user.client_id:
        raise HTTPException(status_code=403, detail="Access denied to this training")
    
    # Remove MongoDB _id
    if "_id" in training:
        del training["_id"]
    
    return Training(**training)

@api_router.put("/trainings/{training_id}", response_model=Training)
async def update_training(
    training_id: str, 
    training_update: TrainingUpdate,
    current_user: User = Depends(get_admin_user)
):
    """Update a training (Admin only)"""
    logging.info(f"📚 PUT /trainings/{training_id} called by admin: {current_user.name}")
    
    # Check if training exists
    existing_training = await db.trainings.find_one({"id": training_id})
    if not existing_training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    # Prepare update data
    update_data = training_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Update training
    result = await db.trainings.update_one(
        {"id": training_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Training not found or no changes made")
    
    # Return updated training
    updated_training = await db.trainings.find_one({"id": training_id})
    if "_id" in updated_training:
        del updated_training["_id"]
    
    logging.info(f"✅ Training updated: {training_id}")
    return Training(**updated_training)

@api_router.delete("/trainings/{training_id}")
async def delete_training(training_id: str, current_user: User = Depends(get_admin_user)):
    """Delete a training (Admin only)"""
    logging.info(f"📚 DELETE /trainings/{training_id} called by admin: {current_user.name}")
    
    # Check if training exists
    training = await db.trainings.find_one({"id": training_id})
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    # Delete training
    result = await db.trainings.delete_one({"id": training_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Training not found")
    
    logging.info(f"✅ Training deleted: {training['name']}")
    return {"message": "Training deleted successfully"}

# Include the router in the main app
# EMAIL NOTIFICATION ENDPOINTS
@api_router.post("/email/test")
async def send_test_email(current_user: User = Depends(get_current_user)):
    """Send test email to current user"""
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        success = await email_service.send_test_email(current_user.email)
        if success:
            return {"message": "Test email gönderildi!", "email": current_user.email}
        else:
            raise HTTPException(status_code=500, detail="Email gönderilemedi")
    except Exception as e:
        logging.error(f"❌ Test email error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

@api_router.post("/email/document-notification")
async def send_document_notification(
    document_id: str = Form(...),
    current_user: User = Depends(get_admin_user)
):
    """Admin-only: Send document upload notification email"""
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        # Get document details
        document = await db.documents.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get client details
        client = await db.clients.find_one({"id": document["client_id"]})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Validate email address
        client_email = client.get("email", "")
        if not client_email or "@" not in client_email or "." not in client_email:
            raise HTTPException(status_code=400, detail=f"Geçersiz email adresi: {client_email}. Lütfen client email'ini düzeltin.")
        
        # Send email
        upload_date = document.get("created_at", "Bilinmiyor")
        if hasattr(upload_date, 'strftime'):
            upload_date = upload_date.strftime("%d.%m.%Y %H:%M")
        elif isinstance(upload_date, str):
            upload_date = upload_date
        else:
            upload_date = "Bilinmiyor"
            
        await email_service.send_document_upload_notification(
            recipient_email=client_email,
            document_name=document.get("name", "Bilinmiyen Doküman"),
            upload_date=upload_date,
            folder_path=document.get("folder_path", "Klasör belirtilmemiş"),
            client_name=client["name"]
        )
        
        return {"message": f"Doküman bildirimi {client['name']} müşterisine gönderildi!"}
        
    except Exception as e:
        logging.error(f"❌ Document notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

@api_router.post("/email/training-notification")
async def send_training_notification(
    training_id: str = Form(...),
    current_user: User = Depends(get_admin_user)
):
    """Admin-only: Send training notification email"""
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        # Get training details
        training = await db.trainings.find_one({"id": training_id})
        if not training:
            raise HTTPException(status_code=404, detail="Training not found")
        
        # Get client details
        client = await db.clients.find_one({"id": training["client_id"]})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Validate email address
        client_email = client.get("email", "")
        if not client_email or "@" not in client_email or "." not in client_email:
            raise HTTPException(status_code=400, detail=f"Geçersiz email adresi: {client_email}. Lütfen client email'ini düzeltin.")
        
        # Send email
        await email_service.send_training_notification(
            recipient_email=client_email,
            training_name=training["name"],
            training_date=training["training_date"],
            trainer=training["trainer"],
            participant_count=training["participant_count"],
            client_name=client["name"]
        )
        
        return {"message": f"Eğitim bildirimi {client['name']} müşterisine gönderildi!"}
        
    except Exception as e:
        logging.error(f"❌ Training notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

@api_router.post("/email/bulk-document-notification")
async def send_bulk_document_notification(
    document_ids: str = Form(...),
    current_user: User = Depends(get_admin_user)
):
    """Admin-only: Send bulk document upload notification email"""
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        doc_ids = document_ids.split(',')
        
        # Get documents
        documents = []
        for doc_id in doc_ids:
            document = await db.documents.find_one({"id": doc_id.strip()})
            if document:
                documents.append(document)
        
        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")
        
        # Group by client (should be same client for bulk)
        client_id = documents[0]["client_id"]
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Send bulk email
        await email_service.send_bulk_document_notification(
            recipient_email=client.get("email", ""),
            documents=documents,
            client_name=client["name"]
        )
        
        return {"message": f"{len(documents)} doküman bildirimi {client['name']} müşterisine gönderildi!"}
        
    except Exception as e:
        logging.error(f"❌ Bulk document notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

# Helper functions for 2FA
def generate_2fa_code():
    """Generate a secure 6-digit 2FA code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

@api_router.post("/send-email")
async def send_custom_email(request: dict, token: str = Depends(verify_token)):
    """Send custom email via EmailManagement"""
    try:
        to_email = request.get('to_email')
        subject = request.get('subject')
        html_content = request.get('html_content')
        template_type = request.get('template_type', 'custom')
        
        if not to_email or not subject:
            raise HTTPException(status_code=422, detail="Email and subject are required")
        
        if not email_service:
            raise HTTPException(status_code=500, detail="Email service not available")
            
        # If no custom content, use basic template
        if not html_content:
            html_content = f"""
            <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 20px;">
              <div style="background: white; border-radius: 15px; padding: 30px;">
                <h2 style="color: #1f2937; margin: 0 0 20px 0;">{subject}</h2>
                <p style="color: #4b5563; line-height: 1.6;">Bu email Rota CRM üzerinden gönderilmiştir.</p>
                <div style="text-align: center; margin: 30px 0; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                  <p style="color: #6b7280; font-size: 14px; margin: 0;">© 2025 Sustainable Tourism CRM</p>
                </div>
              </div>
            </div>
            """
            
        await email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )
        
        return {"message": "Email sent successfully", "status": "sent"}
        
    except Exception as e:
        logging.error(f"Error sending custom email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

@api_router.get("/email-history")
async def get_email_history(token: str = Depends(verify_token)):
    """Get email history for EmailManagement"""
    try:
        # For now, return mock data since we don't store email history
        return {
            "emails": [
                {
                    "id": 1,
                    "to": "user@example.com",
                    "subject": "Hoş Geldiniz - Elite CRM",
                    "sent_at": datetime.utcnow().isoformat(),
                    "status": "delivered"
                },
                {
                    "id": 2,
                    "to": "client@test.com", 
                    "subject": "Aylık Rapor - Sürdürülebilirlik",
                    "sent_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "status": "sent"
                },
                {
                    "id": 3,
                    "to": "admin@rotakalitedanismanlik.com",
                    "subject": "Sistem Bildirimi",
                    "sent_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "status": "delivered"
                }
            ]
        }
    except Exception as e:
        logging.error(f"Error fetching email history: {str(e)}")
        raise HTTPException(status_code=500, detail="Email geçmişi alınamadı")

# 2FA Endpoints
@api_router.post("/auth/2fa/send-code")
async def send_2fa_code(request: dict):
    """Send 2FA code to user's email"""
    try:
        user_email = request.get('email')
        if not user_email:
            raise HTTPException(status_code=422, detail="Email is required")
            
        verification_code = generate_2fa_code()
        
        # Store the code with expiration (5 minutes)
        expiration = datetime.utcnow() + timedelta(minutes=5)
        await db.verification_codes.update_one(
            {"email": user_email},
            {
                "$set": {
                    "code": verification_code,
                    "expires_at": expiration,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Send email
        if not email_service:
            raise HTTPException(status_code=500, detail="Email service not available")
            
        try:
            await email_service.send_email(
                to_email=user_email,
                subject="🔐 Rota CRM - Elite Güvenlik Kodu",
                html_content=f"""
                <div style="max-width: 600px; margin: 0 auto; font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 0; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                  <div style="background: white; margin: 20px; border-radius: 15px; overflow: hidden;">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 40px 30px; text-align: center;">
                      <div style="background: white; width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
                        <span style="font-size: 40px;">🔐</span>
                      </div>
                      <h1 style="color: white; margin: 0; font-size: 28px; font-weight: bold;">Güvenlik Kodu</h1>
                      <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Rota CRM Elite Security</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 40px 30px; text-align: center;">
                      <h2 style="color: #1f2937; margin: 0 0 20px 0; font-size: 24px;">Merhaba! 👋</h2>
                      <p style="color: #4b5563; line-height: 1.6; margin: 0 0 30px 0; font-size: 16px;">
                        Rota CRM hesabınıza güvenli giriş için doğrulama kodunuz aşağıdadır:
                      </p>
                      
                      <!-- Code Display -->
                      <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 30px; border-radius: 15px; margin: 30px 0; border: 2px dashed #cbd5e1;">
                        <p style="color: #64748b; margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold;">Doğrulama Kodu</p>
                        <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; font-size: 32px; font-weight: bold; padding: 20px; border-radius: 12px; letter-spacing: 8px; font-family: 'Courier New', monospace; box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);">
                          {verification_code}
                        </div>
                      </div>
                      
                      <!-- Security Info -->
                      <div style="background: #fef3cd; border: 1px solid #fbbf24; padding: 20px; border-radius: 12px; margin: 30px 0;">
                        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                          <span style="font-size: 24px; margin-right: 10px;">⚠️</span>
                          <h3 style="color: #92400e; margin: 0; font-size: 16px; font-weight: bold;">Güvenlik Uyarısı</h3>
                        </div>
                        <ul style="color: #92400e; margin: 0; padding-left: 20px; text-align: left; font-size: 14px;">
                          <li style="margin-bottom: 5px;">⏱️ Bu kod <strong>5 dakika</strong> boyunca geçerlidir</li>
                          <li style="margin-bottom: 5px;">🔒 Bu kodu kimseyle paylaşmayın</li>
                          <li style="margin-bottom: 5px;">🚫 Eğer bu işlemi siz yapmadıysanız, lütfen hesabınızı kontrol edin</li>
                        </ul>
                      </div>
                      
                      <!-- Footer -->
                      <div style="text-align: center; margin: 30px 0; padding-top: 30px; border-top: 1px solid #e5e7eb;">
                        <p style="color: #6b7280; font-size: 14px; margin: 0;">
                          Bu email <strong>Sustainable Tourism CRM</strong> tarafından otomatik olarak gönderilmiştir.
                        </p>
                        <p style="color: #9ca3af; font-size: 12px; margin: 10px 0 0 0;">
                          © 2025 Rota Kalite Danışmanlık - Tüm hakları saklıdır.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                """
            )
            return {"message": "Verification code sent successfully"}
            
        except Exception as e:
            logging.error(f"Error sending 2FA code email: {str(e)}")
            raise HTTPException(status_code=500, detail=f"2FA kod gönderme hatası: {str(e)}")
        
    except Exception as e:
        logging.error(f"Error sending 2FA code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"2FA kod gönderme hatası: {str(e)}")

@api_router.post("/auth/2fa/verify-code")
async def verify_2fa_code(request: dict):
    """Verify 2FA code"""
    try:
        user_email = request.get('email')
        code = request.get('code')
        
        if not user_email or not code:
            raise HTTPException(status_code=422, detail="Email and code are required")
        
        # Get stored code
        stored = await db.verification_codes.find_one({"email": user_email})
        
        if not stored:
            raise HTTPException(status_code=400, detail="Verification code not found")
            
        # Check expiration
        if datetime.utcnow() > stored["expires_at"]:
            # Clean up expired code
            await db.verification_codes.delete_one({"email": user_email})
            raise HTTPException(status_code=400, detail="Verification code expired")
            
        # Verify code
        if stored["code"] != code:
            raise HTTPException(status_code=400, detail="Invalid verification code")
            
        # Clean up used code
        await db.verification_codes.delete_one({"email": user_email})
        
        return {"message": "Code verified successfully", "verified": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error verifying 2FA code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"2FA kod doğrulama hatası: {str(e)}")

@api_router.get("/auth/2fa/status")
async def get_2fa_status(user_email: str):
    """Get 2FA status for user"""
    try:
        stored = await db.verification_codes.find_one({"email": user_email})
        
        if not stored:
            return {"has_pending_code": False}
            
        # Check if code is still valid
        if datetime.utcnow() > stored["expires_at"]:
            # Clean up expired code
            await db.verification_codes.delete_one({"email": user_email})
            return {"has_pending_code": False}
            
        return {
            "has_pending_code": True,
            "expires_at": stored["expires_at"].isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting 2FA status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"2FA durum hatası: {str(e)}")

# Include the API router in the app
@api_router.post("/email/bulk-document-notification")
async def send_bulk_document_notification(
    document_ids: str = Form(...),
    current_user: User = Depends(get_admin_user)
):
    """Admin-only: Send bulk document upload notification email"""
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        doc_ids = document_ids.split(',')
        
        # Get documents
        documents = []
        for doc_id in doc_ids:
            document = await db.documents.find_one({"id": doc_id.strip()})
            if document:
                documents.append(document)
        
        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")
        
        # Group by client (should be same client for bulk)
        client_id = documents[0]["client_id"]
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Send bulk email
        await email_service.send_bulk_document_notification(
            recipient_email=client.get("email", ""),
            documents=documents,
            client_name=client["name"]
        )
        
        return {"message": f"{len(documents)} doküman bildirimi {client['name']} müşterisine gönderildi!"}
        
    except Exception as e:
        logging.error(f"❌ Bulk document notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

# ====================================
# SUPPLIER MANAGEMENT MODELS & ENDPOINTS
# ====================================

# Supplier Models
class SupplierInput(BaseModel):
    company_name: str
    contact_person: str
    email: str
    phone: str
    address: str
    category: str  # Food, Cleaning, Energy, Textile, Technology, etc.
    sustainability_score: int = Field(ge=0, le=100)  # 0-100 score
    certifications: List[str] = []  # ["Organic", "Fair Trade", "ISO 14001", etc.]
    local_supplier: bool = False  # Is it a local supplier?
    website: Optional[str] = None
    description: Optional[str] = None
    client_id: Optional[str] = None  # For admin users

class Supplier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    company_name: str
    contact_person: str
    email: str
    phone: str
    address: str
    category: str
    sustainability_score: int
    certifications: List[str] = []
    local_supplier: bool = False
    website: Optional[str] = None
    description: Optional[str] = None
    quality_score: Optional[int] = Field(default=None, ge=0, le=100)
    cost_score: Optional[int] = Field(default=None, ge=0, le=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Supplier Categories for filtering
SUPPLIER_CATEGORIES = [
    "Gıda & İçecek",
    "Temizlik & Hijyen", 
    "Enerji & Yakıt",
    "Tekstil & Çamaşırhane",
    "Teknoloji & Ekipman",
    "Mobilya & Dekorasyon",
    "Güvenlik & Güvenlik",
    "Taşımacılık & Lojistik",
    "Bahçe & Peyzaj",
    "Spa & Wellness",
    "Eğlence & Aktivite",
    "İnşaat & Bakım",
    "Diğer"
]

# Available Certifications
AVAILABLE_CERTIFICATIONS = [
    "ISO 14001",
    "Organik Sertifika",
    "Fair Trade",
    "Carbon Neutral",
    "LEED Certified",
    "Energy Star",
    "Rainforest Alliance",
    "B-Corp",
    "Cradle to Cradle",
    "EU Ecolabel",
    "Green Seal",
    "OEKO-TEX",
    "FSC (Forest Stewardship)",
    "Yerel Üretici",
    "Sıfır Atık"
]

# ====================================
# SUPPLIER ENDPOINTS
# ====================================

@api_router.get("/suppliers/categories/list")
async def get_supplier_categories():
    """Get available supplier categories"""
    return {"categories": SUPPLIER_CATEGORIES}

@api_router.get("/suppliers/certifications/list")
async def get_available_certifications():
    """Get available certifications"""
    return {"certifications": AVAILABLE_CERTIFICATIONS}

@api_router.get("/suppliers/analytics/dashboard")
async def get_suppliers_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get supplier analytics dashboard data"""
    try:
        # Build filter based on user role
        filter_query = {}
        if current_user.role == UserRole.CLIENT:
            filter_query["client_id"] = current_user.client_id

        suppliers = await db.suppliers.find(filter_query).to_list(length=None)
        
        if not suppliers:
            return {
                "total_suppliers": 0,
                "category_distribution": {},
                "sustainability_stats": {},
                "certification_stats": {},
                "local_vs_global": {"local": 0, "global": 0},
                "average_scores": {}
            }

        # Category distribution
        category_dist = {}
        for supplier in suppliers:
            cat = supplier.get("category", "Diğer")
            category_dist[cat] = category_dist.get(cat, 0) + 1

        # Sustainability score distribution
        score_ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        total_sustainability = 0
        for supplier in suppliers:
            score = supplier.get("sustainability_score", 0)
            total_sustainability += score
            
            if score <= 20:
                score_ranges["0-20"] += 1
            elif score <= 40:
                score_ranges["21-40"] += 1
            elif score <= 60:
                score_ranges["41-60"] += 1
            elif score <= 80:
                score_ranges["61-80"] += 1
            else:
                score_ranges["81-100"] += 1

        # Certification statistics
        cert_stats = {}
        for supplier in suppliers:
            for cert in supplier.get("certifications", []):
                cert_stats[cert] = cert_stats.get(cert, 0) + 1

        # Local vs Global
        local_count = sum(1 for s in suppliers if s.get("local_supplier", False))
        global_count = len(suppliers) - local_count

        # Average scores
        avg_sustainability = total_sustainability / len(suppliers) if suppliers else 0
        
        quality_scores = [s.get("quality_score", 0) for s in suppliers if s.get("quality_score")]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        cost_scores = [s.get("cost_score", 0) for s in suppliers if s.get("cost_score")]
        avg_cost = sum(cost_scores) / len(cost_scores) if cost_scores else 0

        return {
            "total_suppliers": len(suppliers),
            "category_distribution": category_dist,
            "sustainability_stats": {
                "average_score": round(avg_sustainability, 1),
                "score_distribution": score_ranges
            },
            "certification_stats": cert_stats,
            "local_vs_global": {
                "local": local_count,
                "global": global_count
            },
            "average_scores": {
                "sustainability": round(avg_sustainability, 1),
                "quality": round(avg_quality, 1),
                "cost_effectiveness": round(avg_cost, 1)
            }
        }

    except Exception as e:
        logger.error(f"Error fetching supplier analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.post("/suppliers")
async def create_supplier(
    supplier_data: SupplierInput,
    current_user: User = Depends(get_current_user)
):
    """Create a new supplier"""
    try:
        client_id = supplier_data.client_id if current_user.role == UserRole.ADMIN else current_user.client_id
        if not client_id:
            raise HTTPException(status_code=400, detail="Client ID required")

        # Check if supplier already exists for this client
        existing = await db.suppliers.find_one({
            "client_id": client_id,
            "company_name": supplier_data.company_name
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Supplier with this company name already exists")

        supplier = Supplier(
            client_id=client_id,
            company_name=supplier_data.company_name,
            contact_person=supplier_data.contact_person,
            email=supplier_data.email,
            phone=supplier_data.phone,
            address=supplier_data.address,
            category=supplier_data.category,
            sustainability_score=supplier_data.sustainability_score,
            certifications=supplier_data.certifications,
            local_supplier=supplier_data.local_supplier,
            website=supplier_data.website,
            description=supplier_data.description
        ).dict()

        result = await db.suppliers.insert_one(supplier)
        
        return {
            "message": "Supplier created successfully",
            "supplier_id": supplier["id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/suppliers")
async def get_suppliers(
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    certification: Optional[str] = None,
    local_only: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """Get suppliers with optional filtering"""
    try:
        # Build filter query
        filter_query = {}
        
        # Role-based filtering
        if current_user.role == UserRole.CLIENT:
            filter_query["client_id"] = current_user.client_id
        # Admin users can see all suppliers or filter by client_id if needed
        
        # Apply filters
        if category:
            filter_query["category"] = category
            
        if min_score is not None:
            filter_query["sustainability_score"] = {"$gte": min_score}
            
        if max_score is not None:
            if "sustainability_score" in filter_query:
                filter_query["sustainability_score"]["$lte"] = max_score
            else:
                filter_query["sustainability_score"] = {"$lte": max_score}
                
        if certification:
            filter_query["certifications"] = {"$in": [certification]}
            
        if local_only is not None:
            filter_query["local_supplier"] = local_only

        suppliers = await db.suppliers.find(filter_query).sort("company_name", 1).to_list(length=None)
        
        return suppliers

    except Exception as e:
        logger.error(f"Error fetching suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/suppliers/{supplier_id}")
async def get_supplier(
    supplier_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific supplier"""
    try:
        supplier = await db.suppliers.find_one({"id": supplier_id})
        
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
            
        # Check permissions
        if current_user.role == UserRole.CLIENT and supplier["client_id"] != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return supplier

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    supplier_data: SupplierInput,
    current_user: User = Depends(get_current_user)
):
    """Update a supplier"""
    try:
        # Get existing supplier
        existing = await db.suppliers.find_one({"id": supplier_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Supplier not found")
            
        # Check permissions
        if current_user.role == UserRole.CLIENT and existing["client_id"] != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update data
        update_data = supplier_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Don't allow client_id changes for security
        if "client_id" in update_data:
            del update_data["client_id"]

        result = await db.suppliers.update_one(
            {"id": supplier_id},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Supplier not found or no changes made")

        return {"message": "Supplier updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a supplier"""
    try:
        # Get existing supplier
        existing = await db.suppliers.find_one({"id": supplier_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Supplier not found")
            
        # Check permissions
        if current_user.role == UserRole.CLIENT and existing["client_id"] != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete supplier
        result = await db.suppliers.delete_one({"id": supplier_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Supplier not found")

        # Also delete related evaluations
        await db.supplier_evaluations.delete_many({"supplier_id": supplier_id})

        return {"message": "Supplier deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting supplier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Mount static files (React build) - KALICI ÇÖZÜM!
# Bu CORS problemini tamamen ortadan kaldırır çünkü frontend ve backend aynı domain'de
frontend_build_path = "/app/frontend/build"
if os.path.exists(frontend_build_path):
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="frontend")
    logging.info(f"🌐 Frontend mounted from {frontend_build_path}")
else:
    logging.warning(f"⚠️ Frontend build not found at {frontend_build_path}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Document & Training Email Management Endpoints
@api_router.get("/trainings")
async def get_trainings(current_user: User = Depends(get_current_user)):
    """Get trainings for email management - CLIENT sees own trainings, ADMIN sees all"""
    try:
        logging.info(f"📧 Email Management - GET /trainings called by: {current_user.role} - {current_user.name}")
        
        if current_user.role == UserRole.CLIENT:
            # CLIENT users only see their own trainings
            client_id = current_user.client_id
            if not client_id:
                logging.warning(f"⚠️ CLIENT user {current_user.name} has no client_id")
                return {"trainings": []}
            
            trainings_from_db = await db.trainings.find({"client_id": client_id}).to_list(length=None)
            
            # Format trainings for frontend with client info
            formatted_trainings = []
            for training in trainings_from_db:
                if "_id" in training:
                    del training["_id"]
                
                formatted_training = {
                    "id": training.get("id", str(training.get("_id", ""))),
                    "title": training.get("name", training.get("title", "Untitled Training")),
                    "description": training.get("subject", "No description available"),
                    "duration": f"{training.get('duration', 2)} saat",
                    "level": "Orta",  # Default level
                    "category": training.get("category", "General"),
                    "client_id": training.get("client_id", ""),
                    "client_name": current_user.hotel_name or current_user.name or "My Hotel",
                    "trainer": training.get("trainer", ""),
                    "training_date": training.get("training_date", ""),
                    "status": training.get("status", "planned")
                }
                formatted_trainings.append(formatted_training)
            
            logging.info(f"✅ CLIENT user - returning {len(formatted_trainings)} own trainings")
            return {"trainings": formatted_trainings}
            
        elif current_user.role == UserRole.ADMIN:
            # ADMIN users see all trainings from database
            trainings_from_db = await db.trainings.find().to_list(length=None)
            
            # Format trainings for frontend with client info
            formatted_trainings = []
            for training in trainings_from_db:
                if "_id" in training:
                    del training["_id"]
                
                # Get client info
                client = await db.clients.find_one({"id": training.get("client_id", "")})
                client_name = client.get("hotel_name", "Unknown Client") if client else "Unknown Client"
                
                formatted_training = {
                    "id": training.get("id", str(training.get("_id", ""))),
                    "title": training.get("name", training.get("title", "Untitled Training")),
                    "description": training.get("subject", "No description available"),
                    "duration": f"{training.get('duration', 2)} saat",
                    "level": "Orta",  # Default level
                    "category": training.get("category", "General"),
                    "client_id": training.get("client_id", ""),
                    "client_name": client_name,
                    "trainer": training.get("trainer", ""),
                    "training_date": training.get("training_date", ""),
                    "status": training.get("status", "planned")
                }
                formatted_trainings.append(formatted_training)
            
            # If no real trainings found, return sample data with client info
            if not formatted_trainings:
                trainings = [
                    {
                        "id": 1,
                        "title": "Sürdürülebilir Turizm Eğitimi",
                        "description": "Temel sürdürülebilirlik prensipleri ve uygulamaları",
                        "duration": "2 saat",
                        "level": "Başlangıç",
                        "category": "Environment",
                        "content_type": "Video + PDF",
                        "created_date": datetime.utcnow().isoformat(),
                        "client_id": "paradise-resort",
                        "client_name": "Paradise Resort & Spa"
                    },
                    {
                        "id": 2,
                        "title": "Enerji Tasarrufu ve Verimlilik Eğitimi",
                        "description": "Otel operasyonlarında enerji verimliliği teknikleri",
                        "duration": "1.5 saat",
                        "level": "Orta",
                        "category": "Energy",
                        "content_type": "Interactive Course",
                        "created_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                        "client_id": "green-valley",
                        "client_name": "Green Valley Hotel"
                    }
                ]
                logging.info(f"No real trainings found, returning {len(trainings)} sample trainings")
                return {"trainings": trainings}
            
            logging.info(f"✅ ADMIN user - returning {len(formatted_trainings)} real trainings")
            return {"trainings": formatted_trainings}
        else:
            logging.warning(f"⚠️ Unknown user role: {current_user.role}")
            return {"trainings": []}
    except Exception as e:
        logging.error(f"Error fetching trainings: {str(e)}")
        raise HTTPException(status_code=500, detail="Eğitimler alınamadı")

# TEST ENDPOINT - Remove authentication for debugging
@api_router.get("/email-test/clients")
async def get_clients_for_email_test():
    """TEMPORARY: Get all clients for email management - NO AUTH for testing"""
    try:
        logging.info(f"📧 TEST - GET /email-test/clients called without auth")
        
        # Get all clients from database
        clients_from_db = await db.clients.find().to_list(length=None)
        
        # Format clients for frontend
        formatted_clients = []
        for client in clients_from_db:
            if "_id" in client:
                del client["_id"]
            
            formatted_client = {
                "id": client.get("id", str(client.get("_id", ""))),
                "name": client.get("hotel_name", client.get("name", "Unknown Client")),
                "email": client.get("email", ""),
                "contact_person": client.get("contact_person", ""),
                "category": client.get("current_stage", "General"),
                "client_id": client.get("id", str(client.get("_id", "")))  # For mapping
            }
            formatted_clients.append(formatted_client)
        
        # Also try to get from users collection in case clients are stored there
        try:
            users_from_db = await db.users.find({"role": "CLIENT"}).to_list(length=None)
            for user in users_from_db:
                if "_id" in user:
                    del user["_id"]
                
                formatted_client = {
                    "id": user.get("client_id", str(user.get("_id", ""))),
                    "name": user.get("hotel_name", user.get("name", "Unknown Client")),
                    "email": user.get("email", ""),
                    "contact_person": user.get("name", ""),
                    "category": "Client User",
                    "client_id": user.get("client_id", str(user.get("_id", "")))
                }
                formatted_clients.append(formatted_client)
            logging.info(f"Also found {len(users_from_db)} client users")
        except Exception as e:
            logging.info(f"No users collection or error: {e}")
        
        # If no real clients found, return sample data
        if not formatted_clients:
            clients = [
                {
                    "id": 1,
                    "name": "Paradise Resort & Spa",
                    "email": "info@paradiseresort.com",
                    "contact_person": "Ahmet Yılmaz",
                    "category": "5 Star Resort",
                    "client_id": "paradise-resort"
                },
                {
                    "id": 2,
                    "name": "Green Valley Hotel",
                    "email": "contact@greenvalley.com",
                    "contact_person": "Elif Özkan",
                    "category": "Boutique Hotel",
                    "client_id": "green-valley"
                }
            ]
            logging.info(f"No real clients found, returning {len(clients)} sample clients")
            return {"clients": clients}
        
        logging.info(f"✅ TEST - returning {len(formatted_clients)} clients from database")
        return {"clients": formatted_clients}
    except Exception as e:
        logging.error(f"Error fetching clients for test: {str(e)}")
        return {"clients": [{"error": str(e)}]}
    except Exception as e:
        logging.error(f"Error fetching clients: {str(e)}")
        raise HTTPException(status_code=500, detail="Müşteriler alınamadı")


# Real Data Endpoints for Email Management
@api_router.get("/email-management/documents-real")
async def get_real_documents_for_email(current_user: User = Depends(get_current_user)):
    """Get real documents from database for email management"""
    try:
        # Get all documents from database
        documents = await db.documents.find().to_list(length=None)
        
        # Also check rotacrm database
        rotacrm_db = client["rotacrm"]
        rotacrm_documents = await rotacrm_db.documents.find().to_list(length=None)
        
        # Combine documents from both databases
        all_documents = documents + rotacrm_documents
        
        # Format documents for frontend with client info
        formatted_documents = []
        for doc in all_documents:
            if "_id" in doc:
                del doc["_id"]
            
            # Get client info from both databases
            client = await db.clients.find_one({"id": doc.get("client_id", "")})
            if not client:
                client = await rotacrm_db.clients.find_one({"id": doc.get("client_id", "")})
            
            client_name = client.get("hotel_name", client.get("client_name", "Unknown Client")) if client else "Unknown Client"
            
            formatted_doc = {
                "id": doc.get("id", ""),
                "title": doc.get("name", doc.get("title", "Untitled Document")),
                "type": "PDF",  # Default type
                "category": doc.get("document_type", "General"),
                "upload_date": doc.get("upload_date", datetime.utcnow().isoformat()),
                "file_size": doc.get("file_size", "N/A"),
                "file_path": doc.get("file_path", ""),
                "client_id": doc.get("client_id", ""),
                "client_name": client_name
            }
            formatted_documents.append(formatted_doc)
        
        logging.info(f"Found {len(formatted_documents)} real documents for email management")
        return formatted_documents
        
    except Exception as e:
        logging.error(f"Error fetching real documents: {str(e)}")
        # Return empty list on error
        return []

@api_router.get("/email-management/trainings-real")
async def get_real_trainings_for_email(current_user: User = Depends(get_current_user)):
    """Get real trainings from database for email management"""
    try:
        # Get all trainings from database
        trainings = await db.trainings.find().to_list(length=None)
        
        # Also check rotacrm database
        rotacrm_db = client["rotacrm"]
        rotacrm_trainings = await rotacrm_db.trainings.find().to_list(length=None)
        
        # Combine trainings from both databases
        all_trainings = trainings + rotacrm_trainings
        
        # Format trainings for frontend with client info
        formatted_trainings = []
        for training in all_trainings:
            if "_id" in training:
                del training["_id"]
            
            # Get client info from both databases
            client = await db.clients.find_one({"id": training.get("client_id", "")})
            if not client:
                client = await rotacrm_db.clients.find_one({"id": training.get("client_id", "")})
            
            client_name = client.get("hotel_name", client.get("client_name", "Unknown Client")) if client else "Unknown Client"
            
            formatted_training = {
                "id": training.get("id", ""),
                "title": training.get("name", training.get("title", "Untitled Training")),
                "description": training.get("subject", "No description available"),
                "duration": f"{training.get('duration', 2)} saat",
                "level": "Orta",  # Default level
                "category": training.get("category", "General"),
                "client_id": training.get("client_id", ""),
                "client_name": client_name,
                "trainer": training.get("trainer", ""),
                "training_date": training.get("training_date", ""),
                "status": training.get("status", "planned")
            }
            formatted_trainings.append(formatted_training)
        
        logging.info(f"Found {len(formatted_trainings)} real trainings for email management")
        return formatted_trainings
        
    except Exception as e:
        logging.error(f"Error fetching real trainings: {str(e)}")
        # Return empty list on error
        return []

@api_router.get("/email-management/clients-real")
async def get_real_clients_for_email(current_user: User = Depends(get_current_user)):
    """Get real clients from database for email management"""
    try:
        # Get all clients from database
        clients = await db.clients.find().to_list(length=None)
        
        # Also check rotacrm database
        rotacrm_db = client["rotacrm"]
        rotacrm_clients = await rotacrm_db.clients.find().to_list(length=None)
        
        # Combine clients from both databases
        all_clients = clients + rotacrm_clients
        
        # Format clients for frontend
        formatted_clients = []
        for client in all_clients:
            if "_id" in client:
                del client["_id"]
            
            formatted_client = {
                "id": client.get("id", ""),
                "name": client.get("hotel_name", client.get("client_name", client.get("name", "Unknown Client"))),
                "email": client.get("email", ""),
                "contact_person": client.get("contact_person", ""),
                "category": client.get("current_stage", "General"),
                "client_id": client.get("id", "")  # For mapping
            }
            formatted_clients.append(formatted_client)
        
        logging.info(f"Found {len(formatted_clients)} real clients for email management")
        return formatted_clients
        
    except Exception as e:
        logging.error(f"Error fetching real clients: {str(e)}")
        # Return empty list on error
        return []

# ==========================================
# API ROUTER REGISTRATION - MUST BE AT END
# ==========================================
app.include_router(api_router, prefix="/api")