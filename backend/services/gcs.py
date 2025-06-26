from google.cloud import storage
from google.oauth2 import service_account
import os
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GoogleCloudStorage:
    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        self.project_id = os.getenv("GCS_PROJECT_ID")
        self.credentials_path = os.getenv("GCS_CREDENTIALS_PATH")
        
        # Initialize client
        try:
            logger.info(f"GCS_BUCKET_NAME: {self.bucket_name}")
            logger.info(f"GCS_PROJECT_ID: {self.project_id}")
            logger.info(f"GCS_CREDENTIALS_PATH: {self.credentials_path}")
            logger.info(f"Credentials path exists: {os.path.exists(self.credentials_path) if self.credentials_path else False}")
            
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = storage.Client(credentials=credentials, project=self.project_id)
                logger.info("GCS client initialized successfully")
            else:
                # For development without credentials, use mock mode
                logger.warning("GCS credentials not found, using mock mode")
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
            
            # Don't make public - use signed URLs instead for security
            logger.info(f"File uploaded to: {blob_name}")
            
            # Generate signed URL for secure access
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
            if not self.bucket:
                return f"https://storage.googleapis.com/{self.bucket_name or 'mock-bucket'}/{file_path}"
                
            blob = self.bucket.blob(file_path)
            url = blob.generate_signed_url(
                expiration=datetime.utcnow() + timedelta(hours=expiration_hours),
                method='GET'
            )
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return f"https://storage.googleapis.com/{self.bucket_name or 'mock-bucket'}/{file_path}"

# Global instance
gcs_service = GoogleCloudStorage()