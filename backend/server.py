import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware import Middleware
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

# Import GCS service
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from services.gcs import gcs_service
    logging.info("✅ GCS service imported successfully")
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

# Add CORS middleware first (CRITICAL FOR FRONTEND ACCESS)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Allow ALL origins completely
    allow_methods=["*"],  # Allow ALL methods
    allow_headers=["*"],  # Allow ALL headers
    expose_headers=["*"],
    max_age=0  # No caching to avoid CORS issues
)

# Set maximum request size to 500MB
app.state.max_request_size = 500 * 1024 * 1024  # 500MB

# Add custom middleware for large uploads and CORS
@app.middleware("http")
async def cors_and_upload_middleware(request, call_next):
    # Allow large uploads for upload endpoints
    if request.url.path.endswith("/upload-document"):
        request.state.max_request_size = 500 * 1024 * 1024
    
    response = await call_next(request)
    
    # Force CORS headers for all responses
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
jwks_client = PyJWKClient(CLERK_JWKS_URL)

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
    file_path: str
    file_size: Optional[int] = None
    uploaded_by: str = "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentCreate(BaseModel):
    client_id: str
    name: str
    document_type: DocumentType
    stage: ProjectStage
    file_path: str
    file_size: Optional[int] = None

class Training(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    title: str
    description: str
    training_date: datetime
    participants: int
    status: str = "Planned"  # Planned, Completed, Cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TrainingCreate(BaseModel):
    client_id: str
    title: str
    description: str
    training_date: datetime
    participants: int

# Authentication Functions
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        logging.info(f"🔍 TOKEN VERIFICATION START")
        logging.info(f"🔍 Received token length: {len(token)}")
        logging.info(f"🔍 Token preview: {token[:50]}...")
        
        # Get the signing key from Clerk
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            logging.info("✅ Got signing key from Clerk")
        except Exception as key_error:
            logging.error(f"❌ Failed to get signing key: {str(key_error)}")
            raise HTTPException(status_code=401, detail="Invalid token: could not get signing key")
        
        # Decode and verify the token
        try:
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=None,  # Clerk doesn't use audience
                options={"verify_aud": False}
            )
            logging.info(f"✅ JWT decode successful")
        except jwt.ExpiredSignatureError:
            logging.error("❌ Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            logging.error(f"❌ Invalid token during decode: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Log all available token data for debugging
        logging.info(f"🔍 Token payload keys: {list(payload.keys())}")
        logging.info(f"👤 User info in token - sub: {payload.get('sub')}")
        logging.info(f"📧 Email in token: {payload.get('email', payload.get('email_addresses', 'Not found'))}")
        logging.info(f"👤 Name info: given_name={payload.get('given_name')}, family_name={payload.get('family_name')}, name={payload.get('name')}")
        
        logging.info(f"✅ Token verified for user: {payload.get('sub', 'unknown')}")
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
    
    logging.info(f"🔍 Looking for user with Clerk ID: {clerk_user_id}")
    
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
        
        # Determine user role based on email domain or default to client
        if user_email.endswith("@rotakalitedanismanlik.com") or user_email == "bilgi@rotakalitedanismanlik.com":
            user_role = UserRole.ADMIN
            client_id = None  # Admin doesn't need client_id
            logging.info("🎭 Creating ADMIN user")
        else:
            user_role = UserRole.CLIENT
            # Get first client for now, later admin can assign proper client
            first_client = await db.clients.find_one()
            client_id = first_client["id"] if first_client else None
            logging.info(f"👤 Creating CLIENT user with client_id: {client_id}")
        
        # Create new user from Clerk data
        new_user = {
            "id": str(uuid.uuid4()),
            "clerk_user_id": clerk_user_id,
            "name": user_name,
            "email": user_email,
            "role": user_role.value,
            "client_id": client_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            # Save to database
            await db.users.insert_one(new_user)
            logging.info(f"✅ NEW USER CREATED: {user_name} ({user_email}) - Role: {user_role.value}")
            
            # Return new user
            return User(**new_user)
        except Exception as save_error:
            logging.error(f"❌ Failed to save new user: {str(save_error)}")
            raise HTTPException(status_code=500, detail="Failed to create user")
    
    logging.info(f"✅ User found: {user['name']} ({user['email']}) - Role: {user['role']}")
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def get_client_access(current_user: User = Depends(get_current_user)):
    # Both admin and client can access, but with different permissions
    return current_user

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
        return User(**existing_user)
    
    user_dict = user_data.dict()
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
    
    # If client user is creating their own record, update their user record
    if current_user.role == UserRole.CLIENT:
        await db.users.update_one(
            {"clerk_user_id": current_user.clerk_user_id},
            {"$set": {"client_id": client.id, "updated_at": datetime.utcnow()}}
        )
    
    return client

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user)):
    logging.info(f"🔍 GET /clients called by user: {current_user.role} - {current_user.name} - client_id: {current_user.client_id}")
    
    try:
        if current_user.role == UserRole.ADMIN:
            # Admin can see all clients
            clients = await db.clients.find().to_list(1000)
            logging.info(f"✅ Admin user - returning {len(clients)} clients:")
            for client in clients:
                logging.info(f"   - {client['hotel_name']} (ID: {client['id']})")
            return [Client(**client) for client in clients]
        else:
            # Client users can only see their own client
            if not current_user.client_id:
                logging.warning(f"⚠️ Client user has no client_id: {current_user.name}")
                return []
            
            client = await db.clients.find_one({"id": current_user.client_id})
            if not client:
                logging.warning(f"⚠️ Client not found for user: {current_user.client_id}")
                return []
            
            logging.info(f"✅ Client user - returning own client: {client['hotel_name']}")
            return [Client(**client)]
    except Exception as e:
        logging.error(f"❌ Error in get_clients: {str(e)}")
        # Fallback: return empty list instead of error
        return []
    else:
        # Client can only see their own record
        if not current_user.client_id:
            logging.info("⚠️ Client user has no client_id - returning empty list")
            return []
        client = await db.clients.find_one({"id": current_user.client_id})
        result = [Client(**client)] if client else []
        logging.info(f"✅ Client user - returning {len(result)} clients")
        return result

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: User = Depends(get_client_access)):
    # Check permissions
    if current_user.role != UserRole.ADMIN and current_user.client_id != client_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client(**client)

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

