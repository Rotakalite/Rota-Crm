import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from typing import Optional
import uuid
from datetime import datetime
from bson import ObjectId
from io import BytesIO

logger = logging.getLogger(__name__)

class MongoGridFS:
    def __init__(self):
        self.mongo_url = os.getenv("MONGO_URL")
        self.db_name = os.getenv("DB_NAME")
        
        print(f"🔍 Debug - MONGO_URL: {self.mongo_url}")
        print(f"🔍 Debug - DB_NAME: {self.db_name}")
        
        if not self.mongo_url or not self.db_name:
            logger.error("❌ MongoDB credentials not found!")
            self.client = None
            self.db = None
            self.fs = None
            return
            
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            # GridFS bucket for file storage
            self.fs = AsyncIOMotorGridFSBucket(self.db, bucket_name="documents")
            logger.info(f"✅ MongoDB GridFS initialized - Database: {self.db_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB GridFS: {e}")
            self.client = None
            self.db = None
            self.fs = None

    async def upload_file(self, file_content: bytes, filename: str, user_id: str, content_type: str = None, metadata: dict = None) -> dict:
        """Upload file to MongoDB GridFS"""
        if not self.fs:
            raise Exception("MongoDB GridFS not initialized")
        
        try:
            # Create metadata
            file_metadata = {
                "user_id": user_id,
                "original_filename": filename,
                "content_type": content_type or "application/octet-stream",
                "upload_date": datetime.utcnow(),
                "file_size": len(file_content)
            }
            
            # Add custom metadata if provided
            if metadata:
                file_metadata.update(metadata)
            
            # Generate unique filename
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
            
            logger.info(f"📤 Uploading file to MongoDB GridFS: {unique_filename}")
            
            # Upload to GridFS
            file_stream = BytesIO(file_content)
            file_id = await self.fs.upload_from_stream(
                filename=unique_filename,
                source=file_stream,
                metadata=file_metadata
            )
            
            logger.info(f"✅ File uploaded successfully to GridFS - ID: {file_id}")
            
            return {
                "file_id": str(file_id),
                "filename": unique_filename,
                "original_filename": filename,
                "file_size": len(file_content),
                "gridfs_upload": True,
                "metadata": file_metadata
            }
            
        except Exception as e:
            logger.error(f"❌ MongoDB GridFS upload failed: {e}")
            raise Exception(f"File upload failed: {str(e)}")

    async def download_file(self, file_id: str) -> tuple[bytes, dict]:
        """Download file from MongoDB GridFS"""
        if not self.fs:
            raise Exception("MongoDB GridFS not initialized")
        
        try:
            logger.info(f"📥 Downloading file from GridFS: {file_id}")
            
            # Convert string ID to ObjectId
            object_id = ObjectId(file_id)
            
            # Download file data
            file_stream = BytesIO()
            await self.fs.download_to_stream(object_id, file_stream)
            file_content = file_stream.getvalue()
            
            # Get file metadata
            file_info = await self.fs.find_one({"_id": object_id})
            if not file_info:
                raise Exception("File metadata not found")
            
            metadata = {
                "filename": file_info.filename,
                "original_filename": file_info.metadata.get("original_filename", file_info.filename),
                "content_type": file_info.metadata.get("content_type", "application/octet-stream"),
                "file_size": file_info.length,
                "upload_date": file_info.upload_date,
                "user_id": file_info.metadata.get("user_id")
            }
            
            logger.info(f"✅ File downloaded successfully from GridFS")
            return file_content, metadata
            
        except Exception as e:
            logger.error(f"❌ MongoDB GridFS download failed: {e}")
            raise Exception(f"File download failed: {str(e)}")

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from MongoDB GridFS"""
        if not self.fs:
            raise Exception("MongoDB GridFS not initialized")
        
        try:
            logger.info(f"🗑️ Deleting file from GridFS: {file_id}")
            
            # Convert string ID to ObjectId
            object_id = ObjectId(file_id)
            
            # Delete from GridFS
            await self.fs.delete(object_id)
            
            logger.info(f"✅ File deleted successfully from GridFS")
            return True
            
        except Exception as e:
            logger.error(f"❌ MongoDB GridFS delete failed: {e}")
            raise Exception(f"File deletion failed: {str(e)}")

    async def list_user_files(self, user_id: str) -> list:
        """List all files for a specific user"""
        if not self.fs:
            raise Exception("MongoDB GridFS not initialized")
        
        try:
            logger.info(f"📋 Listing files for user: {user_id}")
            
            files = []
            async for file_info in self.fs.find({"metadata.user_id": user_id}):
                files.append({
                    "file_id": str(file_info._id),
                    "filename": file_info.filename,
                    "original_filename": file_info.metadata.get("original_filename", file_info.filename),
                    "file_size": file_info.length,
                    "upload_date": file_info.upload_date,
                    "content_type": file_info.metadata.get("content_type")
                })
            
            logger.info(f"✅ Found {len(files)} files for user {user_id}")
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to list user files: {e}")
            raise Exception(f"File listing failed: {str(e)}")

    async def get_file_info(self, file_id: str) -> dict:
        """Get file information without downloading content"""
        if not self.fs:
            raise Exception("MongoDB GridFS not initialized")
        
        try:
            object_id = ObjectId(file_id)
            file_info = await self.fs.find_one({"_id": object_id})
            
            if not file_info:
                raise Exception("File not found")
            
            return {
                "file_id": str(file_info._id),
                "filename": file_info.filename,
                "original_filename": file_info.metadata.get("original_filename", file_info.filename),
                "file_size": file_info.length,
                "upload_date": file_info.upload_date,
                "content_type": file_info.metadata.get("content_type"),
                "user_id": file_info.metadata.get("user_id"),
                "metadata": file_info.metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get file info: {e}")
            raise Exception(f"Get file info failed: {str(e)}")

# Global instance
mongo_gridfs = MongoGridFS()