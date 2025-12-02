#!/usr/bin/env python3
"""
Quote document management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_current_tenant
from app.models.quotes import Quote
from app.models.quote_documents import QuoteDocument, QuoteDocumentVersion, DocumentType
from app.models.tenant import User, Tenant
from app.services.quote_versioning_service import QuoteVersioningService
from app.services.quote_builder_service import QuoteBuilderService

router = APIRouter()


class DocumentUpdate(BaseModel):
    content: Dict[str, Any]
    changes_summary: Optional[str] = None


class DocumentVersionCreate(BaseModel):
    changes_summary: Optional[str] = None


@router.get("/quotes/{quote_id}/documents")
async def get_quote_documents(
    quote_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get all documents for a quote"""
    # Verify quote exists and belongs to tenant
    quote_result = await db.execute(
        select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_tenant.id
        )
    )
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Get all documents
    documents_result = await db.execute(
        select(QuoteDocument).where(
            QuoteDocument.quote_id == quote_id,
            QuoteDocument.tenant_id == current_tenant.id
        )
    )
    documents = documents_result.scalars().all()
    
    return {
        "success": True,
        "documents": [
            {
                "id": doc.id,
                "document_type": doc.document_type,
                "version": doc.version,
                "content": doc.content,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            for doc in documents
        ]
    }


@router.get("/quotes/{quote_id}/documents/{document_type}")
async def get_quote_document(
    quote_id: str,
    document_type: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get a specific document for a quote"""
    # Verify quote exists
    quote_result = await db.execute(
        select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_tenant.id
        )
    )
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Get document
    document_result = await db.execute(
        select(QuoteDocument).where(
            QuoteDocument.quote_id == quote_id,
            QuoteDocument.document_type == document_type,
            QuoteDocument.tenant_id == current_tenant.id
        )
    )
    document = document_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document of type '{document_type}' not found"
        )
    
    return {
        "success": True,
        "document": {
            "id": document.id,
            "document_type": document.document_type,
            "version": document.version,
            "content": document.content,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }
    }


@router.put("/quotes/{quote_id}/documents/{document_type}")
async def update_quote_document(
    quote_id: str,
    document_type: str,
    update: DocumentUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Update a quote document"""
    # Verify quote exists
    quote_result = await db.execute(
        select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_tenant.id
        )
    )
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Get document
    document_result = await db.execute(
        select(QuoteDocument).where(
            QuoteDocument.quote_id == quote_id,
            QuoteDocument.document_type == document_type,
            QuoteDocument.tenant_id == current_tenant.id
        )
    )
    document = document_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document of type '{document_type}' not found"
        )
    
    # Create version before updating
    from app.core.database import SessionLocal
    sync_db = SessionLocal()
    try:
        versioning_service = QuoteVersioningService(sync_db, current_tenant.id)
        versioning_service.create_version(
            document=document,
            changes_summary=update.changes_summary,
            user_id=current_user.id
        )
    finally:
        sync_db.close()
    
    # Update document content
    document.content = update.content
    
    await db.commit()
    await db.refresh(document)
    
    return {
        "success": True,
        "document": {
            "id": document.id,
            "document_type": document.document_type,
            "version": document.version,
            "content": document.content,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None
        }
    }


@router.post("/quotes/{quote_id}/documents/{document_type}/version")
async def create_document_version(
    quote_id: str,
    document_type: str,
    version_data: DocumentVersionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Create a new version of a document"""
    # Verify quote exists
    quote_result = await db.execute(
        select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_tenant.id
        )
    )
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Get document
    document_result = await db.execute(
        select(QuoteDocument).where(
            QuoteDocument.quote_id == quote_id,
            QuoteDocument.document_type == document_type,
            QuoteDocument.tenant_id == current_tenant.id
        )
    )
    document = document_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document of type '{document_type}' not found"
        )
    
    # Create version
    from app.core.database import SessionLocal
    sync_db = SessionLocal()
    try:
        versioning_service = QuoteVersioningService(sync_db, current_tenant.id)
        version = versioning_service.create_version(
            document=document,
            changes_summary=version_data.changes_summary,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "version": {
                "id": version.id,
                "version": version.version,
                "changes_summary": version.changes_summary,
                "created_at": version.created_at.isoformat() if version.created_at else None
            }
        }
    finally:
        sync_db.close()


@router.get("/quotes/{quote_id}/documents/{document_type}/versions")
async def get_document_versions(
    quote_id: str,
    document_type: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Get version history for a document"""
    # Verify quote exists
    quote_result = await db.execute(
        select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_tenant.id
        )
    )
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Get document
    document_result = await db.execute(
        select(QuoteDocument).where(
            QuoteDocument.quote_id == quote_id,
            QuoteDocument.document_type == document_type,
            QuoteDocument.tenant_id == current_tenant.id
        )
    )
    document = document_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document of type '{document_type}' not found"
        )
    
    # Get versions
    versions_result = await db.execute(
        select(QuoteDocumentVersion).where(
            QuoteDocumentVersion.document_id == document.id
        ).order_by(QuoteDocumentVersion.version.desc())
    )
    versions = versions_result.scalars().all()
    
    return {
        "success": True,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "changes_summary": v.changes_summary,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "created_by": v.created_by
            }
            for v in versions
        ]
    }


@router.post("/quotes/{quote_id}/documents/{document_type}/rollback/{version}")
async def rollback_document_version(
    quote_id: str,
    document_type: str,
    version: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Rollback a document to a specific version"""
    # Verify quote exists
    quote_result = await db.execute(
        select(Quote).where(
            Quote.id == quote_id,
            Quote.tenant_id == current_tenant.id
        )
    )
    quote = quote_result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Get document
    document_result = await db.execute(
        select(QuoteDocument).where(
            QuoteDocument.quote_id == quote_id,
            QuoteDocument.document_type == document_type,
            QuoteDocument.tenant_id == current_tenant.id
        )
    )
    document = document_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document of type '{document_type}' not found"
        )
    
    # Rollback
    from app.core.database import SessionLocal
    sync_db = SessionLocal()
    try:
        versioning_service = QuoteVersioningService(sync_db, current_tenant.id)
        success = versioning_service.rollback_to_version(
            document=document,
            target_version=version,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version {version} not found"
            )
        
        await db.refresh(document)
        
        return {
            "success": True,
            "message": f"Document rolled back to version {version}",
            "document": {
                "id": document.id,
                "version": document.version,
                "content": document.content
            }
        }
    finally:
        sync_db.close()

