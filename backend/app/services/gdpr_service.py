#!/usr/bin/env python3
"""
GDPR Compliance Service

COMPLIANCE: Service for GDPR compliance including policy generation, SAR processing, and data collection tracking.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.gdpr import (
    DataCollectionRecord, PrivacyPolicy, SubjectAccessRequest,
    DataCollectionPurpose, SARStatus
)
from app.models.tenant import Tenant, User, Customer, Contact
from app.models.helpdesk import Ticket, TicketComment
from app.models.quotes import Quote
from app.models.sales import SalesActivity
from app.core.config import settings

logger = logging.getLogger(__name__)


class GDPRService:
    """Service for GDPR compliance operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_privacy_policy(
        self,
        tenant_id: str,
        use_ai: bool = True,
        custom_prompt: Optional[str] = None
    ) -> PrivacyPolicy:
        """
        Generate a privacy policy using AI based on data collection records
        
        Args:
            tenant_id: Tenant ID
            use_ai: Whether to use AI generation (default: True)
            custom_prompt: Optional custom prompt for AI generation
            
        Returns:
            Generated PrivacyPolicy
        """
        import uuid
        
        # Get data collection records for tenant
        stmt = select(DataCollectionRecord).where(
            DataCollectionRecord.tenant_id == tenant_id
        )
        result = self.db.execute(stmt)
        records = result.scalars().all()
        
        if use_ai:
            # Build prompt from data collection records
            data_summary = self._build_data_collection_summary(records)
            
            prompt = custom_prompt or f"""
Generate a comprehensive GDPR-compliant privacy policy for a SaaS CRM and quoting platform.

Data Collection Summary:
{data_summary}

The policy should include:
1. Introduction and company information
2. What data we collect and why
3. Legal basis for processing
4. How we use the data
5. Data retention periods
6. Data sharing and third parties
7. Data subject rights (access, rectification, erasure, etc.)
8. Security measures
9. Contact information for data protection officer
10. How to make a Subject Access Request

Make it clear, comprehensive, and GDPR Article 13/14 compliant.
"""
            
            # Use AI service to generate policy
            try:
                from app.services.ai_service import AIService
                ai_service = AIService()
                
                response = ai_service.generate_completion(
                    system_prompt="You are a legal compliance expert specializing in GDPR and data protection. Generate clear, comprehensive privacy policies.",
                    user_prompt=prompt,
                    model=settings.OPENAI_MODEL
                )
                
                policy_content = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                logger.error(f"AI policy generation failed: {e}")
                policy_content = self._generate_template_policy(records)
        else:
            policy_content = self._generate_template_policy(records)
        
        # Get latest version number
        stmt = select(PrivacyPolicy).where(
            PrivacyPolicy.tenant_id == tenant_id
        ).order_by(PrivacyPolicy.created_at.desc())
        result = self.db.execute(stmt)
        latest = result.scalars().first()
        
        version = "1.0"
        if latest:
            try:
                current_version = float(latest.version)
                version = f"{current_version + 0.1:.1f}"
            except ValueError:
                version = "1.0"
        
        # Create policy
        policy = PrivacyPolicy(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            version=version,
            title=f"Privacy Policy v{version}",
            content=policy_content,
            is_active=True,
            generated_by_ai=use_ai,
            generation_prompt=prompt if use_ai else None,
            effective_date=datetime.now(timezone.utc),
            next_review_date=datetime.now(timezone.utc) + timedelta(days=365)
        )
        
        # Deactivate old policies
        stmt = select(PrivacyPolicy).where(
            and_(
                PrivacyPolicy.tenant_id == tenant_id,
                PrivacyPolicy.is_active == True
            )
        )
        result = self.db.execute(stmt)
        for old_policy in result.scalars().all():
            old_policy.is_active = False
        
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        
        return policy
    
    def _build_data_collection_summary(self, records: List[DataCollectionRecord]) -> str:
        """Build a summary of data collection from records"""
        if not records:
            return "No specific data collection records found. Using standard SaaS data collection practices."
        
        summary_parts = []
        for record in records:
            summary_parts.append(
                f"- {record.data_category} ({record.data_type}): "
                f"Purpose: {record.purpose}, Legal Basis: {record.legal_basis}"
            )
        
        return "\n".join(summary_parts)
    
    def _generate_template_policy(self, records: List[DataCollectionRecord]) -> str:
        """Generate a template privacy policy without AI"""
        return f"""
# Privacy Policy

## 1. Introduction
This privacy policy explains how we collect, use, and protect your personal data in accordance with GDPR.

## 2. Data We Collect
{self._build_data_collection_summary(records)}

## 3. Legal Basis
We process your data based on: contract performance, legal obligations, legitimate interests, and consent where applicable.

## 4. Your Rights
You have the right to:
- Access your data
- Rectify inaccurate data
- Erasure of your data
- Data portability
- Object to processing
- Restrict processing

## 5. Contact
For data protection inquiries, contact: {settings.SMTP_FROM_EMAIL}
"""
    
    def create_sar(
        self,
        tenant_id: str,
        requestor_email: str,
        requestor_name: Optional[str] = None,
        requested_data_types: Optional[List[str]] = None
    ) -> SubjectAccessRequest:
        """
        Create a Subject Access Request
        
        Args:
            tenant_id: Tenant ID
            requestor_email: Email of person making the request
            requestor_name: Optional name
            requested_data_types: Optional list of data types requested
            
        Returns:
            Created SubjectAccessRequest
        """
        import uuid
        
        # Check if requestor is a user
        stmt = select(User).where(
            and_(
                User.email == requestor_email,
                User.tenant_id == tenant_id
            )
        )
        result = self.db.execute(stmt)
        user = result.scalars().first()
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Calculate due date (30 days from now per GDPR)
        due_date = datetime.now(timezone.utc) + timedelta(days=30)
        
        sar = SubjectAccessRequest(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            requestor_email=requestor_email,
            requestor_name=requestor_name,
            requestor_id=user.id if user else None,
            status=SARStatus.PENDING.value,
            requested_data_types=requested_data_types or [],
            request_date=datetime.now(timezone.utc),
            due_date=due_date,
            verification_token=verification_token,
            verified=False
        )
        
        self.db.add(sar)
        self.db.commit()
        self.db.refresh(sar)
        
        # Send verification email
        try:
            from app.services.email_service import get_email_service
            email_service = get_email_service()
            
            verification_url = f"{settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else 'http://localhost:3000'}/compliance/sar/verify?token={verification_token}"
            
            email_body = f"""
            <html>
            <body>
                <h2>Subject Access Request Verification</h2>
                <p>Hello {requestor_name or requestor_email},</p>
                <p>You have submitted a Subject Access Request. Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_url}">Verify Email Address</a></p>
                <p>Or copy and paste this link: {verification_url}</p>
                <p>This link will expire in 7 days.</p>
            </body>
            </html>
            """
            
            # Note: This would need to be async, but for now we'll log it
            logger.info(f"SAR verification email should be sent to {requestor_email}")
        except Exception as e:
            logger.error(f"Failed to send SAR verification email: {e}")
        
        return sar
    
    def generate_sar_export(self, sar_id: str) -> Dict[str, Any]:
        """
        Generate data export for a Subject Access Request
        
        Args:
            sar_id: Subject Access Request ID
            
        Returns:
            Dictionary containing all user data
        """
        stmt = select(SubjectAccessRequest).where(SubjectAccessRequest.id == sar_id)
        result = self.db.execute(stmt)
        sar = result.scalar_one_or_none()
        
        if not sar:
            raise ValueError("Subject Access Request not found")
        
        if not sar.verified:
            raise ValueError("SAR must be verified before export")
        
        export_data = {
            "request_id": sar.id,
            "export_date": datetime.now(timezone.utc).isoformat(),
            "requestor_email": sar.requestor_email,
            "requestor_name": sar.requestor_name,
        }
        
        # If requestor is a user, get their data
        if sar.requestor_id:
            user_stmt = select(User).where(User.id == sar.requestor_id)
            user_result = self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if user:
                export_data["user_data"] = {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                }
        
        # Get customer data if email matches
        customer_stmt = select(Customer).where(
            and_(
                Customer.tenant_id == sar.tenant_id,
                Customer.main_email == sar.requestor_email
            )
        )
        customer_result = self.db.execute(customer_stmt)
        customers = customer_result.scalars().all()
        
        if customers:
            export_data["customer_data"] = []
            for customer in customers:
                export_data["customer_data"].append({
                    "id": customer.id,
                    "company_name": customer.company_name,
                    "main_email": customer.main_email,
                    "main_phone": customer.main_phone,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None,
                })
        
        # Get tickets
        if sar.requestor_id:
            ticket_stmt = select(Ticket).where(
                and_(
                    Ticket.tenant_id == sar.tenant_id,
                    Ticket.customer_id.in_([c.id for c in customers]) if customers else False
                )
            )
            ticket_result = self.db.execute(ticket_stmt)
            tickets = ticket_result.scalars().all()
            
            if tickets:
                export_data["tickets"] = []
                for ticket in tickets:
                    export_data["tickets"].append({
                        "id": ticket.id,
                        "subject": ticket.subject,
                        "description": ticket.description,
                        "status": ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status),
                        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                    })
        
        # Get quotes
        if customers:
            quote_stmt = select(Quote).where(
                and_(
                    Quote.tenant_id == sar.tenant_id,
                    Quote.customer_id.in_([c.id for c in customers])
                )
            )
            quote_result = self.db.execute(quote_stmt)
            quotes = quote_result.scalars().all()
            
            if quotes:
                export_data["quotes"] = []
                for quote in quotes:
                    export_data["quotes"].append({
                        "id": quote.id,
                        "quote_number": quote.quote_number,
                        "total_amount": float(quote.total_amount) if quote.total_amount else None,
                        "status": quote.status.value if hasattr(quote.status, 'value') else str(quote.status),
                        "created_at": quote.created_at.isoformat() if quote.created_at else None,
                    })
        
        return export_data