@api_router.get("/documents", response_model=List[Document])
async def get_all_documents(current_user: User = Depends(get_current_user)):
    """Get all documents (Admin only) or user's documents (Client)"""
    if current_user.role == UserRole.ADMIN:
        # Admin can see all documents
        documents = await db.documents.find().to_list(1000)
        return [Document(**doc) for doc in documents]
    else:
        # Client can only see their own documents
        if not current_user.client_id:
            return []
        
        documents = await db.documents.find({"client_id": current_user.client_id}).to_list(1000)
        return [Document(**doc) for doc in documents]

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
    # Check if admin can access this client
    client = await db.clients.find_one({"id": training_data.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    training_dict = training_data.dict()
    training = Training(**training_dict)
    await db.trainings.insert_one(training.dict())
    return training

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
            # Client sees only their own statistics
            if not current_user.client_id:
                return {
                    "total_clients": 0,
                    "stage_distribution": {"stage_1": 0, "stage_2": 0, "stage_3": 0},
                    "total_documents": 0,
                    "total_trainings": 0
                }
            
            client = await db.clients.find_one({"id": current_user.client_id})
            client_documents = await db.documents.count_documents({"client_id": current_user.client_id})
            client_trainings = await db.trainings.count_documents({"client_id": current_user.client_id})
            
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
                "total_trainings": client_trainings
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
    current_user: User = Depends(get_current_user)
):
    """Upload document file to Google Cloud Storage and save metadata to database"""
    
    logging.info(f"📤 Upload document request - User: {current_user.role} - Client: {client_id} - File: {file.filename}")
    
    # Check file size (500MB limit)
    if file.size and file.size > 500 * 1024 * 1024:  # 500MB
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 500MB.")
    
    logging.info(f"📦 File size: {file.size / 1024 / 1024:.2f}MB")
    
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
        
        # Upload to Google Cloud Storage
        upload_result = await gcs_service.upload_file(
            file_content=file_content,
            filename=file.filename,
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
            "file_size": upload_result["file_size"],
            "file_url": upload_result["url"],
            "uploaded_by": current_user.clerk_user_id,
            "created_at": datetime.utcnow(),
            "mock_upload": upload_result.get("mock", False)
        }
        
        await db.documents.insert_one(document_data)
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document_data["id"],
            "file_url": upload_result["url"],
            "file_size": upload_result["file_size"],
            "mock_upload": upload_result.get("mock", False)
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
        # Generate signed URL for secure access
        if document.get("mock_upload", False) or not gcs_service or not gcs_service.client:
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

# Chunked Upload Endpoints
@api_router.post("/upload-chunk")
async def upload_chunk(
    file_chunk: UploadFile = File(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    upload_id: str = Form(...),
    original_filename: str = Form(...),
    client_id: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload a file chunk"""
    try:
        logging.info(f"📦 Chunk upload: {chunk_index + 1}/{total_chunks} for upload_id: {upload_id}")
        
        # Create temp directory for chunks if not exists
        import tempfile
        temp_dir = f"/tmp/chunks_{upload_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save chunk to temporary file
        chunk_path = f"{temp_dir}/chunk_{chunk_index:04d}"
        with open(chunk_path, "wb") as chunk_file:
            content = await file_chunk.read()
            chunk_file.write(content)
        
        logging.info(f"✅ Chunk {chunk_index + 1} saved: {len(content)} bytes")
        
        # Store chunk metadata in database for tracking
        chunk_record = {
            "upload_id": upload_id,
            "chunk_index": chunk_index,
            "chunk_path": chunk_path,
            "chunk_size": len(content),
            "uploaded_at": datetime.utcnow(),
            "original_filename": original_filename
        }
        
        await db.upload_chunks.insert_one(chunk_record)
        
        return {
            "message": f"Chunk {chunk_index + 1}/{total_chunks} uploaded successfully",
            "upload_id": upload_id,
            "chunk_index": chunk_index
        }
        
    except Exception as e:
        logging.error(f"❌ Chunk upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chunk upload failed: {str(e)}")

@api_router.post("/finalize-upload")
async def finalize_upload(
    upload_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Finalize chunked upload by combining chunks"""
    try:
        upload_id = upload_data.get("upload_id")
        total_chunks = upload_data.get("total_chunks")
        filename = upload_data.get("filename")
        file_size = upload_data.get("file_size")
        
        logging.info(f"🔗 Finalizing upload: {upload_id} with {total_chunks} chunks")
        
        # Get all chunks for this upload
        chunks = await db.upload_chunks.find({
            "upload_id": upload_id
        }).sort("chunk_index", 1).to_list(length=total_chunks)
        
        if len(chunks) != total_chunks:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing chunks: expected {total_chunks}, got {len(chunks)}"
            )
        
        # Combine chunks into final file
        temp_dir = f"/tmp/chunks_{upload_id}"
        final_file_path = f"/tmp/final_{upload_id}_{filename}"
        
        with open(final_file_path, "wb") as final_file:
            for chunk in chunks:
                chunk_path = chunk["chunk_path"]
                with open(chunk_path, "rb") as chunk_file:
                    final_file.write(chunk_file.read())
        
        # Upload final file to GCS
        with open(final_file_path, "rb") as final_file:
            file_content = final_file.read()
            
        # Generate file path and upload
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        gcs_filename = f"documents/{filename}_{int(datetime.now().timestamp() * 1000)}.{file_extension}"
        
        upload_result = await gcs_service.upload_file(
            file_content=file_content,
            file_name=gcs_filename,
            content_type=f"application/{file_extension}"
        )
        
        # Cleanup temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        os.remove(final_file_path)
        
        # Remove chunk records
        await db.upload_chunks.delete_many({"upload_id": upload_id})
        
        logging.info(f"✅ Chunked upload finalized: {gcs_filename}")
        
        return {
            "message": "File upload completed successfully",
            "file_path": gcs_filename,
            "file_size": file_size,
            "upload_id": upload_id
        }
        
    except Exception as e:
        logging.error(f"❌ Upload finalization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload finalization failed: {str(e)}")

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

# Include the router in the main app
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()