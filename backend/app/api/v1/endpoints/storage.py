"""
Storage endpoints for file upload/download
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import io
import logging

from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.tenant import User, UserRole
from app.services.storage_service import get_storage_service

router = APIRouter()
logger = logging.getLogger(__name__)


class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    object_name: Optional[str] = None
    url: Optional[str] = None
    message: str


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    bucket: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload a file to MinIO storage
    
    Requires authentication. Files are stored in the configured bucket.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        storage_service = get_storage_service()
        
        # Read file data
        file_data = await file.read()
        
        # Generate object name (use tenant_id/user_id for organization)
        object_name = f"{current_user.tenant_id}/{current_user.id}/{file.filename}"
        
        # Upload file
        uploaded_name = await storage_service.upload_file(
            file_data=file_data,
            object_name=object_name,
            bucket_name=bucket,
            content_type=file.content_type
        )
        
        # Generate presigned URL for access
        url = storage_service.get_presigned_url(uploaded_name, bucket)
        
        return UploadResponse(
            success=True,
            object_name=uploaded_name,
            url=url,
            message="File uploaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to upload file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/download/{object_name:path}")
async def download_file(
    object_name: str,
    bucket: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Download a file from MinIO storage
    
    Requires authentication. Users can only download files from their tenant.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        storage_service = get_storage_service()
        
        # Verify file belongs to user's tenant (security check)
        if not object_name.startswith(f"{current_user.tenant_id}/"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Download file
        file_data = await storage_service.download_file(
            object_name=object_name,
            bucket_name=bucket
        )
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={object_name.split('/')[-1]}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.delete("/delete/{object_name:path}")
async def delete_file(
    object_name: str,
    bucket: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a file from MinIO storage
    
    Requires authentication. Users can only delete files from their tenant.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        storage_service = get_storage_service()
        
        # Verify file belongs to user's tenant (security check)
        if not object_name.startswith(f"{current_user.tenant_id}/"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete file
        success = await storage_service.delete_file(
            object_name=object_name,
            bucket_name=bucket
        )
        
        if success:
            return {"success": True, "message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/list")
async def list_files(
    prefix: Optional[str] = None,
    bucket: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List files in MinIO storage
    
    Requires authentication. Users can only list files from their tenant.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        storage_service = get_storage_service()
        
        # Ensure prefix is tenant-scoped for security
        tenant_prefix = f"{current_user.tenant_id}/"
        if prefix:
            # Ensure prefix starts with tenant_id
            if not prefix.startswith(tenant_prefix):
                prefix = f"{tenant_prefix}{prefix}"
        else:
            prefix = tenant_prefix
        
        # List files
        files = await storage_service.list_files(
            prefix=prefix,
            bucket_name=bucket
        )
        
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Failed to list files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/info/{object_name:path}")
async def get_file_info(
    object_name: str,
    bucket: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get file metadata from MinIO storage
    
    Requires authentication. Users can only access files from their tenant.
    
    PERFORMANCE: Uses AsyncSession to prevent blocking the event loop.
    """
    try:
        storage_service = get_storage_service()
        
        # Verify file belongs to user's tenant (security check)
        if not object_name.startswith(f"{current_user.tenant_id}/"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get file info
        file_info = await storage_service.get_file_info(
            object_name=object_name,
            bucket_name=bucket
        )
        
        if file_info:
            return {
                "success": True,
                "file": file_info
            }
        else:
            raise HTTPException(status_code=404, detail="File not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


