from fastapi import FastAPI, APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from enum import Enum
import requests
import jwt
from jwt import PyJWKClient
import json

# Import GCS after other imports to avoid path issues
import sys
sys.path.append(os.path.dirname(__file__))
from services.gcs import gcs_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Clerk configuration
CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY')
CLERK_JWKS_URL = os.environ.get('CLERK_JWKS_URL')

# Create the main app without a prefix
app = FastAPI()

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

class ServiceType(str, Enum):
    SITUATION_ANALYSIS = "Mevcut durum analizi"
    TEAM_DETERMINATION = "Çalışma ekibinin belirlenmesi"
    PROJECT_PLANNING = "Proje planının oluşturulması"
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
        logging.info(f"🔍 Received token: {token[:50]}...")
        
        # Get the signing key from Clerk
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        logging.info("✅ Got signing key from Clerk")
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=None,  # Clerk doesn't use audience
            options={"verify_aud": False}
        )
        
        clerk_user_id = payload.get("sub")
        if not clerk_user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        logging.info(f"✅ Token verified successfully for user: {clerk_user_id}")
        return clerk_user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

async def get_current_user(clerk_user_id: str = Depends(verify_token)):
    user = await db.users.find_one({"clerk_user_id": clerk_user_id})
    if not user:
        logging.error(f"❌ User not found in database for clerk_user_id: {clerk_user_id}")
        raise HTTPException(status_code=404, detail="User not found in database")
    
    logging.info(f"✅ User found: {user.get('role')} - {user.get('name', 'Unknown')}")
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
    if current_user.role == UserRole.ADMIN:
        # Admin can see all clients
        clients = await db.clients.find().to_list(1000)
        return [Client(**client) for client in clients]
    else:
        # Client can only see their own record
        if not current_user.client_id:
            return []
        client = await db.clients.find_one({"id": current_user.client_id})
        return [Client(**client)] if client else []

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
    
    # Find the document
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
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
        if document.get("mock_upload", False):
            # Return the stored URL for mock uploads
            download_url = document.get("file_url", "#")
        else:
            # Generate signed URL for real GCS files
            download_url = await gcs_service.get_signed_url(document["file_path"], expiration_hours=24)
        
        return {
            "download_url": download_url,
            "filename": document["name"],
            "file_size": document["file_size"],
            "document_type": document["document_type"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
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