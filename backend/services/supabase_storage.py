import os
import logging
from supabase import create_client, Client
from typing import Optional
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseStorage:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "documents")
        
        if not self.url or not self.service_key:
            logger.error("❌ Supabase credentials not found!")
            self.client = None
            return
            
        try:
            # Use service key for backend operations
            self.client: Client = create_client(self.url, self.service_key)
            logger.info(f"✅ Supabase client initialized - Bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self.client = None

    async def upload_file(self, file_content: bytes, filename: str, user_id: str, content_type: str = None) -> dict:
        """Upload file to Supabase Storage"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        try:
            # Create user-specific path
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = f"{user_id}/{unique_filename}"
            
            logger.info(f"📤 Uploading file to Supabase: {file_path}")
            
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "upsert": False  # Don't overwrite existing files
                }
            )
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Upload failed: {response.error}")
            
            logger.info(f"✅ File uploaded successfully: {file_path}")
            
            return {
                "file_path": file_path,
                "original_filename": filename,
                "file_size": len(file_content),
                "supabase_upload": True
            }
            
        except Exception as e:
            logger.error(f"❌ Supabase upload failed: {e}")
            raise Exception(f"File upload failed: {str(e)}")

    async def download_file(self, file_path: str) -> bytes:
        """Download file from Supabase Storage"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        try:
            logger.info(f"📥 Downloading file from Supabase: {file_path}")
            
            response = self.client.storage.from_(self.bucket_name).download(file_path)
            
            if not response:
                raise Exception("File not found")
            
            logger.info(f"✅ File downloaded successfully: {file_path}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Supabase download failed: {e}")
            raise Exception(f"File download failed: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase Storage"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        try:
            logger.info(f"🗑️ Deleting file from Supabase: {file_path}")
            
            response = self.client.storage.from_(self.bucket_name).remove([file_path])
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Delete failed: {response.error}")
            
            logger.info(f"✅ File deleted successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Supabase delete failed: {e}")
            raise Exception(f"File deletion failed: {str(e)}")

    async def get_signed_url(self, file_path: str, expiration_seconds: int = 3600) -> str:
        """Get signed URL for private file access"""
        if not self.client:
            raise Exception("Supabase client not initialized")
        
        try:
            logger.info(f"🔐 Creating signed URL for: {file_path}")
            
            response = self.client.storage.from_(self.bucket_name).create_signed_url(
                path=file_path,
                expires_in=expiration_seconds
            )
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Signed URL creation failed: {response.error}")
            
            signed_url = response.get('signedURL')
            if not signed_url:
                raise Exception("No signed URL returned")
            
            logger.info(f"✅ Signed URL created successfully")
            return signed_url
            
        except Exception as e:
            logger.error(f"❌ Signed URL creation failed: {e}")
            raise Exception(f"Signed URL creation failed: {str(e)}")

# Global instance
supabase_storage = SupabaseStorage()