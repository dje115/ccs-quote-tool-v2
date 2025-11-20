#!/usr/bin/env python3
"""
Quote Versioning Service

Handles document versioning:
- Auto-version on save
- Version history with diffs
- Rollback capability
"""

import logging
import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.quote_documents import QuoteDocument, QuoteDocumentVersion

logger = logging.getLogger(__name__)


class QuoteVersioningService:
    """
    Service for quote document versioning
    
    Features:
    - Auto-version on save
    - Version history
    - Diff generation
    - Rollback capability
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    def create_version(
        self,
        document: QuoteDocument,
        changes_summary: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> QuoteDocumentVersion:
        """
        Create a new version of a document
        
        Args:
            document: Document to version
            changes_summary: Summary of changes
            user_id: User creating the version
        
        Returns:
            Created version record
        """
        import uuid
        
        # Get next version number
        max_version = self.db.query(QuoteDocumentVersion).filter(
            QuoteDocumentVersion.document_id == document.id
        ).order_by(QuoteDocumentVersion.version.desc()).first()
        
        next_version = (max_version.version + 1) if max_version else 1
        
        # Create version record
        version = QuoteDocumentVersion(
            id=str(uuid.uuid4()),
            document_id=document.id,
            version=next_version,
            content=document.content.copy() if isinstance(document.content, dict) else document.content,
            changes_summary=changes_summary,
            created_by=user_id
        )
        
        self.db.add(version)
        
        # Update document version
        document.version = next_version
        
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def get_version_history(
        self,
        document_id: str
    ) -> List[QuoteDocumentVersion]:
        """
        Get version history for a document
        
        Args:
            document_id: Document ID
        
        Returns:
            List of versions ordered by version number
        """
        return self.db.query(QuoteDocumentVersion).filter(
            QuoteDocumentVersion.document_id == document_id
        ).order_by(QuoteDocumentVersion.version.desc()).all()
    
    def rollback_to_version(
        self,
        document: QuoteDocument,
        target_version: int,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Rollback document to a specific version
        
        Args:
            document: Document to rollback
            target_version: Version number to rollback to
            user_id: User performing rollback
        
        Returns:
            True if successful
        """
        # Get target version
        version = self.db.query(QuoteDocumentVersion).filter(
            QuoteDocumentVersion.document_id == document.id,
            QuoteDocumentVersion.version == target_version
        ).first()
        
        if not version:
            return False
        
        # Create new version with rollback content
        self.create_version(
            document=document,
            changes_summary=f"Rolled back to version {target_version}",
            user_id=user_id
        )
        
        # Restore content
        document.content = version.content.copy() if isinstance(version.content, dict) else version.content
        
        self.db.commit()
        
        return True
    
    def get_version_diff(
        self,
        document_id: str,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """
        Get diff between two versions
        
        Args:
            document_id: Document ID
            version1: First version number
            version2: Second version number
        
        Returns:
            Dict with diff information
        """
        v1 = self.db.query(QuoteDocumentVersion).filter(
            QuoteDocumentVersion.document_id == document_id,
            QuoteDocumentVersion.version == version1
        ).first()
        
        v2 = self.db.query(QuoteDocumentVersion).filter(
            QuoteDocumentVersion.document_id == document_id,
            QuoteDocumentVersion.version == version2
        ).first()
        
        if not v1 or not v2:
            return {"error": "One or both versions not found"}
        
        # Simple diff - compare JSON structures
        # In production, you might want to use a proper diff library
        diff = {
            "version1": version1,
            "version2": version2,
            "changes": self._compare_content(v1.content, v2.content)
        }
        
        return diff
    
    def _compare_content(
        self,
        content1: Dict[str, Any],
        content2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Compare two content structures and return changes"""
        changes = []
        
        # Compare sections
        sections1 = content1.get("sections", [])
        sections2 = content2.get("sections", [])
        
        # Simple comparison - in production, use proper diff algorithm
        if json.dumps(sections1, sort_keys=True) != json.dumps(sections2, sort_keys=True):
            changes.append({
                "type": "sections_changed",
                "description": "Document sections were modified"
            })
        
        return changes

