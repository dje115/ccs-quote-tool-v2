#!/usr/bin/env python3
"""
Storage Service
Handles file storage using MinIO (S3-compatible object storage)
"""

from typing import Optional, BinaryIO, Dict, Any
from minio import Minio
from minio.error import S3Error
from minio.commonconfig import Tags
from datetime import timedelta
import logging
from io import BytesIO

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage with MinIO"""
    
    def __init__(self):
        """Initialize MinIO client"""
        # MinIO configuration (defaults for development)
        self.endpoint = getattr(settings, 'MINIO_ENDPOINT', 'minio:9000')
        self.access_key = getattr(settings, 'MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = getattr(settings, 'MINIO_SECRET_KEY', 'minioadmin123')
        self.secure = getattr(settings, 'MINIO_SECURE', False)  # False for development
        self.region = getattr(settings, 'MINIO_REGION', None)
        
        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
            region=self.region
        )
        
        # Ensure default bucket exists
        self.default_bucket = getattr(settings, 'MINIO_BUCKET', 'ccs-quote-tool')
        self._ensure_bucket_exists(self.default_bucket)
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """Ensure bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    async def upload_file(
        self,
        file_data: bytes | BinaryIO,
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to MinIO
        
        Args:
            file_data: File data as bytes or file-like object
            object_name: Object name (path) in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            content_type: MIME type of the file
            metadata: Optional metadata dictionary
        
        Returns:
            Object name (path) of uploaded file
        """
        try:
            bucket = bucket_name or self.default_bucket
            self._ensure_bucket_exists(bucket)
            
            # Convert bytes to BytesIO if needed
            if isinstance(file_data, bytes):
                file_obj = BytesIO(file_data)
                length = len(file_data)
            else:
                file_obj = file_data
                file_obj.seek(0, 2)  # Seek to end
                length = file_obj.tell()
                file_obj.seek(0)  # Reset to start
            
            # Upload file
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=file_obj,
                length=length,
                content_type=content_type or 'application/octet-stream',
                metadata=metadata or {}
            )
            
            logger.info(f"File uploaded successfully: {bucket}/{object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def download_file(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> bytes:
        """
        Download a file from MinIO
        
        Args:
            object_name: Object name (path) in bucket
            bucket_name: Bucket name (defaults to configured bucket)
        
        Returns:
            File data as bytes
        """
        try:
            bucket = bucket_name or self.default_bucket
            
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def delete_file(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> bool:
        """
        Delete a file from MinIO
        
        Args:
            object_name: Object name (path) in bucket
            bucket_name: Bucket name (defaults to configured bucket)
        
        Returns:
            True if deleted successfully
        """
        try:
            bucket = bucket_name or self.default_bucket
            self.client.remove_object(bucket, object_name)
            logger.info(f"File deleted: {bucket}/{object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def get_presigned_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate a presigned URL for temporary access
        
        Args:
            object_name: Object name (path) in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            expires: Expiration time for the URL
        
        Returns:
            Presigned URL string
        """
        try:
            bucket = bucket_name or self.default_bucket
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=expires
            )
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    async def file_exists(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> bool:
        """
        Check if a file exists
        
        Args:
            object_name: Object name (path) in bucket
            bucket_name: Bucket name (defaults to configured bucket)
        
        Returns:
            True if file exists
        """
        try:
            bucket = bucket_name or self.default_bucket
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False


# Global storage service instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service

