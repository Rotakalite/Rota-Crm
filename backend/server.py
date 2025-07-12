import os
import uuid
import logging
import shutil
import re
import secrets
import asyncio
from pymongo import MongoClient
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

# Import MongoDB GridFS service (ENABLED)
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from services.mongo_gridfs import MongoGridFS
    mongo_gridfs = MongoGridFS()
    logging.info("✅ MongoDB GridFS service imported successfully")
except Exception as e:
    logging.error(f"❌ Failed to import MongoDB GridFS service: {e}")
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

# Basic test endpoint
@app.get("/test")
async def test_endpoint():
    return {"status": "working", "message": "Basic endpoint is functional"}

@app.post("/email-template-test")
async def test_email_templates():
    """Test email templates directly"""
    if not email_service:
        return {"error": "Email service not available"}
    
    try:
        # Test document upload template
        await email_service.send_document_upload_notification(
            recipient_email="test@example.com",
            document_name="Test Doküman",
            upload_date="25.01.2025 14:30",
            folder_path="Test Klasör / Alt Klasör",
            client_name="Test Müşteri"
        )
        
        return {
            "success": True,
            "message": "Email templates tested successfully!",
            "templates_used": ["document_upload_tr.html"],
            "email_sent_to": "test@example.com"
        }
    except Exception as e:
        return {
            "error": str(e),
            "templates_status": "error during email send"
        }

# RAILWAY CORS CONFIGURATION - KALICI ÇÖZÜM: TÜM ORIGIN'LERE İZİN VER
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TÜM ORIGIN'LERE İZİN VER - RAILWAY/VERCEL DEĞİŞKEN URL PROBLEMİ İÇİN
    allow_credentials=False,  # "*" kullanırken credentials false olmalı
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],  # TÜM HEADER'LARA İZİN VER
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

# Additional OPTIONS handler for API routes - DISABLED to prevent route conflicts
# @api_router.options("/{full_path:path}")
# async def api_options_handler(full_path: str):
#     """Handle CORS preflight requests for API routes"""
#     return Response(
#         status_code=200,
#         headers={
#             "Access-Control-Allow-Origin": "*",
#             "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
#             "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers, Cache-Control, Pragma, Expires, X-CSRF-Token",
#             "Access-Control-Expose-Headers": "*",
#             "Access-Control-Allow-Credentials": "true",
#             "Access-Control-Max-Age": "86400",
#             "Content-Length": "0"
#         }
#     )

# CORS OPTIONS handler - ONLY for specific paths, not catch-all
@app.options("/")
async def root_options():
    """Handle CORS preflight for root"""
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
    CONSULTANT = "consultant"

# Authentication Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clerk_user_id: str
    email: str
    name: str
    role: UserRole = UserRole.CLIENT
    client_id: Optional[str] = None  # For client users, links to their client record
    consultant_id: Optional[str] = None  # For consultant users, links to their consultant record
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    clerk_user_id: str
    email: str
    name: str
    role: UserRole = UserRole.CLIENT
    client_id: Optional[str] = None
    consultant_id: Optional[str] = None

# Consultant Models
class Consultant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    authorized_person_name: str
    email: str
    phone: str
    address: str
    is_active: bool = True
    total_clients: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConsultantCreate(BaseModel):
    company_name: str
    authorized_person_name: str
    email: str
    phone: str
    address: str

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
    consultant_id: Optional[str] = None  # Which consultant manages this client
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

