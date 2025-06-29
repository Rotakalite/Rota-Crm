import os
import uuid
import logging
import shutil
import re
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
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

# WhatsApp service import
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from whatsapp_service import whatsapp_service
    logging.info("✅ WhatsApp service imported successfully")
except Exception as e:
    logging.error(f"❌ Failed to import WhatsApp service: {e}")
    whatsapp_service = None

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
        "https://rota-a43ap7zfm-rotas-projects-62181e6e.vercel.app",  # Eski Vercel URL
        "https://rota-9asd83vl1-rotas-projects-62181e6e.vercel.app",  # Yeni Vercel URL
        "https://*.vercel.app",  # Tüm Vercel domain'leri  
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
api_router = APIRouter(prefix="/api")

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

class Consumption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    year: int
    month: int  # 1-12
    electricity: float = 0.0  # kWh
    water: float = 0.0        # m³
    natural_gas: float = 0.0  # m³
    coal: float = 0.0         # kg
    accommodation_count: int = 0  # Konaklama sayısı
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConsumptionInput(BaseModel):
    year: int
    month: int
    electricity: float = 0.0
    water: float = 0.0  
    natural_gas: float = 0.0
    coal: float = 0.0
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
            "role": "admin",  # Default role
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
    """Health check endpoint for frontend URL discovery"""
    return {
        "status": "healthy",
        "service": "Rota CRM Backend",
        "timestamp": datetime.now().isoformat(),
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
    logging.info(f"🔍 GET /clients called by user: {current_user.role} - {current_user.name} - client_id: {current_user.client_id}")
    
    if current_user.role == UserRole.ADMIN:
        clients = await db.clients.find().to_list(1000)
        logging.info(f"✅ Admin user - returning {len(clients)} clients")
        return [Client(**client) for client in clients]
    else:
        # SECURITY FIX: Client users must only see their own data
        if not current_user.client_id:
            logging.error(f"🚨 SECURITY BREACH: Client user {current_user.name} has no client_id - BLOCKING ACCESS")
            return []
        
        client = await db.clients.find_one({"id": current_user.client_id})
        if not client:
            logging.error(f"🚨 SECURITY: Client user {current_user.name} has invalid client_id {current_user.client_id}")
            return []
            
        result = [Client(**client)]
        logging.info(f"✅ Client user - returning {len(result)} clients (ONLY THEIR OWN)")
        return result

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
async def get_all_documents(current_user: User = Depends(get_current_user)):
    """Get all documents (Admin only) or user's documents (Client)"""
    try:
        logging.info(f"📋 GET /documents called by: {current_user.role} - {current_user.name}")
        
        if current_user.role == UserRole.ADMIN:
            # Admin can see all documents
            documents = await db.documents.find().to_list(1000)
            logging.info(f"✅ Admin - returning {len(documents)} documents")
        else:
            # Client users can only see their own documents
            if not current_user.client_id:
                logging.warning(f"⚠️ Client user {current_user.name} has no client_id")
                return []
            
            documents = await db.documents.find({"client_id": current_user.client_id}).to_list(1000)
            logging.info(f"✅ Client - returning {len(documents)} documents for client: {current_user.client_id}")
        
        # Convert MongoDB documents to JSON-serializable format
        serialized_documents = []
        for doc in documents:
            logging.info(f"📄 Processing document: {doc.get('name')} - folder_id: {doc.get('folder_id')}")
            
            # Remove MongoDB-specific fields and convert to dict
            doc_dict = {
                "id": doc.get("id"),
                "client_id": doc.get("client_id"),
                "name": doc.get("name"),
                "document_type": doc.get("document_type"),
                "stage": doc.get("stage"),
                "file_path": doc.get("file_path"),
                "original_filename": doc.get("original_filename"),
                "file_size": doc.get("file_size"),
                "uploaded_by": doc.get("uploaded_by"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "folder_id": doc.get("folder_id"),
                "folder_path": doc.get("folder_path"),
                "folder_level": doc.get("folder_level", 0),
                "local_upload": doc.get("local_upload", False),
                "gridfs_upload": doc.get("gridfs_upload", False),
                "mock_upload": doc.get("mock_upload", False)
            }
            logging.info(f"📄 Serialized document folder_id: {doc_dict['folder_id']}")
            serialized_documents.append(doc_dict)
        
        return serialized_documents
            
    except Exception as e:
        logging.error(f"❌ Error in get_all_documents: {str(e)}")
        # Return empty list instead of error
        return []

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
    consumption = Consumption(
        client_id=client_id,
        year=consumption_data.year,
        month=consumption_data.month,
        electricity=consumption_data.electricity,
        water=consumption_data.water,
        natural_gas=consumption_data.natural_gas,
        coal=consumption_data.coal,
        accommodation_count=consumption_data.accommodation_count
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
    
    # Update consumption
    update_data = consumption_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
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
            month_data["current_year_per_person"] = {
                "electricity": month_data["current_year"]["electricity"] / month_data["current_year"]["accommodation_count"],
                "water": month_data["current_year"]["water"] / month_data["current_year"]["accommodation_count"],
                "natural_gas": month_data["current_year"]["natural_gas"] / month_data["current_year"]["accommodation_count"],
                "coal": month_data["current_year"]["coal"] / month_data["current_year"]["accommodation_count"]
            }
        else:
            month_data["current_year_per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
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

# Health check and CORS test endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint for testing CORS and connectivity"""
    return {
        "status": "healthy",
        "message": "CRM API is running",
        "timestamp": datetime.utcnow().isoformat(),
        "cors_enabled": True
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
app.include_router(api_router)

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