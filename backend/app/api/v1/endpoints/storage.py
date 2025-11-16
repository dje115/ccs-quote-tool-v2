"""
Storage endpoints for file upload/download
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import io

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.tenant import User, UserRole
from app.services.storage_service import get_storage_service

router = APIRouter()


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
    db: Session = Depends(get_db)
):
    """
    Upload a file to MinIO storage
    
    Requires authentication. Files are stored in the configured bucket.
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
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/download/{object_name:path}")
async def download_file(
    object_name: str,
    bucket: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a file from MinIO storage
    
    Requires authentication. Users can only download files from their tenant.
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


@router.delete("/delete/{object_name:path}")
async def delete_file(
    object_name: str,
    bucket: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file from MinIO storage
    
    Requires authentication. Users can only delete files from their tenant.
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
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