async def get_current_user_for_role_setup(payload: dict = Depends(verify_token)):
    """Get current user for role setup - allows users without role"""
    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        logging.error("❌ Missing user ID in token payload")
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    logging.info(f"🔍 ROLE SETUP: Looking for user with Clerk ID: {clerk_user_id}")
    
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
        
        logging.info(f"👤 CREATING NEW USER FOR ROLE SETUP - Name: '{user_name}', Email: '{user_email}'")
        
        # Create new user in database WITHOUT role
        new_user = {
            "id": str(uuid.uuid4()),
            "clerk_user_id": clerk_user_id,
            "name": user_name,
            "email": user_email,
            "role": None,  # No role yet - will be set by role setup
            "client_id": "",
            "created_at": datetime.utcnow()
        }
        
        await db.users.insert_one(new_user)
        user = new_user
        logging.info(f"✅ NEW USER CREATED FOR ROLE SETUP: {user['id']} - {user['name']} ({user['email']})")
    else:
        # Eski user kayıtlarında 'id' field'ı olmayabilir, kontrol edelim
        if 'id' not in user:
            # Eski kayıt için UUID oluştur ve güncelle
            user_id = str(uuid.uuid4())
            await db.users.update_one(
                {"clerk_user_id": clerk_user_id},
                {"$set": {"id": user_id}}
            )
            user['id'] = user_id
            logging.info(f"🔧 UPDATED OLD USER RECORD with ID: {user_id}")
        
        logging.info(f"✅ USER FOUND FOR ROLE SETUP: {user['id']} - {user['name']} ({user['email']}) - Role: {user.get('role', 'None')}")
    
    # Return user data as dict (not User object since role might be None)
    return {
        "id": user["id"],
        "clerk_user_id": user["clerk_user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role"),
        "client_id": user.get("client_id", ""),
        "created_at": user["created_at"]
    }

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
        # Eski user kayıtlarında 'id' field'ı olmayabilir, kontrol edelim
        if 'id' not in user:
            # Eski kayıt için UUID oluştur ve güncelle
            user_id = str(uuid.uuid4())
            await db.users.update_one(
                {"clerk_user_id": clerk_user_id},
                {"$set": {"id": user_id}}
            )
            user['id'] = user_id
            logging.info(f"🔧 UPDATED OLD USER RECORD with ID: {user_id}")
            
        logging.info(f"✅ USER FOUND: {user['id']} - {user['name']} ({user['email']}) - Role: {user['role']}")
    
    # Convert to User object
    user_role = user.get("role")
    if not user_role or user_role in [None, "", "null"]:
        # If no role set, raise specific exception for role setup
        raise HTTPException(status_code=422, detail="User role not set, needs role selection")
    
    return User(
        id=user["id"],
        clerk_user_id=user["clerk_user_id"],
        name=user["name"],
        email=user["email"],
        role=UserRole(user_role),
        client_id=user.get("client_id", ""),
        consultant_id=user.get("consultant_id"),
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
    """Health check endpoint - NO AUTHENTICATION REQUIRED"""
    return {
        "status": "healthy",
        "service": "Rota CRM Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "api_router_mounted": True
    }

# Root path for testing
@app.get("/")
async def root():
    """Root endpoint for testing"""
    return {"message": "Rota CRM Backend is running", "status": "ok"}

# Health endpoint also on main app for testing
@app.get("/health")  
async def health_check_main():
    """Main app health check - NO AUTH"""
    return {
        "status": "healthy",
        "service": "Rota CRM Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "main_app": True
    }

# ==========================================
# CONSULTANT MANAGEMENT - MAIN APP ENDPOINTS
# ==========================================

@app.post("/api/consultants")
async def create_consultant(consultant_data: ConsultantCreate):
    """Create a new consultant - NO AUTH for registration"""
    try:
        consultant = Consultant(**consultant_data.dict()).dict()
        result = await db.consultants.insert_one(consultant)
        
        return {
            "message": "Consultant created successfully",
            "consultant_id": consultant["id"]
        }
    except Exception as e:
        logging.error(f"Error creating consultant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/consultants/register-with-user")
async def register_consultant_with_user(
    request_data: dict,
    current_user_data: dict = Depends(get_current_user_for_role_setup)
):
    """Register consultant and update user role - AUTH required"""
    try:
        consultant_data = request_data.get("consultant_data")
        if not consultant_data:
            raise HTTPException(status_code=400, detail="Consultant data is required")
        
        # Create consultant record
        consultant = Consultant(**consultant_data).dict()
        await db.consultants.insert_one(consultant)
        
        # Update user role to CONSULTANT
        await db.users.update_one(
            {"id": current_user_data["id"]},
            {"$set": {
                "role": "consultant",
                "consultant_id": consultant["id"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        logging.info(f"✅ USER ROLE UPDATED: {current_user_data['id']} is now CONSULTANT")
        
        return {
            "message": "Consultant created and user role updated successfully",
            "consultant_id": consultant["id"]
        }
    except Exception as e:
        logging.error(f"Error creating consultant with user update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/clients/register-with-user")
async def register_client_with_user(
    request_data: dict,
    current_user_data: dict = Depends(get_current_user_for_role_setup)
):
    """Register client and update user role - AUTH required"""
    try:
        client_data = request_data.get("client_data")
        if not client_data:
            raise HTTPException(status_code=400, detail="Client data is required")
        
        # Create client record
        client = Client(**client_data).dict()
        await db.clients.insert_one(client)
        
        # 🏗️ AUTOMATIC FOLDER CREATION FOR NEW CLIENT
        try:
            logging.info(f"🏗️ AUTO FOLDER CREATION: Starting for client {client['id']}")
            # Client model'inda field name -> 'name', hotel_name -> 'hotel_name'
            client_display_name = client.get("name") or client.get("hotel_name") or "Unknown Client"
            await create_client_root_folder(client["id"], client_display_name)
            logging.info(f"✅ AUTO FOLDER CREATION: Completed for client {client['id']} - {client_display_name}")
        except Exception as folder_error:
            logging.error(f"❌ AUTO FOLDER CREATION ERROR: {str(folder_error)}")
            # Don't fail the registration if folder creation fails
            pass
        
        # Update user role to CLIENT and link to client
        await db.users.update_one(
            {"id": current_user_data["id"]},
            {"$set": {
                "role": "client",
                "client_id": client["id"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        logging.info(f"✅ USER ROLE UPDATED: {current_user_data['id']} is now CLIENT")
        
        return {
            "message": "Client created and user role updated successfully",
            "client_id": client["id"]
        }
    except Exception as e:
        logging.error(f"Error creating client with user update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/init-default-consultant")
async def init_default_consultant():
    """Initialize default ROTA consultant - NO AUTH needed"""
    try:
        # Check if ROTA consultant already exists
        existing = await db.consultants.find_one({"company_name": "ROTA"})
        if existing:
            return {"message": "ROTA consultant already exists", "consultant_id": existing["id"]}
        
        # Create ROTA as the default consultant
        rota_consultant = Consultant(
            company_name="ROTA",
            authorized_person_name="ROTA Sistem Yöneticisi",
            email="admin@rota.com",
            phone="0532 000 00 00",
            address="ROTA Merkez Ofis",
            is_active=True,
            total_clients=0
        ).dict()
        
        result = await db.consultants.insert_one(rota_consultant)
        
        return {
            "message": "ROTA default consultant created successfully",
            "consultant_id": rota_consultant["id"]
        }
    except Exception as e:
        logging.error(f"Error creating default consultant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/consultants")
async def get_consultants():
    """Get all active consultants - NO AUTH for client signup"""
    try:
        consultants = await db.consultants.find({"is_active": True}).to_list(length=None)
        
        clean_consultants = []
        for consultant in consultants:
            if "_id" in consultant:
                del consultant["_id"]
            clean_consultants.append(consultant)
        
        return clean_consultants
    except Exception as e:
        logging.error(f"Error fetching consultants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/init-admin-user")
async def init_admin_user(admin_data: dict):
    """Initialize admin user for ROTA - Special endpoint"""
    try:
        # Create admin user in users collection
        admin_user = User(
            clerk_user_id=admin_data.get("clerk_user_id", "admin_rota"),
            email=admin_data.get("email", "admin@rota.com"),
            name=admin_data.get("name", "ROTA Admin"),
            role=UserRole.ADMIN,
            consultant_id=admin_data.get("consultant_id")  # Link to ROTA consultant
        ).dict()
        
        # Check if admin already exists
        existing = await db.users.find_one({"email": admin_user["email"]})
        if existing:
            return {"message": "Admin user already exists", "user_id": existing["id"]}
        
        result = await db.users.insert_one(admin_user)
        
        return {
            "message": "Admin user created successfully",
            "user_id": admin_user["id"],
            "instructions": "Bu kullanıcı ile Clerk'te aynı email ile kayıt olun ve admin yetkileriniz otomatik aktif olacaktır."
        }
    except Exception as e:
        logging.error(f"Error creating admin user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/consultants/{consultant_id}")
async def get_consultant(consultant_id: str, current_user: User = Depends(get_current_user)):
    """Get consultant details"""
    try:
        consultant = await db.consultants.find_one({"id": consultant_id})
        if not consultant:
            raise HTTPException(status_code=404, detail="Consultant not found")
        
        if "_id" in consultant:
            del consultant["_id"]
        
        return consultant
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching consultant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.put("/api/consultants/{consultant_id}")
async def update_consultant(
    consultant_id: str,
    consultant_data: ConsultantCreate,
    current_user: User = Depends(get_current_user)
):
    """Update consultant - Admin or self only"""
    try:
        # Check if consultant exists
        existing = await db.consultants.find_one({"id": consultant_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Consultant not found")
        
        # Check permissions
        if current_user.role != UserRole.ADMIN and current_user.consultant_id != consultant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        update_data = consultant_data.dict()
        update_data["updated_at"] = datetime.utcnow()
        
        await db.consultants.update_one(
            {"id": consultant_id},
            {"$set": update_data}
        )
        
        return {"message": "Consultant updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating consultant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/consultants/{consultant_id}/clients")
async def get_consultant_clients(
    consultant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get clients managed by consultant"""
    try:
        # Check permissions
        if current_user.role != UserRole.ADMIN and current_user.consultant_id != consultant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
        
        clean_clients = []
        for client in clients:
            if "_id" in client:
                del client["_id"]
            clean_clients.append(client)
        
        return clean_clients
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching consultant clients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/consultants/{consultant_id}/dashboard")
async def get_consultant_dashboard(
    consultant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get consultant dashboard data"""
    try:
        # Check permissions
        if current_user.role != UserRole.ADMIN and current_user.consultant_id != consultant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get consultant clients
        clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
        
        # Calculate stats
        total_clients = len(clients)
        active_clients = len([c for c in clients if c.get("current_stage") != ProjectStage.STAGE_3])
        
        # Get all module data for clients
        client_ids = [c["id"] for c in clients]
        
        # Personnel count
        personnel_count = await db.personnel.count_documents({"client_id": {"$in": client_ids}})
        
        # Suppliers count
        suppliers_count = await db.suppliers.count_documents({"client_id": {"$in": client_ids}})
        
        # Sustainability targets count
        targets_count = await db.sustainability_targets.count_documents({"client_id": {"$in": client_ids}})
        
        # Recent activity - last 10 documents
        recent_documents = await db.documents.find(
            {"client_id": {"$in": client_ids}}
        ).sort("created_at", -1).limit(10).to_list(length=None)
        
        return {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "completed_clients": total_clients - active_clients,
            "personnel_count": personnel_count,
            "suppliers_count": suppliers_count,
            "targets_count": targets_count,
            "recent_documents": len(recent_documents),
            "clients": [{"id": c["id"], "name": c["name"], "hotel_name": c["hotel_name"], "current_stage": c["current_stage"]} for c in clients]
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching consultant dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/api/consultants/{consultant_id}")
async def delete_consultant(
    consultant_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete consultant - Admin only"""
    try:
        # Only admin can delete consultants
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if consultant exists
        existing = await db.consultants.find_one({"id": consultant_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Consultant not found")
        
        # Don't allow deletion of ROTA consultant
        if existing.get("company_name") == "ROTA":
            raise HTTPException(status_code=400, detail="Cannot delete ROTA consultant")
        
        # Check if consultant has clients
        clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
        if clients:
            raise HTTPException(status_code=400, detail="Cannot delete consultant with assigned clients")
        
        # Delete consultant
        await db.consultants.delete_one({"id": consultant_id})
        
        return {"message": "Consultant deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting consultant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.put("/api/clients/{client_id}/consultant")
async def assign_client_to_consultant(
    client_id: str,
    consultant_assignment: dict,
    current_user: User = Depends(get_current_user)
):
    """Assign client to consultant - Admin only"""
    try:
        # Only admin can assign clients
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
        
        consultant_id = consultant_assignment.get("consultant_id")
        if not consultant_id:
            raise HTTPException(status_code=400, detail="Consultant ID is required")
        
        # Check if client exists
        existing_client = await db.clients.find_one({"id": client_id})
        if not existing_client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check if consultant exists
        existing_consultant = await db.consultants.find_one({"id": consultant_id})
        if not existing_consultant:
            raise HTTPException(status_code=404, detail="Consultant not found")
        
        # Update client's consultant_id
        await db.clients.update_one(
            {"id": client_id},
            {"$set": {
                "consultant_id": consultant_id,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Update consultant's total_clients count
        client_count = await db.clients.count_documents({"consultant_id": consultant_id})
        await db.consultants.update_one(
            {"id": consultant_id},
            {"$set": {
                "total_clients": client_count,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {"message": "Client assigned to consultant successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error assigning client to consultant: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/consultants/assign-unassigned")
async def assign_unassigned_clients_to_rota(
    current_user: User = Depends(get_current_user)
):
    """Assign all unassigned clients to ROTA consultant - Admin only"""
    try:
        # Only admin can perform this action
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Find ROTA consultant
        rota_consultant = await db.consultants.find_one({"company_name": "ROTA"})
        if not rota_consultant:
            raise HTTPException(status_code=404, detail="ROTA consultant not found")
        
        # Find all unassigned clients
        unassigned_clients = await db.clients.find({
            "$or": [
                {"consultant_id": {"$exists": False}},
                {"consultant_id": None},
                {"consultant_id": ""}
            ]
        }).to_list(length=None)
        
        if not unassigned_clients:
            return {"message": "No unassigned clients found", "assigned_count": 0}
        
        # Assign all unassigned clients to ROTA
        client_ids = [client["id"] for client in unassigned_clients]
        await db.clients.update_many(
            {"id": {"$in": client_ids}},
            {"$set": {
                "consultant_id": rota_consultant["id"],
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Update ROTA consultant's total_clients count
        total_clients = await db.clients.count_documents({"consultant_id": rota_consultant["id"]})
        await db.consultants.update_one(
            {"id": rota_consultant["id"]},
            {"$set": {
                "total_clients": total_clients,
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {
            "message": "Unassigned clients assigned to ROTA successfully",
            "assigned_count": len(unassigned_clients),
            "client_names": [client.get("hotel_name", client.get("name", "Unknown")) for client in unassigned_clients]
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error assigning unassigned clients: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/debug/users")
async def debug_users():
    """Debug endpoint to check user roles - REMOVE IN PRODUCTION"""
    try:
        users = await db.users.find({}).to_list(length=None)
        
        clean_users = []
        for user in users:
            if "_id" in user:
                del user["_id"]
            clean_users.append(user)
        
        return {
            "total_users": len(clean_users),
            "users": clean_users
        }
    except Exception as e:
        logging.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/debug/consultants")
async def debug_consultants():
    """Debug endpoint to check consultants - REMOVE IN PRODUCTION"""
    try:
        consultants = await db.consultants.find({}).to_list(length=None)
        
        clean_consultants = []
        for consultant in consultants:
            if "_id" in consultant:
                del consultant["_id"]
            clean_consultants.append(consultant)
        
        return {
            "total_consultants": len(clean_consultants),
            "consultants": clean_consultants
        }
    except Exception as e:
        logging.error(f"Error fetching consultants: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/debug/fix-user-role")
async def fix_user_role(request_data: dict):
    """Fix user role - REMOVE IN PRODUCTION"""
    try:
        email = request_data.get("email")
        new_role = request_data.get("role")  # "consultant", "client", "admin"
        
        if not email or not new_role:
            raise HTTPException(status_code=400, detail="Email and role are required")
        
        if new_role not in ["consultant", "client", "admin"]:
            raise HTTPException(status_code=400, detail="Role must be consultant, client, or admin")
        
        # Find user by email
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user role
        update_data = {"role": new_role, "updated_at": datetime.utcnow()}
        
        # If changing to consultant, find their consultant record
        if new_role == "consultant":
            consultant = await db.consultants.find_one({"email": email})
            if consultant:
                update_data["consultant_id"] = consultant["id"]
        
        await db.users.update_one(
            {"email": email},
            {"$set": update_data}
        )
        
        return {
            "message": f"User role updated to {new_role}",
            "user_email": email,
            "old_role": user.get("role"),
            "new_role": new_role
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fixing user role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/debug/database-check")
async def debug_database_check():
    """DEBUG: Check database state for consultant-client relationships"""
    try:
        # Check all consultants
        consultants = await db.consultants.find().to_list(length=None)
        logging.info(f"🔍 DB DEBUG - Found {len(consultants)} consultants")
        
        # Check all clients with full data
        clients = await db.clients.find().to_list(length=None)
        logging.info(f"🔍 DB DEBUG - Found {len(clients)} clients")
        
        # Log each client's full data
        for i, client in enumerate(clients):
            logging.info(f"🔍 CLIENT {i+1} FULL DATA: {client}")
        
        # Check specific consultant
        target_consultant_id = "678d2dfc-b008-4cbc-99d2-1aeed51c81d3"
        assigned_clients = await db.clients.find({"consultant_id": target_consultant_id}).to_list(length=None)
        logging.info(f"🔍 DB DEBUG - Clients assigned to {target_consultant_id}: {len(assigned_clients)}")
        
        # Log assigned clients full data
        for i, client in enumerate(assigned_clients):
            logging.info(f"🔍 ASSIGNED CLIENT {i+1} FULL DATA: {client}")
        
        return {
            "total_consultants": len(consultants),
            "total_clients": len(clients),
            "target_consultant_id": target_consultant_id,
            "assigned_clients_count": len(assigned_clients),
            "consultants": [{"id": c.get("id"), "name": c.get("name"), "email": c.get("email")} for c in consultants],
            "clients": clients,  # Return full client objects
            "assigned_clients": assigned_clients  # Return full assigned client objects
        }
    except Exception as e:
        logging.error(f"Error in database debug: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@app.get("/api/debug/clients-query")
async def debug_clients_query(current_user: User = Depends(get_current_user)):
    """DEBUG: Test MongoDB clients query for consultant"""
    try:
        logging.info(f"🔍 DEBUG CLIENTS QUERY - User: {current_user.email}")
        logging.info(f"🔍 DEBUG CLIENTS QUERY - Role: {current_user.role}")
        logging.info(f"🔍 DEBUG CLIENTS QUERY - consultant_id: {getattr(current_user, 'consultant_id', None)}")
        
        consultant_id = getattr(current_user, 'consultant_id', None)
        
        # Raw MongoDB query
        all_clients = await db.clients.find().to_list(length=None)
        logging.info(f"🔍 ALL CLIENTS IN DB: {len(all_clients)}")
        
        for client in all_clients:
            logging.info(f"🔍 CLIENT: id={client.get('id')}, consultant_id={client.get('consultant_id')}, type={type(client.get('consultant_id'))}")
        
        # Filtered query
        if consultant_id:
            filtered_clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
            logging.info(f"🔍 FILTERED CLIENTS: {len(filtered_clients)}")
            logging.info(f"🔍 QUERY: consultant_id={consultant_id}, type={type(consultant_id)}")
        
        return {
            "user_consultant_id": consultant_id,
            "user_consultant_id_type": str(type(consultant_id)),
            "total_clients": len(all_clients),
            "filtered_clients": len(filtered_clients) if consultant_id else 0,
            "all_clients": [{"id": c.get("id"), "consultant_id": c.get("consultant_id"), "consultant_id_type": str(type(c.get("consultant_id")))} for c in all_clients]
        }
    except Exception as e:
        logging.error(f"Error in debug clients query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@app.get("/api/debug/user-info")
async def debug_user_info(current_user: User = Depends(get_current_user)):
    """DEBUG: Get complete user information"""
    try:
        logging.info(f"🔍 DEBUG USER INFO - ID: {current_user.id}")
        logging.info(f"🔍 DEBUG USER INFO - Email: {current_user.email}")
        logging.info(f"🔍 DEBUG USER INFO - Role: {current_user.role}")
        logging.info(f"🔍 DEBUG USER INFO - Client ID: {current_user.client_id}")
        logging.info(f"🔍 DEBUG USER INFO - Consultant ID: {getattr(current_user, 'consultant_id', None)}")
        
        # If consultant, find clients assigned to this consultant
        if current_user.role == UserRole.CONSULTANT:
            consultant_id = getattr(current_user, 'consultant_id', None)
            logging.info(f"🔍 CONSULTANT DEBUG - Looking for clients with consultant_id: {consultant_id}")
            
            if consultant_id:
                clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
                logging.info(f"🔍 CONSULTANT DEBUG - Found {len(clients)} clients assigned to consultant")
                for client in clients:
                    logging.info(f"🔍 CLIENT DEBUG - ID: {client.get('id')}, Name: {client.get('client_name')}")
            else:
                logging.warning("⚠️ CONSULTANT has no consultant_id assigned!")
        
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role.value,
            "client_id": current_user.client_id,
            "consultant_id": getattr(current_user, 'consultant_id', None),
            "debug": "Check server logs for detailed information"
        }
    except Exception as e:
        logging.error(f"Error in debug user info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    try:
        return {
            "id": current_user.id,
            "clerk_user_id": current_user.clerk_user_id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role.value,
            "client_id": current_user.client_id,
            "consultant_id": getattr(current_user, 'consultant_id', None),
            "created_at": current_user.created_at
        }
    except Exception as e:
        logging.error(f"Error getting current user info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Sustainability Target Models
class SustainabilityTargetInput(BaseModel):
    target_name: str
    category: str  # "Çevresel", "Sosyal", "Ekonomik"
    target_type: str  # "Karbon Ayak İzi", "Su Tüketimi", "Yerel İstihdam", etc.
    target_value: float
    unit: str  # "%", "kg", "litre", "TL", "saat"
    target_period: str  # "Aylık", "Çeyreklik", "Yıllık"
    deadline: datetime
    description: Optional[str] = None
    client_id: Optional[str] = None

class SustainabilityTarget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    target_name: str
    category: str
    target_type: str
    target_value: float
    unit: str
    target_period: str
    deadline: datetime
    description: Optional[str] = None
    status: str = Field(default="active")  # "active", "completed", "overdue"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TargetProgressInput(BaseModel):
    target_id: str
    actual_value: float
    progress_date: datetime
    notes: Optional[str] = None

class TargetProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str
    actual_value: float
    progress_date: datetime
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ALSO ADD API HEALTH TO MAIN APP - WORKAROUND
@app.get("/api/health")
async def api_health_check_direct():
    """Direct API health check on main app - NO AUTH"""
    return {
        "status": "healthy",
        "service": "Rota CRM Backend", 
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "api_direct": True
    }

# ==========================================
# YENİ BELGE YÖNETİMİ - MAIN APP ENDPOINTS
# ==========================================

@app.post("/api/belge/upload")
async def upload_belge_main_app(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_id: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    stage: str = Form(...),
    description: str = Form(default=""),
    current_user: User = Depends(get_current_user)
):
    """🚀 YENİ BELGE YÜKLEME - MAIN APP"""
    try:
        logging.info(f"📤 BELGE UPLOAD MAIN APP: {file.filename} -> Client: {client_id}, User: {current_user.email}")
        
        # Security: Check if user can upload to this client
        if current_user.role == UserRole.CLIENT:
            if current_user.client_id != client_id:
                raise HTTPException(status_code=403, detail="Bu müşteri için belge yükleme yetkiniz yok")
        elif current_user.role == UserRole.CONSULTANT:
            # Check if client is assigned to this consultant
            consultant_id = getattr(current_user, 'consultant_id', None)
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Danışman ID bulunamadı")
            
            # Get MongoDB connection
            mongo_client = MongoClient(mongo_url)
            db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
            
            client = await asyncio.to_thread(db.clients.find_one, {"id": client_id})
            if not client or client.get("consultant_id") != consultant_id:
                raise HTTPException(status_code=403, detail="Bu müşteri için belge yükleme yetkiniz yok")
        # Admin can upload to any client
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Basic validation
        if not client_id or not folder_id:
            raise HTTPException(status_code=400, detail="Client ID ve Folder ID gerekli")
        
        # Generate document ID and save file
        document_id = str(uuid.uuid4())
        
        # EMERGENCY FIX: Direct MongoDB Binary Storage (GridFS yerine)
        # Save file content as binary in MongoDB document
        file_content = await file.read()
        file_size = len(file_content)
        
        # SIMPLE MONGODB BINARY STORAGE - NO GRIDFS
        # Store file content directly in document as binary
        logging.info(f"✅ File content read: {file_size} bytes, storing directly in MongoDB")
        
        # Generate a unique file ID for reference
        file_id = str(uuid.uuid4())
        
        # Save metadata AND binary content to MongoDB
        document_data = {
            "id": document_id,
            "client_id": client_id,
            "folder_id": folder_id,
            "document_name": document_name,
            "document_type": document_type,
            "stage": stage,
            "description": description,
            "filename": file.filename,
            "original_filename": file.filename,
            "file_id": file_id,
            "file_content": file_content,  # DIRECT BINARY STORAGE
            "file_size": file_size,
            "created_at": datetime.utcnow(),
            "status": "active",
            "binary_storage": True  # Mark as direct binary storage
        }
        
        result = await asyncio.to_thread(db.documents.insert_one, document_data)
        logging.info(f"✅ Metadata saved: {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "message": "Belge başarıyla yüklendi",
            "file_size": file_size
        }
        
    except Exception as e:
        logging.error(f"❌ BELGE UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload hatası: {str(e)}")

@app.get("/api/belge/list")
async def list_belge_main_app(current_user: User = Depends(get_current_user)):
    """📋 BELGE LİSTESİ - MAIN APP"""
    try:
        logging.info(f"📋 BELGE LIST MAIN APP: User: {current_user.email}, Role: {current_user.role}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Build query based on user role
        query = {"status": {"$ne": "deleted"}}
        
        if current_user.role == UserRole.ADMIN:
            # Admin sees all documents
            pass  # No additional filtering
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant sees documents for their assigned clients
            consultant_id = getattr(current_user, 'consultant_id', None)
            if not consultant_id:
                return {"success": True, "documents": [], "count": 0}
            
            # Get all clients assigned to this consultant
            clients = list(db.clients.find({"consultant_id": consultant_id}))
            client_ids = [client.get("id") for client in clients]
            
            if client_ids:
                query["client_id"] = {"$in": client_ids}
            else:
                return {"success": True, "documents": [], "count": 0}
        else:
            # Client sees only their own documents
            if not current_user.client_id:
                return {"success": True, "documents": [], "count": 0}
            query["client_id"] = current_user.client_id
        
        # Get documents
        documents = await asyncio.to_thread(
            lambda: list(db.documents.find(query).sort("created_at", -1))
        )
        
        # Format response - EXCLUDE BINARY CONTENT from list
        formatted_docs = []
        for doc in documents:
            if "_id" in doc:
                del doc["_id"]
            # EXCLUDE binary content field from list response (too large for JSON)
            if "file_content" in doc:
                del doc["file_content"]
            formatted_docs.append(doc)
        
        logging.info(f"✅ Found {len(formatted_docs)} documents")
        
        return {
            "success": True,
            "documents": formatted_docs,
            "count": len(formatted_docs)
        }
        
    except Exception as e:
        logging.error(f"❌ BELGE LIST ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Liste hatası: {str(e)}")

@app.get("/api/belge/download/{document_id}")
async def download_belge_main_app(document_id: str, current_user: User = Depends(get_current_user)):
    """📥 BELGE İNDİRME - MAIN APP"""
    try:
        logging.info(f"📥 BELGE DOWNLOAD MAIN APP: {document_id}, User: {current_user.email}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Find document
        document = await asyncio.to_thread(db.documents.find_one, {"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Belge bulunamadı")
        
        # Security: Check if user can download this document
        document_client_id = document.get("client_id")
        if current_user.role == UserRole.CLIENT:
            if current_user.client_id != document_client_id:
                raise HTTPException(status_code=403, detail="Bu belgeye erişim yetkiniz yok")
        elif current_user.role == UserRole.CONSULTANT:
            # Check if document's client is assigned to this consultant
            consultant_id = getattr(current_user, 'consultant_id', None)
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Danışman ID bulunamadı")
            
            client = await asyncio.to_thread(db.clients.find_one, {"id": document_client_id})
            if not client or client.get("consultant_id") != consultant_id:
                raise HTTPException(status_code=403, detail="Bu belgeye erişim yetkiniz yok")
        # Admin can download any document
        
        # SIMPLE MONGODB BINARY STORAGE - NO GRIDFS
        if document.get("binary_storage", False) and document.get("file_content"):
            # New binary storage files
            try:
                file_data = document["file_content"]
                original_filename = document.get("original_filename", "document.pdf")
                
                # FIX: UTF-8 filename encoding for Turkish characters
                import urllib.parse
                encoded_filename = urllib.parse.quote(original_filename, safe='')
                
                logging.info(f"✅ Downloaded from MongoDB binary: {original_filename} ({len(file_data)} bytes)")
                
                return Response(
                    content=file_data,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                    }
                )
            except Exception as e:
                logging.error(f"❌ Binary download error: {str(e)}")
                raise HTTPException(status_code=404, detail="Binary dosya bulunamadı")
        elif document.get("gridfs_upload", False) and document.get("file_id"):
            # Legacy GridFS files
            try:
                # Handle both string and object file_id formats
                file_id_data = document["file_id"]
                if isinstance(file_id_data, dict):
                    # Object format: {"file_id": "actual_id", ...}
                    actual_file_id = file_id_data.get("file_id")
                else:
                    # String format: "actual_id"
                    actual_file_id = file_id_data
                
                if not actual_file_id:
                    raise Exception("file_id not found in document")
                
                file_data, file_metadata = await mongo_gridfs.download_file(actual_file_id)
                original_filename = document.get("original_filename", "document.pdf")
                
                # FIX: UTF-8 filename encoding for Turkish characters
                import urllib.parse
                encoded_filename = urllib.parse.quote(original_filename, safe='')
                
                logging.info(f"✅ Downloaded from GridFS: {original_filename} ({len(file_data)} bytes)")
                
                return Response(
                    content=file_data,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                    }
                )
            except Exception as e:
                logging.error(f"❌ GridFS download error: {str(e)}")
                raise HTTPException(status_code=404, detail="GridFS dosya bulunamadı")
        else:
            # Legacy disk files (will be 404 after restart)
            file_path = document.get("file_path")
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Dosya bulunamadı (disk storage deprecated)")
            
            original_filename = document.get("original_filename", "document.pdf")
            logging.info(f"✅ Returning legacy file: {original_filename}")
            
            return FileResponse(
                path=file_path,
                filename=original_filename,
                headers={
                    "Content-Disposition": f'attachment; filename="{original_filename}"',
                    "Content-Type": "application/octet-stream"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ BELGE DOWNLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"İndirme hatası: {str(e)}")

@app.delete("/api/belge/delete/{document_id}")
async def delete_belge_main_app(document_id: str, current_user: User = Depends(get_current_user)):
    """🗑️ BELGE SİLME - MAIN APP - GERÇEK SİLME"""
    try:
        logging.info(f"🗑️ BELGE DELETE MAIN APP: {document_id}, User: {current_user.email}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Find document
        document = await asyncio.to_thread(db.documents.find_one, {"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Belge bulunamadı")
        
        # Security: Check if user can delete this document
        document_client_id = document.get("client_id")
        if current_user.role == UserRole.CLIENT:
            # Clients generally shouldn't delete documents, but if allowed:
            if current_user.client_id != document_client_id:
                raise HTTPException(status_code=403, detail="Bu belgeyi silme yetkiniz yok")
        elif current_user.role == UserRole.CONSULTANT:
            # Check if document's client is assigned to this consultant
            consultant_id = getattr(current_user, 'consultant_id', None)
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Danışman ID bulunamadı")
            
            client = await asyncio.to_thread(db.clients.find_one, {"id": document_client_id})
            if not client or client.get("consultant_id") != consultant_id:
                raise HTTPException(status_code=403, detail="Bu belgeyi silme yetkiniz yok")
        # Admin can delete any document
        
        # 1. DELETE FILE FROM DISK FIRST
        file_path = document.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"✅ File removed from disk: {file_path}")
        
        # 2. DELETE DOCUMENT FROM DATABASE (REAL DELETE)
        delete_result = await asyncio.to_thread(
            db.documents.delete_one,
            {"id": document_id}
        )
        
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Doküman silinemedi")
        
        logging.info(f"✅ Document PERMANENTLY deleted: {document_id}")
        
        return {"success": True, "message": "Belge kalıcı olarak silindi"}
        
    except Exception as e:
        logging.error(f"❌ BELGE DELETE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Silme hatası: {str(e)}")

@app.get("/api/clients")
async def get_clients_main_app(current_user: User = Depends(get_current_user)):
    """📋 CLİENTS LİSTESİ - MAIN APP WITH RBAC"""
    try:
        logging.info(f"📋 CLIENTS LIST MAIN APP - Role: {current_user.role}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Apply RBAC filtering
        if current_user.role == UserRole.ADMIN:
            # Admin sees all clients
            clients = await asyncio.to_thread(
                lambda: list(db.clients.find({}))
            )
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant sees only their assigned clients
            consultant_id = getattr(current_user, 'consultant_id', None)
            logging.info(f"🔍 CONSULTANT USER - consultant_id: {consultant_id}")
            logging.info(f"🔍 CONSULTANT USER - consultant_id type: {type(consultant_id)}")
            
            if not consultant_id:
                logging.warning(f"⚠️ CONSULTANT USER has no consultant_id assigned: {current_user.email}")
                return []
            
            # DEBUG: Check all clients in database
            all_clients_debug = await asyncio.to_thread(
                lambda: list(db.clients.find({}))
            )
            logging.info(f"🔍 DEBUG - Total clients in DB: {len(all_clients_debug)}")
            for i, client in enumerate(all_clients_debug):
                client_consultant_id = client.get("consultant_id")
                logging.info(f"🔍 DEBUG CLIENT {i+1}: id={client.get('id')}, consultant_id={client_consultant_id}, type={type(client_consultant_id)}")
                logging.info(f"🔍 DEBUG MATCH CHECK: {consultant_id} == {client_consultant_id} = {consultant_id == client_consultant_id}")
            
            # Try multiple query approaches to handle type mismatches
            query_approaches = [
                {"consultant_id": consultant_id},                    # Direct match
                {"consultant_id": str(consultant_id)},               # String conversion
                {"consultant_id": {"$in": [consultant_id, str(consultant_id)]}}  # Either type
            ]
            
            clients = []
            for i, query in enumerate(query_approaches):
                try:
                    clients = await asyncio.to_thread(
                        lambda q=query: list(db.clients.find(q))
                    )
                    logging.info(f"📋 Query approach {i+1}: {query} -> Found {len(clients)} clients")
                    if len(clients) > 0:
                        break
                except Exception as e:
                    logging.error(f"❌ Query approach {i+1} failed: {str(e)}")
            
            logging.info(f"📋 FINAL RESULT: Found {len(clients)} clients for consultant: {consultant_id}")
        else:
            # Client sees only their own data
            if not current_user.client_id:
                return []
            
            clients = await asyncio.to_thread(
                lambda: list(db.clients.find({"id": current_user.client_id}))
            )
        
        # Format response
        formatted_clients = []
        for client in clients:
            if "_id" in client:
                del client["_id"]
            formatted_clients.append(client)
        
        logging.info(f"✅ Found {len(formatted_clients)} clients for {current_user.role}")
        return formatted_clients
        
    except Exception as e:
        logging.error(f"❌ CLIENTS LIST ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Clients liste hatası: {str(e)}")

@app.post("/api/folders/fix-d-level3-structure")
async def fix_d_level3_structure():
    """D level 3 klasörlerini sil ve doğru formatta yeniden oluştur"""
    try:
        logging.info("🏗️ Fixing D Level 3 structure with correct format (D1.1, D1.2, etc.)")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # DELETE existing level 3 folders for D1, D2, D3
        deleted_result = await asyncio.to_thread(
            db.folders.delete_many, {
                "level": 3,
                "name": {"$regex": "^D[123]"}
            }
        )
        logging.info(f"🗑️ Deleted {deleted_result.deleted_count} existing D-level3 folders")
        
        # CORRECT Level 3 structure for D folders (with dots)
        d_level3_structure = {
            "D1": ["D1.1", "D1.2", "D1.3", "D1.4"],
            "D2": ["D2.1", "D2.2", "D2.3", "D2.4", "D2.5", "D2.6"], 
            "D3": ["D3.1", "D3.2", "D3.3", "D3.4", "D3.5", "D3.6"]
        }
        
        # Get all D1, D2, D3 folders (level 2)
        d_folders = await asyncio.to_thread(
            lambda: list(db.folders.find({
                "level": 2,
                "name": {"$in": ["D1", "D2", "D3"]}
            }))
        )
        
        created_count = 0
        
        for d_folder in d_folders:
            folder_name = d_folder["name"]  # D1, D2, or D3
            client_id = d_folder["client_id"]
            
            if folder_name in d_level3_structure:
                level3_subfolders = d_level3_structure[folder_name]
                
                for subfolder_name in level3_subfolders:
                    # Use safe ID (replace dots with underscores for ID)
                    safe_name = subfolder_name.replace(".", "_")
                    level3_id = f"level3_{d_folder['id']}_{safe_name}"
                    level3_path = f"{d_folder['folder_path']}/{subfolder_name}"
                    
                    level3_data = {
                        "id": level3_id,
                        "client_id": client_id,
                        "name": subfolder_name,  # Display name with dots
                        "parent_folder_id": d_folder["id"],
                        "folder_path": level3_path,
                        "level": 3,
                        "created_at": datetime.utcnow()
                    }
                    
                    await asyncio.to_thread(db.folders.insert_one, level3_data)
                    created_count += 1
        
        logging.info(f"✅ Created {created_count} corrected D-level3 folders")
        
        return {
            "success": True,
            "message": f"Successfully fixed D-Level3 structure. Deleted old and created {created_count} correct folders",
            "structure": d_level3_structure,
            "folders_processed": len(d_folders)
        }
        
    except Exception as e:
        logging.error(f"❌ D-LEVEL3 FIX ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"D-Level3 fix error: {str(e)}")

@app.post("/api/folders/create-level4-structure")
async def create_level4_structure():
    """Tüm Level 2 ve Level 3 klasörleri için Level 4 yapısını oluştur"""
    try:
        logging.info("🏗️ Creating Level 4 structure for all Level 2 & 3 folders")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Level 4 klasörler - her Level 2 ve Level 3 için
        level4_folders = [
            "POLİTİKALAR",
            "PROSEDÜRLER", 
            "FORMLAR",
            "LİSTELER",
            "KAYITLAR"
        ]
        
        # Get all Level 2 and Level 3 folders
        parent_folders = await asyncio.to_thread(
            lambda: list(db.folders.find({"level": {"$in": [2, 3]}}))
        )
        
        created_count = 0
        
        for parent_folder in parent_folders:
            client_id = parent_folder["client_id"]
            parent_id = parent_folder["id"]
            parent_name = parent_folder["name"]
            parent_path = parent_folder["folder_path"]
            
            for folder_name in level4_folders:
                level4_id = f"level4_{parent_id}_{folder_name.lower()}"
                level4_path = f"{parent_path}/{folder_name}"
                
                # Check if already exists
                existing = await asyncio.to_thread(
                    db.folders.find_one, {"id": level4_id}
                )
                
                if not existing:
                    level4_data = {
                        "id": level4_id,
                        "client_id": client_id,
                        "name": folder_name,
                        "parent_folder_id": parent_id,
                        "folder_path": level4_path,
                        "level": 4,
                        "created_at": datetime.utcnow()
                    }
                    
                    await asyncio.to_thread(db.folders.insert_one, level4_data)
                    created_count += 1
        
        logging.info(f"✅ Created {created_count} Level 4 folders")
        
        return {
            "success": True,
            "message": f"Successfully created {created_count} Level 4 folders",
            "level4_structure": level4_folders,
            "parent_folders_processed": len(parent_folders)
        }
        
    except Exception as e:
        logging.error(f"❌ LEVEL4 CREATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Level4 creation error: {str(e)}")

@app.post("/api/folders/create-d-level3-structure")
async def create_d_level3_structure():
    """D1, D2, D3 klasörleri için level 3 yapısını oluştur"""
    try:
        logging.info("🏗️ Creating Level 3 structure for D1, D2, D3 folders")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Level 3 structure for D folders from photos
        d_level3_structure = {
            "D1": ["D11", "D12", "D13", "D14"],
            "D2": ["D21", "D22", "D23", "D24", "D25", "D26"], 
            "D3": ["D31", "D32", "D33", "D34", "D35", "D36"]
        }
        
        # Get all D1, D2, D3 folders (level 2)
        d_folders = await asyncio.to_thread(
            lambda: list(db.folders.find({
                "level": 2,
                "name": {"$in": ["D1", "D2", "D3"]}
            }))
        )
        
        created_count = 0
        
        for d_folder in d_folders:
            folder_name = d_folder["name"]  # D1, D2, or D3
            client_id = d_folder["client_id"]
            
            if folder_name in d_level3_structure:
                level3_subfolders = d_level3_structure[folder_name]
                
                for subfolder_name in level3_subfolders:
                    level3_id = f"level3_{d_folder['id']}_{subfolder_name}"
                    level3_path = f"{d_folder['folder_path']}/{subfolder_name}"
                    
                    # Check if already exists
                    existing = await asyncio.to_thread(
                        db.folders.find_one, {"id": level3_id}
                    )
                    
                    if not existing:
                        level3_data = {
                            "id": level3_id,
                            "client_id": client_id,
                            "name": subfolder_name,
                            "parent_folder_id": d_folder["id"],
                            "folder_path": level3_path,
                            "level": 3,
                            "created_at": datetime.utcnow()
                        }
                        
                        await asyncio.to_thread(db.folders.insert_one, level3_data)
                        created_count += 1
        
        logging.info(f"✅ Created {created_count} D-level3 folders")
        
        return {
            "success": True,
            "message": f"Successfully created {created_count} Level 3 folders for D1, D2, D3",
            "structure": d_level3_structure,
            "folders_processed": len(d_folders)
        }
        
    except Exception as e:
        logging.error(f"❌ D-LEVEL3 CREATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"D-Level3 creation error: {str(e)}")

@app.post("/api/folders/recreate-correct-structure")
async def recreate_correct_folder_structure():
    """Mevcut level 2,3 klasörleri sil ve doğru yapıyı oluştur"""
    try:
        logging.info("🏗️ Recreating correct folder structure from photos")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # DELETE all existing level 2 and level 3 folders
        deleted_level2 = await asyncio.to_thread(
            db.folders.delete_many, {"level": {"$in": [2, 3]}}
        )
        logging.info(f"🗑️ Deleted {deleted_level2.deleted_count} existing level 2&3 folders")
        
        # Get all clients
        clients = await asyncio.to_thread(lambda: list(db.clients.find({})))
        
        created_count = 0
        
        # Define correct folder structure from photos
        folder_structure = {
            "A SÜTUNU": ["A1", "A2", "A3", "A4", "A5", "A7.1", "A7.2", "A7.3", "A7.4", "A8", "A9", "A10"],
            "B SÜTUNU": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
            "C SÜTUNU": ["C1", "C2", "C3", "C4"],
            "D SÜTUNU": ["D1", "D2", "D3"]
        }
        
        for client in clients:
            client_id = client.get("id") or client.get("client_id")
            client_name = client.get("client_name", "Unknown Client")
            
            # Get level 1 folders for this client (A, B, C, D columns)
            level1_folders = await asyncio.to_thread(
                lambda: list(db.folders.find({"client_id": client_id, "level": 1}))
            )
            
            for level1_folder in level1_folders:
                folder_id = level1_folder["id"]
                folder_name = level1_folder["name"]  # A SÜTUNU, B SÜTUNU, etc.
                
                # Get correct subfolders for this column
                if folder_name in folder_structure:
                    subfolders = folder_structure[folder_name]
                    
                    for subfolder_name in subfolders:
                        level2_id = f"level2_{folder_id}_{subfolder_name.replace('.', '_')}"
                        level2_path = f"{level1_folder['folder_path']}/{subfolder_name}"
                        
                        level2_data = {
                            "id": level2_id,
                            "client_id": client_id,
                            "name": subfolder_name,
                            "parent_folder_id": folder_id,
                            "folder_path": level2_path,
                            "level": 2,
                            "created_at": datetime.utcnow()
                        }
                        
                        await asyncio.to_thread(db.folders.insert_one, level2_data)
                        created_count += 1
        
        logging.info(f"✅ Created {created_count} new correct folders")
        
        return {
            "success": True,
            "message": f"Successfully recreated folder structure. Deleted old folders and created {created_count} correct ones",
            "clients_processed": len(clients),
            "folder_structure": folder_structure
        }
        
    except Exception as e:
        logging.error(f"❌ FOLDER RECREATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Folder recreation error: {str(e)}")

@app.get("/api/folders/by-client/{client_id}")
async def get_folders_by_client(client_id: str):
    """Get folders for specific client only"""
    try:
        logging.info(f"📋 FOLDERS BY CLIENT: {client_id}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Get folders for specific client only
        folders = await asyncio.to_thread(
            lambda: list(db.folders.find({"client_id": client_id}).sort("level", 1))
        )
        
        # Format response
        formatted_folders = []
        for folder in folders:
            if "_id" in folder:
                del folder["_id"]
            formatted_folders.append(folder)
        
        logging.info(f"✅ Found {len(formatted_folders)} folders for client {client_id}")
        return formatted_folders
        
    except Exception as e:
        logging.error(f"❌ FOLDERS BY CLIENT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Folders by client error: {str(e)}")

@app.post("/api/folders/create-for-new-clients")
async def create_folders_for_new_clients():
    """Create complete folder structure for clients who don't have folders"""
    try:
        logging.info("🏗️ Creating folders for new clients")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Get all clients
        clients = await asyncio.to_thread(lambda: list(db.clients.find({})))
        
        created_count = 0
        
        for client in clients:
            client_id = client.get("id") or client.get("client_id")
            client_name = client.get("client_name", "Unknown Client")
            
            # Check if client already has folders
            existing_folders = await asyncio.to_thread(
                lambda: list(db.folders.find({"client_id": client_id}))
            )
            
            if existing_folders:
                continue  # Skip if client already has folders
            
            # Create root folder (level 0)
            root_id = f"root_{client_id}"
            root_data = {
                "id": root_id,
                "client_id": client_id,
                "name": f"{client_name} SYS",
                "parent_folder_id": None,
                "folder_path": f"{client_name} SYS",
                "level": 0,
                "created_at": datetime.utcnow()
            }
            
            await asyncio.to_thread(db.folders.insert_one, root_data)
            created_count += 1
            
            # Create level 1 folders (A, B, C, D columns)
            columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
            
            for column in columns:
                level1_id = f"{column.lower().replace(' ', '_')}_{client_id}"
                level1_data = {
                    "id": level1_id,
                    "client_id": client_id,
                    "name": column,
                    "parent_folder_id": root_id,
                    "folder_path": f"{client_name} SYS/{column}",
                    "level": 1,
                    "created_at": datetime.utcnow()
                }
                
                await asyncio.to_thread(db.folders.insert_one, level1_data)
                created_count += 1
                
                # Create level 2 folders (categories)
                level2_categories = [
                    "Politikalar",
                    "Prosedürler", 
                    "Talimatlar",
                    "Formlar",
                    "Kayıtlar"
                ]
                
                for category in level2_categories:
                    level2_id = f"level2_{level1_id}_{category.lower()}"
                    level2_data = {
                        "id": level2_id,
                        "client_id": client_id,
                        "name": category,
                        "parent_folder_id": level1_id,
                        "folder_path": f"{client_name} SYS/{column}/{category}",
                        "level": 2,
                        "created_at": datetime.utcnow()
                    }
                    
                    await asyncio.to_thread(db.folders.insert_one, level2_data)
                    created_count += 1
                    
                    # Create level 3 folders (document types)
                    level3_types = [
                        "TR1 Kriterleri",
                        "I. Aşama Belgesi",
                        "II. Aşama Belgesi", 
                        "III. Aşama Belgesi",
                        "Karbon Raporu",
                        "Sürdürülebilirlik Raporu"
                    ]
                    
                    for doc_type in level3_types:
                        level3_id = f"level3_{level2_id}_{doc_type.lower().replace(' ', '_').replace('.', '')}"
                        level3_data = {
                            "id": level3_id,
                            "client_id": client_id,
                            "name": doc_type,
                            "parent_folder_id": level2_id,
                            "folder_path": f"{client_name} SYS/{column}/{category}/{doc_type}",
                            "level": 3,
                            "created_at": datetime.utcnow()
                        }
                        
                        await asyncio.to_thread(db.folders.insert_one, level3_data)
                        created_count += 1
        
        logging.info(f"✅ Created {created_count} folders for new clients")
        
        return {
            "success": True,
            "message": f"Successfully created {created_count} folders for new clients",
            "clients_processed": len(clients)
        }
        
    except Exception as e:
        logging.error(f"❌ NEW CLIENT FOLDER CREATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"New client folder creation error: {str(e)}")

@app.post("/api/clients/create-test-clients")
async def create_test_clients():
    """Create test clients for today"""
    try:
        logging.info("🏨 Creating test clients for today")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        today = datetime.utcnow()
        test_clients = [
            {
                "id": f"GUNCEL_CLIENT_{today.strftime('%Y%m%d')}_001",
                "client_id": f"GUNCEL_CLIENT_{today.strftime('%Y%m%d')}_001",
                "client_name": "Güncel Test Otel",
                "hotel_name": "Güncel Test Otel", 
                "contact_person": "test@guncelotel.com",
                "email": "info@guncelotel.com",
                "current_stage": "I.Aşama",
                "created_at": today,
                "updated_at": today
            },
            {
                "id": f"YENI_CLIENT_{today.strftime('%Y%m%d')}_002",
                "client_id": f"YENI_CLIENT_{today.strftime('%Y%m%d')}_002", 
                "client_name": "Yeni Kalite Otel",
                "hotel_name": "Yeni Kalite Otel",
                "contact_person": "info@yenikalitotel.com",
                "email": "contact@yenikalitotel.com", 
                "current_stage": "II.Aşama",
                "created_at": today,
                "updated_at": today
            },
            {
                "id": f"MODERN_CLIENT_{today.strftime('%Y%m%d')}_003",
                "client_id": f"MODERN_CLIENT_{today.strftime('%Y%m%d')}_003",
                "client_name": "Modern Boutique Otel",
                "hotel_name": "Modern Boutique Otel",
                "contact_person": "rezervasyon@modernboutique.com",
                "email": "info@modernboutique.com",
                "current_stage": "I.Aşama", 
                "created_at": today,
                "updated_at": today
            }
        ]
        
        created_count = 0
        for client_data in test_clients:
            # Check if client already exists
            existing = await asyncio.to_thread(
                db.clients.find_one, {"id": client_data["id"]}
            )
            
            if not existing:
                await asyncio.to_thread(db.clients.insert_one, client_data)
                created_count += 1
        
        logging.info(f"✅ Created {created_count} new test clients")
        
        return {
            "success": True,
            "message": f"Successfully created {created_count} test clients for {today.strftime('%Y-%m-%d')}",
            "date": today.isoformat()
        }
        
    except Exception as e:
        logging.error(f"❌ CLIENT CREATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Client creation error: {str(e)}")

@app.post("/api/folders/create-missing-levels")
async def create_missing_folder_levels():
    """Create missing level 2 and level 3 folders for all clients"""
    try:
        logging.info("🏗️ Creating missing folder levels")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Get all clients
        clients = await asyncio.to_thread(lambda: list(db.clients.find({})))
        
        created_count = 0
        
        for client in clients:
            client_id = client.get("id") or client.get("client_id")
            client_name = client.get("client_name", "Unknown Client")
            
            # Get level 1 folders for this client (A, B, C, D columns)
            level1_folders = await asyncio.to_thread(
                lambda: list(db.folders.find({"client_id": client_id, "level": 1}))
            )
            
            for level1_folder in level1_folders:
                folder_id = level1_folder["id"]
                folder_name = level1_folder["name"]
                
                # Create level 2 folders (sub-categories)
                level2_categories = [
                    "Politikalar",
                    "Prosedürler", 
                    "Talimatlar",
                    "Formlar",
                    "Kayıtlar"
                ]
                
                for category in level2_categories:
                    level2_id = f"level2_{folder_id}_{category.lower()}"
                    level2_name = category
                    level2_path = f"{level1_folder['folder_path']}/{category}"
                    
                    # Check if already exists
                    existing = await asyncio.to_thread(
                        db.folders.find_one, {"id": level2_id}
                    )
                    
                    if not existing:
                        level2_data = {
                            "id": level2_id,
                            "client_id": client_id,
                            "name": level2_name,
                            "parent_folder_id": folder_id,
                            "folder_path": level2_path,
                            "level": 2,
                            "created_at": datetime.utcnow()
                        }
                        
                        await asyncio.to_thread(db.folders.insert_one, level2_data)
                        created_count += 1
                        
                        # Create level 3 folders (document types)
                        level3_types = [
                            "TR1 Kriterleri",
                            "I. Aşama Belgesi",
                            "II. Aşama Belgesi", 
                            "III. Aşama Belgesi",
                            "Karbon Raporu",
                            "Sürdürülebilirlik Raporu"
                        ]
                        
                        for doc_type in level3_types:
                            level3_id = f"level3_{level2_id}_{doc_type.lower().replace(' ', '_')}"
                            level3_name = doc_type
                            level3_path = f"{level2_path}/{doc_type}"
                            
                            level3_data = {
                                "id": level3_id,
                                "client_id": client_id,
                                "name": level3_name,
                                "parent_folder_id": level2_id,
                                "folder_path": level3_path,
                                "level": 3,
                                "created_at": datetime.utcnow()
                            }
                            
                            await asyncio.to_thread(db.folders.insert_one, level3_data)
                            created_count += 1
        
        logging.info(f"✅ Created {created_count} new folders")
        
        return {
            "success": True,
            "message": f"Successfully created {created_count} missing folder levels",
            "clients_processed": len(clients)
        }
        
    except Exception as e:
        logging.error(f"❌ FOLDER CREATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Folder creation error: {str(e)}")

# DOCUMENT MANAGEMENT ENDPOINTS - DIRECT TO MAIN APP
@app.get("/documents")
async def get_documents_direct(current_user: User = Depends(get_current_user)):
    """Get documents for email management - DIRECT ON MAIN APP"""
    try:
        # Get MongoDB connection - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Get documents from rotacrm
        documents = list(db.documents.find({}))
        
        # Format documents for frontend
        formatted_documents = []
        for doc in documents:
            if "_id" in doc:
                del doc["_id"]
            
            # DEBUG: Log folder_id info
            logging.info(f"🔍 Document: {doc.get('name', 'Unknown')} - Folder ID: {doc.get('folder_id', 'NULL')} - Folder Path: {doc.get('folder_path', 'NULL')}")
            
            # Handle datetime serialization for upload_date
            upload_date = doc.get("created_at")
            if upload_date and hasattr(upload_date, 'isoformat'):
                upload_date = upload_date.isoformat()
            elif not upload_date:
                upload_date = "2024-12-20T10:30:00.000Z"
            
            formatted_doc = {
                "id": doc.get("id", ""),
                "title": doc.get("name", doc.get("document_name", "Unknown Document")),
                "type": doc.get("document_type", "PDF"),
                "category": doc.get("stage", "General"),
                "upload_date": upload_date,  # Fixed datetime format
                "file_size": doc.get("file_size", "N/A"),
                "client_id": doc.get("client_id", "general"),
                "client_name": doc.get("client_name", "General"),
                "folder_id": doc.get("folder_id", ""),  # IMPORTANT: Add folder_id to response
                "folder_path": doc.get("folder_path", "")  # IMPORTANT: Add folder_path to response
            }
            formatted_documents.append(formatted_doc)
        
        return formatted_documents
        
    except Exception as e:
        print(f"Error in direct documents endpoint: {e}")
        return []

# ALSO ADD API DOCUMENTS ENDPOINT FOR DOCUMENT MANAGEMENT
@app.get("/api/documents")
async def get_documents_api_direct(current_user: User = Depends(get_current_user)):
    """Get documents for document management - DIRECT ON MAIN APP"""
    # Delegate to main documents function
    return await get_documents_direct(current_user)

# DOCUMENT DOWNLOAD ENDPOINTS - DIRECT TO MAIN APP
@app.get("/documents/{document_id}/download")
async def download_document_direct(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download document - DIRECT ON MAIN APP"""
    try:
        logging.info(f"📥 Direct download request: {current_user.name} - Document: {document_id}")
        
        # Get MongoDB connection - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Find document
        document = await asyncio.to_thread(db.documents.find_one, {"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user has access to this document
        if current_user.role == UserRole.CLIENT and current_user.client_id != document.get("client_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get file from GridFS
        import gridfs
        fs = gridfs.GridFS(db)
        
        # Get GridFS file ID
        gridfs_id = document.get("gridfs_id")
        if not gridfs_id:
            raise HTTPException(status_code=404, detail="File not found in storage")
        
        try:
            # Convert string ID to ObjectId
            from bson import ObjectId
            file_id = ObjectId(gridfs_id)
            
            # Get file from GridFS
            grid_file = fs.get(file_id)
            file_content = grid_file.read()
            
            from fastapi.responses import Response
            
            # Encode filename for Turkish characters
            filename = document.get('original_filename', 'document.pdf')
            # URL encode filename for Turkish characters
            import urllib.parse
            encoded_filename = urllib.parse.quote(filename, safe='')
            
            return Response(
                content=file_content,
                media_type=document.get('content_type', 'application/octet-stream'),
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                    "Content-Length": str(len(file_content))
                }
            )
            
        except Exception as e:
            logging.error(f"❌ Error retrieving file from GridFS: {e}")
            raise HTTPException(status_code=500, detail="Error retrieving file from storage")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Direct download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

# ALSO ADD API DOWNLOAD ENDPOINT FOR FRONTEND /api CALLS
@app.get("/api/documents/{document_id}/download")
async def download_document_api_direct(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download document via /api endpoint - DIRECT ON MAIN APP"""
    # Delegate to main download function
    return await download_document_direct(document_id, current_user)

@app.get("/trainings")  
async def get_trainings_direct(current_user: User = Depends(get_current_user)):
    """Get trainings for email management - DIRECT ON MAIN APP"""
    try:
        # Get MongoDB connections - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Get trainings from rotacrm
        trainings = list(db.trainings.find({}))
        
        # Format trainings for frontend
        formatted_trainings = []
        for training in trainings:
            if "_id" in training:
                del training["_id"]
            
            # Handle datetime serialization
            training_date = training.get("training_date")
            if training_date and hasattr(training_date, 'isoformat'):
                training_date = training_date.isoformat()
            elif not training_date:
                training_date = "2024-12-20T10:30:00.000Z"
                
            # Handle time serialization
            training_time = training.get("training_time", "09:00")
            
            formatted_training = {
                "id": training.get("id", ""),
                "title": training.get("name", training.get("training_name", training.get("title", "Unknown Training"))),
                "description": training.get("description", training.get("subject", training.get("details", "No description"))),
                "duration": training.get("duration", "N/A"),
                "level": training.get("level", "Başlangıç"),
                "category": training.get("category", training.get("subject", "General")),
                "client_id": training.get("client_id", "general"),
                "client_name": training.get("client_name", "General"),
                "trainer": training.get("trainer", "Unknown"),
                "participant_count": training.get("participant_count", 0),
                "training_date": training_date,
                "training_time": training_time,  # Add training time
                "status": training.get("status", "planned")
            }
            formatted_trainings.append(formatted_training)
        
        return formatted_trainings
        
    except Exception as e:
        print(f"Error in direct trainings endpoint: {e}")
        return []

@app.get("/clients")
async def get_clients_direct(current_user: User = Depends(get_current_user)):
    """Get clients for email management - DIRECT ON MAIN APP"""
    try:
        # Get MongoDB connections - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Get clients from rotacrm
        clients = list(db.clients.find({}))
        
        # Format clients for frontend
        formatted_clients = []
        for client in clients:
            if "_id" in client:
                del client["_id"]
            
            formatted_client = {
                "id": client.get("id", ""),
                "name": client.get("hotel_name", client.get("name", "Unknown Client")),
                "email": client.get("email", ""),
                "client_id": client.get("id", "")
            }
            formatted_clients.append(formatted_client)
        
        return formatted_clients
        
    except Exception as e:
        print(f"Error in direct clients endpoint: {e}")
        return []

# DOCUMENT UPLOAD ENDPOINT - DIRECT TO MAIN APP
@app.post("/upload-document")
async def upload_document_direct(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_id: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    stage: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload document - DIRECT ON MAIN APP"""
    document_id = None
    try:
        logging.info(f"📤 Direct upload: {current_user.name} - Client: {client_id} - Folder: {folder_id} - File: {file.filename}")
        
        # Get MongoDB connection - ROTACRM
        logging.info(f"🔗 Connecting to MongoDB...")
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        logging.info(f"✅ MongoDB connected successfully")
        
        # Verify client exists
        logging.info(f"👤 Checking client: {client_id}")
        client = await asyncio.to_thread(db.clients.find_one, {"id": client_id})
        if not client:
            logging.error(f"❌ Client not found: {client_id}")
            raise HTTPException(status_code=404, detail="Client not found")
        logging.info(f"✅ Client found: {client.get('name', 'Unknown')}")
            
        # Verify folder exists
        logging.info(f"📁 Checking folder: {folder_id}")
        folder = await asyncio.to_thread(db.folders.find_one, {"id": folder_id})
        if not folder:
            logging.error(f"❌ Folder not found: {folder_id}")
            raise HTTPException(status_code=404, detail="Folder not found")
        logging.info(f"✅ Folder found: {folder.get('name', 'Unknown')}")
        
        # Create document metadata
        document_id = str(uuid.uuid4())
        logging.info(f"🆔 Generated document ID: {document_id}")
        
        # Save file content to GridFS
        logging.info(f"📥 Reading file content...")
        file_content = await file.read()
        logging.info(f"✅ File content read: {len(file_content)} bytes")
        
        # Initialize GridFS
        logging.info(f"🗄️ Initializing GridFS...")
        import gridfs
        fs = gridfs.GridFS(db)
        logging.info(f"✅ GridFS initialized")
        
        # Store file in GridFS
        logging.info(f"💾 Storing file in GridFS...")
        file_id = fs.put(
            file_content,
            filename=file.filename,
            content_type=file.content_type,
            metadata={
                "document_id": document_id,
                "client_id": client_id,
                "uploaded_by": current_user.clerk_user_id,
                "document_name": document_name,
                "document_type": document_type,
                "stage": stage
            }
        )
        logging.info(f"✅ File stored in GridFS: {file_id}")
        
        document_data = {
            "id": document_id,
            "client_id": client_id,
            "name": document_name,
            "document_name": document_name,
            "document_type": document_type,
            "stage": stage,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(file_content),
            "original_filename": file.filename,
            "uploaded_by": current_user.clerk_user_id,
            "created_at": datetime.utcnow(),
            "folder_id": folder_id,
            "folder_path": folder["folder_path"],
            "folder_level": folder["level"],
            "gridfs_id": str(file_id)  # Store GridFS file ID
        }
        
        # Insert document to rotacrm
        logging.info(f"📝 Inserting document record to MongoDB...")
        result = await asyncio.to_thread(db.documents.insert_one, document_data)
        logging.info(f"✅ Document record inserted: {result.inserted_id}")
        
        # Verify the insertion
        logging.info(f"🔍 Verifying document insertion...")
        verification = await asyncio.to_thread(db.documents.find_one, {"id": document_id})
        if verification:
            logging.info(f"✅ Document verified in database: {verification.get('name')}")
        else:
            logging.error(f"❌ Document verification failed!")
            raise HTTPException(status_code=500, detail="Document verification failed")
        
        logging.info(f"✅ Document saved to ROTACRM: {document_id}")
        
        return {"message": "Document uploaded successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Direct upload error: {e}")
        logging.error(f"❌ Error type: {type(e)}")
        logging.error(f"❌ Error details: {str(e)}")
        if document_id:
            logging.error(f"❌ Failed document ID: {document_id}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ALSO ADD API UPLOAD ENDPOINT FOR FRONTEND /api CALLS
@app.post("/api/upload-document")
async def upload_document_api_direct(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_id: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    stage: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload document via /api endpoint - DIRECT ON MAIN APP"""
    # Delegate to main upload function
    return await upload_document_direct(file, client_id, folder_id, document_name, document_type, stage, current_user)

# STATS ENDPOINT - DIRECT TO MAIN APP
@app.get("/stats")
async def get_statistics_direct(current_user: User = Depends(get_current_user)):
    """Get statistics - DIRECT ON MAIN APP"""
    try:
        # Get MongoDB connection - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        if current_user.role == UserRole.ADMIN:
            # Admin sees all statistics from ROTACRM
            total_clients = await asyncio.to_thread(db.clients.count_documents, {})
            stage_1_clients = await asyncio.to_thread(db.clients.count_documents, {"current_stage": "I.Aşama"})
            stage_2_clients = await asyncio.to_thread(db.clients.count_documents, {"current_stage": "II.Aşama"})
            stage_3_clients = await asyncio.to_thread(db.clients.count_documents, {"current_stage": "III.Aşama"})
            
            # COUNT ALL DOCUMENTS FROM YENİ BELGE YÖNETİMİ - SIMPLE COUNT
            total_documents = await asyncio.to_thread(db.documents.count_documents, {})
            
            total_trainings = await asyncio.to_thread(db.trainings.count_documents, {})
            
            logging.info(f"📊 ROTACRM Stats: {total_documents} active docs, {total_trainings} trainings, {total_clients} clients")
            
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
            # Client sees only their own statistics
            if not current_user.client_id:
                return {
                    "total_clients": 0,
                    "stage_distribution": {"stage_1": 0, "stage_2": 0, "stage_3": 0},
                    "total_documents": 0,
                    "total_trainings": 0,
                    "document_type_distribution": {
                        "TR1_CRITERIA": 0,
                        "STAGE_1_DOC": 0,
                        "CARBON_REPORT": 0
                    }
                }
            
            # Client specific stats from ROTACRM - ALL DOCS FOR CLIENT
            client_documents = await asyncio.to_thread(
                db.documents.count_documents, 
                {"client_id": current_user.client_id}
            )
            client_trainings = await asyncio.to_thread(db.trainings.count_documents, {"client_id": current_user.client_id})
            
            return {
                "total_clients": 1,
                "stage_distribution": {"stage_1": 1, "stage_2": 0, "stage_3": 0},
                "total_documents": client_documents,
                "total_trainings": client_trainings,
                "document_type_distribution": {
                    "TR1_CRITERIA": client_documents,
                    "STAGE_1_DOC": 0,
                    "CARBON_REPORT": 0
                }
            }
            
    except Exception as e:
        logging.error(f"❌ Direct stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

# CLIENT REGISTRATION ENDPOINTS - DIRECT TO MAIN APP
@app.post("/clients")
async def create_client_direct(
    client_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create client - DIRECT ON MAIN APP"""
    try:
        logging.info(f"🏨 Direct client creation: {current_user.name} - Role: {current_user.role}")
        
        # Get MongoDB connection - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Admin can create any client, client users can only create for themselves
        if current_user.role == UserRole.CLIENT and current_user.client_id:
            # If client user already has a client record, return the existing one
            existing_client = await asyncio.to_thread(db.clients.find_one, {"id": current_user.client_id})
            if existing_client:
                if "_id" in existing_client:
                    del existing_client["_id"]
                return existing_client
            else:
                # If client_id exists but no client record, remove client_id and continue
                await asyncio.to_thread(
                    db.users.update_one,
                    {"clerk_user_id": current_user.clerk_user_id},
                    {"$unset": {"client_id": ""}, "$set": {"updated_at": datetime.utcnow()}}
                )
        
        # Create new client
        client_id = str(uuid.uuid4())
        client_data["id"] = client_id
        client_data["created_at"] = datetime.utcnow()
        client_data["updated_at"] = datetime.utcnow()
        
        await asyncio.to_thread(db.clients.insert_one, client_data)
        
        # TODO: Create root folder for the new client (if needed)
        
        # If client user is creating their own record, update their user record
        if current_user.role == UserRole.CLIENT:
            await asyncio.to_thread(
                db.users.update_one,
                {"clerk_user_id": current_user.clerk_user_id},
                {"$set": {"client_id": client_id, "updated_at": datetime.utcnow()}}
            )
        
        logging.info(f"✅ Client created in ROTACRM: {client_id}")
        return client_data
        
    except Exception as e:
        logging.error(f"❌ Direct client creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Client creation failed: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info_direct(current_user: User = Depends(get_current_user)):
    """Get current user info - DIRECT ON MAIN APP"""
    return current_user

@app.put("/auth/me")
async def update_current_user_direct(
    user_update: dict,
    current_user: User = Depends(get_current_user)
):
    """Update current user - DIRECT ON MAIN APP"""
    try:
        logging.info(f"👤 Direct user update: {current_user.name}")
        
        # Get MongoDB connection - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        update_data = {k: v for k, v in user_update.items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        result = await asyncio.to_thread(
            db.users.update_one,
            {"clerk_user_id": current_user.clerk_user_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_user = await asyncio.to_thread(db.users.find_one, {"clerk_user_id": current_user.clerk_user_id})
        if "_id" in updated_user:
            del updated_user["_id"]
            
        logging.info(f"✅ User updated in ROTACRM: {current_user.clerk_user_id}")
        return updated_user
        
    except Exception as e:
        logging.error(f"❌ Direct user update error: {e}")
        raise HTTPException(status_code=500, detail=f"User update failed: {str(e)}")

# EMAIL SENDING ENDPOINT - DIRECT TO MAIN APP
@app.post("/send-email")
async def send_email_direct(request: dict, current_user: User = Depends(get_current_user)):
    """Send email - DIRECT ON MAIN APP"""
    try:
        from services.email_service import EmailService
        email_service = EmailService()
        
        to_email = request.get("to_email")
        subject = request.get("subject")
        html_content = request.get("html_content")
        
        if not to_email or not subject or not html_content:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Send email
        success = email_service.send_email(to_email, subject, html_content)
        
        if success:
            return {"message": "Email sent successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
            
    except Exception as e:
        print(f"Error in direct send-email endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

# CRITICAL CONSUMPTION ENDPOINTS - DIRECT TO MAIN APP
@app.post("/consumptions")
async def create_consumption_direct(consumption_data: dict, current_user: User = Depends(get_current_user)):
    """Create consumption - DIRECT ON MAIN APP"""
    try:
        # Get MongoDB connection - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Add metadata
        consumption_data["id"] = str(uuid.uuid4())
        consumption_data["created_at"] = datetime.utcnow()
        consumption_data["updated_at"] = datetime.utcnow()
        
        # Insert consumption
        result = db.consumptions.insert_one(consumption_data)
        
        return {"message": "Consumption created successfully", "consumption_id": consumption_data["id"]}
        
    except Exception as e:
        print(f"Error in direct create consumption: {e}")
        raise HTTPException(status_code=500, detail=f"Consumption creation failed: {str(e)}")

@app.get("/consumptions")
async def get_consumptions_direct(year: Optional[int] = None, client_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Get consumptions - DIRECT ON MAIN APP"""
    try:
        # Get MongoDB connection - ONLY ROTACRM
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Build query
        query = {}
        if year:
            query["year"] = year
        if client_id:
            query["client_id"] = client_id
            
        # Get consumptions
        consumptions = list(db.consumptions.find(query))
        
        # Format for frontend
        for consumption in consumptions:
            if "_id" in consumption:
                del consumption["_id"]
        
        return consumptions
        
    except Exception as e:
        print(f"Error in direct get consumptions: {e}")
        return []

# Test endpoint directly on api_router
@api_router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router mounting - NO AUTHENTICATION REQUIRED"""
    return {
        "message": "API Router is working perfectly!",
        "status": "ok",
        "routes_count": len(api_router.routes),
        "timestamp": datetime.utcnow().isoformat()
    }


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
        
        # 🏗️ CREATE LEVEL 4 FOLDERS AUTOMATICALLY
        logging.info(f"🏗️ Creating Level 4 folders for new client: {client_id}")
        level4_count = await create_level4_for_client(client_id)
        logging.info(f"✅ Created {level4_count} Level 4 folders for new client: {client_id}")
        
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

async def create_level4_for_client(client_id: str):
    """Create Level 4 folders (POLİTİKALAR, PROSEDÜRLER, etc.) for a specific client"""
    try:
        logging.info(f"🏗️ Creating Level 4 folders for client: {client_id}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Level 4 klasörler
        level4_folders = [
            "POLİTİKALAR",
            "PROSEDÜRLER", 
            "FORMLAR",
            "LİSTELER",
            "KAYITLAR"
        ]
        
        # Level 2 ve Level 3 klasörleri bul
        parent_folders = await asyncio.to_thread(
            lambda: list(db.folders.find({
                "client_id": client_id,
                "level": {"$in": [2, 3]}
            }))
        )
        
        created_count = 0
        
        for parent_folder in parent_folders:
            parent_id = parent_folder["id"]
            parent_path = parent_folder["folder_path"]
            
            for folder_name in level4_folders:
                level4_id = f"level4_{parent_id}_{folder_name.lower().replace('i̇', 'i')}"
                level4_path = f"{parent_path}/{folder_name}"
                
                # Check if already exists
                existing = await asyncio.to_thread(
                    db.folders.find_one, {"id": level4_id}
                )
                
                if existing:
                    continue
                
                # Create Level 4 folder
                level4_folder = {
                    "id": level4_id,
                    "client_id": client_id,
                    "name": folder_name,
                    "parent_folder_id": parent_id,
                    "folder_path": level4_path,
                    "level": 4,
                    "created_at": datetime.utcnow()
                }
                
                await asyncio.to_thread(db.folders.insert_one, level4_folder)
                created_count += 1
        
        logging.info(f"✅ Created {created_count} Level 4 folders for client: {client_id}")
        return created_count
        
    except Exception as e:
        logging.error(f"❌ Failed to create Level 4 folders for client {client_id}: {str(e)}")
        return 0

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

# Test endpoint to verify API Router is working
@api_router.get("/test-router")
async def test_api_router():
    """Simple test endpoint to verify API Router works"""
    return {"message": "API Router is working!", "timestamp": datetime.utcnow().isoformat()}

# Routes
@api_router.get("/status")
async def api_status():
    return {"message": "Sürdürülebilir Turizm Danışmanlık CRM API", "status": "active"}

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
    current_user: User = Depends(get_current_user)  # Allow admin and consultant
):
    try:
        logging.info(f"📚 Creating training with data: {training_data} by user: {current_user.email} ({current_user.role})")
        
        # Check if client exists
        client = await db.clients.find_one({"id": training_data.client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Check permissions
        if current_user.role == UserRole.ADMIN:
            # Admin can create training for any client
            pass
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant can create training for their assigned clients
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            if client.get("consultant_id") != consultant_id:
                raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
        else:
            raise HTTPException(status_code=403, detail="Bu müşteri için eğitim oluşturma yetkiniz yok")
        
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
    current_user: User = Depends(get_current_user)  # Allow admin and consultant
):
    # Find the training first
    training = await db.trainings.find_one({"id": training_id})
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can update any training
        pass
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant can update training for their assigned clients
        consultant_id = current_user.consultant_id
        if not consultant_id:
            raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
        
        # Check if the training's client is assigned to this consultant
        client = await db.clients.find_one({"id": training["client_id"], "consultant_id": consultant_id})
        if not client:
            raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
    else:
        raise HTTPException(status_code=403, detail="Bu eğitimi güncelleme yetkiniz yok")
    
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
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant sees only their assigned clients' statistics
            consultant_id = getattr(current_user, 'consultant_id', None)
            if not consultant_id:
                return {
                    "total_clients": 0,
                    "stage_distribution": {"stage_1": 0, "stage_2": 0, "stage_3": 0},
                    "total_documents": 0,
                    "total_trainings": 0
                }
            
            # Get consultant's clients
            consultant_clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
            client_ids = [client["id"] for client in consultant_clients]
            
            total_clients = len(consultant_clients)
            stage_1_clients = len([c for c in consultant_clients if c.get("current_stage") == "I.Aşama"])
            stage_2_clients = len([c for c in consultant_clients if c.get("current_stage") == "II.Aşama"])
            stage_3_clients = len([c for c in consultant_clients if c.get("current_stage") == "III.Aşama"])
            
            # Count documents and trainings for consultant's clients only
            total_documents = await db.documents.count_documents({"client_id": {"$in": client_ids}})
            total_trainings = await db.trainings.count_documents({"client_id": {"$in": client_ids}})
            
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
@api_router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    try:
        return {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "client_id": getattr(current_user, 'client_id', None),
            "consultant_id": getattr(current_user, 'consultant_id', None),
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    except Exception as e:
        logging.error(f"❌ Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="User bilgisi alınamadı")

@api_router.get("/folders")
async def get_folders(current_user: User = Depends(get_current_user)):
    """Get folder tree for current user"""
    try:
        if current_user.role == UserRole.ADMIN:
            # Admin sees all folders
            folders = await db.folders.find({}).to_list(length=None)
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant sees folders for their assigned clients
            consultant_id = getattr(current_user, 'consultant_id', None)
            if not consultant_id:
                return []
            
            # Get all clients assigned to this consultant
            clients = await asyncio.to_thread(
                lambda: list(db.clients.find({"consultant_id": consultant_id}))
            )
            client_ids = [client.get("id") for client in clients]
            
            # Get folders for all assigned clients
            if client_ids:
                folders = await db.folders.find({"client_id": {"$in": client_ids}}).to_list(length=None)
            else:
                folders = []
        else:
            # Client sees only their own folders
            if not current_user.client_id:
                return []
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
    
    # Check permissions - only admin can create for any client, client can create for themselves, consultant can create for assigned clients
    if current_user.role == UserRole.ADMIN:
        # Admin can specify client_id in request body
        if consumption_data.client_id:
            client_id = consumption_data.client_id
        else:
            # If no client_id specified, use admin's assigned client (backward compatibility)
            client_id = current_user.client_id
            if not client_id:
                raise HTTPException(status_code=400, detail="Admin must specify client_id")
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant users can create consumption data for their assigned clients
        if consumption_data.client_id:
            # Verify that the consultant has access to this client
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=400, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            client = await db.clients.find_one({"id": consumption_data.client_id, "consultant_id": consultant_id})
            if not client:
                raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
            
            client_id = consumption_data.client_id
        else:
            raise HTTPException(status_code=400, detail="Consultant must specify client_id")
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
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant users can see consumption data for their assigned clients
        if client_id:
            # Verify that the consultant has access to this client
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=400, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            client = await db.clients.find_one({"id": client_id, "consultant_id": consultant_id})
            if not client:
                raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
            
            target_client_id = client_id
        else:
            # If no client_id specified, return error - consultants must specify client
            raise HTTPException(status_code=400, detail="Consultant must specify client_id parameter")
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
    if current_user.role == UserRole.CLIENT:
        if current_user.client_id != consumption["client_id"]:
            raise HTTPException(status_code=403, detail="Bu tüketim verisini güncelleme yetkiniz yok")
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant can update consumption data for their assigned clients
        consultant_id = current_user.consultant_id
        if not consultant_id:
            raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
        
        # Check if the consumption's client is assigned to this consultant
        client = await db.clients.find_one({"id": consumption["client_id"], "consultant_id": consultant_id})
        if not client:
            raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
    elif current_user.role == UserRole.ADMIN:
        # Admin can update any consumption
        pass
    else:
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
    current_user: User = Depends(get_current_user)  # Allow admin and consultant
):
    """Delete consumption record"""
    
    logging.info(f"🗑️ DELETE /consumptions/{consumption_id} called by user: {current_user.name} ({current_user.role})")
    
    # Check if consumption exists
    existing = await db.consumptions.find_one({"id": consumption_id})
    if not existing:
        logging.info(f"❌ Consumption not found: {consumption_id}")
        raise HTTPException(status_code=404, detail="Tüketim verisi bulunamadı")
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can delete any consumption
        pass
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant can delete consumption data for their assigned clients
        consultant_id = current_user.consultant_id
        if not consultant_id:
            raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
        
        # Check if the consumption's client is assigned to this consultant
        client = await db.clients.find_one({"id": existing["client_id"], "consultant_id": consultant_id})
        if not client:
            raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
    else:
        raise HTTPException(status_code=403, detail="Bu tüketim verisini silme yetkiniz yok")
    
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
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant users can see analytics for their assigned clients
        if client_id:
            # Verify that the consultant has access to this client
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=400, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            client = await db.clients.find_one({"id": client_id, "consultant_id": consultant_id})
            if not client:
                raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
            
            target_client_id = client_id
        else:
            raise HTTPException(status_code=400, detail="Consultant must specify client_id parameter")
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
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant users can see carbon data for their assigned clients
        if client_id:
            # Verify that the consultant has access to this client
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            assigned_client = await db.clients.find_one({"id": client_id, "consultant_id": consultant_id})
            if not assigned_client:
                raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
            
            target_client_id = client_id
        else:
            # If no client_id specified, consultant must specify which client
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
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant users can create waste data for their assigned clients
        if waste_data.client_id:
            # Verify that the consultant has access to this client
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            assigned_client = await db.clients.find_one({"id": waste_data.client_id, "consultant_id": consultant_id})
            if not assigned_client:
                raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
            
            client_id = waste_data.client_id
        else:
            raise HTTPException(status_code=400, detail="Client ID required for waste data creation")
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
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant users can see waste data for their assigned clients
        if client_id:
            # Verify that the consultant has access to this client
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            assigned_client = await db.clients.find_one({"id": client_id, "consultant_id": consultant_id})
            if not assigned_client:
                raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
            
            target_client_id = client_id
        else:
            # If no client_id specified, consultant must specify which client
            raise HTTPException(status_code=400, detail="Client ID required for waste data")
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
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant users can see waste analytics for their assigned clients
        if client_id:
            # Verify that the consultant has access to this client
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            assigned_client = await db.clients.find_one({"id": client_id, "consultant_id": consultant_id})
            if not assigned_client:
                raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
            
            target_client_id = client_id
        else:
            # If no client_id specified, consultant must specify which client
            raise HTTPException(status_code=400, detail="Client ID required for waste analytics")
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
async def delete_training(training_id: str, current_user: User = Depends(get_current_user)):  # Allow admin and consultant
    """Delete a training (Admin and Consultant)"""
    logging.info(f"📚 DELETE /trainings/{training_id} called by user: {current_user.name} ({current_user.role})")
    
    # Check if training exists
    training = await db.trainings.find_one({"id": training_id})
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can delete any training
        pass
    elif current_user.role == UserRole.CONSULTANT:
        # Consultant can delete training for their assigned clients
        consultant_id = current_user.consultant_id
        if not consultant_id:
            raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
        
        # Check if the training's client is assigned to this consultant
        client = await db.clients.find_one({"id": training["client_id"], "consultant_id": consultant_id})
        if not client:
            raise HTTPException(status_code=403, detail="Access denied: Client not assigned to consultant")
    else:
        raise HTTPException(status_code=403, detail="Bu eğitimi silme yetkiniz yok")
    
    # Delete training
    result = await db.trainings.delete_one({"id": training_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Training not found")
    
    logging.info(f"✅ Training deleted: {training['name']}")
    return {"message": "Training deleted successfully"}

# Include the router in the main app
# EMAIL NOTIFICATION ENDPOINTS
# EMAIL NOTIFICATION MODELS
class EmailNotificationInput(BaseModel):
    client_id: str
    type: str  # 'document' | 'training'
    subject: str
    message: str
    items: List[dict]  # Document or training items with details

@api_router.post("/email/send-notification")
async def send_email_notification(
    notification_data: EmailNotificationInput,
    current_user: User = Depends(get_current_user)
):
    """Send email notification for documents or trainings to specific client"""
    try:
        # Verify permission
        if current_user.role not in ['admin', 'consultant']:
            raise HTTPException(status_code=403, detail="Sadece admin ve consultant kullanıcıları email gönderebilir")
        
        # Get client information
        client = await db.clients.find_one({"id": notification_data.client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
        
        # Check if email service is available
        if not email_service:
            raise HTTPException(status_code=500, detail="Email servisi kullanılamıyor")
        
        # Build email content
        client_name = client.get('name') or client.get('hotel_name')
        email_content = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9;">
    <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #2563eb; text-align: center; margin-bottom: 30px;">
            📧 ROTA CRM - Bildirim
        </h1>
        
        <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #374151; margin: 0;">🏢 {client_name}</h2>
            <p style="color: #6b7280; margin: 5px 0 0 0;">İşletme Bilgilendirmesi</p>
        </div>
        
        <h3 style="color: #374151;">{notification_data.subject}</h3>
        <p style="color: #6b7280; line-height: 1.6;">{notification_data.message}</p>
        
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h4 style="color: #1f2937; margin: 0 0 15px 0;">
                {'📄 Doküman Detayları:' if notification_data.type == 'document' else '🎓 Eğitim Detayları:'}
            </h4>
"""
        
        # Add items details
        for i, item in enumerate(notification_data.items, 1):
            if notification_data.type == 'document':
                email_content += f"""
            <div style="border-left: 4px solid #3b82f6; padding-left: 15px; margin-bottom: 15px;">
                <p style="margin: 0; font-weight: bold; color: #1f2937;">{i}. {item.get('name', 'Unknown Document')}</p>
                <p style="margin: 5px 0; color: #6b7280; font-size: 14px;">📁 Klasör: {item.get('folder_path', 'Unknown')}</p>
                <p style="margin: 5px 0; color: #6b7280; font-size: 14px;">📅 Yükleme Tarihi: {item.get('upload_date', 'Unknown')}</p>
            </div>
"""
            else:  # training
                email_content += f"""
            <div style="border-left: 4px solid #10b981; padding-left: 15px; margin-bottom: 15px;">
                <p style="margin: 0; font-weight: bold; color: #1f2937;">{i}. {item.get('name', 'Unknown Training')}</p>
                <p style="margin: 5px 0; color: #6b7280; font-size: 14px;">👨‍🏫 Eğitmen: {item.get('trainer', 'Unknown')}</p>
                <p style="margin: 5px 0; color: #6b7280; font-size: 14px;">📅 Tarih: {item.get('training_date', 'Unknown')}</p>
                <p style="margin: 5px 0; color: #6b7280; font-size: 14px;">⏰ Eğitim Saati: {item.get('hours', 'Unknown')}</p>
            </div>
"""
        
        email_content += f"""
        </div>
        
        <div style="background-color: #e5e7eb; padding: 15px; border-radius: 6px; margin-top: 30px;">
            <p style="margin: 0; color: #374151; font-size: 12px; text-align: center;">
                Bu email otomatik olarak ROTA CRM sistemi tarafından gönderilmiştir.<br>
                Gönderen: {current_user.name} ({current_user.role})<br>
                Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}
            </p>
        </div>
    </div>
</div>
"""
        
        # Send email
        success = await email_service.send_email(
            to_email=client.get('email', 'test@example.com'),
            subject=f"ROTA CRM - {notification_data.subject}",
            html_content=email_content
        )
        
        if success:
            logging.info(f"✅ Email notification sent: {notification_data.type} to {client_name}")
            return {
                "success": True,
                "message": f"Email başarıyla gönderildi: {client_name}",
                "details": {
                    "type": notification_data.type,
                    "items_count": len(notification_data.items),
                    "client": client_name,
                    "sent_by": current_user.name
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Email gönderilemedi")
            
    except Exception as e:
        logging.error(f"❌ Email notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

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
        
        # FOLDER PATH FIX: Get proper folder path for email
        folder_doc = await asyncio.to_thread(db.folders.find_one, {"id": document.get("folder_id")})
        folder_path = "Klasör belirtilmemiş"
        if folder_doc:
            folder_path = folder_doc.get("folder_path") or folder_doc.get("name", "Klasör belirtilmemiş")
        
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
            document_name=document.get("document_name") or document.get("name", "Bilinmiyen Doküman"),
            upload_date=upload_date,
            folder_path=folder_path,
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
        
        # TRAINING DATA FIX: Handle missing fields with fallbacks
        training_name = training.get("name") or training.get("training_name") or "Eğitim adı belirtilmemiş"
        training_date = training.get("training_date") or "Tarih belirtilmemiş"
        trainer = training.get("trainer") or "Eğitmen belirtilmemiş"
        participant_count = training.get("participant_count") or 0
        
        # Send email
        await email_service.send_training_notification(
            recipient_email=client_email,
            training_name=training_name,
            training_date=training_date,
            trainer=trainer,
            participant_count=participant_count,
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

# ====================================
# SUSTAINABILITY TARGET TRACKING MODELS & ENDPOINTS
# ====================================

# Sustainability Target Models
class SustainabilityTargetInput(BaseModel):
    target_name: str
    category: str  # "Çevresel", "Sosyal", "Ekonomik"
    target_type: str  # "Karbon Ayak İzi", "Su Tüketimi", "Yerel İstihdam", etc.
    target_value: float
    unit: str  # "%", "kg", "litre", "TL", "saat"
    target_period: str  # "Aylık", "Çeyreklik", "Yıllık"
    deadline: datetime
    description: Optional[str] = None
    client_id: Optional[str] = None

class SustainabilityTarget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    target_name: str
    category: str
    target_type: str
    target_value: float
    unit: str
    target_period: str
    deadline: datetime
    description: Optional[str] = None
    status: str = Field(default="active")  # "active", "completed", "overdue"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TargetProgressInput(BaseModel):
    target_id: str
    actual_value: float
    progress_date: datetime
    notes: Optional[str] = None

class TargetProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str
    actual_value: float
    progress_date: datetime
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

@api_router.post("/sustainability-targets")
async def create_sustainability_target(
    target_data: SustainabilityTargetInput,
    current_user: User = Depends(get_current_user)  # Allow consultants
):
    """Create a new sustainability target (Admin and Consultant access)"""
    try:
        # Determine client_id based on user role
        if current_user.role == UserRole.CLIENT:
            client_id = current_user.client_id
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant users can create targets for their assigned clients
            if target_data.client_id:
                # Verify that the consultant has access to this client
                consultant_id = current_user.consultant_id
                if not consultant_id:
                    raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
                
                # Check if the client is assigned to this consultant
                assigned_client = await db.clients.find_one({"id": target_data.client_id, "consultant_id": consultant_id})
                if not assigned_client:
                    raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
                
                client_id = target_data.client_id
            else:
                raise HTTPException(status_code=400, detail="Client ID required for target creation")
        else:
            # Admin users
            client_id = target_data.client_id
            if not client_id:
                raise HTTPException(status_code=400, detail="client_id is required")

        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        target = SustainabilityTarget(
            client_id=client_id,
            target_name=target_data.target_name,
            category=target_data.category,
            target_type=target_data.target_type,
            target_value=target_data.target_value,
            unit=target_data.unit,
            target_period=target_data.target_period,
            deadline=target_data.deadline,
            description=target_data.description
        ).dict()

        result = await db.sustainability_targets.insert_one(target)
        
        return {
            "message": "Sustainability target created successfully",
            "target_id": target["id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating sustainability target: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/sustainability-targets")
async def get_sustainability_targets(
    client_id: str = None,
    category: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get sustainability targets with optional filtering"""
    try:
        filter_query = {}
        
        if current_user.role == UserRole.CLIENT:
            filter_query["client_id"] = current_user.client_id
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant users can see targets for their assigned clients
            if client_id:
                # Verify that the consultant has access to this client
                consultant_id = current_user.consultant_id
                if not consultant_id:
                    raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
                
                # Check if the client is assigned to this consultant
                assigned_client = await db.clients.find_one({"id": client_id, "consultant_id": consultant_id})
                if not assigned_client:
                    raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
                
                filter_query["client_id"] = client_id
            else:
                # If no client_id specified, return targets for all assigned clients
                consultant_id = current_user.consultant_id
                if not consultant_id:
                    raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
                
                # Get all client IDs assigned to this consultant
                assigned_clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
                client_ids = [client["id"] for client in assigned_clients]
                
                if client_ids:
                    filter_query["client_id"] = {"$in": client_ids}
                else:
                    # No assigned clients, return empty result
                    return []
        elif current_user.role == UserRole.ADMIN and client_id:
            filter_query["client_id"] = client_id

        if category:
            filter_query["category"] = category

        targets = await db.sustainability_targets.find(filter_query).sort("created_at", -1).to_list(length=None)
        
        clean_targets = []
        for target in targets:
            if "_id" in target:
                del target["_id"]
            clean_targets.append(target)
        
        return clean_targets

    except Exception as e:
        logging.error(f"Error fetching sustainability targets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/sustainability-targets/{target_id}")
async def get_sustainability_target(
    target_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single sustainability target with progress data"""
    try:
        target = await db.sustainability_targets.find_one({"id": target_id})
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
            
        if current_user.role == UserRole.CLIENT and target["client_id"] != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")

        progress_list = await db.target_progress.find({"target_id": target_id}).sort("progress_date", -1).to_list(length=None)
        
        if "_id" in target:
            del target["_id"]
        
        clean_progress = []
        for progress in progress_list:
            if "_id" in progress:
                del progress["_id"]
            clean_progress.append(progress)
        
        target["progress"] = clean_progress
        
        return target

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching sustainability target: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/sustainability-targets/{target_id}/progress")
async def get_target_progress(
    target_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get progress data for a specific target"""
    try:
        target = await db.sustainability_targets.find_one({"id": target_id})
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")
            
        if current_user.role == UserRole.CLIENT and target["client_id"] != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")

        progress_list = await db.target_progress.find({"target_id": target_id}).sort("progress_date", -1).to_list(length=None)
        
        clean_progress = []
        for progress in progress_list:
            if "_id" in progress:
                del progress["_id"]
            clean_progress.append(progress)
        
        return clean_progress

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching target progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.post("/sustainability-targets/progress")
async def add_target_progress(
    progress_data: TargetProgressInput,
    current_user: User = Depends(get_admin_user)
):
    """Add progress to a sustainability target (Admin only)"""
    try:
        target = await db.sustainability_targets.find_one({"id": progress_data.target_id})
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

        progress = TargetProgress(
            target_id=progress_data.target_id,
            actual_value=progress_data.actual_value,
            progress_date=progress_data.progress_date,
            notes=progress_data.notes
        ).dict()

        result = await db.target_progress.insert_one(progress)
        
        return {
            "message": "Target progress added successfully",
            "progress_id": progress["id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error adding target progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.put("/sustainability-targets/{target_id}")
async def update_sustainability_target(
    target_id: str,
    target_data: SustainabilityTargetInput,
    current_user: User = Depends(get_current_user)  # Allow consultants
):
    """Update a sustainability target (Admin and Consultant access)"""
    try:
        existing = await db.sustainability_targets.find_one({"id": target_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Target not found")

        # Check permissions
        if current_user.role == UserRole.CLIENT:
            if current_user.client_id != existing["client_id"]:
                raise HTTPException(status_code=403, detail="Bu hedef için yetkiniz yok")
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant can update targets for their assigned clients
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
            
            # Check if the target's client is assigned to this consultant
            assigned_client = await db.clients.find_one({"id": existing["client_id"], "consultant_id": consultant_id})
            if not assigned_client:
                raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")

        if target_data.client_id:
            client = await db.clients.find_one({"id": target_data.client_id})
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")

        update_data = {
            "target_name": target_data.target_name,
            "category": target_data.category,
            "target_type": target_data.target_type,
            "target_value": target_data.target_value,
            "unit": target_data.unit,
            "target_period": target_data.target_period,
            "deadline": target_data.deadline,
            "description": target_data.description,
            "updated_at": datetime.utcnow()
        }
        
        if target_data.client_id:
            update_data["client_id"] = target_data.client_id

        await db.sustainability_targets.update_one(
            {"id": target_id},
            {"$set": update_data}
        )
        
        return {"message": "Sustainability target updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating sustainability target: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.delete("/sustainability-targets/{target_id}")
async def delete_sustainability_target(
    target_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Delete a sustainability target (Admin only)"""
    try:
        existing = await db.sustainability_targets.find_one({"id": target_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Target not found")

        await db.sustainability_targets.delete_one({"id": target_id})
        await db.target_progress.delete_many({"target_id": target_id})
        
        return {"message": "Sustainability target deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting sustainability target: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/sustainability-targets/analytics/dashboard")
async def get_sustainability_analytics(
    client_id: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get sustainability targets analytics for dashboard"""
    try:
        filter_query = {}
        
        if current_user.role == UserRole.CLIENT:
            filter_query["client_id"] = current_user.client_id
        elif current_user.role == UserRole.ADMIN and client_id:
            filter_query["client_id"] = client_id

        targets = await db.sustainability_targets.find(filter_query).to_list(length=None)
        
        total_targets = len(targets)
        active_targets = len([t for t in targets if t.get("status", "active") == "active"])
        completed_targets = len([t for t in targets if t.get("status", "active") == "completed"])
        overdue_targets = len([t for t in targets if t.get("status", "active") == "overdue"])
        
        category_distribution = {}
        for target in targets:
            category = target.get("category", "Unknown")
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        target_type_distribution = {}
        for target in targets:
            target_type = target.get("target_type", "Unknown")
            target_type_distribution[target_type] = target_type_distribution.get(target_type, 0) + 1
        
        progress_data = []
        for target in targets:
            progress_records = await db.target_progress.find({"target_id": target["id"]}).sort("progress_date", -1).to_list(length=1)
            if progress_records:
                latest_progress = progress_records[0]
                progress_percentage = min((latest_progress["actual_value"] / target["target_value"]) * 100, 100)
                progress_data.append({
                    "target_id": target["id"],
                    "target_name": target["target_name"],
                    "progress_percentage": progress_percentage,
                    "actual_value": latest_progress["actual_value"],
                    "target_value": target["target_value"]
                })
        
        return {
            "total_targets": total_targets,
            "active_targets": active_targets,
            "completed_targets": completed_targets,
            "overdue_targets": overdue_targets,
            "category_distribution": category_distribution,
            "target_type_distribution": target_type_distribution,
            "progress_data": progress_data,
            "average_progress": sum([p["progress_percentage"] for p in progress_data]) / len(progress_data) if progress_data else 0
        }

    except Exception as e:
        logging.error(f"Error fetching sustainability analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ====================================
# PERSONNEL MANAGEMENT MODELS & ENDPOINTS
# ====================================

# Personnel Models
class PersonnelInput(BaseModel):
    full_name: str
    position: str  # Görev
    location: str  # İkamet-Memleket
    certifications: List[str] = []  # ["İlk Yardım", "Hijyen", "Can Kurtaran", "Lejyonella", "MYK"]
    is_local: bool = False  # Yerel/Yerel Olmayan
    gender: str  # "Kadın" or "Erkek"
    client_id: Optional[str] = None  # For admin users

class Personnel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    full_name: str
    position: str
    location: str
    certifications: List[str] = []
    is_local: bool = False
    gender: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

@api_router.post("/personnel")
async def create_personnel(
    personnel_data: PersonnelInput,
    current_user: User = Depends(get_current_user)  # Allow consultants to create
):
    """Create a new personnel record (Admin and Consultant access)"""
    try:
        # Determine client_id based on user role
        if current_user.role == UserRole.CLIENT:
            client_id = current_user.client_id
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant users can create personnel for their assigned clients
            if personnel_data.client_id:
                # Verify that the consultant has access to this client
                consultant_id = current_user.consultant_id
                if not consultant_id:
                    raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
                
                # Check if the client is assigned to this consultant
                assigned_client = await db.clients.find_one({"id": personnel_data.client_id, "consultant_id": consultant_id})
                if not assigned_client:
                    raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
                
                client_id = personnel_data.client_id
            else:
                raise HTTPException(status_code=400, detail="Client ID required for personnel creation")
        else:
            # Admin users must provide client_id
            client_id = personnel_data.client_id
            if not client_id:
                raise HTTPException(status_code=400, detail="client_id is required for admin users")

        # Validate client exists
        client = await db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        personnel = Personnel(
            client_id=client_id,
            full_name=personnel_data.full_name,
            position=personnel_data.position,
            location=personnel_data.location,
            certifications=personnel_data.certifications,
            is_local=personnel_data.is_local,
            gender=personnel_data.gender
        ).dict()

        result = await db.personnel.insert_one(personnel)
        
        return {
            "message": "Personnel created successfully",
            "personnel_id": personnel["id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating personnel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/personnel")
async def get_personnel(
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get personnel with optional filtering"""
    try:
        # Build filter query
        filter_query = {}
        
        # Role-based filtering
        if current_user.role == UserRole.CLIENT:
            filter_query["client_id"] = current_user.client_id
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant users can see personnel for their assigned clients
            if client_id:
                # Verify that the consultant has access to this client
                consultant_id = current_user.consultant_id
                if not consultant_id:
                    raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
                
                # Check if the client is assigned to this consultant
                assigned_client = await db.clients.find_one({"id": client_id, "consultant_id": consultant_id})
                if not assigned_client:
                    raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")
                
                filter_query["client_id"] = client_id
            else:
                # If no client_id specified, return personnel for all assigned clients
                consultant_id = current_user.consultant_id
                if not consultant_id:
                    raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
                
                # Get all client IDs assigned to this consultant
                assigned_clients = await db.clients.find({"consultant_id": consultant_id}).to_list(length=None)
                client_ids = [client["id"] for client in assigned_clients]
                
                if client_ids:
                    filter_query["client_id"] = {"$in": client_ids}
                else:
                    # No assigned clients, return empty result
                    return []
        elif current_user.role == UserRole.ADMIN and client_id:
            # Admin users can filter by specific client_id
            filter_query["client_id"] = client_id

        personnel_list = await db.personnel.find(filter_query).sort("full_name", 1).to_list(length=None)
        
        # Clean MongoDB ObjectIds for JSON serialization
        clean_personnel = []
        for person in personnel_list:
            if "_id" in person:
                del person["_id"]  # Remove MongoDB ObjectId
            clean_personnel.append(person)
        
        return clean_personnel

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching personnel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.get("/personnel/{personnel_id}")
async def get_personnel_by_id(
    personnel_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific personnel record"""
    try:
        person = await db.personnel.find_one({"id": personnel_id})
        
        if not person:
            raise HTTPException(status_code=404, detail="Personnel not found")
            
        # Check permissions
        if current_user.role == UserRole.CLIENT and person["client_id"] != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Clean MongoDB ObjectId for JSON serialization
        if "_id" in person:
            del person["_id"]
            
        return person

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching personnel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.delete("/personnel/{personnel_id}")
async def delete_personnel(
    personnel_id: str,
    current_user: User = Depends(get_current_user)  # Allow consultants to delete
):
    """Delete a personnel record (Admin and Consultant access)"""
    try:
        # Get existing personnel
        existing = await db.personnel.find_one({"id": personnel_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Personnel not found")
            
        # Check permissions
        if current_user.role == UserRole.CLIENT and existing["client_id"] != current_user.client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant can delete personnel for their assigned clients
            consultant_id = current_user.consultant_id
            if not consultant_id:
                raise HTTPException(status_code=403, detail="Consultant ID not assigned to user")
            
            # Check if the client is assigned to this consultant
            assigned_client = await db.clients.find_one({"id": existing["client_id"], "consultant_id": consultant_id})
            if not assigned_client:
                raise HTTPException(status_code=403, detail="Bu müşteri için yetkiniz yok")

        result = await db.personnel.delete_one({"id": personnel_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Personnel not found")
            
        return {"message": "Personnel deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting personnel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ====================================
# SUPPLIER MANAGEMENT MODELS & ENDPOINTS
# ====================================

# Supplier Models
class SupplierInput(BaseModel):
    company_name: str
    address: str
    category: str
    certifications: List[str] = []  # ["Organic", "Fair Trade", "ISO 14001", etc.]
    monthly_purchase_amount: Optional[float] = None  # Monthly purchase amount
    monthly_purchase_unit: str = "KG"  # KG or Litre
    local_supplier: bool = False
    description: Optional[str] = None
    client_id: Optional[str] = None  # For admin users

class Supplier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    company_name: str
    address: str
    category: str
    certifications: List[str] = []
    monthly_purchase_amount: Optional[float] = None
    monthly_purchase_unit: str = "KG"
    local_supplier: bool = False
    description: Optional[str] = None
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
    current_user: User = Depends(get_admin_user)  # Only admin can create
):
    """Create a new supplier (Admin only)"""
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
            address=supplier_data.address,
            category=supplier_data.category,
            certifications=supplier_data.certifications,
            monthly_purchase_amount=supplier_data.monthly_purchase_amount,
            monthly_purchase_unit=supplier_data.monthly_purchase_unit,
            local_supplier=supplier_data.local_supplier,
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
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get suppliers with optional filtering"""
    try:
        # Build filter query
        filter_query = {}
        
        # Role-based filtering
        if current_user.role == UserRole.CLIENT:
            filter_query["client_id"] = current_user.client_id
        elif current_user.role == UserRole.ADMIN and client_id:
            # Admin users can filter by specific client_id
            filter_query["client_id"] = client_id
        
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
        
        # Clean MongoDB ObjectIds for JSON serialization
        clean_suppliers = []
        for supplier in suppliers:
            if "_id" in supplier:
                del supplier["_id"]  # Remove MongoDB ObjectId
            clean_suppliers.append(supplier)
        
        return clean_suppliers

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
        
        # Clean MongoDB ObjectId for JSON serialization
        if "_id" in supplier:
            del supplier["_id"]
            
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
    current_user: User = Depends(get_admin_user)  # Only admin can update
):
    """Update a supplier (Admin only)"""
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
    current_user: User = Depends(get_admin_user)  # Only admin can delete
):
    """Delete a supplier (Admin only)"""
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
# SIMPLE UPLOAD/DOWNLOAD - DIRECT ON APP
# ==========================================

@app.post("/api/simple-upload")
async def simple_upload_direct(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_id: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    stage: str = Form(...)
):
    """SIMPLE UPLOAD - NO AUTH"""
    try:
        import os
        
        os.makedirs("/tmp/uploads", exist_ok=True)
        
        doc_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        saved_filename = f"{doc_id}.{file_extension}"
        file_path = f"/tmp/uploads/{saved_filename}"
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        document_data = {
            "id": doc_id,
            "client_id": client_id,
            "name": document_name,
            "document_name": document_name,
            "document_type": document_type,
            "stage": stage,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content),
            "original_filename": file.filename,
            "created_at": datetime.utcnow(),
            "folder_id": folder_id,
            "file_path": file_path,
            "saved_filename": saved_filename
        }
        
        await asyncio.to_thread(db.documents.insert_one, document_data)
        logging.info(f"✅ SIMPLE UPLOAD SUCCESS: {doc_id}")
        
        return {"message": "Upload successful", "document_id": doc_id}
        
    except Exception as e:
        logging.error(f"❌ SIMPLE UPLOAD ERROR: {e}")
        return {"error": str(e)}

@app.get("/api/simple-download/{doc_id}")
async def simple_download_direct(doc_id: str):
    """SIMPLE DOWNLOAD - NO AUTH"""
    try:
        import os
        from fastapi.responses import FileResponse
        
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        doc = await asyncio.to_thread(db.documents.find_one, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        logging.info(f"✅ SIMPLE DOWNLOAD: {doc_id}")
        
        return FileResponse(
            path=file_path,
            filename=doc.get("original_filename", "document.pdf"),
            media_type=doc.get("content_type", "application/pdf")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ SIMPLE DOWNLOAD ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# SIMPLE UPLOAD/DOWNLOAD - NO GRIDFS  
# ==========================================

@api_router.post("/simple-upload")
async def simple_upload_endpoint(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_id: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    stage: str = Form(...)
):
    """SIMPLE UPLOAD - SAVE TO TMP"""
    try:
        import os
        
        # Create uploads directory
        os.makedirs("/tmp/uploads", exist_ok=True)
        
        # Generate unique filename
        doc_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        saved_filename = f"{doc_id}.{file_extension}"
        file_path = f"/tmp/uploads/{saved_filename}"
        
        # Save file to disk
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Save document record to MongoDB
        document_data = {
            "id": doc_id,
            "client_id": client_id,
            "name": document_name,
            "document_name": document_name,
            "document_type": document_type,
            "stage": stage,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content),
            "original_filename": file.filename,
            "created_at": datetime.utcnow(),
            "folder_id": folder_id,
            "file_path": file_path,
            "saved_filename": saved_filename
        }
        
        await asyncio.to_thread(db.documents.insert_one, document_data)
        logging.info(f"✅ SIMPLE UPLOAD SUCCESS: {doc_id}")
        
        return {"message": "Upload successful", "document_id": doc_id}
        
    except Exception as e:
        logging.error(f"❌ SIMPLE UPLOAD ERROR: {e}")
        return {"error": str(e)}

@api_router.get("/simple-download/{doc_id}")
async def simple_download_endpoint(doc_id: str):
    """SIMPLE DOWNLOAD - FROM TMP"""
    try:
        import os
        from fastapi.responses import FileResponse
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Find document in MongoDB
        doc = await asyncio.to_thread(db.documents.find_one, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file path
        file_path = doc.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        logging.info(f"✅ SIMPLE DOWNLOAD: {doc_id} -> {file_path}")
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=doc.get("original_filename", "document.pdf"),
            media_type=doc.get("content_type", "application/pdf")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ SIMPLE DOWNLOAD ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# YENİ BELGE YÖNETİMİ SİSTEMİ - MAIN APP'TE
# ==========================================

from fastapi.responses import FileResponse

# KALICI STORAGE DIRECTORY
DOCUMENTS_DIR = "/app/documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

def create_client_folder_structure(client_id: str):
    """Create folder structure for a client"""
    client_doc_dir = os.path.join(DOCUMENTS_DIR, client_id)
    os.makedirs(client_doc_dir, exist_ok=True)
    return client_doc_dir

def get_safe_filename(filename: str) -> str:
    """Get safe filename for storage"""
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    safe_filename = "".join(c if c in safe_chars else "_" for c in filename)
    return safe_filename[:100]

@app.post("/api/debug/fix-folder-names")
async def fix_folder_names_for_client(request_data: dict):
    """Fix folder names for a specific client"""
    try:
        client_id = request_data.get("client_id")
        correct_name = request_data.get("correct_client_name")
        
        if not client_id or not correct_name:
            raise HTTPException(status_code=400, detail="client_id and correct_client_name required")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Update root folder name
        root_folder_name = f"{correct_name} SYS"
        result = await asyncio.to_thread(
            db.folders.update_many,
            {
                "client_id": client_id,
                "level": 0,
                "name": {"$regex": ".*SYS$"}
            },
            {
                "$set": {
                    "name": root_folder_name,
                    "folder_path": root_folder_name
                }
            }
        )
        
        # Update folder paths for all folders
        folders = await asyncio.to_thread(
            lambda: list(db.folders.find({"client_id": client_id}))
        )
        
        updated_count = 0
        for folder in folders:
            if folder.get("level") == 0:
                continue  # Root already updated
            
            # Reconstruct folder path with correct root name
            old_path = folder.get("folder_path", "")
            if "Unknown Client SYS" in old_path:
                new_path = old_path.replace("Unknown Client SYS", root_folder_name)
                await asyncio.to_thread(
                    db.folders.update_one,
                    {"id": folder["id"]},
                    {"$set": {"folder_path": new_path}}
                )
                updated_count += 1
        
        return {
            "success": True,
            "root_folders_updated": result.modified_count,
            "total_paths_updated": updated_count,
            "new_root_name": root_folder_name
        }
        
    except Exception as e:
        logging.error(f"❌ Fix folder names error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/database-info")
async def debug_database_info():
    """Debug: Database connection info"""
    try:
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Test connection
        server_info = mongo_client.server_info()
        
        # Count collections
        collections = db.list_collection_names()
        
        # Count clients 
        clients_count = db.clients.count_documents({})
        
        # Sample client
        sample_client = db.clients.find_one({})
        
        return {
            "mongo_url": mongo_url[:50] + "..." if len(mongo_url) > 50 else mongo_url,
            "db_name": os.environ.get('DB_NAME', 'rotacrm'),
            "server_version": server_info.get('version'),
            "collections": collections,
            "clients_count": clients_count,
            "sample_client": {
                "id": sample_client.get("id") if sample_client else None,
                "name": sample_client.get("name") if sample_client else None,
                "hotel_name": sample_client.get("hotel_name") if sample_client else None
            } if sample_client else None
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    try:
        return {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
            "client_id": getattr(current_user, 'client_id', None),
            "consultant_id": getattr(current_user, 'consultant_id', None),
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    except Exception as e:
        logging.error(f"❌ Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail="User bilgisi alınamadı")

@app.post("/api/test-auto-folder-creation")
async def test_main_endpoint():
    """Test endpoint on main app"""
    return {"message": "Main app endpoint working!", "status": "ok"}

@app.get("/api/folders")
async def get_folders_main(current_user: User = Depends(get_current_user)):
    """Get folders list - MAIN APP"""
    try:
        logging.info(f"📋 FOLDERS LIST MAIN: User: {current_user.email}, Role: {current_user.role}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Get folders based on user role
        if current_user.role == UserRole.ADMIN:
            # Admin sees all folders
            folders = await asyncio.to_thread(lambda: list(db.folders.find({})))
        elif current_user.role == UserRole.CONSULTANT:
            # Consultant sees folders for their assigned clients
            consultant_id = getattr(current_user, 'consultant_id', None)
            if not consultant_id:
                folders = []
            else:
                # Get all clients assigned to this consultant
                clients = list(db.clients.find({"consultant_id": consultant_id}))
                client_ids = [client.get("id") for client in clients]
                
                if client_ids:
                    folders = await asyncio.to_thread(
                        lambda: list(db.folders.find({"client_id": {"$in": client_ids}}))
                    )
                else:
                    folders = []
        else:
            # Client sees only their own folders
            if not current_user.client_id:
                folders = []
            else:
                folders = await asyncio.to_thread(
                    lambda: list(db.folders.find({"client_id": current_user.client_id}))
                )
        
        # Format response
        formatted_folders = []
        for folder in folders:
            if "_id" in folder:
                del folder["_id"]
            formatted_folders.append(folder)
        
        logging.info(f"✅ Found {len(formatted_folders)} folders")
        
        return formatted_folders
        
    except Exception as e:
        logging.error(f"❌ FOLDERS LIST ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Folders liste hatası: {str(e)}")

@app.post("/api/auth/register")
async def register_user_main_fixed(user_data: dict):
    """User registration - MAIN APP - WORKING VERSION"""
    try:
        logging.info(f"👤 User registration MAIN: {user_data.get('email')}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        clerk_user_id = user_data.get("clerk_user_id")
        email = user_data.get("email", "")
        role = user_data.get("role", "client")
        name = user_data.get("name", "")
        
        if not clerk_user_id or not email:
            raise HTTPException(status_code=400, detail="clerk_user_id and email required")
        
        # Check if user already exists
        existing_user = await asyncio.to_thread(
            db.users.find_one, {"clerk_user_id": clerk_user_id}
        )
        
        if existing_user:
            logging.info(f"🔄 Existing user: {email}")
            
            # SECURITY FIX: Check if existing client user needs client_id linking
            if existing_user.get("role") == "client" and not existing_user.get("client_id"):
                # Try to find matching client by email
                matching_client = await asyncio.to_thread(
                    db.clients.find_one, {"email": email}
                )
                
                if matching_client:
                    # Update existing user with client_id
                    await asyncio.to_thread(
                        db.users.update_one,
                        {"clerk_user_id": clerk_user_id},
                        {"$set": {"client_id": matching_client["id"], "updated_at": datetime.utcnow()}}
                    )
                    existing_user["client_id"] = matching_client["id"]
                    logging.info(f"🔗 Existing client user linked to client: {matching_client['name']} (ID: {matching_client['id']})")
                else:
                    logging.warning(f"⚠️ Existing client user but no matching client found for email: {email}")
            
            # Remove MongoDB _id for response
            if "_id" in existing_user:
                del existing_user["_id"]
            
            return existing_user
        
        # Create new user
        user_document = {
            "clerk_user_id": clerk_user_id,
            "email": email,
            "name": name,
            "role": role,
            "client_id": None,  # Will be set when client creates their record
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # SECURITY FIX: If registering as client, find matching client record by email
        if role == "client":
            matching_client = await asyncio.to_thread(
                db.clients.find_one, {"email": email}
            )
            
            if matching_client:
                # Link this user to the existing client
                user_document["client_id"] = matching_client["id"]
                logging.info(f"🔗 New client user linked to existing client: {matching_client['name']} (ID: {matching_client['id']})")
                
                # TRIGGER AUTOMATIC FOLDER CREATION if client exists but no folders
                folders_count = await asyncio.to_thread(
                    db.folders.count_documents, {"client_id": matching_client["id"]}
                )
                
                if folders_count == 0:
                    logging.info(f"🏗️ Creating automatic folders for linked client: {matching_client['name']}")
                    await create_client_root_folder(matching_client["id"], matching_client["name"])
                    
            else:
                # No matching client found - client_id remains None for manual admin assignment
                logging.warning(f"⚠️ New client user registered but no matching client found for email: {email}")
        
        # Insert user
        await asyncio.to_thread(db.users.insert_one, user_document)
        logging.info(f"✅ User registered successfully: {email}")
        
        # Remove MongoDB _id for response
        if "_id" in user_document:
            del user_document["_id"]
        
        return user_document
        
    except Exception as e:
        logging.error(f"❌ USER REGISTRATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@app.post("/api/cleanup-all-data")
async def cleanup_all_data():
    """Tüm eski client, folder, document verilerini temizle"""
    try:
        logging.info("🧹 Starting complete data cleanup...")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        cleanup_stats = {}
        
        # 1. DELETE all documents from database
        documents_result = await asyncio.to_thread(db.documents.delete_many, {})
        cleanup_stats["documents_deleted"] = documents_result.deleted_count
        logging.info(f"🗑️ Deleted {documents_result.deleted_count} documents from database")
        
        # 2. DELETE all folders
        folders_result = await asyncio.to_thread(db.folders.delete_many, {})
        cleanup_stats["folders_deleted"] = folders_result.deleted_count
        logging.info(f"🗑️ Deleted {folders_result.deleted_count} folders from database")
        
        # 3. DELETE all clients  
        clients_result = await asyncio.to_thread(db.clients.delete_many, {})
        cleanup_stats["clients_deleted"] = clients_result.deleted_count
        logging.info(f"🗑️ Deleted {clients_result.deleted_count} clients from database")
        
        # 4. DELETE all files from storage
        import shutil
        documents_dir = "/app/documents"
        files_deleted = 0
        
        if os.path.exists(documents_dir):
            # Count files before deletion
            for root, dirs, files in os.walk(documents_dir):
                files_deleted += len(files)
            
            # Remove all contents but keep the directory
            for item in os.listdir(documents_dir):
                item_path = os.path.join(documents_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            
            logging.info(f"🗑️ Deleted {files_deleted} files from storage")
        
        cleanup_stats["files_deleted"] = files_deleted
        
        # 5. Verify cleanup
        remaining_clients = await asyncio.to_thread(db.clients.count_documents, {})
        remaining_folders = await asyncio.to_thread(db.folders.count_documents, {})
        remaining_documents = await asyncio.to_thread(db.documents.count_documents, {})
        
        # Keep users and trainings intact
        users_count = await asyncio.to_thread(db.users.count_documents, {})
        trainings_count = await asyncio.to_thread(db.trainings.count_documents, {})
        
        return {
            "success": True,
            "message": "Complete data cleanup completed successfully",
            "cleanup_stats": cleanup_stats,
            "verification": {
                "remaining_clients": remaining_clients,
                "remaining_folders": remaining_folders, 
                "remaining_documents": remaining_documents,
                "preserved_users": users_count,
                "preserved_trainings": trainings_count
            },
            "storage_cleaned": True,
            "ready_for_new_data": True
        }
        
    except Exception as e:
        logging.error(f"❌ CLEANUP ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")

@app.post("/api/clients/create-new")
async def create_new_client_main(
    client_name: str = Form(...),
    hotel_name: str = Form(None),
    contact_person: str = Form(None),
    email: str = Form(None),
    current_stage: str = Form("I.Aşama")
):
    """Create new client with automatic folder structure - MAIN APP"""
    try:
        logging.info(f"🏨 Creating new client: {client_name}")
        
        # Generate unique client ID
        client_id = f"CLIENT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Create client data
        client_data = {
            "id": client_id,
            "client_id": client_id,
            "client_name": client_name,
            "hotel_name": hotel_name or client_name,
            "contact_person": contact_person or "",
            "email": email or "",
            "current_stage": current_stage,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert client
        await asyncio.to_thread(db.clients.insert_one, client_data)
        logging.info(f"✅ Client created: {client_name}")
        
        # AUTOMATIC FOLDER CREATION - 49 folders will be created automatically
        await create_client_root_folder(client_id, client_name)
        
        # Count created folders
        folders = await asyncio.to_thread(
            lambda: list(db.folders.find({"client_id": client_id}))
        )
        
        return {
            "success": True,
            "message": f"Client created successfully with automatic folder structure",
            "client": {
                "id": client_id,
                "name": client_name,
                "hotel_name": hotel_name or client_name,
                "stage": current_stage
            },
            "folders_created": len(folders),
            "auto_structure": "SUCCESS" if len(folders) == 49 else f"PARTIAL ({len(folders)}/49)"
        }
        
    except Exception as e:
        logging.error(f"❌ CLIENT CREATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Client creation error: {str(e)}")

@app.delete("/api/clients/{client_id}")
async def delete_client_main(client_id: str):
    """Delete client - MAIN APP - REAL DELETE"""
    try:
        logging.info(f"🏨 DELETE CLIENT MAIN: {client_id}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Check if client exists
        client = await asyncio.to_thread(db.clients.find_one, {"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
        
        client_name = client.get("client_name", "Unknown")
        
        # 1. DELETE ALL CLIENT'S DOCUMENTS AND FILES
        client_documents = await asyncio.to_thread(
            lambda: list(db.documents.find({"client_id": client_id}))
        )
        
        files_deleted = 0
        for doc in client_documents:
            # Delete file from disk
            file_path = doc.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                files_deleted += 1
        
        # Delete documents from database
        docs_result = await asyncio.to_thread(
            db.documents.delete_many, {"client_id": client_id}
        )
        
        # 2. DELETE ALL CLIENT'S FOLDERS
        folders_result = await asyncio.to_thread(
            db.folders.delete_many, {"client_id": client_id}
        )
        
        # 3. DELETE ALL CLIENT'S TRAININGS
        trainings_result = await asyncio.to_thread(
            db.trainings.delete_many, {"client_id": client_id}
        )
        
        # 4. DELETE CLIENT'S USERS
        users_result = await asyncio.to_thread(
            db.users.delete_many, {"client_id": client_id}
        )
        
        # 5. DELETE CLIENT ITSELF
        client_result = await asyncio.to_thread(
            db.clients.delete_one, {"id": client_id}
        )
        
        if client_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Müşteri silinemedi")
        
        # 6. DELETE CLIENT'S FOLDER FROM DISK
        client_folder = f"/app/documents/{client_id}"
        if os.path.exists(client_folder):
            import shutil
            shutil.rmtree(client_folder)
        
        logging.info(f"✅ Client COMPLETELY deleted: {client_name}")
        logging.info(f"   - {docs_result.deleted_count} documents deleted")
        logging.info(f"   - {folders_result.deleted_count} folders deleted") 
        logging.info(f"   - {trainings_result.deleted_count} trainings deleted")
        logging.info(f"   - {users_result.deleted_count} users deleted")
        logging.info(f"   - {files_deleted} files deleted from disk")
        
        return {
            "success": True,
            "message": f"Müşteri ve tüm verileri kalıcı olarak silindi: {client_name}",
            "deleted": {
                "client": 1,
                "documents": docs_result.deleted_count,
                "folders": folders_result.deleted_count,
                "trainings": trainings_result.deleted_count,
                "users": users_result.deleted_count,
                "files": files_deleted
            }
        }
        
    except Exception as e:
        logging.error(f"❌ CLIENT DELETE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Müşteri silme hatası: {str(e)}")

@app.delete("/api/trainings/{training_id}")
async def delete_training_main(training_id: str):
    """Delete training - MAIN APP - REAL DELETE"""
    try:
        logging.info(f"🎓 DELETE TRAINING MAIN: {training_id}")
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Check if training exists
        training = await asyncio.to_thread(db.trainings.find_one, {"id": training_id})
        if not training:
            raise HTTPException(status_code=404, detail="Eğitim bulunamadı")
        
        training_name = training.get("name", "Unknown")
        
        # DELETE TRAINING COMPLETELY
        result = await asyncio.to_thread(
            db.trainings.delete_one, {"id": training_id}
        )
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Eğitim silinemedi")
        
        logging.info(f"✅ Training PERMANENTLY deleted: {training_name}")
        
        return {
            "success": True,
            "message": f"Eğitim kalıcı olarak silindi: {training_name}"
        }
        
    except Exception as e:
        logging.error(f"❌ TRAINING DELETE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Eğitim silme hatası: {str(e)}")

@app.post("/api/test-auto-folder-creation")
async def test_auto_folder_creation():
    """Test otomatik klasör oluşturma sistemini"""
    try:
        logging.info("🧪 Testing automatic folder creation system")
        
        # Create test client
        test_client_id = f"AUTO_TEST_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        test_client_name = f"Otomatik Test Müşteri {datetime.utcnow().strftime('%H:%M:%S')}"
        
        # Get MongoDB connection
        mongo_client = MongoClient(mongo_url)
        db = mongo_client[os.environ.get('DB_NAME', 'rotacrm')]
        
        # Create client
        client_data = {
            "id": test_client_id,
            "client_id": test_client_id,
            "client_name": test_client_name,
            "hotel_name": test_client_name,
            "contact_person": "test@auto.com",
            "email": "test@auto.com",
            "current_stage": "I.Aşama",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await asyncio.to_thread(db.clients.insert_one, client_data)
        logging.info(f"✅ Test client created: {test_client_name}")
        
        # Trigger automatic folder creation (bu fonksiyon zaten mevcut)
        from server import create_client_root_folder
        await create_client_root_folder(test_client_id, test_client_name)
        
        # Count created folders
        folders = await asyncio.to_thread(
            lambda: list(db.folders.find({"client_id": test_client_id}))
        )
        
        folder_stats = {}
        for folder in folders:
            level = folder["level"]
            if level not in folder_stats:
                folder_stats[level] = 0
            folder_stats[level] += 1
        
        total_folders = len(folders)
        
        return {
            "success": True,
            "message": f"Automatic folder creation test completed",
            "test_client": {
                "id": test_client_id,
                "name": test_client_name
            },
            "folder_stats": folder_stats,
            "total_folders": total_folders,
            "expected_folders": 49,
            "auto_creation": "SUCCESS" if total_folders == 49 else f"PARTIAL ({total_folders}/49)"
        }
        
    except Exception as e:
        logging.error(f"❌ AUTO FOLDER TEST ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auto folder test error: {str(e)}")

# ==========================================
# EMAIL ENDPOINTS - MAIN APP (WORKAROUND FOR ROUTER ISSUES)
# ==========================================

@app.get("/api/email/status")
async def email_status():
    """Check email service status"""
    return {
        "email_service_available": email_service is not None,
        "templates_status": "updated"
    }

@app.post("/api/email/test-main")
async def send_test_email_main():
    """Send test email - main app"""
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        success = await email_service.send_test_email("test@example.com")
        if success:
            return {"message": "Test email gönderildi!", "email": "test@example.com"}
        else:
            raise HTTPException(status_code=500, detail="Email gönderilemedi")
    except Exception as e:
        logging.error(f"❌ Test email error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email gönderme hatası: {str(e)}")

# ==========================================
# API ROUTER REGISTRATION - MUST BE AT END
# ==========================================
app.include_router(api_router, prefix="/api")