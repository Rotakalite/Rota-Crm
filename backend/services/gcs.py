from google.cloud import storage
from google.oauth2 import service_account
import os
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GoogleCloudStorage:
    def __init__(self):
        # Hardcoded values for debugging
        self.bucket_name = "rota-crm-documents"
        self.project_id = "rota-crm-storage"
        self.credentials_path = "/app/backend/gcs-credentials.json"
        
        # Also try environment variables
        env_bucket = os.getenv("GCS_BUCKET_NAME")
        env_project = os.getenv("GCS_PROJECT_ID")
        env_creds = os.getenv("GCS_CREDENTIALS_PATH")
        
        if env_bucket:
            self.bucket_name = env_bucket
        if env_project:
            self.project_id = env_project
        if env_creds:
            self.credentials_path = env_creds
        
        # Initialize client
        try:
            logger.info(f"🔍 GCS Initialization:")
            logger.info(f"   BUCKET_NAME: {self.bucket_name}")
            logger.info(f"   PROJECT_ID: {self.project_id}")
            logger.info(f"   CREDENTIALS_PATH: {self.credentials_path}")
            logger.info(f"   Credentials file exists: {os.path.exists(self.credentials_path) if self.credentials_path else False}")
            
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = storage.Client(credentials=credentials, project=self.project_id)
                logger.info("✅ GCS client initialized successfully")
            else:
                # For development without credentials, use mock mode
                logger.warning("❌ GCS credentials not found, using mock mode")
                self.client = None
                
            if self.client and self.bucket_name:
                self.bucket = self.client.bucket(self.bucket_name)
            else:
                self.bucket = None
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage: {e}")
            self.client = None
            self.bucket = None

    async def upload_file(self, file_content: bytes, filename: str, content_type: str = "application/octet-stream") -> dict:
        """
        Upload file to Google Cloud Storage
        Returns: dict with url, file_path, and file_size
        """
        try:
            if not self.bucket:
                # Mock mode for development
                mock_url = f"https://storage.googleapis.com/{self.bucket_name or 'mock-bucket'}/{filename}"
                return {
                    "url": mock_url,
                    "file_path": f"/documents/{filename}",
                    "file_size": len(file_content),
                    "mock": True
                }
            
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
            blob_name = f"documents/{datetime.now().strftime('%Y/%m')}/{unique_filename}"
            
            # Upload to GCS
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(file_content, content_type=content_type)
            
            # Make blob publicly readable since bucket is public
            try:
                blob.make_public()
                logger.info(f"File made public: {blob.public_url}")
                file_url = blob.public_url
            except Exception as e:
                logger.warning(f"Could not make file public, using signed URL: {e}")
                # Fallback to signed URL
                file_url = blob.generate_signed_url(
                    expiration=datetime.utcnow() + timedelta(hours=24*7),  # 7 days
                    method='GET'
                )
            
            return {
                "url": file_url,
                "file_path": blob_name,
                "file_size": len(file_content),
                "mock": False
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {e}")
            # Fallback to mock
            mock_url = f"https://storage.googleapis.com/{self.bucket_name or 'mock-bucket'}/{filename}"
            return {
                "url": mock_url,
                "file_path": f"/documents/{filename}",
                "file_size": len(file_content),
                "mock": True,
                "error": str(e)
            }

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Google Cloud Storage"""
        try:
            if not self.bucket:
                logger.info(f"Mock delete: {file_path}")
                return True
                
            blob = self.bucket.blob(file_path)
            blob.delete()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from GCS: {e}")
            return False

    async def get_signed_url(self, file_path: str, expiration_hours: int = 1) -> str:
        """Generate signed URL for private file access"""
        try:
            # Clean up file path - remove leading slash if present
            clean_path = file_path.lstrip('/')
            
            if not self.bucket:
                return f"https://storage.googleapis.com/{self.bucket_name or 'mock-bucket'}/{clean_path}"
                
            blob = self.bucket.blob(clean_path)
            url = blob.generate_signed_url(
                expiration=datetime.utcnow() + timedelta(hours=expiration_hours),
                method='GET'
            )
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            clean_path = file_path.lstrip('/')
            return f"https://storage.googleapis.com/{self.bucket_name or 'mock-bucket'}/{clean_path}"

# Global instance
gcs_service = GoogleCloudStorage()